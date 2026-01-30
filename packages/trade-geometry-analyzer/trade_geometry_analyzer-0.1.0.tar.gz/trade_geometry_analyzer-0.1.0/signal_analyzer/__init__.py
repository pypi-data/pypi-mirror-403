"""Signal Analyzer: Trade Geometry Diagnostic Engine.

A library for analyzing the post-entry behavior of trading signals.
"""

__version__ = "0.1.0"

# Main API
from .analyzer import analyze, AnalysisConfig, AnalysisResult

# Core
from .core.events import signal_to_events
from .core.trades import TradeSet, compute_trade_paths

__all__ = [
    "analyze",
    "AnalysisConfig",
    "AnalysisResult",
    "signal_to_events",
    "TradeSet",
    "compute_trade_paths",
]
