"""Convert continuous signals into discrete entry events."""

import numpy as np
import pandas as pd
from typing import Literal


def signal_to_events(
    df: pd.DataFrame,
    sig_col: str = "sig",
    mode: Literal["transitions", "levels"] = "transitions",
) -> dict[str, np.ndarray]:
    """
    Convert continuous signals into discrete entry events (Long/Short).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing signal column
    sig_col : str
        Name of signal column (expected values: +1 for long, -1 for short, 0 for neutral)
    mode : {'transitions', 'levels'}
        'transitions': Fire events only on state changes (enter_long, enter_short)
        'levels': Fire events on all long/short signals

    Returns
    -------
    dict
        Dictionary with keys:
        - 'enter_long': numpy array of integer indices where long entries occur
        - 'enter_short': numpy array of integer indices where short entries occur
        - 'exit_long': numpy array of integer indices where long exits occur (optional)
        - 'exit_short': numpy array of integer indices where short exits occur (optional)

    Notes
    -----
    Transitions are defined as:
    - enter_long: previous signal <= 0 and current signal > 0
    - enter_short: previous signal >= 0 and current signal < 0
    - exit_long: previous signal > 0 and current signal <= 0
    - exit_short: previous signal < 0 and current signal >= 0
    """
    sig = df[sig_col].to_numpy(dtype=float)
    n = len(sig)

    if mode == "transitions":
        # Compute state changes
        sig_prev = np.roll(sig, 1)
        sig_prev[0] = 0  # assume neutral start

        # Enter long: was not-long, now long
        enter_long = np.where((sig_prev <= 0) & (sig > 0))[0]

        # Enter short: was not-short, now short
        enter_short = np.where((sig_prev >= 0) & (sig < 0))[0]

        # Exit long: was long, now not-long
        exit_long = np.where((sig_prev > 0) & (sig <= 0))[0]

        # Exit short: was short, now not-short
        exit_short = np.where((sig_prev < 0) & (sig >= 0))[0]

        return {
            "enter_long": enter_long,
            "enter_short": enter_short,
            "exit_long": exit_long,
            "exit_short": exit_short,
        }

    elif mode == "levels":
        # All bars where signal is long/short
        enter_long = np.where(sig > 0)[0]
        enter_short = np.where(sig < 0)[0]

        return {
            "enter_long": enter_long,
            "enter_short": enter_short,
        }

    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'transitions' or 'levels'.")
