"""Frontier visualization: risk/reward boundaries and knee points."""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any
from matplotlib.figure import Figure

from ..core.trades import TradeSet
from ..analysis.frontiers import compute_frontiers


def plot_frontiers(
    long_trades: TradeSet | None = None,
    short_trades: TradeSet | None = None,
    dd_grid: np.ndarray | None = None,
    tp_grid: np.ndarray | None = None,
    risk_q: float = 0.9,
    opp_q: float = 0.8,
    show_knee: bool = True,
    show_counts: bool = True,
    figsize: tuple = (14, 6),
) -> Figure:
    """
    Plot risk-constrained and opportunity-constrained frontiers.

    Parameters
    ----------
    long_trades : TradeSet, optional
        Long trade geometry data
    short_trades : TradeSet, optional
        Short trade geometry data
    dd_grid : np.ndarray, optional
        Drawdown grid for risk-constrained frontier
    tp_grid : np.ndarray, optional
        Profit target grid for opportunity-constrained frontier
    risk_q : float
        Quantile for risk-constrained frontier MFE
    opp_q : float
        Quantile for opportunity-constrained frontier MAE
    show_knee : bool
        If True, highlight knee points
    show_counts : bool
        If True, show sample counts as text annotations
    figsize : tuple
        Figure size (width, height)

    Returns
    -------
    Figure
        Matplotlib figure object
    """
    has_long = long_trades is not None
    has_short = short_trades is not None

    if not (has_long or has_short):
        raise ValueError("Must provide at least one of long_trades or short_trades")

    n_cols = sum([has_long, has_short])
    fig, axes = plt.subplots(2, n_cols, figsize=figsize)

    if n_cols == 1:
        axes = axes.reshape(2, 1)

    col_idx = 0

    if has_long:
        frontiers = compute_frontiers(
            long_trades, dd_grid, tp_grid, risk_q=risk_q, opp_q=opp_q
        )

        # Risk-constrained frontier (top)
        ax = axes[0, col_idx]
        risk_data = frontiers["risk_constrained"]

        ax.plot(
            risk_data["dd"],
            risk_data["mfe"],
            marker="o",
            markersize=4,
            linewidth=2,
            color="C0",
            label=f"q={risk_q:.0%} MFE",
        )

        if show_knee:
            knee_dd, knee_mfe = risk_data["knee"]
            ax.plot(
                knee_dd,
                knee_mfe,
                marker="*",
                markersize=15,
                color="red",
                label=f"Knee ({knee_dd:.2f}%, {knee_mfe:.2f}%)",
            )

        ax.set_title(f"Long: Risk-Constrained Frontier\n(Max MFE for given DD limit)")
        ax.set_xlabel("Drawdown Cap (%)")
        ax.set_ylabel(f"MFE {risk_q:.0%} quantile (%)")
        ax.grid(alpha=0.3)
        ax.legend()

        # Opportunity-constrained frontier (bottom)
        ax = axes[1, col_idx]
        opp_data = frontiers["opportunity_constrained"]

        ax.plot(
            opp_data["tp"],
            opp_data["dd"],
            marker="o",
            markersize=4,
            linewidth=2,
            color="C0",
            label=f"q={opp_q:.0%} DD",
        )

        if show_knee:
            knee_tp, knee_dd = opp_data["knee"]
            ax.plot(
                knee_tp,
                knee_dd,
                marker="*",
                markersize=15,
                color="red",
                label=f"Knee ({knee_tp:.2f}%, {knee_dd:.2f}%)",
            )

        ax.set_title(
            f"Long: Opportunity-Constrained Frontier\n(DD required for target)"
        )
        ax.set_xlabel("Profit Target (%)")
        ax.set_ylabel(f"Drawdown {opp_q:.0%} quantile (%)")
        ax.grid(alpha=0.3)
        ax.legend()

        col_idx += 1

    if has_short:
        frontiers = compute_frontiers(
            short_trades, dd_grid, tp_grid, risk_q=risk_q, opp_q=opp_q
        )

        # Risk-constrained frontier (top)
        ax = axes[0, col_idx]
        risk_data = frontiers["risk_constrained"]

        ax.plot(
            risk_data["dd"],
            risk_data["mfe"],
            marker="o",
            markersize=4,
            linewidth=2,
            color="C1",
            label=f"q={risk_q:.0%} MFE",
        )

        if show_knee:
            knee_dd, knee_mfe = risk_data["knee"]
            ax.plot(
                knee_dd,
                knee_mfe,
                marker="*",
                markersize=15,
                color="red",
                label=f"Knee ({knee_dd:.2f}%, {knee_mfe:.2f}%)",
            )

        ax.set_title(f"Short: Risk-Constrained Frontier\n(Max MFE for given DD limit)")
        ax.set_xlabel("Drawdown Cap (%)")
        ax.set_ylabel(f"MFE {risk_q:.0%} quantile (%)")
        ax.grid(alpha=0.3)
        ax.legend()

        # Opportunity-constrained frontier (bottom)
        ax = axes[1, col_idx]
        opp_data = frontiers["opportunity_constrained"]

        ax.plot(
            opp_data["tp"],
            opp_data["dd"],
            marker="o",
            markersize=4,
            linewidth=2,
            color="C1",
            label=f"q={opp_q:.0%} DD",
        )

        if show_knee:
            knee_tp, knee_dd = opp_data["knee"]
            ax.plot(
                knee_tp,
                knee_dd,
                marker="*",
                markersize=15,
                color="red",
                label=f"Knee ({knee_tp:.2f}%, {knee_dd:.2f}%)",
            )

        ax.set_title(
            f"Short: Opportunity-Constrained Frontier\n(DD required for target)"
        )
        ax.set_xlabel("Profit Target (%)")
        ax.set_ylabel(f"Drawdown {opp_q:.0%} quantile (%)")
        ax.grid(alpha=0.3)
        ax.legend()

    plt.tight_layout()
    return fig
