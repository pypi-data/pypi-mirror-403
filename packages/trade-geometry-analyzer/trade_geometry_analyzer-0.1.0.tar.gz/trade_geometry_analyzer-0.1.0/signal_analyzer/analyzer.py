"""Main orchestrator for trade geometry analysis."""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Literal
from dataclasses import dataclass, field

from .core.events import signal_to_events
from .core.trades import TradeSet, compute_trade_paths


@dataclass
class AnalysisConfig:
    """Configuration for analysis run."""

    H: int = 10
    """Forward horizon in bars"""

    sections: List[str] = field(default_factory=lambda: ["A", "B", "C", "D", "E", "F"])
    """Sections to run: A, B, C, D, E, F"""

    # Section A: Geometry
    trim_method: str | None = "iqr"
    trim_k: float = 1.5

    # Section B: Frontiers
    risk_q: float = 0.9
    opp_q: float = 0.8

    # Section D: TP/SL Feasibility
    tp_grid: np.ndarray | None = None
    sl_grid: np.ndarray | None = None
    store_paths: bool = True

    # Section E: Vol Normalization
    vol_col: str | None = None
    n_regimes: int = 3

    # Section F: Clusters
    n_clusters: int | None = None


@dataclass
class AnalysisResult:
    """Container for analysis results."""

    config: AnalysisConfig
    long_trades: TradeSet | None = None
    short_trades: TradeSet | None = None

    # Section results
    section_a: Dict[str, Any] = field(default_factory=dict)
    section_b: Dict[str, Any] = field(default_factory=dict)
    section_c: Dict[str, Any] = field(default_factory=dict)
    section_d: Dict[str, Any] = field(default_factory=dict)
    section_e: Dict[str, Any] = field(default_factory=dict)
    section_f: Dict[str, Any] = field(default_factory=dict)

    # Plots
    plots: Dict[str, Any] = field(default_factory=dict)


def analyze(
    ohlc: pd.DataFrame,
    sig_col: str = "sig",
    config: AnalysisConfig | None = None,
    open_col: str = "Open",
    high_col: str = "High",
    low_col: str = "Low",
    sig_mode: Literal["transitions", "levels"] = "transitions",
) -> AnalysisResult:
    """
    Run complete trade geometry analysis.

    Parameters
    ----------
    ohlc : pd.DataFrame
        OHLC data with signal column
    sig_col : str
        Signal column name
    config : AnalysisConfig, optional
        Analysis configuration. If None, uses defaults.
    open_col, high_col, low_col : str
        OHLC column names
    sig_mode : {'transitions', 'levels'}
        Signal interpretation mode

    Returns
    -------
    AnalysisResult
        Container with all analysis results and plots

    Notes
    -----
    This is the main entry point for the library. It orchestrates all
    analysis sections based on the configuration.
    """
    if config is None:
        config = AnalysisConfig()

    result = AnalysisResult(config=config)

    # 1. Extract entry events
    events = signal_to_events(ohlc, sig_col=sig_col, mode=sig_mode)

    # 2. Compute trade paths
    long_trades = None
    short_trades = None

    if len(events["enter_long"]) > 0:
        long_trades = compute_trade_paths(
            ohlc,
            events["enter_long"],
            config.H,
            side="long",
            open_col=open_col,
            high_col=high_col,
            low_col=low_col,
            vol_col=config.vol_col,
            store_paths=config.store_paths,
        )
        result.long_trades = long_trades

    if len(events["enter_short"]) > 0:
        short_trades = compute_trade_paths(
            ohlc,
            events["enter_short"],
            config.H,
            side="short",
            open_col=open_col,
            high_col=high_col,
            low_col=low_col,
            vol_col=config.vol_col,
            store_paths=config.store_paths,
        )
        result.short_trades = short_trades

    # 3. Run sections
    if "A" in config.sections:
        _run_section_a(result, config)

    if "B" in config.sections:
        _run_section_b(result, config)

    if "C" in config.sections:
        _run_section_c(result, config)

    if "D" in config.sections:
        _run_section_d(result, config)

    if "E" in config.sections and config.vol_col is not None:
        _run_section_e(result, config)

    if "F" in config.sections:
        _run_section_f(result, config)

    return result


def _run_section_a(result: AnalysisResult, config: AnalysisConfig):
    """Run Section A: Geometry Overview."""
    from .analysis.geometry import scatter_data, marginals, geometry_metrics
    from .plotting.scatter import plot_scatter, plot_marginals

    result.section_a["long"] = {}
    result.section_a["short"] = {}

    if result.long_trades is not None:
        result.section_a["long"]["scatter"] = scatter_data(
            result.long_trades, trim_method=config.trim_method, trim_k=config.trim_k
        )
        result.section_a["long"]["marginals"] = marginals(result.long_trades)
        result.section_a["long"]["metrics"] = geometry_metrics(result.long_trades)

    if result.short_trades is not None:
        result.section_a["short"]["scatter"] = scatter_data(
            result.short_trades, trim_method=config.trim_method, trim_k=config.trim_k
        )
        result.section_a["short"]["marginals"] = marginals(result.short_trades)
        result.section_a["short"]["metrics"] = geometry_metrics(result.short_trades)

    # Plots
    result.plots["scatter"] = plot_scatter(
        result.long_trades,
        result.short_trades,
        H=config.H,
        trim_method=config.trim_method,
        trim_k=config.trim_k,
    )

    result.plots["marginals"] = plot_marginals(
        result.long_trades, result.short_trades
    )


