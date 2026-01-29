import httpx
import pytest

from signalzero_sdk import SignalZeroPartnerClient, SignalZeroPublicClient
from signalzero_sdk.errors import SignalZeroError


def test_public_wallet_status_builds_request_and_returns_json():
  address = "0x" + "a" * 40

  def handler(request: httpx.Request) -> httpx.Response:
    assert request.method == "GET"
    assert request.url.path == f"/v1/wallet/{address}/status"
    assert request.url.params.get("chainId") == "84532"
    return httpx.Response(
      200,
      json={
        "hasGenesis": False,
        "genesisTimestamp": None,
        "totalSignals": 0,
        "lastSignalTimestamp": None,
        "activeStreak": 0,
        "longestStreak": 0,
        "continuityStatus": "DORMANT",
      },
    )

  transport = httpx.MockTransport(handler)
  client = SignalZeroPublicClient(base_url="https://example.test", transport=transport)

  status = client.wallet_status(address, chain_id=84532)
  assert status["hasGenesis"] is False
  assert status["continuityStatus"] == "DORMANT"


def test_partner_client_raises_typed_error():
  address = "0x" + "b" * 40

  def handler(request: httpx.Request) -> httpx.Response:
    assert request.headers.get("x-api-key") == "sz_test_123"
    return httpx.Response(403, json={"error": "genesis_required"})

  transport = httpx.MockTransport(handler)
  client = SignalZeroPartnerClient(base_url="https://example.test", api_key="sz_test_123", transport=transport)

  with pytest.raises(SignalZeroError) as e:
    client.wallet_history(address)

  assert e.value.status_code == 403
  assert e.value.error == "genesis_required"


def test_retries_on_retryable_status():
  address = "0x" + "c" * 40
  calls = {"n": 0}

  def handler(request: httpx.Request) -> httpx.Response:
    calls["n"] += 1
    if calls["n"] == 1:
      return httpx.Response(429, json={"error": "rate_limited"})
    return httpx.Response(
      200,
      json={
        "hasGenesis": True,
        "genesisTimestamp": None,
        "totalSignals": 1,
        "lastSignalTimestamp": None,
        "activeStreak": 1,
        "longestStreak": 1,
        "continuityStatus": "ACTIVE",
      },
    )

  transport = httpx.MockTransport(handler)
  client = SignalZeroPublicClient(
    base_url="https://example.test",
    transport=transport,
    retries=1,
    retry_backoff_seconds=0,
  )

  status = client.wallet_status(address)
  assert calls["n"] == 2
  assert status["hasGenesis"] is True
  assert status["continuityStatus"] == "ACTIVE"
