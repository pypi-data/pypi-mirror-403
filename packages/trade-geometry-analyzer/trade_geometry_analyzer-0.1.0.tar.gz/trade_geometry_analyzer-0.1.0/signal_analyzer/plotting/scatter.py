"""Scatter plot visualizations for trade geometry."""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any
from matplotlib.figure import Figure

from ..core.trades import TradeSet
from ..analysis.geometry import scatter_data
from ..analysis.ordering import split_by_ordering


def plot_scatter(
    long_trades: TradeSet | None = None,
    short_trades: TradeSet | None = None,
    H: int | None = None,
    trim_method: str | None = "iqr",
    trim_k: float = 1.5,
    show_raw: bool = False,
    alpha: float = 0.25,
    s: float = 6,
    figsize: tuple = (12, 5),
) -> Figure:
    """
    Create 2D scatter plots of MFE vs MAE for long and short trades.

    Parameters
    ----------
    long_trades : TradeSet, optional
        Long trade geometry data
    short_trades : TradeSet, optional
        Short trade geometry data
    H : int, optional
        Horizon (for title display)
    trim_method : {'iqr', 'percentile', None}
        Outlier removal method
    trim_k : float
        IQR multiplier (used if trim_method='iqr')
    show_raw : bool
        If True, show raw data in lighter color behind trimmed data
    alpha : float
        Scatter point transparency
    s : float
        Scatter point size
    figsize : tuple
        Figure size (width, height)

    Returns
    -------
    Figure
        Matplotlib figure object
    """
    # Determine number of subplots
    n_plots = sum([long_trades is not None, short_trades is not None])
    if n_plots == 0:
        raise ValueError("Must provide at least one of long_trades or short_trades")

    fig, axes = plt.subplots(1, n_plots, figsize=figsize, sharex=True, sharey=True)
    if n_plots == 1:
        axes = [axes]

    plot_idx = 0

    if long_trades is not None:
        ax = axes[plot_idx]
        data = scatter_data(long_trades, trim_method=trim_method, trim_k=trim_k)

        if show_raw:
            # Show raw data in light gray
            ax.scatter(
                data["raw"]["mfe"],
                data["raw"]["mae"],
                s=s,
                alpha=alpha * 0.3,
                color="lightgray",
                label="raw",
            )

        # Show trimmed data
        ax.scatter(
            data["trimmed"]["mfe"],
            data["trimmed"]["mae"],
            s=s,
            alpha=alpha,
            color="C0",
            label="trimmed" if show_raw else None,
        )

        ax.axhline(0, color="black", lw=1, ls="--", alpha=0.5)
        ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)

        title = f"Long: MAE vs MFE"
        if H is not None:
            title += f" (H={H})"
        title += f"\nn={data['n_trimmed']}/{data['n_raw']}"
        if trim_method:
            title += f" (trim={trim_method}, k={trim_k})"

        ax.set_title(title)
        ax.set_xlabel("MFE (%)")
        ax.set_ylabel("MAE (%)")
        ax.grid(alpha=0.3)

        if show_raw:
            ax.legend()

        plot_idx += 1

    if short_trades is not None:
        ax = axes[plot_idx]
        data = scatter_data(short_trades, trim_method=trim_method, trim_k=trim_k)

        if show_raw:
            ax.scatter(
                data["raw"]["mfe"],
                data["raw"]["mae"],
                s=s,
                alpha=alpha * 0.3,
                color="lightgray",
                label="raw",
            )

        ax.scatter(
            data["trimmed"]["mfe"],
            data["trimmed"]["mae"],
            s=s,
            alpha=alpha,
            color="C1",
            label="trimmed" if show_raw else None,
        )

        ax.axhline(0, color="black", lw=1, ls="--", alpha=0.5)
        ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)

        title = f"Short: MAE vs MFE"
        if H is not None:
            title += f" (H={H})"
        title += f"\nn={data['n_trimmed']}/{data['n_raw']}"
        if trim_method:
            title += f" (trim={trim_method}, k={trim_k})"

        ax.set_title(title)
        ax.set_xlabel("MFE (%)")
        if plot_idx == 0:  # Only label y-axis for leftmost plot
            ax.set_ylabel("MAE (%)")
        ax.grid(alpha=0.3)

        if show_raw:
            ax.legend()

    plt.tight_layout()
    return fig


