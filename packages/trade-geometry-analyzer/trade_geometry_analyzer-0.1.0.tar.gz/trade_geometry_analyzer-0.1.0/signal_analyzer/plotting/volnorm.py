"""Visualization for volatility normalization and regime analysis."""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any
from matplotlib.figure import Figure

from ..core.trades import TradeSet
from ..analysis.volnorm import (
    normalize_metrics,
    split_by_vol_regime,
    compare_percent_vs_volnorm,
)
from ..analysis.frontiers import compute_frontiers


def plot_percent_vs_volnorm(
    trades: TradeSet,
    figsize: tuple = (14, 5),
) -> Figure:
    """
    Side-by-side scatter plots: % space vs vol-normalized space.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data (must have vol_at_entry)
    figsize : tuple
        Figure size (width, height)

    Returns
    -------
    Figure
        Matplotlib figure object
    """
    norm_trades = normalize_metrics(trades)

    fig, axes = plt.subplots(1, 2, figsize=figsize)

    # Left: % space
    ax = axes[0]
    ax.scatter(trades.mfe, trades.mae, s=6, alpha=0.3, color="C0")
    ax.axhline(0, color="black", lw=1, ls="--", alpha=0.5)
    ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)
    ax.set_title(f"{trades.side.capitalize()}: Percent Space\nn={trades.n_trades}")
    ax.set_xlabel("MFE (%)")
    ax.set_ylabel("MAE (%)")
    ax.grid(alpha=0.3)

    # Right: Vol-normalized space
    ax = axes[1]
    ax.scatter(norm_trades.mfe, norm_trades.mae, s=6, alpha=0.3, color="C1")
    ax.axhline(0, color="black", lw=1, ls="--", alpha=0.5)
    ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)
    ax.set_title(
        f"{trades.side.capitalize()}: Vol-Normalized Space\nn={norm_trades.n_trades}"
    )
    ax.set_xlabel("MFE (vol units)")
    ax.set_ylabel("MAE (vol units)")
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_regime_comparison(
    trades: TradeSet,
    n_regimes: int = 3,
    figsize: tuple = (14, 5),
) -> Figure:
    """
    Compare trade geometry across volatility regimes.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data (must have vol_at_entry)
    n_regimes : int
        Number of regimes
    figsize : tuple
        Figure size (width, height)

    Returns
    -------
    Figure
        Matplotlib figure object
    """
    regimes = split_by_vol_regime(trades, n_regimes=n_regimes)

    fig, axes = plt.subplots(1, n_regimes, figsize=figsize, sharex=True, sharey=True)

    if n_regimes == 1:
        axes = [axes]

    colors = ["blue", "orange", "green", "red", "purple"]

    for i, (regime_name, regime_trades) in enumerate(regimes.items()):
        ax = axes[i]

        ax.scatter(
            regime_trades.mfe,
            regime_trades.mae,
            s=6,
            alpha=0.3,
            color=colors[i % len(colors)],
        )

        ax.axhline(0, color="black", lw=1, ls="--", alpha=0.5)
        ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)

        avg_vol = np.mean(regime_trades.vol_at_entry)
        ax.set_title(
            f"{regime_name.capitalize()} Vol\n"
            f"n={regime_trades.n_trades}, avg_vol={avg_vol:.2f}%"
        )
        ax.set_xlabel("MFE (%)")

        if i == 0:
            ax.set_ylabel("MAE (%)")

        ax.grid(alpha=0.3)

    plt.suptitle(f"{trades.side.capitalize()}: Regime Comparison", y=1.02)
    plt.tight_layout()
    return fig


def plot_frontiers_percent_vs_volnorm(
    trades: TradeSet,
    figsize: tuple = (14, 10),
) -> Figure:
    """
    Compare frontiers in % space vs vol-normalized space.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data (must have vol_at_entry)
    figsize : tuple
        Figure size (width, height)

    Returns
    -------
    Figure
        Matplotlib figure object
    """
    norm_trades = normalize_metrics(trades)

    # Compute frontiers for both
    frontiers_pct = compute_frontiers(trades)
    frontiers_norm = compute_frontiers(norm_trades)

    fig, axes = plt.subplots(2, 2, figsize=figsize)

    # Top-left: Risk-constrained (%)
    ax = axes[0, 0]
    risk_data = frontiers_pct["risk_constrained"]
    ax.plot(
        risk_data["dd"],
        risk_data["mfe"],
        marker="o",
        markersize=4,
        linewidth=2,
        color="C0",
    )
    knee_dd, knee_mfe = risk_data["knee"]
    ax.plot(knee_dd, knee_mfe, marker="*", markersize=15, color="red")
    ax.set_title(f"{trades.side.capitalize()}: Risk Frontier (% space)")
    ax.set_xlabel("Drawdown Cap (%)")
    ax.set_ylabel("MFE 90th pct (%)")
    ax.grid(alpha=0.3)

    # Top-right: Risk-constrained (vol-norm)
    ax = axes[0, 1]
    risk_data = frontiers_norm["risk_constrained"]
    ax.plot(
        risk_data["dd"],
        risk_data["mfe"],
        marker="o",
        markersize=4,
        linewidth=2,
        color="C1",
    )
    knee_dd, knee_mfe = risk_data["knee"]
    ax.plot(knee_dd, knee_mfe, marker="*", markersize=15, color="red")
    ax.set_title(f"{trades.side.capitalize()}: Risk Frontier (vol-norm)")
    ax.set_xlabel("Drawdown Cap (vol units)")
    ax.set_ylabel("MFE 90th pct (vol units)")
    ax.grid(alpha=0.3)

    # Bottom-left: Opportunity-constrained (%)
    ax = axes[1, 0]
    opp_data = frontiers_pct["opportunity_constrained"]
    ax.plot(
        opp_data["tp"],
        opp_data["dd"],
        marker="o",
        markersize=4,
        linewidth=2,
        color="C0",
    )
    knee_tp, knee_dd = opp_data["knee"]
    ax.plot(knee_tp, knee_dd, marker="*", markersize=15, color="red")
    ax.set_title(f"{trades.side.capitalize()}: Opportunity Frontier (% space)")
    ax.set_xlabel("Profit Target (%)")
    ax.set_ylabel("DD 80th pct (%)")
    ax.grid(alpha=0.3)

    # Bottom-right: Opportunity-constrained (vol-norm)
    ax = axes[1, 1]
    opp_data = frontiers_norm["opportunity_constrained"]
    ax.plot(
        opp_data["tp"],
        opp_data["dd"],
        marker="o",
        markersize=4,
        linewidth=2,
        color="C1",
    )
    knee_tp, knee_dd = opp_data["knee"]
    ax.plot(knee_tp, knee_dd, marker="*", markersize=15, color="red")
    ax.set_title(f"{trades.side.capitalize()}: Opportunity Frontier (vol-norm)")
    ax.set_xlabel("Profit Target (vol units)")
    ax.set_ylabel("DD 80th pct (vol units)")
    ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig
