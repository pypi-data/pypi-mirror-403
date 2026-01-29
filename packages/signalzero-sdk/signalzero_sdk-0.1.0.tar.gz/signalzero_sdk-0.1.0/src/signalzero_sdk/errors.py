from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class SignalZeroError(Exception):
  status_code: int
  error: Optional[str] = None
  message: str = ""
  response_json: Any = None
  request_id: Optional[str] = None

  def __str__(self) -> str:
    base = f"SignalZeroError(status_code={self.status_code}"
    if self.error:
      base += f", error={self.error}"
    if self.request_id:
      base += f", request_id={self.request_id}"
    base += ")"
    if self.message:
      return f"{base}: {self.message}"
    return base


def parse_error_payload(payload: Any) -> tuple[Optional[str], str]:
  if isinstance(payload, Mapping):
    err = payload.get("error")
    if isinstance(err, str) and err:
      return err, err
    msg = payload.get("message")
    if isinstance(msg, str) and msg:
      return None, msg
  return None, "request_failed"
