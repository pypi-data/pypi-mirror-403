from __future__ import annotations
import time
from typing import Any, Dict, List, TYPE_CHECKING
from starlette.requests import Request
from starlette.responses import StreamingResponse
from ..core import body_from_content_type, normalize_headers, normalize_peer_ip, try_json, MAX_RESPONSE_BODY

if TYPE_CHECKING:
  from ..main import Monitor

def _now_ms() -> int: return int(time.time() * 1000)

def _to_bytes(chunks: List[Any], limit: int = MAX_RESPONSE_BODY) -> bytes:
  buf = bytearray()
  for c in chunks:
    chunk = c if isinstance(c, (bytes, bytearray)) else str(c).encode("utf-8", errors="replace")
    remaining = limit - len(buf)
    if remaining <= 0: break
    buf += chunk[:remaining]
  return bytes(buf)

async def _iter_chunks(chunks: List[Any]):
  for c in chunks: yield c

async def _capture_body(response: StreamingResponse) -> bytes:
  chunks = [chunk async for chunk in response.body_iterator]
  response.body_iterator = _iter_chunks(chunks)
  return _to_bytes(chunks)

def _build_event(url: str, endpoint: str, method: str, status: int, req_headers: Dict, req_body: Any, res_headers: Dict, res_body: Any, latency: int, version: str) -> Dict[str, Any]:
  return {"url": url, "endpoint": endpoint, "method": method, "status_code": status, "request_headers": {**req_headers, "x-kohi-version": f"python:{version}"}, "request_body": req_body, "response_headers": res_headers, "response_body": res_body, "duration_ms": latency}

def instrument(monitor: "Monitor", app, version: str) -> None:
  @app.middleware("http")
  async def _kohi_mw(request: Request, call_next):
    start = _now_ms()
    req_headers = normalize_headers(dict(request.headers))
    peer_ip = normalize_peer_ip(request.client.host if request.client else None)
    if peer_ip: req_headers["x-kohi-peer-ip"] = peer_ip
    try: req_body = try_json(await request.body())
    except (ValueError, TypeError, UnicodeDecodeError): req_body = None
    url, path = str(request.url), request.url.path
    endpoint = f"{path}?{request.url.query}" if request.url.query else path
    try:
      response: StreamingResponse = await call_next(request)
      try: raw = await _capture_body(response)
      except (TypeError, RuntimeError): raw = b""
      res_headers = normalize_headers(dict(response.headers))
      try: res_body = body_from_content_type(res_headers.get("content-type", ""), raw)
      except (ValueError, TypeError, UnicodeDecodeError): res_body = None
      monitor.add_event(_build_event(url, endpoint, request.method, response.status_code, req_headers, req_body, res_headers, res_body, _now_ms() - start, version))
      return response
    except Exception as exc:
      status = getattr(exc, "status_code", 500)
      monitor.add_event(_build_event(url, endpoint, request.method, status, req_headers, req_body, {}, {"error": str(exc)}, _now_ms() - start, version))
      raise
