from __future__ import annotations
import atexit, logging, queue, random, threading, time
from typing import Any, Dict
import httpx
from .core import b64url_decode, extract_client_ip, gzip_event, redact_event, sign, SchemaUserConfig, INGEST_ENDPOINT

_logger = logging.getLogger("kohi")
_pools: list["SenderPool"] = []

def _shutdown_all():
  for pool in _pools: pool.shutdown(timeout=5.0)
atexit.register(_shutdown_all)

class SenderPool:
  def __init__(self, *, cfg: SchemaUserConfig, workers: int = 5, max_queue: int = 5000, retry_count: int = 3, timeout_s: float = 10.0):
    self.cfg, self.retry_count, self.timeout_s = cfg, retry_count, timeout_s
    self._secret = b64url_decode(self.cfg.secret_key)
    self.q: queue.Queue[Dict[str, Any]] = queue.Queue(maxsize=max_queue)
    self.stop, self._shutdown_complete = threading.Event(), threading.Event()
    self.threads = [threading.Thread(target=self._worker, name=f"kohi-sender-{i}", daemon=True) for i in range(workers)]
    for t in self.threads: t.start()
    _pools.append(self)

  def submit(self, event: Dict[str, Any]) -> None:
    try: self.q.put_nowait(event)
    except queue.Full: _logger.warning("kohi monitor queue is full; dropping event")

  def shutdown(self, timeout: float = 30.0) -> None:
    if self._shutdown_complete.is_set(): return
    self.stop.set()
    try: self.q.join()
    except: pass
    deadline = time.time() + timeout
    for t in self.threads: t.join(timeout=max(0.01, deadline - time.time()))
    self._shutdown_complete.set()

  def _new_client(self) -> httpx.Client:
    return httpx.Client(timeout=httpx.Timeout(self.timeout_s), limits=httpx.Limits(max_connections=100, max_keepalive_connections=20))

  def _worker(self) -> None:
    client: httpx.Client | None = None
    try:
      client = self._new_client()
      while not self.stop.is_set():
        try: event = self.q.get(timeout=0.2)
        except queue.Empty: continue
        try: self._send(client, event)
        finally: self.q.task_done()
      while True:
        try: event = self.q.get_nowait()
        except queue.Empty: break
        try: self._send(client, event)
        finally: self.q.task_done()
    finally:
      if client: client.close()

  def _send(self, client: httpx.Client, event: Dict[str, Any]) -> bool:
    request_headers = dict(event.get("request_headers") or {})
    peer_ip = request_headers.pop("x-kohi-peer-ip", None)
    client_ip = extract_client_ip(request_headers, peer_ip)
    sanitized = {**event, "request_headers": request_headers}
    body = gzip_event(redact_event(sanitized))
    sig = sign(self._secret, body)
    headers = {"Content-Type": "application/json", "Content-Encoding": "gzip", "X-Project-Key": self.cfg.project_key, "X-Signature": sig}
    if client_ip: headers["X-Client-IP"] = client_ip
    backoff = 0.25
    for attempt in range(self.retry_count + 1):
      try:
        r = client.post(INGEST_ENDPOINT, content=body, headers=headers)
        if r.is_success: return True
        if r.status_code not in (408, 429) and not (500 <= r.status_code < 600): return False
      except httpx.RequestError: pass
      if attempt < self.retry_count:
        time.sleep(backoff * (0.8 + 0.4 * random.random()))
        backoff = min(backoff * 2, 2.0)
    return False
