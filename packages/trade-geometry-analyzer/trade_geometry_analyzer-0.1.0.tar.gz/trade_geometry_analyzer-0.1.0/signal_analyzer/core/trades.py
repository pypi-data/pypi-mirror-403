"""Compute trade paths and geometry metrics (MFE, MAE, timing)."""

import numpy as np
import pandas as pd
from typing import Literal
from dataclasses import dataclass


@dataclass
class TradeSet:
    """
    Container for trade geometry data.

    Attributes
    ----------
    side : {'long', 'short'}
        Trade direction
    n_trades : int
        Number of trades
    entry_idx : np.ndarray
        Entry bar indices (shape: n_trades)
    entry_price : np.ndarray
        Entry prices (shape: n_trades)
    mfe : np.ndarray
        Max Favorable Excursion in % (shape: n_trades)
    mae : np.ndarray
        Max Adverse Excursion in % (typically negative) (shape: n_trades)
    t_mfe : np.ndarray
        Time (bars) to reach MFE (shape: n_trades)
    t_mae : np.ndarray
        Time (bars) to reach MAE (shape: n_trades)
    vol_at_entry : np.ndarray, optional
        Volatility at entry (for normalization) (shape: n_trades)
    mfe_path : np.ndarray, optional
        Full MFE path over horizon (shape: n_trades, H)
    mae_path : np.ndarray, optional
        Full MAE path over horizon (shape: n_trades, H)
    """

    side: Literal["long", "short"]
    n_trades: int
    entry_idx: np.ndarray
    entry_price: np.ndarray
    mfe: np.ndarray
    mae: np.ndarray
    t_mfe: np.ndarray
    t_mae: np.ndarray
    vol_at_entry: np.ndarray | None = None
    mfe_path: np.ndarray | None = None
    mae_path: np.ndarray | None = None

    def __repr__(self):
        return (
            f"TradeSet(side={self.side}, n_trades={self.n_trades}, "
            f"median_mfe={np.median(self.mfe):.2f}%, "
            f"median_mae={np.median(self.mae):.2f}%)"
        )


def compute_trade_paths(
    ohlc: pd.DataFrame,
    entries: np.ndarray,
    H: int,
    side: Literal["long", "short"],
    open_col: str = "Open",
    high_col: str = "High",
    low_col: str = "Low",
    vol_col: str | None = None,
    store_paths: bool = False,
) -> TradeSet:
    """
    Extract forward windows for each trade and compute MFE/MAE metrics.

    Parameters
    ----------
    ohlc : pd.DataFrame
        OHLC data with columns: Open, High, Low (and optionally volatility)
    entries : np.ndarray
        Array of entry indices (from signal_to_events)
    H : int
        Forward horizon in bars
    side : {'long', 'short'}
        Trade direction
    open_col, high_col, low_col : str
        Column names for OHLC
    vol_col : str, optional
        Column name for volatility (e.g., ATR)
    store_paths : bool
        If True, store full MFE/MAE paths (shape: n_trades, H)

    Returns
    -------
    TradeSet
        Container with trade geometry data

    Notes
    -----
    - MFE: Max Favorable Excursion (best achievable profit %)
    - MAE: Max Adverse Excursion (worst drawdown %, typically negative)
    - For longs: favorable = high, adverse = low
    - For shorts: favorable = low (inverted for PnL), adverse = high
    - Trades with insufficient forward bars or invalid data are excluded
    """
    o = ohlc[open_col].to_numpy(dtype=float)
    hi = ohlc[high_col].to_numpy(dtype=float)
    lo = ohlc[low_col].to_numpy(dtype=float)
    n = len(ohlc)

    vol = None
    if vol_col and vol_col in ohlc.columns:
        vol = ohlc[vol_col].to_numpy(dtype=float)

    # Filter valid entries (must have H bars ahead)
    valid_entries = entries[entries < n - H]

    # Pre-allocate arrays
    n_valid = len(valid_entries)
    entry_prices = np.full(n_valid, np.nan)
    mfe_arr = np.full(n_valid, np.nan)
    mae_arr = np.full(n_valid, np.nan)
    t_mfe_arr = np.full(n_valid, -1, dtype=int)  # Use -1 as sentinel for invalid
    t_mae_arr = np.full(n_valid, -1, dtype=int)  # Use -1 as sentinel for invalid
    vol_arr = np.full(n_valid, np.nan) if vol is not None else None

    if store_paths:
        mfe_path_arr = np.full((n_valid, H), np.nan)
        mae_path_arr = np.full((n_valid, H), np.nan)
    else:
        mfe_path_arr = None
        mae_path_arr = None

    valid_mask = np.ones(n_valid, dtype=bool)

    for i, t in enumerate(valid_entries):
        entry = o[t]

        # Skip invalid entries
        if not np.isfinite(entry) or entry <= 0:
            valid_mask[i] = False
            continue

        # Extract forward window
        w_hi = hi[t + 1 : t + H + 1]
        w_lo = lo[t + 1 : t + H + 1]

        # Skip if no valid data in window
        if not np.isfinite(w_hi).any() or not np.isfinite(w_lo).any():
            valid_mask[i] = False
            continue

        entry_prices[i] = entry

        if vol is not None:
            vol_arr[i] = vol[t]

        if side == "long":
            # Long: profit from high, loss from low
            fav_path = (w_hi / entry - 1.0) * 100.0  # % gains
            adv_path = (w_lo / entry - 1.0) * 100.0  # % drawdowns (negative)

        else:  # short
            # Short: profit when price drops, loss when price rises
            fav_path = (entry / w_lo - 1.0) * 100.0  # % gains
            adv_path = (entry / w_hi - 1.0) * 100.0  # % drawdowns (negative)

        # Compute cumulative extremes
        fav_cum = np.maximum.accumulate(fav_path)
        adv_cum = np.minimum.accumulate(adv_path)

        # Final MFE/MAE
        mfe = np.nanmax(fav_cum)
        mae = np.nanmin(adv_cum)

        # Time to reach MFE/MAE (first occurrence)
        t_mfe = np.nanargmax(fav_cum) + 1  # +1 for bar offset
        t_mae = np.nanargmin(adv_cum) + 1

        # Validate results
        if not (np.isfinite(mfe) and np.isfinite(mae)):
            valid_mask[i] = False
            continue

        mfe_arr[i] = mfe
        mae_arr[i] = mae
        t_mfe_arr[i] = t_mfe
        t_mae_arr[i] = t_mae

        if store_paths:
            mfe_path_arr[i] = fav_cum
            mae_path_arr[i] = adv_cum

    # Filter out invalid trades
    entry_idx_final = valid_entries[valid_mask]
    entry_price_final = entry_prices[valid_mask]
    mfe_final = mfe_arr[valid_mask]
    mae_final = mae_arr[valid_mask]
    t_mfe_final = t_mfe_arr[valid_mask]
    t_mae_final = t_mae_arr[valid_mask]
    vol_final = vol_arr[valid_mask] if vol_arr is not None else None

    if store_paths:
        mfe_path_final = mfe_path_arr[valid_mask]
        mae_path_final = mae_path_arr[valid_mask]
    else:
        mfe_path_final = None
        mae_path_final = None

    return TradeSet(
        side=side,
        n_trades=len(entry_idx_final),
        entry_idx=entry_idx_final,
        entry_price=entry_price_final,
        mfe=mfe_final,
        mae=mae_final,
        t_mfe=t_mfe_final,
        t_mae=t_mae_final,
        vol_at_entry=vol_final,
        mfe_path=mfe_path_final,
        mae_path=mae_path_final,
    )
