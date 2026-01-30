"""Statistical and utility helpers for trade geometry analysis."""

import numpy as np
from typing import Tuple


def trim_iqr(
    x: np.ndarray, y: np.ndarray, k: float = 1.5
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Remove outliers using IQR (Interquartile Range) fences.

    Parameters
    ----------
    x : np.ndarray
        X-axis values (e.g., MFE)
    y : np.ndarray
        Y-axis values (e.g., MAE)
    k : float
        IQR multiplier for fence distance (default 1.5, use 3.0 for very permissive)

    Returns
    -------
    x_trimmed : np.ndarray
        Trimmed x values
    y_trimmed : np.ndarray
        Trimmed y values
    keep_mask : np.ndarray
        Boolean mask indicating which points were kept

    Notes
    -----
    Fences are applied independently to both x and y:
    - Lower fence: Q1 - k * IQR
    - Upper fence: Q3 + k * IQR
    Points outside either fence are removed.
    """
    if x.size == 0:
        return x, y, np.ones_like(x, dtype=bool)

    # Fences for x
    q1x, q3x = np.percentile(x, [25, 75])
    iqr_x = q3x - q1x
    lo_x, hi_x = q1x - k * iqr_x, q3x + k * iqr_x

    # Fences for y
    q1y, q3y = np.percentile(y, [25, 75])
    iqr_y = q3y - q1y
    lo_y, hi_y = q1y - k * iqr_y, q3y + k * iqr_y

    # Keep points within both fences
    keep = (x >= lo_x) & (x <= hi_x) & (y >= lo_y) & (y <= hi_y)

    return x[keep], y[keep], keep


def trim_percentile(
    x: np.ndarray,
    y: np.ndarray,
    p: Tuple[float, float] = (1.0, 99.0),
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Remove outliers using percentile bounds.

    Parameters
    ----------
    x : np.ndarray
        X-axis values (e.g., MFE)
    y : np.ndarray
        Y-axis values (e.g., MAE)
    p : tuple of (low, high)
        Percentile bounds (default: 1st to 99th percentile)

    Returns
    -------
    x_trimmed : np.ndarray
        Trimmed x values
    y_trimmed : np.ndarray
        Trimmed y values
    keep_mask : np.ndarray
        Boolean mask indicating which points were kept
    """
    if x.size == 0:
        return x, y, np.ones_like(x, dtype=bool)

    # Percentile bounds for x
    lo_x, hi_x = np.percentile(x, p)

    # Percentile bounds for y
    lo_y, hi_y = np.percentile(y, p)

    # Keep points within both bounds
    keep = (x >= lo_x) & (x <= hi_x) & (y >= lo_y) & (y <= hi_y)

    return x[keep], y[keep], keep


def knee_point(curve_x: np.ndarray, curve_y: np.ndarray) -> Tuple[float, float]:
    """
    Find the knee point (elbow) on a curve using maximum distance to line method.

    The knee point is the point on the curve with maximum perpendicular distance
    to the straight line connecting the first and last points of the curve.

    Parameters
    ----------
    curve_x : np.ndarray
        X-coordinates of the curve (should be sorted)
    curve_y : np.ndarray
        Y-coordinates of the curve

    Returns
    -------
    knee_x : float
        X-coordinate of the knee point
    knee_y : float
        Y-coordinate of the knee point

    Notes
    -----
    This is a simple but robust method for finding diminishing returns points
    on frontier curves. It works well for convex/concave curves but may not
    be ideal for noisy or multi-modal curves.
    """
    if len(curve_x) < 3:
        # Not enough points for a knee
        return curve_x[0], curve_y[0]

    # Line from first to last point: (x0, y0) to (xn, yn)
    x0, y0 = curve_x[0], curve_y[0]
    xn, yn = curve_x[-1], curve_y[-1]

    # Vector of the line
    line_vec = np.array([xn - x0, yn - y0])
    line_len = np.linalg.norm(line_vec)

    if line_len == 0:
        # Degenerate case: all points are the same
        return x0, y0

    # Unit vector along the line
    line_unit = line_vec / line_len

    # For each point, compute perpendicular distance to line
    distances = []
    for i in range(len(curve_x)):
        # Vector from first point to current point
        point_vec = np.array([curve_x[i] - x0, curve_y[i] - y0])

        # Project onto line
        proj_len = np.dot(point_vec, line_unit)

        # Perpendicular vector
        perp_vec = point_vec - proj_len * line_unit

        # Distance
        dist = np.linalg.norm(perp_vec)
        distances.append(dist)

    # Knee is the point with maximum distance
    knee_idx = np.argmax(distances)

    return curve_x[knee_idx], curve_y[knee_idx]


def safe_divide(
    a: np.ndarray, b: np.ndarray, fill_value: float = 0.0
) -> np.ndarray:
    """
    Safe element-wise division handling division by zero.

    Parameters
    ----------
    a : np.ndarray
        Numerator
    b : np.ndarray
        Denominator
    fill_value : float
        Value to use when denominator is zero or invalid

    Returns
    -------
    np.ndarray
        Result of division with fill_value for invalid cases
    """
    result = np.full_like(a, fill_value, dtype=float)
    valid = (b != 0) & np.isfinite(b)
    result[valid] = a[valid] / b[valid]
    return result
