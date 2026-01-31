from __future__ import annotations
import logging
from typing import Any, Dict, Optional
from .core import SchemaUserConfig
from .send import SenderPool

VERSION = "0.1.2"
logger = logging.getLogger("kohi.monitor")

class Monitor:
  def __init__(self, app: Optional[Any] = None, *, project_key: str, secret_key: str, enabled: bool = True):
    if not enabled:
      self.cfg, self._pool = None, None
      return
    self.cfg = SchemaUserConfig(project_key=project_key, secret_key=secret_key, enabled=enabled)
    self._pool = SenderPool(cfg=self.cfg, workers=5, timeout_s=10.0)
    self._auto_instrument(app)

  def _auto_instrument(self, app) -> None:
    if app is None: return
    try:
      app_type = type(app).__name__
      if app_type == "FastAPI":
        from .integrations.fastapi import instrument
        instrument(self, app, VERSION)
      elif app_type == "Flask":
        from .integrations.flask import instrument
        instrument(self, app, VERSION)
      else: logger.warning(f"unsupported app type: {app_type}")
    except ImportError as e: logger.error(f"missing integration: {e}")
    except Exception as e: logger.error(f"instrumentation failed: {e}")

  def is_enabled(self) -> bool: return self._pool is not None
  def add_event(self, event: Dict[str, Any]) -> None:
    if self._pool: self._pool.submit(event)
  def shutdown(self, timeout: float = 30.0) -> None:
    if self._pool: self._pool.shutdown(timeout)
  def close(self) -> None: self.shutdown()
