from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from .errors import SignalZeroError, parse_error_payload
from .types import ContinuityQueryResponse, WalletHistory, WalletStatus
from .version import __version__


def _normalize_base_url(base_url: str) -> str:
  u = (base_url or "").strip()
  if not u:
    return "https://www.signalzero.ink"
  return u[:-1] if u.endswith("/") else u


def _is_address(value: str) -> bool:
  v = (value or "").strip().lower()
  return v.startswith("0x") and len(v) == 42


@dataclass
class _BaseClient:
  base_url: str = "https://www.signalzero.ink"
  timeout: float = 20.0
  retries: int = 0
  retry_backoff_seconds: float = 0.5
  transport: Optional[httpx.BaseTransport] = None

  def __post_init__(self) -> None:
    self.base_url = _normalize_base_url(self.base_url)
    self._client = httpx.Client(
      timeout=self.timeout,
      headers={"user-agent": f"signalzero-sdk-python/{__version__}"},
      transport=self.transport,
    )

  def close(self) -> None:
    self._client.close()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc, tb):
    self.close()

  def _request(
    self,
    method: str,
    path: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Any = None,
  ) -> Any:
    url = f"{self.base_url}{path}"

    last_error: Optional[SignalZeroError] = None

    for attempt in range(self.retries + 1):
      try:
        res = self._client.request(method, url, headers=headers, params=params, json=json)
      except httpx.TimeoutException as e:
        last_error = SignalZeroError(status_code=0, error="timeout", message=str(e))
        if attempt < self.retries:
          time.sleep(self.retry_backoff_seconds * (2**attempt))
          continue
        raise last_error from e
      except httpx.HTTPError as e:
        last_error = SignalZeroError(status_code=0, error="network_error", message=str(e))
        if attempt < self.retries:
          time.sleep(self.retry_backoff_seconds * (2**attempt))
          continue
        raise last_error from e

      request_id = res.headers.get("x-request-id") or res.headers.get("x-vercel-id")

      if res.status_code >= 400:
        payload: Any = None
        try:
          payload = res.json()
        except Exception:
          payload = res.text

        err, msg = parse_error_payload(payload)
        last_error = SignalZeroError(
          status_code=res.status_code,
          error=err,
          message=msg,
          response_json=payload,
          request_id=request_id,
        )

        retryable = res.status_code == 429 or res.status_code >= 500
        if retryable and attempt < self.retries:
          time.sleep(self.retry_backoff_seconds * (2**attempt))
          continue
        raise last_error

      try:
        return res.json()
      except Exception as e:
        raise SignalZeroError(
          status_code=res.status_code,
          error="invalid_json",
          message=str(e),
          request_id=request_id,
        ) from e

    raise last_error if last_error is not None else SignalZeroError(status_code=0, error="request_failed", message="request_failed")


@dataclass
class SignalZeroPublicClient(_BaseClient):
  def wallet_status(self, address: str, *, chain_id: Optional[int] = None) -> WalletStatus:
    if not _is_address(address):
      raise ValueError("invalid_address")

    params: Dict[str, Any] = {}
    if chain_id is not None:
      params["chainId"] = int(chain_id)

    data = self._request("GET", f"/v1/wallet/{address}/status", params=params)
    return data  # type: ignore[return-value]


@dataclass
class SignalZeroPartnerClient(_BaseClient):
  api_key: str = ""

  def __post_init__(self) -> None:
    super().__post_init__()
    self.api_key = (self.api_key or "").strip()
    if not self.api_key:
      raise ValueError("missing_api_key")

  def _auth_headers(self) -> Dict[str, str]:
    return {"x-api-key": self.api_key}

  def wallet_history(self, address: str, *, limit: int = 200) -> WalletHistory:
    if not _is_address(address):
      raise ValueError("invalid_address")

    params: Dict[str, Any] = {"limit": int(limit)}
    data = self._request(
      "GET",
      f"/v1/wallet/{address}/history",
      params=params,
      headers=self._auth_headers(),
    )
    return data  # type: ignore[return-value]

  def query_continuity(
    self,
    wallets: List[str],
    *,
    from_day: Optional[str] = None,
    to_day: Optional[str] = None,
    min_signals: int = 1,
  ) -> ContinuityQueryResponse:
    normalized = [w.strip().lower() for w in wallets if isinstance(w, str)]
    normalized = [w for w in normalized if _is_address(w)]
    if len(normalized) == 0 or len(normalized) > 500:
      raise ValueError("invalid_wallets")

    body: Dict[str, Any] = {
      "wallets": normalized,
      "minSignals": int(min_signals),
    }
    if from_day is not None:
      body["fromDay"] = from_day
    if to_day is not None:
      body["toDay"] = to_day

    data = self._request(
      "POST",
      "/v1/query/continuity",
      json=body,
      headers={"content-type": "application/json", **self._auth_headers()},
    )
    return data  # type: ignore[return-value]
