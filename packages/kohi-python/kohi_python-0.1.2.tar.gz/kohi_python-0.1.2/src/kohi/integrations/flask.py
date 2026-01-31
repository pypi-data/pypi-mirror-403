from __future__ import annotations
import time
from typing import TYPE_CHECKING
from flask import g, request
from ..core import body_from_content_type, normalize_headers, normalize_peer_ip, try_json, MAX_RESPONSE_BODY

if TYPE_CHECKING:
  from ..main import Monitor

def _now_ms() -> int: return int(time.time() * 1000)

def instrument(monitor: "Monitor", app, version: str) -> None:
  @app.before_request
  def _kohi_before():
    g._kohi_start = _now_ms()
    try: request.get_data(cache=True, as_text=False)
    except (RuntimeError, ValueError): pass

  @app.after_request
  def _kohi_after(response):
    try:
      g._kohi_logged = True
      start = getattr(g, "_kohi_start", _now_ms())
      req_headers = normalize_headers(dict(request.headers))
      res_headers = normalize_headers(dict(response.headers))
      peer_ip = normalize_peer_ip(request.remote_addr)
      if peer_ip: req_headers["x-kohi-peer-ip"] = peer_ip
      try: req_body = try_json(request.get_data(cache=True))
      except (ValueError, TypeError, UnicodeDecodeError): req_body = None
      try:
        raw = response.get_data(as_text=False)
        res_body = body_from_content_type(res_headers.get("content-type", ""), raw[:MAX_RESPONSE_BODY])
      except (ValueError, TypeError, RuntimeError): res_body = None
      path, query = request.path, request.query_string.decode("utf-8") if request.query_string else ""
      endpoint = f"{path}?{query}" if query else path
      monitor.add_event({"url": request.url, "endpoint": endpoint, "method": request.method, "status_code": response.status_code, "request_headers": {**req_headers, "x-kohi-version": f"python:{version}"}, "request_body": req_body, "response_headers": res_headers, "response_body": res_body, "duration_ms": _now_ms() - start})
    except Exception: pass
    return response

  @app.teardown_request
  def _kohi_teardown(exc):
    if exc is None or getattr(g, "_kohi_logged", False): return
    try:
      start = getattr(g, "_kohi_start", _now_ms())
      req_headers = normalize_headers(dict(request.headers))
      peer_ip = normalize_peer_ip(request.remote_addr)
      if peer_ip: req_headers["x-kohi-peer-ip"] = peer_ip
      try: req_body = try_json(request.get_data(cache=True))
      except Exception: req_body = None
      path, query = request.path, request.query_string.decode("utf-8") if request.query_string else ""
      endpoint = f"{path}?{query}" if query else path
      monitor.add_event({"url": request.url, "endpoint": endpoint, "method": request.method, "status_code": 500, "request_headers": {**req_headers, "x-kohi-version": f"python:{version}"}, "request_body": req_body, "response_headers": {}, "response_body": {"error": str(exc)}, "duration_ms": _now_ms() - start})
    except Exception: pass

  @app.errorhandler(Exception)
  def _kohi_error_handler(err):
    if getattr(g, "_kohi_logged", False):
      return err
    try:
      g._kohi_logged = True
      start = getattr(g, "_kohi_start", _now_ms())
      req_headers = normalize_headers(dict(request.headers))
      peer_ip = normalize_peer_ip(request.remote_addr)
      if peer_ip: req_headers["x-kohi-peer-ip"] = peer_ip
      try: req_body = try_json(request.get_data(cache=True))
      except Exception: req_body = None
      path, query = request.path, request.query_string.decode("utf-8") if request.query_string else ""
      endpoint = f"{path}?{query}" if query else path
      monitor.add_event({"url": request.url, "endpoint": endpoint, "method": request.method, "status_code": 500, "request_headers": {**req_headers, "x-kohi-version": f"python:{version}"}, "request_body": req_body, "response_headers": {}, "response_body": {"error": str(err)}, "duration_ms": _now_ms() - start})
    except Exception: pass
    return {"error": "internal server error"}, 500
