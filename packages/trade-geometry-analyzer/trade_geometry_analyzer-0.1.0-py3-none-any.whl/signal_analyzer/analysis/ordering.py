"""Time-sequencing analysis: Profit first vs Pain first."""

import numpy as np
from typing import Dict, Any, Literal

from ..core.trades import TradeSet


def ordering_label(trades: TradeSet) -> np.ndarray:
    """
    Classify each trade as MFE-first, MAE-first, or tie.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data (must have t_mfe and t_mae)

    Returns
    -------
    np.ndarray
        Array of strings: 'mfe_first', 'mae_first', or 'tie'

    Notes
    -----
    - mfe_first: profit came before pain (t_mfe < t_mae)
    - mae_first: pain came before profit (t_mae < t_mfe)
    - tie: both occurred at same time (rare)
    """
    labels = np.empty(trades.n_trades, dtype=object)

    mfe_first_mask = trades.t_mfe < trades.t_mae
    mae_first_mask = trades.t_mae < trades.t_mfe
    tie_mask = trades.t_mfe == trades.t_mae

    labels[mfe_first_mask] = "mfe_first"
    labels[mae_first_mask] = "mae_first"
    labels[tie_mask] = "tie"

    return labels


def split_by_ordering(trades: TradeSet) -> Dict[str, Dict[str, np.ndarray]]:
    """
    Split trades into subsets based on ordering.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data

    Returns
    -------
    dict
        Dictionary with keys 'mfe_first', 'mae_first', 'tie', each containing:
        - 'mfe': MFE values
        - 'mae': MAE values
        - 'indices': original indices
        - 'count': number of trades
    """
    labels = ordering_label(trades)

    result = {}
    for label in ["mfe_first", "mae_first", "tie"]:
        mask = labels == label
        result[label] = {
            "mfe": trades.mfe[mask],
            "mae": trades.mae[mask],
            "indices": np.where(mask)[0],
            "count": np.sum(mask),
        }

    return result


def ordering_proportions(trades: TradeSet) -> Dict[str, float]:
    """
    Calculate proportions of each ordering type.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data

    Returns
    -------
    dict
        Dictionary with proportions:
        - 'mfe_first': fraction of MFE-first trades
        - 'mae_first': fraction of MAE-first trades
        - 'tie': fraction of ties
    """
    labels = ordering_label(trades)

    n = trades.n_trades
    return {
        "mfe_first": np.sum(labels == "mfe_first") / n,
        "mae_first": np.sum(labels == "mae_first") / n,
        "tie": np.sum(labels == "tie") / n,
    }


def trailing_suitability(
    trades: TradeSet,
    mfe_threshold: float = 0.0,
    mae_threshold: float = -1.0,
) -> Dict[str, Any]:
    """
    Calculate "trailing stop suitability" metric.

    This measures the fraction of MFE-first trades where profit exceeded
    a threshold before drawdown exceeded a threshold.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    mfe_threshold : float
        Minimum MFE required to consider (e.g., 0.5% profit)
    mae_threshold : float
        Maximum MAE tolerated (e.g., -1.0% drawdown)

    Returns
    -------
    dict
        Dictionary with:
        - 'suitable_count': number of suitable trades
        - 'total_count': total number of trades
        - 'suitability_rate': fraction suitable
        - 'mfe_first_rate': fraction that are MFE-first among suitable
    """
    labels = ordering_label(trades)

    # Suitable trades: MFE > threshold AND MAE > threshold (less negative)
    suitable_mask = (trades.mfe >= mfe_threshold) & (trades.mae >= mae_threshold)
    suitable_trades = np.sum(suitable_mask)

    # Among suitable, how many are MFE-first?
    mfe_first_suitable = np.sum(
        suitable_mask & (labels == "mfe_first")
    )

    mfe_first_rate = (
        mfe_first_suitable / suitable_trades if suitable_trades > 0 else 0.0
    )

    return {
        "suitable_count": suitable_trades,
        "total_count": trades.n_trades,
        "suitability_rate": suitable_trades / trades.n_trades,
        "mfe_first_rate": mfe_first_rate,
    }


def needs_room(
    trades: TradeSet,
    mfe_threshold: float = 1.0,
) -> Dict[str, Any]:
    """
    Calculate "needs room" metric.

    This measures the success rate of MAE-first trades (trades that had
    to endure drawdown before profit).

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    mfe_threshold : float
        Minimum MFE required to be considered a "winner"

    Returns
    -------
    dict
        Dictionary with:
        - 'mae_first_count': number of MAE-first trades
        - 'mae_first_winners': number of MAE-first trades that became winners
        - 'success_rate': fraction of MAE-first trades that succeeded
        - 'median_dd_winners': median drawdown of winning MAE-first trades
        - 'median_dd_losers': median drawdown of losing MAE-first trades
    """
    labels = ordering_label(trades)

    mae_first_mask = labels == "mae_first"
    mae_first_count = np.sum(mae_first_mask)

    if mae_first_count == 0:
        return {
            "mae_first_count": 0,
            "mae_first_winners": 0,
            "success_rate": 0.0,
            "median_dd_winners": np.nan,
            "median_dd_losers": np.nan,
        }

    # Winners among MAE-first
    mae_first_winners_mask = mae_first_mask & (trades.mfe >= mfe_threshold)
    mae_first_winners = np.sum(mae_first_winners_mask)

    # Losers among MAE-first
    mae_first_losers_mask = mae_first_mask & (trades.mfe < mfe_threshold)

    median_dd_winners = (
        np.median(-trades.mae[mae_first_winners_mask])
        if mae_first_winners > 0
        else np.nan
    )

    median_dd_losers = (
        np.median(-trades.mae[mae_first_losers_mask])
        if np.sum(mae_first_losers_mask) > 0
        else np.nan
    )

    return {
        "mae_first_count": mae_first_count,
        "mae_first_winners": mae_first_winners,
        "success_rate": mae_first_winners / mae_first_count,
        "median_dd_winners": median_dd_winners,
        "median_dd_losers": median_dd_losers,
    }


def ordering_vs_horizon(
    ohlc,
    entries: np.ndarray,
    side: Literal["long", "short"],
    H_list: list[int],
    **kwargs,
) -> Dict[int, Dict[str, float]]:
    """
    Analyze how ordering proportions change with different horizons.

    Parameters
    ----------
    ohlc : pd.DataFrame
        OHLC data
    entries : np.ndarray
        Entry indices
    side : {'long', 'short'}
        Trade direction
    H_list : list of int
        List of horizons to test
    **kwargs
        Additional arguments for compute_trade_paths

    Returns
    -------
    dict
        Dictionary mapping H -> ordering proportions
        {H: {'mfe_first': float, 'mae_first': float, 'tie': float}}
    """
    from ..core.trades import compute_trade_paths

    result = {}

    for H in H_list:
        trades = compute_trade_paths(ohlc, entries, H, side, **kwargs)
        props = ordering_proportions(trades)
        result[H] = props

    return result
