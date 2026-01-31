from __future__ import annotations
import base64, gzip, hashlib, hmac, ipaddress, json, re
from typing import Any, Dict, Mapping, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator

INGEST_ENDPOINT = "https://kohicorp.com/api/ingest"
SENSITIVE_KEYS = {"password", "secret", "token", "authorization", "api_key", "x-api-key", "apikey", "x-auth-token", "x-access-token", "bearer", "credential", "credentials", "private_key", "private-key", "secret_key", "secret-key"}
EMAIL_KEYS = {"email", "email_address", "emailaddress"}
REDACTION_MASK = "[REDACTED]"
MAX_RESPONSE_BODY = 64 * 1024
IP_HEADERS = ["cf-connecting-ip", "x-vercel-forwarded-for", "x-forwarded-for", "x-real-ip", "x-cluster-client-ip", "fastly-client-ip"]
Redactable = Union[str, int, float, bool, None, list, Mapping[str, Any]]

class SchemaUserConfig(BaseModel):
  model_config = ConfigDict(extra="forbid")
  project_key: str
  secret_key: str = Field(..., min_length=43, max_length=43, repr=False)
  enabled: bool = True
  @field_validator("project_key", mode="before")
  @classmethod
  def check_project_key(cls, v: Any) -> str:
    if not isinstance(v, str): raise TypeError("project_key must be a string")
    if not re.match(r"^pk_[A-Za-z0-9_-]{22}$", v): raise ValueError("project_key must start with 'pk_' followed by 22 base64url characters")
    return v

def try_json(buf: bytes | None):
  if not buf: return None
  try: return json.loads(buf.decode("utf-8"))
  except (json.JSONDecodeError, UnicodeDecodeError): return safe_text(buf)

def safe_text(buf: bytes):
  try: return buf.decode("utf-8")
  except UnicodeDecodeError: return {"base64": buf.hex()}

def body_from_content_type(ct: str, raw: bytes):
  if not raw: return None
  ct = (ct or "").lower()
  if "application/json" in ct:
    try: return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError): return raw.decode("utf-8", errors="ignore")
  if ct.startswith("text/") or "html" in ct or "xml" in ct: return raw.decode("utf-8", errors="ignore")
  return {"base64": raw.hex()}

def normalize_headers(headers: Dict[str, Any] | None) -> Dict[str, str]:
  if not headers: return {}
  out = {}
  for k, v in headers.items():
    if v is None: continue
    out[str(k).lower()] = ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)
  return out

def _norm_ip(v: str) -> str: return v.strip().lstrip("[").rstrip("]")
def _valid_ip(s: str) -> bool:
  try: ipaddress.ip_address(_norm_ip(s)); return True
  except ValueError: return False

def _first_ip(v: str) -> str | None:
  for p in (x.strip().strip('"') for x in v.split(",") if x.strip()):
    if _valid_ip(p): return _norm_ip(p)
  return None

def extract_client_ip(headers: Mapping[str, str], peer_ip: str | None) -> str | None:
  low = {k.lower(): v for k, v in headers.items()}
  for name in IP_HEADERS:
    if (v := low.get(name)) and (ip := _first_ip(v)): return ip
  if (n := normalize_peer_ip(peer_ip)): return n
  return None

def normalize_peer_ip(peer_ip: str | None) -> str | None:
  if not peer_ip: return None
  c = _norm_ip(peer_ip)
  return c if _valid_ip(c) else None

def _mask_email(email: Any) -> str:
  if not isinstance(email, str): return REDACTION_MASK
  at = email.find("@")
  if at < 1: return REDACTION_MASK
  return email[:min(2, at)] + "***" + email[at:]

def redact_any(x: Redactable) -> Redactable:
  if isinstance(x, dict):
    out = {}
    for k, v in x.items():
      key = k.lower() if isinstance(k, str) else k
      out[k] = REDACTION_MASK if key in SENSITIVE_KEYS else _mask_email(v) if key in EMAIL_KEYS else redact_any(v)
    return out
  if isinstance(x, list): return [redact_any(i) for i in x]
  return x

def redact_event(evt: Dict[str, Any]) -> Dict[str, Any]:
  return {"url": evt.get("url", ""), "endpoint": evt.get("endpoint", ""), "method": evt.get("method", ""), "status_code": evt.get("status_code", 0),
          "request_headers": redact_any(normalize_headers(evt.get("request_headers"))), "request_body": redact_any(evt.get("request_body")),
          "response_headers": redact_any(normalize_headers(evt.get("response_headers"))), "response_body": redact_any(evt.get("response_body")), "duration_ms": evt.get("duration_ms", 0)}

def sign(secret: bytes, data: bytes) -> str: return hmac.new(secret, data, hashlib.sha256).hexdigest()
def gzip_event(event: Dict[str, Any]) -> bytes: return gzip.compress(json.dumps(event).encode("utf-8"))
def b64url_decode(s: str) -> bytes: return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
