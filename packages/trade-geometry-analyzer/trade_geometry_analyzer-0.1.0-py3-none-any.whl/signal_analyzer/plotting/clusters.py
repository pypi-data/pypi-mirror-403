"""Visualization for cluster analysis."""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any
from matplotlib.figure import Figure

from ..core.trades import TradeSet
from ..analysis.clusters import cluster_trades, cluster_summary, suggest_exit_rules


def plot_clusters_scatter(
    trades: TradeSet,
    cluster_result: Dict[str, Any] | None = None,
    n_clusters: int | None = None,
    figsize: tuple = (10, 8),
) -> Figure:
    """
    Scatter plot colored by cluster ID.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    cluster_result : dict, optional
        Output from cluster_trades. If None, will compute clustering.
    n_clusters : int, optional
        Number of clusters (used if cluster_result is None)
    figsize : tuple
        Figure size (width, height)

    Returns
    -------
    Figure
        Matplotlib figure object
    """
    if cluster_result is None:
        cluster_result = cluster_trades(trades, n_clusters=n_clusters)

    labels = cluster_result["labels"]
    unique_labels = np.unique(labels)

    # Filter out noise (-1 for HDBSCAN)
    unique_labels = unique_labels[unique_labels >= 0]

    fig, ax = plt.subplots(figsize=figsize)

    # Use a colormap
    colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))

    for i, cluster_id in enumerate(unique_labels):
        mask = labels == cluster_id
        ax.scatter(
            trades.mfe[mask],
            trades.mae[mask],
            s=20,
            alpha=0.6,
            color=colors[i],
            label=f"Cluster {cluster_id} (n={np.sum(mask)})",
        )

    # Plot noise points separately if present
    if -1 in labels:
        noise_mask = labels == -1
        ax.scatter(
            trades.mfe[noise_mask],
            trades.mae[noise_mask],
            s=10,
            alpha=0.3,
            color="gray",
            label=f"Noise (n={np.sum(noise_mask)})",
        )

    ax.axhline(0, color="black", lw=1, ls="--", alpha=0.5)
    ax.axvline(0, color="black", lw=1, ls="--", alpha=0.5)

    ax.set_title(
        f"{trades.side.capitalize()}: Trade Clusters\n"
        f"n_clusters={cluster_result['n_clusters']}, total={trades.n_trades}"
    )
    ax.set_xlabel("MFE (%)")
    ax.set_ylabel("MAE (%)")
    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)

    plt.tight_layout()
    return fig


def plot_cluster_stats(
    trades: TradeSet,
    cluster_result: Dict[str, Any] | None = None,
    n_clusters: int | None = None,
    figsize: tuple = (14, 10),
) -> Figure:
    """
    Bar charts showing statistics for each cluster.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    cluster_result : dict, optional
        Output from cluster_trades
    n_clusters : int, optional
        Number of clusters (used if cluster_result is None)
    figsize : tuple
        Figure size (width, height)

    Returns
    -------
    Figure
        Matplotlib figure object
    """
    if cluster_result is None:
        cluster_result = cluster_trades(trades, n_clusters=n_clusters)

    summaries = cluster_summary(trades, cluster_result)
    archetypes = suggest_exit_rules(summaries)

    cluster_ids = sorted(summaries.keys())
    n_clusters_actual = len(cluster_ids)

    fig, axes = plt.subplots(3, 2, figsize=figsize)
    axes = axes.flatten()

    # 1. Cluster sizes
    ax = axes[0]
    counts = [summaries[cid]["count"] for cid in cluster_ids]
    ax.bar(cluster_ids, counts, color="steelblue", alpha=0.7)
    ax.set_title("Cluster Sizes")
    ax.set_xlabel("Cluster ID")
    ax.set_ylabel("Number of Trades")
    ax.grid(alpha=0.3, axis="y")

    # 2. Median MFE
    ax = axes[1]
    mfes = [summaries[cid]["median_mfe"] for cid in cluster_ids]
    colors = ["green" if m > 0 else "red" for m in mfes]
    ax.bar(cluster_ids, mfes, color=colors, alpha=0.7)
    ax.axhline(0, color="black", lw=1, ls="--")
    ax.set_title("Median MFE by Cluster")
    ax.set_xlabel("Cluster ID")
    ax.set_ylabel("Median MFE (%)")
    ax.grid(alpha=0.3, axis="y")

    # 3. Median MAE (as positive DD)
    ax = axes[2]
    maes = [-summaries[cid]["median_mae"] for cid in cluster_ids]
    ax.bar(cluster_ids, maes, color="orange", alpha=0.7)
    ax.set_title("Median Drawdown by Cluster")
    ax.set_xlabel("Cluster ID")
    ax.set_ylabel("Median DD (%)")
    ax.grid(alpha=0.3, axis="y")

    # 4. Win Rate
    ax = axes[3]
    win_rates = [summaries[cid]["win_rate"] * 100 for cid in cluster_ids]
    ax.bar(cluster_ids, win_rates, color="purple", alpha=0.7)
    ax.axhline(50, color="black", lw=1, ls="--")
    ax.set_title("Win Rate by Cluster")
    ax.set_xlabel("Cluster ID")
    ax.set_ylabel("Win Rate (%)")
    ax.set_ylim(0, 100)
    ax.grid(alpha=0.3, axis="y")

    # 5. Ordering proportions (stacked bar)
    ax = axes[4]
    mfe_first_rates = [summaries[cid]["mfe_first_rate"] * 100 for cid in cluster_ids]
    mae_first_rates = [summaries[cid]["mae_first_rate"] * 100 for cid in cluster_ids]

    ax.bar(cluster_ids, mfe_first_rates, color="green", alpha=0.7, label="MFE-first")
    ax.bar(
        cluster_ids,
        mae_first_rates,
        bottom=mfe_first_rates,
        color="red",
        alpha=0.7,
        label="MAE-first",
    )

    ax.set_title("Ordering Distribution by Cluster")
    ax.set_xlabel("Cluster ID")
    ax.set_ylabel("Proportion (%)")
    ax.set_ylim(0, 100)
    ax.legend()
    ax.grid(alpha=0.3, axis="y")

    # 6. Suggested archetypes (text)
    ax = axes[5]
    ax.axis("off")
    ax.set_title("Suggested Exit Strategies", fontsize=12, fontweight="bold")

    text_lines = []
    for cid in cluster_ids:
        archetype = archetypes[cid]
        text_lines.append(f"Cluster {cid}: {archetype}")

    text_str = "\n".join(text_lines)
    ax.text(
        0.1,
        0.9,
        text_str,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        family="monospace",
    )

    plt.suptitle(
        f"{trades.side.capitalize()}: Cluster Analysis Summary", fontsize=14, y=0.995
    )
    plt.tight_layout()
    return fig
