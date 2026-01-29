"""Data provider for Python."""

from __future__ import annotations

from typing import Final

from .data_provider import (
    DataProvider,
    FpmmTransaction,
    HistoryPoint,
    Market,
    MarketToken,
    OffChain,
    OnChain,
    OnchainTrade,
    OrderFilledEvent,
    OrdersIterator,
    Timeseries,
    Trading,
)

__all__ = [
    "DataProvider",
    "OnChain",
    "OffChain",
    "Trading",
    "OrderFilledEvent",
    "FpmmTransaction",
    "OrdersIterator",
    "Market",
    "MarketToken",
    "HistoryPoint",
    "Timeseries",
    "OnchainTrade",
]

__version__: Final[str]
