"""Clustering analysis: identify trade archetypes."""

import numpy as np
from typing import Dict, Any, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from ..core.trades import TradeSet
from ..analysis.ordering import ordering_label


def cluster_features(trades: TradeSet) -> Tuple[np.ndarray, list[str]]:
    """
    Construct feature matrix for clustering.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data

    Returns
    -------
    features : np.ndarray
        Feature matrix (n_trades x n_features)
    feature_names : list of str
        Names of features

    Notes
    -----
    Features include:
    - MFE (max favorable excursion)
    - MAE (max adverse excursion)
    - MFE/|MAE| ratio (avoid div by zero)
    - t_mfe (time to reach MFE)
    - t_mae (time to reach MAE)
    - ordering_encoded (0=tie, 1=mfe_first, 2=mae_first)
    """
    mfe = trades.mfe
    mae = trades.mae
    dd = -mae  # Positive drawdown

    # Avoid division by zero in ratio
    ratio = np.zeros_like(mfe, dtype=float)
    valid_mask = dd > 0
    ratio[valid_mask] = mfe[valid_mask] / dd[valid_mask]

    # Ordering encoding
    labels = ordering_label(trades)
    ordering_encoded = np.zeros(len(labels))
    ordering_encoded[labels == "mfe_first"] = 1
    ordering_encoded[labels == "mae_first"] = 2

    # Time features
    t_mfe = trades.t_mfe.astype(float)
    t_mae = trades.t_mae.astype(float)

    features = np.column_stack([mfe, mae, ratio, t_mfe, t_mae, ordering_encoded])

    feature_names = [
        "mfe",
        "mae",
        "mfe_mae_ratio",
        "t_mfe",
        "t_mae",
        "ordering",
    ]

    return features, feature_names


def cluster_trades(
    trades: TradeSet,
    n_clusters: int | None = None,
    max_clusters: int = 6,
    method: str = "kmeans",
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Cluster trades into archetypes.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    n_clusters : int, optional
        Number of clusters. If None, automatically select using silhouette score.
    max_clusters : int
        Maximum number of clusters to test for auto-selection
    method : {'kmeans', 'hdbscan'}
        Clustering method
    random_state : int
        Random seed for reproducibility

    Returns
    -------
    dict
        Dictionary containing:
        - 'labels': cluster labels (n_trades,)
        - 'n_clusters': number of clusters
        - 'features': feature matrix
        - 'feature_names': list of feature names
        - 'scaler': fitted StandardScaler
        - 'model': fitted clustering model
    """
    features, feature_names = cluster_features(trades)

    # Standardize features
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    if method == "kmeans":
        if n_clusters is None:
            # Auto-select using silhouette score
            best_k = 3
            best_score = -1

            for k in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
                labels = kmeans.fit_predict(features_scaled)

                if len(np.unique(labels)) < 2:
                    continue

                score = silhouette_score(features_scaled, labels)

                if score > best_score:
                    best_score = score
                    best_k = k

            n_clusters = best_k

        model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        labels = model.fit_predict(features_scaled)

    elif method == "hdbscan":
        try:
            import hdbscan

            model = hdbscan.HDBSCAN(min_cluster_size=max(5, trades.n_trades // 20))
            labels = model.fit_predict(features_scaled)
            n_clusters = len(np.unique(labels[labels >= 0]))

        except ImportError:
            raise ImportError(
                "HDBSCAN not available. Install with: pip install hdbscan"
            )

    else:
        raise ValueError(f"Unknown method: {method}")

    return {
        "labels": labels,
        "n_clusters": n_clusters,
        "features": features,
        "features_scaled": features_scaled,
        "feature_names": feature_names,
        "scaler": scaler,
        "model": model,
    }


def cluster_summary(trades: TradeSet, cluster_result: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
    """
    Generate summary statistics for each cluster.

    Parameters
    ----------
    trades : TradeSet
        Trade geometry data
    cluster_result : dict
        Output from cluster_trades

    Returns
    -------
    dict
        Dictionary mapping cluster_id -> summary dict with:
        - 'count': number of trades
        - 'median_mfe': median MFE
        - 'median_mae': median MAE
        - 'win_rate': fraction with MFE > 0
        - 'mfe_first_rate': fraction where MFE came first
        - 'mae_first_rate': fraction where MAE came first
        - 'median_t_mfe': median time to MFE
        - 'median_t_mae': median time to MAE
    """
    labels = cluster_result["labels"]
    cluster_ids = np.unique(labels)

    # Filter out noise points (label = -1 for HDBSCAN)
    cluster_ids = cluster_ids[cluster_ids >= 0]

    summaries = {}

    for cluster_id in cluster_ids:
        mask = labels == cluster_id

        cluster_mfe = trades.mfe[mask]
        cluster_mae = trades.mae[mask]
        cluster_t_mfe = trades.t_mfe[mask]
        cluster_t_mae = trades.t_mae[mask]

        # Ordering
        ordering = ordering_label(trades)
        cluster_ordering = ordering[mask]

        summaries[int(cluster_id)] = {
            "count": int(np.sum(mask)),
            "median_mfe": float(np.median(cluster_mfe)),
            "median_mae": float(np.median(cluster_mae)),
            "win_rate": float(np.mean(cluster_mfe > 0)),
            "mfe_first_rate": float(np.mean(cluster_ordering == "mfe_first")),
            "mae_first_rate": float(np.mean(cluster_ordering == "mae_first")),
            "median_t_mfe": float(np.median(cluster_t_mfe)),
            "median_t_mae": float(np.median(cluster_t_mae)),
        }

    return summaries


def suggest_exit_rules(
    cluster_summaries: Dict[int, Dict[str, Any]],
    mfe_threshold_fast: float = 1.0,
    dd_threshold_tight: float = 1.0,
) -> Dict[int, str]:
    """
    Suggest exit rule archetypes based on cluster characteristics.

    Parameters
    ----------
    cluster_summaries : dict
        Output from cluster_summary
    mfe_threshold_fast : float
        MFE threshold to consider "fast winner"
    dd_threshold_tight : float
        DD threshold to consider "tight stop friendly"

    Returns
    -------
    dict
        Dictionary mapping cluster_id -> archetype description
    """
    archetypes = {}

    for cluster_id, summary in cluster_summaries.items():
        mfe = summary["median_mfe"]
        dd = -summary["median_mae"]
        mfe_first_rate = summary["mfe_first_rate"]
        win_rate = summary["win_rate"]

        # Classify archetype
        if mfe > mfe_threshold_fast and dd < dd_threshold_tight and mfe_first_rate > 0.6:
            archetype = "Fast Winner (trailing stop)"
        elif mfe > mfe_threshold_fast and dd > dd_threshold_tight and mfe_first_rate < 0.4:
            archetype = "Needs Room (wide SL, time stop)"
        elif mfe < 0.5 and win_rate < 0.4:
            archetype = "Noise (consider filtering)"
        elif mfe > 2.0 and win_rate > 0.6:
            archetype = "Strong Edge (hold longer)"
        else:
            archetype = "Mixed (context-dependent)"

        archetypes[cluster_id] = archetype

    return archetypes
