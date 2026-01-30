"""Geometry analysis: scatter data preparation and marginal distributions."""

import numpy as np
from typing import Tuple, Dict, Any
from scipy import stats

from ..core.trades import TradeSet
from ..core.utils import trim_iqr, trim_percentile


def scatter_data(
    trades: TradeSet,
    trim_method: str | None = "iqr",
    trim_k: float = 1.5,
    trim_percentile_range: Tuple[float, float] = (1.0, 99.0),
) -> Dict[str, Any]:
    """
    Prepare raw and trimmed scatter data for plotting.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    trim_method : {'iqr', 'percentile', None}
        Outlier removal method
    trim_k : float
        IQR multiplier (used if trim_method='iqr')
    trim_percentile_range : tuple
        Percentile bounds (used if trim_method='percentile')

    Returns
    -------
    dict
        Dictionary containing:
        - 'raw': {'mfe': array, 'mae': array}
        - 'trimmed': {'mfe': array, 'mae': array, 'keep_mask': array}
        - 'n_raw': int
        - 'n_trimmed': int
    """
    mfe = trades.mfe
    mae = trades.mae

    if trim_method == "iqr":
        mfe_t, mae_t, keep = trim_iqr(mfe, mae, k=trim_k)
    elif trim_method == "percentile":
        mfe_t, mae_t, keep = trim_percentile(mfe, mae, p=trim_percentile_range)
    elif trim_method is None:
        mfe_t, mae_t = mfe, mae
        keep = np.ones(len(mfe), dtype=bool)
    else:
        raise ValueError(
            f"Unknown trim_method: {trim_method}. Use 'iqr', 'percentile', or None."
        )

    return {
        "raw": {"mfe": mfe, "mae": mae},
        "trimmed": {"mfe": mfe_t, "mae": mae_t, "keep_mask": keep},
        "n_raw": len(mfe),
        "n_trimmed": len(mfe_t),
    }


def marginals(
    trades: TradeSet,
    bins: int = 50,
    use_kde: bool = True,
) -> Dict[str, Any]:
    """
    Calculate marginal distributions for MFE and MAE separately.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    bins : int
        Number of bins for histogram
    use_kde : bool
        If True, also compute Kernel Density Estimate

    Returns
    -------
    dict
        Dictionary containing:
        - 'mfe_hist': {'bins': array, 'counts': array, 'density': array}
        - 'mae_hist': {'bins': array, 'counts': array, 'density': array}
        - 'mfe_kde': {'x': array, 'density': array} (if use_kde=True)
        - 'mae_kde': {'x': array, 'density': array} (if use_kde=True)
    """
    mfe = trades.mfe
    mae = trades.mae

    # MFE histogram
    mfe_counts, mfe_bins = np.histogram(mfe, bins=bins)
    mfe_density = mfe_counts / mfe_counts.sum()

    # MAE histogram
    mae_counts, mae_bins = np.histogram(mae, bins=bins)
    mae_density = mae_counts / mae_counts.sum()

    result = {
        "mfe_hist": {
            "bins": mfe_bins,
            "counts": mfe_counts,
            "density": mfe_density,
        },
        "mae_hist": {
            "bins": mae_bins,
            "counts": mae_counts,
            "density": mae_density,
        },
    }

    if use_kde:
        # KDE for MFE
        mfe_kde = stats.gaussian_kde(mfe)
        mfe_x = np.linspace(mfe.min(), mfe.max(), 200)
        mfe_y = mfe_kde(mfe_x)

        # KDE for MAE
        mae_kde = stats.gaussian_kde(mae)
        mae_x = np.linspace(mae.min(), mae.max(), 200)
        mae_y = mae_kde(mae_x)

        result["mfe_kde"] = {"x": mfe_x, "density": mfe_y}
        result["mae_kde"] = {"x": mae_x, "density": mae_y}

    return result


def geometry_metrics(trades: TradeSet) -> Dict[str, float]:
    """
    Compute summary statistics for trade geometry.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data

    Returns
    -------
    dict
        Dictionary of metrics:
        - n_trades: Number of trades
        - median_mfe: Median MFE (%)
        - median_mae: Median MAE (%)
        - mean_mfe: Mean MFE (%)
        - mean_mae: Mean MAE (%)
        - win_rate: Fraction of trades with MFE > 0
        - mfe_p95: 95th percentile MFE
        - mfe_p99: 99th percentile MFE
        - mae_p5: 5th percentile MAE (tail risk)
        - mae_p1: 1st percentile MAE (extreme tail risk)
        - mfe_mae_corr: Correlation between MFE and MAE
    """
    mfe = trades.mfe
    mae = trades.mae

    return {
        "n_trades": trades.n_trades,
        "median_mfe": float(np.median(mfe)),
        "median_mae": float(np.median(mae)),
        "mean_mfe": float(np.mean(mfe)),
        "mean_mae": float(np.mean(mae)),
        "win_rate": float(np.mean(mfe > 0)),
        "mfe_p95": float(np.percentile(mfe, 95)),
        "mfe_p99": float(np.percentile(mfe, 99)),
        "mae_p5": float(np.percentile(mae, 5)),
        "mae_p1": float(np.percentile(mae, 1)),
        "mfe_mae_corr": float(np.corrcoef(mfe, mae)[0, 1]),
    }
