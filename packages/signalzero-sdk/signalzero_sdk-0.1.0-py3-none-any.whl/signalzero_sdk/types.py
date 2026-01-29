from __future__ import annotations

from typing import List, Literal, Optional, TypedDict


class WalletStatus(TypedDict):
  hasGenesis: bool
  genesisTimestamp: Optional[str]
  totalSignals: int
  lastSignalTimestamp: Optional[str]
  activeStreak: int
  longestStreak: int
  continuityStatus: str


class WalletHistoryEntry(TypedDict):
  day: str
  createdAt: str


class WalletHistory(TypedDict):
  address: str
  chainId: int
  history: List[WalletHistoryEntry]


class ContinuityQuerySnapshot(TypedDict):
  hasGenesis: bool
  genesisTimestamp: Optional[str]
  totalSignals: int
  lastSignalTimestamp: Optional[str]
  activeStreak: int
  longestStreak: int
  continuityStatus: str


ContinuityQueryResult = TypedDict(
  "ContinuityQueryResult",
  {
    "address": str,
    "pass": bool,
    "signalsInWindow": int,
    "snapshot": ContinuityQuerySnapshot,
  },
)


class ContinuityQuerySummary(TypedDict):
  total: int
  passed: int
  failed: int


class ContinuityQueryResponse(TypedDict):
  chainId: int
  fromDay: Optional[str]
  toDay: Optional[str]
  minSignals: int
  results: List[ContinuityQueryResult]
  summary: ContinuityQuerySummary