def plot_marginals(
    long_trades: TradeSet | None = None,
    short_trades: TradeSet | None = None,
    bins: int = 50,
    use_kde: bool = True,
    figsize: tuple = (12, 8),
) -> Figure:
    """
    Plot marginal distributions (histograms/KDE) for MFE and MAE.

    Parameters
    ----------
    long_trades : TradeSet, optional
        Long trade geometry data
    short_trades : TradeSet, optional
        Short trade geometry data
    bins : int
        Number of histogram bins
    use_kde : bool
        If True, overlay KDE curve
    figsize : tuple
        Figure size (width, height)

    Returns
    -------
    Figure
        Matplotlib figure object
    """
    from ..analysis.geometry import marginals

    # Determine what to plot
    has_long = long_trades is not None
    has_short = short_trades is not None

    if not (has_long or has_short):
        raise ValueError("Must provide at least one of long_trades or short_trades")

    # Create subplots: 2 rows (MFE, MAE) x N cols (long, short)
    n_cols = sum([has_long, has_short])
    fig, axes = plt.subplots(2, n_cols, figsize=figsize)

    if n_cols == 1:
        axes = axes.reshape(2, 1)

    col_idx = 0

    if has_long:
        data = marginals(long_trades, bins=bins, use_kde=use_kde)

        # MFE (top)
        ax = axes[0, col_idx]
        mfe_bins = data["mfe_hist"]["bins"]
        mfe_counts = data["mfe_hist"]["counts"]
        ax.hist(
            long_trades.mfe,
            bins=mfe_bins,
            alpha=0.6,
            color="C0",
            edgecolor="black",
            label="histogram",
        )

        if use_kde:
            ax2 = ax.twinx()
            ax2.plot(
                data["mfe_kde"]["x"],
                data["mfe_kde"]["density"],
                color="red",
                lw=2,
                label="KDE",
            )
            ax2.set_ylabel("Density (KDE)", color="red")
            ax2.tick_params(axis="y", labelcolor="red")

        ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)
        ax.set_title(f"Long MFE Distribution (n={long_trades.n_trades})")
        ax.set_xlabel("MFE (%)")
        ax.set_ylabel("Count")
        ax.grid(alpha=0.3)

        # MAE (bottom)
        ax = axes[1, col_idx]
        mae_bins = data["mae_hist"]["bins"]
        mae_counts = data["mae_hist"]["counts"]
        ax.hist(
            long_trades.mae,
            bins=mae_bins,
            alpha=0.6,
            color="C0",
            edgecolor="black",
            label="histogram",
        )

        if use_kde:
            ax2 = ax.twinx()
            ax2.plot(
                data["mae_kde"]["x"],
                data["mae_kde"]["density"],
                color="red",
                lw=2,
                label="KDE",
            )
            ax2.set_ylabel("Density (KDE)", color="red")
            ax2.tick_params(axis="y", labelcolor="red")

        ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)
        ax.set_title(f"Long MAE Distribution")
        ax.set_xlabel("MAE (%)")
        ax.set_ylabel("Count")
        ax.grid(alpha=0.3)

        col_idx += 1

    if has_short:
        data = marginals(short_trades, bins=bins, use_kde=use_kde)

        # MFE (top)
        ax = axes[0, col_idx]
        mfe_bins = data["mfe_hist"]["bins"]
        mfe_counts = data["mfe_hist"]["counts"]
        ax.hist(
            short_trades.mfe,
            bins=mfe_bins,
            alpha=0.6,
            color="C1",
            edgecolor="black",
            label="histogram",
        )

        if use_kde:
            ax2 = ax.twinx()
            ax2.plot(
                data["mfe_kde"]["x"],
                data["mfe_kde"]["density"],
                color="red",
                lw=2,
                label="KDE",
            )
            ax2.set_ylabel("Density (KDE)", color="red")
            ax2.tick_params(axis="y", labelcolor="red")

        ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)
        ax.set_title(f"Short MFE Distribution (n={short_trades.n_trades})")
        ax.set_xlabel("MFE (%)")
        ax.set_ylabel("Count")
        ax.grid(alpha=0.3)

        # MAE (bottom)
        ax = axes[1, col_idx]
        mae_bins = data["mae_hist"]["bins"]
        mae_counts = data["mae_hist"]["counts"]
        ax.hist(
            short_trades.mae,
            bins=mae_bins,
            alpha=0.6,
            color="C1",
            edgecolor="black",
            label="histogram",
        )

        if use_kde:
            ax2 = ax.twinx()
            ax2.plot(
                data["mae_kde"]["x"],
                data["mae_kde"]["density"],
                color="red",
                lw=2,
                label="KDE",
            )
            ax2.set_ylabel("Density (KDE)", color="red")
            ax2.tick_params(axis="y", labelcolor="red")

        ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)
        ax.set_title(f"Short MAE Distribution")
        ax.set_xlabel("MAE (%)")
        ax.set_ylabel("Count")
        ax.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def plot_scatter_by_ordering(
    long_trades: TradeSet | None = None,
    short_trades: TradeSet | None = None,
    H: int | None = None,
    alpha: float = 0.35,
    s: float = 8,
    figsize: tuple = (12, 5),
) -> Figure:
    """
    Create scatter plots colored by ordering (MFE-first vs MAE-first).

    Parameters
    ----------
    long_trades : TradeSet, optional
        Long trade geometry data
    short_trades : TradeSet, optional
        Short trade geometry data
    H : int, optional
        Horizon (for title display)
    alpha : float
        Scatter point transparency
    s : float
        Scatter point size
    figsize : tuple
        Figure size (width, height)

    Returns
    -------
    Figure
        Matplotlib figure object

    Notes
    -----
    - Green: MFE-first (profit came before pain)
    - Red: MAE-first (pain came before profit)
    - Gray: Tie (simultaneous)
    """
    n_plots = sum([long_trades is not None, short_trades is not None])
    if n_plots == 0:
        raise ValueError("Must provide at least one of long_trades or short_trades")

    fig, axes = plt.subplots(1, n_plots, figsize=figsize, sharex=True, sharey=True)
    if n_plots == 1:
        axes = [axes]

    plot_idx = 0

    if long_trades is not None:
        ax = axes[plot_idx]
        splits = split_by_ordering(long_trades)

        # Plot MFE-first in green
        if splits["mfe_first"]["count"] > 0:
            ax.scatter(
                splits["mfe_first"]["mfe"],
                splits["mfe_first"]["mae"],
                s=s,
                alpha=alpha,
                color="green",
                label=f"MFE-first ({splits['mfe_first']['count']})",
            )

        # Plot MAE-first in red
        if splits["mae_first"]["count"] > 0:
            ax.scatter(
                splits["mae_first"]["mfe"],
                splits["mae_first"]["mae"],
                s=s,
                alpha=alpha,
                color="red",
                label=f"MAE-first ({splits['mae_first']['count']})",
            )

        # Plot ties in gray
        if splits["tie"]["count"] > 0:
            ax.scatter(
                splits["tie"]["mfe"],
                splits["tie"]["mae"],
                s=s,
                alpha=alpha,
                color="gray",
                label=f"Tie ({splits['tie']['count']})",
            )

        ax.axhline(0, color="black", lw=1, ls="--", alpha=0.5)
        ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)

        title = f"Long: Ordering Analysis"
        if H is not None:
            title += f" (H={H})"
        title += f"\nTotal: {long_trades.n_trades} trades"

        ax.set_title(title)
        ax.set_xlabel("MFE (%)")
        ax.set_ylabel("MAE (%)")
        ax.grid(alpha=0.3)
        ax.legend()

        plot_idx += 1

    if short_trades is not None:
        ax = axes[plot_idx]
        splits = split_by_ordering(short_trades)

        # Plot MFE-first in green
        if splits["mfe_first"]["count"] > 0:
            ax.scatter(
                splits["mfe_first"]["mfe"],
                splits["mfe_first"]["mae"],
                s=s,
                alpha=alpha,
                color="green",
                label=f"MFE-first ({splits['mfe_first']['count']})",
            )

        # Plot MAE-first in red
        if splits["mae_first"]["count"] > 0:
            ax.scatter(
                splits["mae_first"]["mfe"],
                splits["mae_first"]["mae"],
                s=s,
                alpha=alpha,
                color="red",
                label=f"MAE-first ({splits['mae_first']['count']})",
            )

        # Plot ties in gray
        if splits["tie"]["count"] > 0:
            ax.scatter(
                splits["tie"]["mfe"],
                splits["tie"]["mae"],
                s=s,
                alpha=alpha,
                color="gray",
                label=f"Tie ({splits['tie']['count']})",
            )

        ax.axhline(0, color="black", lw=1, ls="--", alpha=0.5)
        ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)

        title = f"Short: Ordering Analysis"
        if H is not None:
            title += f" (H={H})"
        title += f"\nTotal: {short_trades.n_trades} trades"

        ax.set_title(title)
        ax.set_xlabel("MFE (%)")
        if plot_idx == 0:
            ax.set_ylabel("MAE (%)")
        ax.grid(alpha=0.3)
        ax.legend()

    plt.tight_layout()
    return fig
