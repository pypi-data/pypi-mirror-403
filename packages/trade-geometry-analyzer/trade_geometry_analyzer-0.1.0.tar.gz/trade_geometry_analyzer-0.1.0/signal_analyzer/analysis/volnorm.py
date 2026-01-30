"""Volatility normalization and regime-based analysis."""

import numpy as np
from typing import Dict, Any, List
from dataclasses import replace

from ..core.trades import TradeSet


def normalize_metrics(trades: TradeSet) -> TradeSet:
    """
    Convert % MFE/MAE to volatility-adjusted units (R-multiples).

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data (must have vol_at_entry)

    Returns
    -------
    TradeSet
        New TradeSet with normalized MFE/MAE values

    Notes
    -----
    Normalization: MFE_norm = MFE / vol_at_entry
    This converts percentage moves into "volatility units" or "R-multiples".
    """
    if trades.vol_at_entry is None:
        raise ValueError("TradeSet must have vol_at_entry for normalization")

    # Avoid division by zero
    vol_safe = np.where(trades.vol_at_entry > 0, trades.vol_at_entry, np.nan)

    mfe_norm = trades.mfe / vol_safe
    mae_norm = trades.mae / vol_safe

    # Filter out invalid normalized values
    valid = np.isfinite(mfe_norm) & np.isfinite(mae_norm)

    # Create new TradeSet with normalized values
    return TradeSet(
        side=trades.side,
        n_trades=np.sum(valid),
        entry_idx=trades.entry_idx[valid],
        entry_price=trades.entry_price[valid],
        mfe=mfe_norm[valid],
        mae=mae_norm[valid],
        t_mfe=trades.t_mfe[valid],
        t_mae=trades.t_mae[valid],
        vol_at_entry=trades.vol_at_entry[valid],
        mfe_path=trades.mfe_path[valid] / vol_safe[valid, np.newaxis]
        if trades.mfe_path is not None
        else None,
        mae_path=trades.mae_path[valid] / vol_safe[valid, np.newaxis]
        if trades.mae_path is not None
        else None,
    )


def split_by_vol_regime(
    trades: TradeSet,
    n_regimes: int = 3,
    regime_method: str = "quantile",
) -> Dict[str, TradeSet]:
    """
    Split trades by volatility regimes.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data (must have vol_at_entry)
    n_regimes : int
        Number of regimes (e.g., 3 for low/mid/high)
    regime_method : {'quantile', 'kmeans'}
        Method for defining regimes

    Returns
    -------
    dict
        Dictionary mapping regime names to TradeSet objects
        e.g., {'low': TradeSet(...), 'mid': TradeSet(...), 'high': TradeSet(...)}
    """
    if trades.vol_at_entry is None:
        raise ValueError("TradeSet must have vol_at_entry for regime splitting")

    vol = trades.vol_at_entry

    if regime_method == "quantile":
        # Split by quantiles
        quantiles = np.linspace(0, 100, n_regimes + 1)
        edges = np.percentile(vol, quantiles)

        regime_labels = np.digitize(vol, edges[1:-1])

        # Label regimes
        if n_regimes == 3:
            regime_names = ["low", "mid", "high"]
        else:
            regime_names = [f"regime_{i}" for i in range(n_regimes)]

    elif regime_method == "kmeans":
        from sklearn.cluster import KMeans

        kmeans = KMeans(n_clusters=n_regimes, random_state=42)
        regime_labels = kmeans.fit_predict(vol.reshape(-1, 1))

        # Sort by cluster center (low to high vol)
        centers = kmeans.cluster_centers_.flatten()
        order = np.argsort(centers)
        label_map = {old: new for new, old in enumerate(order)}
        regime_labels = np.array([label_map[label] for label in regime_labels])

        if n_regimes == 3:
            regime_names = ["low", "mid", "high"]
        else:
            regime_names = [f"regime_{i}" for i in range(n_regimes)]

    else:
        raise ValueError(f"Unknown regime_method: {regime_method}")

    # Split into separate TradeSets
    result = {}
    for i, name in enumerate(regime_names):
        mask = regime_labels == i

        if np.sum(mask) == 0:
            continue

        result[name] = TradeSet(
            side=trades.side,
            n_trades=np.sum(mask),
            entry_idx=trades.entry_idx[mask],
            entry_price=trades.entry_price[mask],
            mfe=trades.mfe[mask],
            mae=trades.mae[mask],
            t_mfe=trades.t_mfe[mask],
            t_mae=trades.t_mae[mask],
            vol_at_entry=trades.vol_at_entry[mask],
            mfe_path=trades.mfe_path[mask] if trades.mfe_path is not None else None,
            mae_path=trades.mae_path[mask] if trades.mae_path is not None else None,
        )

    return result


def compare_percent_vs_volnorm(
    trades: TradeSet,
) -> Dict[str, Dict[str, float]]:
    """
    Compare key metrics in % space vs vol-normalized space.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data (must have vol_at_entry)

    Returns
    -------
    dict
        Dictionary with 'percent' and 'volnorm' keys, each containing metrics:
        - median_mfe, median_mae, mfe_p95, mae_p5
    """
    from ..analysis.geometry import geometry_metrics

    # Original % metrics
    pct_metrics = geometry_metrics(trades)

    # Normalized metrics
    norm_trades = normalize_metrics(trades)
    norm_metrics = geometry_metrics(norm_trades)

    return {
        "percent": {
            "median_mfe": pct_metrics["median_mfe"],
            "median_mae": pct_metrics["median_mae"],
            "mfe_p95": pct_metrics["mfe_p95"],
            "mae_p5": pct_metrics["mae_p5"],
        },
        "volnorm": {
            "median_mfe": norm_metrics["median_mfe"],
            "median_mae": norm_metrics["median_mae"],
            "mfe_p95": norm_metrics["mfe_p95"],
            "mae_p5": norm_metrics["mae_p5"],
        },
    }


def regime_dependence_analysis(
    trades: TradeSet,
    n_regimes: int = 3,
) -> Dict[str, Dict[str, float]]:
    """
    Analyze metrics per volatility regime.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data (must have vol_at_entry)
    n_regimes : int
        Number of regimes

    Returns
    -------
    dict
        Dictionary mapping regime names to metrics
    """
    from ..analysis.geometry import geometry_metrics

    regimes = split_by_vol_regime(trades, n_regimes=n_regimes)

    result = {}
    for regime_name, regime_trades in regimes.items():
        metrics = geometry_metrics(regime_trades)
        result[regime_name] = {
            "n_trades": metrics["n_trades"],
            "median_mfe": metrics["median_mfe"],
            "median_mae": metrics["median_mae"],
            "win_rate": metrics["win_rate"],
            "mfe_mae_corr": metrics["mfe_mae_corr"],
            "avg_vol": float(np.mean(regime_trades.vol_at_entry)),
        }

    return result
