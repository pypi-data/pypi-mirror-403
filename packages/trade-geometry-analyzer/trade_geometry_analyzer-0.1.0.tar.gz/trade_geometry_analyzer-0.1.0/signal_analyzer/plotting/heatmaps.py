"""Heatmap visualizations for TP/SL feasibility analysis."""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any
from matplotlib.figure import Figure

from ..core.trades import TradeSet
from ..analysis.feasibility import hit_matrix, ev_proxy


def plot_heatmap_prob(
    long_trades: TradeSet | None = None,
    short_trades: TradeSet | None = None,
    tp_grid: np.ndarray | None = None,
    sl_grid: np.ndarray | None = None,
    min_sample: int = 5,
    figsize: tuple = (14, 6),
    cmap: str = "RdYlGn",
) -> Figure:
    """
    Plot probability heatmaps: P(hit TP before SL).

    Parameters
    ----------
    long_trades : TradeSet, optional
        Long trade geometry data (must have paths)
    short_trades : TradeSet, optional
        Short trade geometry data (must have paths)
    tp_grid : np.ndarray, optional
        Array of TP values (if None, auto-generate)
    sl_grid : np.ndarray, optional
        Array of SL values (if None, auto-generate)
    min_sample : int
        Minimum sample size for valid cells
    figsize : tuple
        Figure size (width, height)
    cmap : str
        Colormap name

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
    fig, axes = plt.subplots(1, n_cols, figsize=figsize)

    if n_cols == 1:
        axes = [axes]

    col_idx = 0

    if has_long:
        # Auto-generate grids if not provided
        if tp_grid is None:
            tp_max = long_trades.mfe.max()
            tp_grid = np.linspace(0.1, min(tp_max, 10), 25)

        if sl_grid is None:
            sl_max = -long_trades.mae.min()
            sl_grid = np.linspace(0.1, min(sl_max, 10), 25)

        hit_data = hit_matrix(long_trades, tp_grid, sl_grid, min_sample)

        ax = axes[col_idx]
        im = ax.imshow(
            hit_data["prob_matrix"],
            aspect="auto",
            origin="lower",
            cmap=cmap,
            vmin=0,
            vmax=1,
            extent=[
                sl_grid[0],
                sl_grid[-1],
                tp_grid[0],
                tp_grid[-1],
            ],
        )

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("P(TP before SL)")

        # Add contour lines
        ax.contour(
            sl_grid,
            tp_grid,
            hit_data["prob_matrix"],
            levels=[0.3, 0.5, 0.7],
            colors="black",
            linewidths=0.5,
            alpha=0.5,
        )

        # Diagonal line (TP = SL)
        max_val = max(sl_grid[-1], tp_grid[-1])
        ax.plot([0, max_val], [0, max_val], "k--", lw=1, alpha=0.5, label="TP=SL")

        ax.set_title(f"Long: P(TP before SL)\nn={long_trades.n_trades} trades")
        ax.set_xlabel("Stop Loss (%)")
        ax.set_ylabel("Take Profit (%)")
        ax.legend()

        col_idx += 1

    if has_short:
        # Auto-generate grids if not provided
        if tp_grid is None:
            tp_max = short_trades.mfe.max()
            tp_grid = np.linspace(0.1, min(tp_max, 10), 25)

        if sl_grid is None:
            sl_max = -short_trades.mae.min()
            sl_grid = np.linspace(0.1, min(sl_max, 10), 25)

        hit_data = hit_matrix(short_trades, tp_grid, sl_grid, min_sample)

        ax = axes[col_idx]
        im = ax.imshow(
            hit_data["prob_matrix"],
            aspect="auto",
            origin="lower",
            cmap=cmap,
            vmin=0,
            vmax=1,
            extent=[
                sl_grid[0],
                sl_grid[-1],
                tp_grid[0],
                tp_grid[-1],
            ],
        )

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("P(TP before SL)")

        ax.contour(
            sl_grid,
            tp_grid,
            hit_data["prob_matrix"],
            levels=[0.3, 0.5, 0.7],
            colors="black",
            linewidths=0.5,
            alpha=0.5,
        )

        max_val = max(sl_grid[-1], tp_grid[-1])
        ax.plot([0, max_val], [0, max_val], "k--", lw=1, alpha=0.5, label="TP=SL")

        ax.set_title(f"Short: P(TP before SL)\nn={short_trades.n_trades} trades")
        ax.set_xlabel("Stop Loss (%)")
        ax.set_ylabel("Take Profit (%)")
        ax.legend()

    plt.tight_layout()
    return fig


def plot_heatmap_ev(
    long_trades: TradeSet | None = None,
    short_trades: TradeSet | None = None,
    tp_grid: np.ndarray | None = None,
    sl_grid: np.ndarray | None = None,
    slippage: float = 0.0,
    commission: float = 0.0,
    min_sample: int = 5,
    figsize: tuple = (14, 6),
    cmap: str = "RdYlGn",
) -> Figure:
    """
    Plot expected value heatmaps for TP/SL grid.

    Parameters
    ----------
    long_trades : TradeSet, optional
        Long trade geometry data (must have paths)
    short_trades : TradeSet, optional
        Short trade geometry data (must have paths)
    tp_grid : np.ndarray, optional
        Array of TP values
    sl_grid : np.ndarray, optional
        Array of SL values
    slippage : float
        Slippage cost (%)
    commission : float
        Commission cost (%)
    min_sample : int
        Minimum sample size for valid cells
    figsize : tuple
        Figure size (width, height)
    cmap : str
        Colormap name

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
    fig, axes = plt.subplots(1, n_cols, figsize=figsize)

    if n_cols == 1:
        axes = [axes]

    col_idx = 0

    if has_long:
        if tp_grid is None:
            tp_max = long_trades.mfe.max()
            tp_grid = np.linspace(0.1, min(tp_max, 10), 25)

        if sl_grid is None:
            sl_max = -long_trades.mae.min()
            sl_grid = np.linspace(0.1, min(sl_max, 10), 25)

        hit_data = hit_matrix(long_trades, tp_grid, sl_grid, min_sample)
        ev_data = ev_proxy(hit_data, slippage, commission)

        ax = axes[col_idx]

        # Mask out low-count cells
        ev_masked = ev_data["ev_matrix"].copy()
        ev_masked[hit_data["count_matrix"] < min_sample] = np.nan

        im = ax.imshow(
            ev_masked,
            aspect="auto",
            origin="lower",
            cmap=cmap,
            extent=[
                sl_grid[0],
                sl_grid[-1],
                tp_grid[0],
                tp_grid[-1],
            ],
        )

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Expected Value (%)")

        # Zero contour (break-even line)
        ax.contour(
            sl_grid,
            tp_grid,
            ev_masked,
            levels=[0],
            colors="black",
            linewidths=2,
            alpha=0.8,
        )

        # Overlay robust zones
        if ev_data["robust_zones"].any():
            ax.contourf(
                sl_grid,
                tp_grid,
                ev_data["robust_zones"].astype(float),
                levels=[0.5, 1.5],
                colors="none",
                hatches=[".."],
                alpha=0,
            )

        max_val = max(sl_grid[-1], tp_grid[-1])
        ax.plot([0, max_val], [0, max_val], "k--", lw=1, alpha=0.5, label="TP=SL")

        ax.set_title(f"Long: Expected Value\n(costs: slip={slippage}%, comm={commission}%)")
        ax.set_xlabel("Stop Loss (%)")
        ax.set_ylabel("Take Profit (%)")
        ax.legend()

        col_idx += 1

    if has_short:
        if tp_grid is None:
            tp_max = short_trades.mfe.max()
            tp_grid = np.linspace(0.1, min(tp_max, 10), 25)

        if sl_grid is None:
            sl_max = -short_trades.mae.min()
            sl_grid = np.linspace(0.1, min(sl_max, 10), 25)

        hit_data = hit_matrix(short_trades, tp_grid, sl_grid, min_sample)
        ev_data = ev_proxy(hit_data, slippage, commission)

        ax = axes[col_idx]

        ev_masked = ev_data["ev_matrix"].copy()
        ev_masked[hit_data["count_matrix"] < min_sample] = np.nan

        im = ax.imshow(
            ev_masked,
            aspect="auto",
            origin="lower",
            cmap=cmap,
            extent=[
                sl_grid[0],
                sl_grid[-1],
                tp_grid[0],
                tp_grid[-1],
            ],
        )

        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label("Expected Value (%)")

        ax.contour(
            sl_grid,
            tp_grid,
            ev_masked,
            levels=[0],
            colors="black",
            linewidths=2,
            alpha=0.8,
        )

        if ev_data["robust_zones"].any():
            ax.contourf(
                sl_grid,
                tp_grid,
                ev_data["robust_zones"].astype(float),
                levels=[0.5, 1.5],
                colors="none",
                hatches=[".."],
                alpha=0,
            )

        max_val = max(sl_grid[-1], tp_grid[-1])
        ax.plot([0, max_val], [0, max_val], "k--", lw=1, alpha=0.5, label="TP=SL")

        ax.set_title(f"Short: Expected Value\n(costs: slip={slippage}%, comm={commission}%)")
        ax.set_xlabel("Stop Loss (%)")
        ax.set_ylabel("Take Profit (%)")
        ax.legend()

    plt.tight_layout()
    return fig