def _run_section_b(result: AnalysisResult, config: AnalysisConfig):
    """Run Section B: Frontiers."""
    from .analysis.frontiers import compute_frontiers
    from .plotting.frontiers import plot_frontiers

    if result.long_trades is not None:
        result.section_b["long"] = compute_frontiers(
            result.long_trades, risk_q=config.risk_q, opp_q=config.opp_q
        )

    if result.short_trades is not None:
        result.section_b["short"] = compute_frontiers(
            result.short_trades, risk_q=config.risk_q, opp_q=config.opp_q
        )

    result.plots["frontiers"] = plot_frontiers(
        result.long_trades,
        result.short_trades,
        risk_q=config.risk_q,
        opp_q=config.opp_q,
    )


def _run_section_c(result: AnalysisResult, config: AnalysisConfig):
    """Run Section C: Ordering."""
    from .analysis.ordering import (
        ordering_proportions,
        trailing_suitability,
        needs_room,
    )
    from .plotting.scatter import plot_scatter_by_ordering

    if result.long_trades is not None:
        result.section_c["long"] = {
            "proportions": ordering_proportions(result.long_trades),
            "trailing_suitability": trailing_suitability(result.long_trades),
            "needs_room": needs_room(result.long_trades),
        }

    if result.short_trades is not None:
        result.section_c["short"] = {
            "proportions": ordering_proportions(result.short_trades),
            "trailing_suitability": trailing_suitability(result.short_trades),
            "needs_room": needs_room(result.short_trades),
        }

    result.plots["ordering"] = plot_scatter_by_ordering(
        result.long_trades, result.short_trades, H=config.H
    )


def _run_section_d(result: AnalysisResult, config: AnalysisConfig):
    """Run Section D: TP/SL Feasibility."""
    from .analysis.feasibility import hit_matrix, ev_proxy, find_best_zones
    from .plotting.heatmaps import plot_heatmap_prob, plot_heatmap_ev

    if not config.store_paths:
        print("Warning: Section D requires store_paths=True. Skipping.")
        return

    if result.long_trades is not None:
        hit_data = hit_matrix(
            result.long_trades, config.tp_grid or np.linspace(0.1, 5, 25), config.sl_grid or np.linspace(0.1, 5, 25)
        )
        ev_data = ev_proxy(hit_data)
        best_zones = find_best_zones(ev_data)

        result.section_d["long"] = {
            "hit_matrix": hit_data,
            "ev_proxy": ev_data,
            "best_zones": best_zones,
        }

    if result.short_trades is not None:
        hit_data = hit_matrix(
            result.short_trades, config.tp_grid or np.linspace(0.1, 5, 25), config.sl_grid or np.linspace(0.1, 5, 25)
        )
        ev_data = ev_proxy(hit_data)
        best_zones = find_best_zones(ev_data)

        result.section_d["short"] = {
            "hit_matrix": hit_data,
            "ev_proxy": ev_data,
            "best_zones": best_zones,
        }

    result.plots["heatmap_prob"] = plot_heatmap_prob(
        result.long_trades, result.short_trades
    )

    result.plots["heatmap_ev"] = plot_heatmap_ev(
        result.long_trades, result.short_trades
    )


def _run_section_e(result: AnalysisResult, config: AnalysisConfig):
    """Run Section E: Volatility Normalization."""
    from .analysis.volnorm import (
        normalize_metrics,
        split_by_vol_regime,
        compare_percent_vs_volnorm,
    )
    from .plotting.volnorm import plot_percent_vs_volnorm, plot_regime_comparison

    if result.long_trades is not None and result.long_trades.vol_at_entry is not None:
        result.section_e["long"] = {
            "comparison": compare_percent_vs_volnorm(result.long_trades),
            "regimes": split_by_vol_regime(result.long_trades, n_regimes=config.n_regimes),
        }

        result.plots["volnorm_long"] = plot_percent_vs_volnorm(result.long_trades)
        result.plots["regime_long"] = plot_regime_comparison(
            result.long_trades, n_regimes=config.n_regimes
        )

    if result.short_trades is not None and result.short_trades.vol_at_entry is not None:
        result.section_e["short"] = {
            "comparison": compare_percent_vs_volnorm(result.short_trades),
            "regimes": split_by_vol_regime(result.short_trades, n_regimes=config.n_regimes),
        }

        result.plots["volnorm_short"] = plot_percent_vs_volnorm(result.short_trades)
        result.plots["regime_short"] = plot_regime_comparison(
            result.short_trades, n_regimes=config.n_regimes
        )


def _run_section_f(result: AnalysisResult, config: AnalysisConfig):
    """Run Section F: Clusters."""
    from .analysis.clusters import cluster_trades, cluster_summary
    from .plotting.clusters import plot_clusters_scatter, plot_cluster_stats

    if result.long_trades is not None:
        cluster_result = cluster_trades(result.long_trades, n_clusters=config.n_clusters)
        result.section_f["long"] = {
            "clusters": cluster_result,
            "summary": cluster_summary(result.long_trades, cluster_result),
        }

        result.plots["clusters_long"] = plot_clusters_scatter(
            result.long_trades, cluster_result
        )
        result.plots["cluster_stats_long"] = plot_cluster_stats(
            result.long_trades, cluster_result
        )

    if result.short_trades is not None:
        cluster_result = cluster_trades(result.short_trades, n_clusters=config.n_clusters)
        result.section_f["short"] = {
            "clusters": cluster_result,
            "summary": cluster_summary(result.short_trades, cluster_result),
        }

        result.plots["clusters_short"] = plot_clusters_scatter(
            result.short_trades, cluster_result
        )
        result.plots["cluster_stats_short"] = plot_cluster_stats(
            result.short_trades, cluster_result
        )
