"""Core modules for trade geometry analysis."""

from .events import signal_to_events
from .trades import TradeSet, compute_trade_paths
from .utils import trim_iqr, trim_percentile, knee_point

__all__ = [
    "signal_to_events",
    "TradeSet",
    "compute_trade_paths",
    "trim_iqr",
    "trim_percentile",
    "knee_point",
]
