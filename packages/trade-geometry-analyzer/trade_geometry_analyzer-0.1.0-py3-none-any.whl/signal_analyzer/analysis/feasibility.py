"""TP/SL feasibility analysis: probabilistic hitting of targets vs stops."""

import numpy as np
from typing import Dict, Any, Tuple

from ..core.trades import TradeSet


def hit_matrix(
    trades: TradeSet,
    tp_grid: np.ndarray,
    sl_grid: np.ndarray,
    min_sample: int = 5,
) -> Dict[str, Any]:
    """
    Compute probability heatmap: P(hit TP before SL) for grid of TP/SL values.

    This is path-dependent: checks if price hits TP before hitting SL within
    the trade horizon.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data (must have mfe_path and mae_path)
    tp_grid : np.ndarray
        Array of take-profit levels (positive %, e.g., [0.5, 1.0, 1.5, ...])
    sl_grid : np.ndarray
        Array of stop-loss levels (positive %, e.g., [0.5, 1.0, 1.5, ...])
    min_sample : int
        Minimum sample size required for valid cell

    Returns
    -------
    dict
        Dictionary containing:
        - 'tp_grid': array of TP values
        - 'sl_grid': array of SL values
        - 'prob_matrix': 2D array of P(TP before SL) [shape: len(tp_grid) x len(sl_grid)]
        - 'count_matrix': 2D array of sample counts
        - 'tp_hit_matrix': 2D array of TP hit counts
        - 'sl_hit_matrix': 2D array of SL hit counts

    Notes
    -----
    For each trade, we check the paths:
    - TP hit: first bar where MFE >= tp
    - SL hit: first bar where -MAE >= sl (i.e., MAE <= -sl)
    - TP before SL: t_tp < t_sl (or SL never hit)
    """
    if trades.mfe_path is None or trades.mae_path is None:
        raise ValueError(
            "TradeSet must have mfe_path and mae_path. "
            "Call compute_trade_paths with store_paths=True."
        )

    n_tp = len(tp_grid)
    n_sl = len(sl_grid)

    prob_matrix = np.full((n_tp, n_sl), np.nan)
    count_matrix = np.zeros((n_tp, n_sl), dtype=int)
    tp_hit_matrix = np.zeros((n_tp, n_sl), dtype=int)
    sl_hit_matrix = np.zeros((n_tp, n_sl), dtype=int)

    # For each trade, compute first hit times for all TP/SL combinations
    n_trades = trades.n_trades
    H = trades.mfe_path.shape[1]

    for i_tp, tp in enumerate(tp_grid):
        for i_sl, sl in enumerate(sl_grid):
            tp_before_sl_count = 0
            valid_trades = 0

            for i_trade in range(n_trades):
                mfe_path = trades.mfe_path[i_trade]
                mae_path = trades.mae_path[i_trade]

                # Find first hit times
                tp_hit_bars = np.where(mfe_path >= tp)[0]
                sl_hit_bars = np.where(mae_path <= -sl)[0]

                t_tp = tp_hit_bars[0] if len(tp_hit_bars) > 0 else H + 1
                t_sl = sl_hit_bars[0] if len(sl_hit_bars) > 0 else H + 1

                # Valid trade: at least one was hit
                if t_tp <= H or t_sl <= H:
                    valid_trades += 1

                    if t_tp < t_sl:  # TP before SL
                        tp_before_sl_count += 1

                    if t_tp <= H:
                        tp_hit_matrix[i_tp, i_sl] += 1
                    if t_sl <= H:
                        sl_hit_matrix[i_tp, i_sl] += 1

            count_matrix[i_tp, i_sl] = valid_trades

            if valid_trades >= min_sample:
                prob_matrix[i_tp, i_sl] = tp_before_sl_count / valid_trades

    return {
        "tp_grid": tp_grid,
        "sl_grid": sl_grid,
        "prob_matrix": prob_matrix,
        "count_matrix": count_matrix,
        "tp_hit_matrix": tp_hit_matrix,
        "sl_hit_matrix": sl_hit_matrix,
    }


def ev_proxy(
    hit_data: Dict[str, Any],
    slippage: float = 0.0,
    commission: float = 0.0,
) -> Dict[str, Any]:
    """
    Compute expected value proxy for TP/SL grid.

    EV = P(TP) * TP - P(SL) * SL - costs

    Parameters
    ----------
    hit_data : dict
        Output from hit_matrix
    slippage : float
        Slippage cost per trade (% of entry)
    commission : float
        Commission cost per trade (% of entry)

    Returns
    -------
    dict
        Dictionary containing:
        - 'ev_matrix': 2D array of expected values
        - 'risk_reward_ratio': 2D array of TP/SL ratios
        - 'robust_zones': boolean mask where EV is positive and stable
    """
    tp_grid = hit_data["tp_grid"]
    sl_grid = hit_data["sl_grid"]
    prob_matrix = hit_data["prob_matrix"]

    # Create meshgrid for TP and SL
    TP, SL = np.meshgrid(tp_grid, sl_grid, indexing="ij")

    # EV calculation
    # EV = P(win) * TP - P(loss) * SL - costs
    ev_matrix = prob_matrix * TP - (1 - prob_matrix) * SL - (slippage + commission)

    # Risk-reward ratio
    risk_reward_ratio = TP / SL

    # Define "robust zones": EV > 0 and sufficient sample count
    min_count = 10
    robust_zones = (
        (ev_matrix > 0)
        & (hit_data["count_matrix"] >= min_count)
        & (~np.isnan(prob_matrix))
    )

    return {
        "ev_matrix": ev_matrix,
        "risk_reward_ratio": risk_reward_ratio,
        "robust_zones": robust_zones,
        "tp_grid": tp_grid,
        "sl_grid": sl_grid,
    }


def find_best_zones(
    ev_data: Dict[str, Any],
    top_n: int = 5,
) -> list[Dict[str, float]]:
    """
    Find the top N TP/SL zones by expected value.

    Parameters
    ----------
    ev_data : dict
        Output from ev_proxy
    top_n : int
        Number of top zones to return

    Returns
    -------
    list of dict
        List of top zones, each containing:
        - 'tp': take-profit level
        - 'sl': stop-loss level
        - 'ev': expected value
        - 'rr': risk-reward ratio
    """
    ev_matrix = ev_data["ev_matrix"]
    tp_grid = ev_data["tp_grid"]
    sl_grid = ev_data["sl_grid"]
    rr_matrix = ev_data["risk_reward_ratio"]
    robust_zones = ev_data["robust_zones"]

    # Mask with robust zones only
    ev_masked = ev_matrix.copy()
    ev_masked[~robust_zones] = -np.inf

    # Find top N indices
    flat_indices = np.argsort(ev_masked.ravel())[::-1][:top_n]
    top_indices = np.unravel_index(flat_indices, ev_matrix.shape)

    results = []
    for i in range(len(top_indices[0])):
        i_tp = top_indices[0][i]
        i_sl = top_indices[1][i]

        ev_val = ev_matrix[i_tp, i_sl]

        if np.isnan(ev_val) or ev_val == -np.inf:
            continue

        results.append(
            {
                "tp": tp_grid[i_tp],
                "sl": sl_grid[i_sl],
                "ev": ev_val,
                "rr": rr_matrix[i_tp, i_sl],
            }
        )

    return results
