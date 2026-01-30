"""Frontier analysis: risk/reward boundaries and knee points."""

import numpy as np
from typing import Dict, Any, Tuple

from ..core.trades import TradeSet
from ..core.utils import knee_point


def frontier_risk_constrained(
    trades: TradeSet,
    dd_grid: np.ndarray,
    q: float = 0.9,
    min_sample: int = 5,
) -> Dict[str, Any]:
    """
    Compute risk-constrained frontier: Max MFE for given MAE limits.

    For each drawdown cap in dd_grid, find the q-th quantile of MFE
    among trades that stay within that drawdown limit.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    dd_grid : np.ndarray
        Array of drawdown limits (positive values, e.g., [0.5, 1.0, 1.5, ...])
    q : float
        Quantile for MFE (e.g., 0.9 = 90th percentile)
    min_sample : int
        Minimum number of trades required for valid point

    Returns
    -------
    dict
        Dictionary containing:
        - 'dd': array of drawdown caps (x-axis)
        - 'mfe': array of MFE quantiles (y-axis)
        - 'counts': array of sample counts at each point
        - 'knee': tuple of (knee_dd, knee_mfe)
    """
    mfe = trades.mfe
    mae = trades.mae
    dd = -mae  # Convert MAE to positive drawdown

    dd_arr = []
    mfe_arr = []
    counts = []

    for dd_cap in dd_grid:
        # Select trades within drawdown limit
        mask = dd <= dd_cap
        trades_subset = mfe[mask]

        if len(trades_subset) < min_sample:
            continue

        # Compute quantile of MFE
        mfe_q = np.percentile(trades_subset, q * 100)

        dd_arr.append(dd_cap)
        mfe_arr.append(mfe_q)
        counts.append(len(trades_subset))

    dd_arr = np.array(dd_arr)
    mfe_arr = np.array(mfe_arr)
    counts = np.array(counts)

    # Find knee point
    if len(dd_arr) >= 3:
        knee_dd, knee_mfe = knee_point(dd_arr, mfe_arr)
    else:
        knee_dd, knee_mfe = dd_arr[0] if len(dd_arr) > 0 else 0, mfe_arr[0] if len(mfe_arr) > 0 else 0

    return {
        "dd": dd_arr,
        "mfe": mfe_arr,
        "counts": counts,
        "knee": (knee_dd, knee_mfe),
    }


def frontier_opportunity_constrained(
    trades: TradeSet,
    tp_grid: np.ndarray,
    q: float = 0.8,
    min_sample: int = 5,
) -> Dict[str, Any]:
    """
    Compute opportunity-constrained frontier: Min MAE for desired MFE targets.

    For each profit target in tp_grid, find the q-th quantile of MAE
    (drawdown) among trades that achieved that target.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    tp_grid : np.ndarray
        Array of profit targets (positive values, e.g., [0.5, 1.0, 1.5, ...])
    q : float
        Quantile for MAE/drawdown (e.g., 0.8 = 80th percentile worst drawdown)
    min_sample : int
        Minimum number of trades required for valid point

    Returns
    -------
    dict
        Dictionary containing:
        - 'tp': array of profit targets (x-axis)
        - 'dd': array of drawdown quantiles (y-axis, positive values)
        - 'counts': array of sample counts at each point
        - 'knee': tuple of (knee_tp, knee_dd)
    """
    mfe = trades.mfe
    mae = trades.mae
    dd = -mae  # Convert MAE to positive drawdown

    tp_arr = []
    dd_arr = []
    counts = []

    for tp in tp_grid:
        # Select trades that achieved target
        mask = mfe >= tp
        trades_subset = dd[mask]

        if len(trades_subset) < min_sample:
            continue

        # Compute quantile of drawdown (typically upper quantile = worse case)
        dd_q = np.percentile(trades_subset, q * 100)

        tp_arr.append(tp)
        dd_arr.append(dd_q)
        counts.append(len(trades_subset))

    tp_arr = np.array(tp_arr)
    dd_arr = np.array(dd_arr)
    counts = np.array(counts)

    # Find knee point
    if len(tp_arr) >= 3:
        knee_tp, knee_dd = knee_point(tp_arr, dd_arr)
    else:
        knee_tp, knee_dd = tp_arr[0] if len(tp_arr) > 0 else 0, dd_arr[0] if len(dd_arr) > 0 else 0

    return {
        "tp": tp_arr,
        "dd": dd_arr,
        "counts": counts,
        "knee": (knee_tp, knee_dd),
    }


def compute_frontiers(
    trades: TradeSet,
    dd_grid: np.ndarray | None = None,
    tp_grid: np.ndarray | None = None,
    risk_q: float = 0.9,
    opp_q: float = 0.8,
) -> Dict[str, Any]:
    """
    Compute both risk-constrained and opportunity-constrained frontiers.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    dd_grid : np.ndarray, optional
        Drawdown grid for risk-constrained frontier.
        If None, auto-generate based on data.
    tp_grid : np.ndarray, optional
        Profit target grid for opportunity-constrained frontier.
        If None, auto-generate based on data.
    risk_q : float
        Quantile for risk-constrained frontier MFE
    opp_q : float
        Quantile for opportunity-constrained frontier MAE

    Returns
    -------
    dict
        Dictionary with keys:
        - 'risk_constrained': output from frontier_risk_constrained
        - 'opportunity_constrained': output from frontier_opportunity_constrained
    """
    # Auto-generate grids if not provided
    if dd_grid is None:
        dd_max = -trades.mae.min()  # Max observed drawdown
        dd_grid = np.linspace(0.1, dd_max, 30)

    if tp_grid is None:
        tp_max = trades.mfe.max()
        tp_grid = np.linspace(0.1, tp_max, 30)

    risk_frontier = frontier_risk_constrained(trades, dd_grid, q=risk_q)
    opp_frontier = frontier_opportunity_constrained(trades, tp_grid, q=opp_q)

    return {
        "risk_constrained": risk_frontier,
        "opportunity_constrained": opp_frontier,
    }
