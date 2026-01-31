# v16_hazard_index.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple, Union, List, Set

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree


@dataclass(frozen=True)
class HazardParams:
    R0: float      # meters
    r: float       # meters
    L: int
    gamma: float
    alpha: float
    d0: float      # meters


def _to_utc_ts(x: Union[str, datetime, pd.Timestamp]) -> pd.Timestamp:
    return pd.to_datetime(x, utc=True, errors="raise")


def _ensure_utc_col(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        raise KeyError(f"Missing required column: {col}")
    return pd.to_datetime(df[col], utc=True, errors="coerce")


def _active_anytime_in_window(df2: pd.DataFrame, w_start: pd.Timestamp, w_end: pd.Timestamp) -> pd.DataFrame:
    start = _ensure_utc_col(df2, "situation_record_creation_time")
    end = _ensure_utc_col(df2, "situation_record_end_time")
    mask = (start <= w_end) & (end.isna() | (end >= w_start))
    out = df2.loc[mask].copy()
    out["situation_record_creation_time"] = start.loc[mask]
    out["situation_record_end_time"] = end.loc[mask]
    return out


def _compute_midpoint_latlon(df: pd.DataFrame) -> pd.DataFrame:
    needed = {"from_latitude", "from_longitude", "to_latitude", "to_longitude"}
    missing = needed - set(df.columns)
    if missing:
        raise KeyError(f"Missing coordinate columns: {sorted(missing)}")

    out = df.copy()
    for c in ["from_latitude", "from_longitude", "to_latitude", "to_longitude"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out["latitude"] = out[["from_latitude", "to_latitude"]].mean(axis=1)
    out["longitude"] = out[["from_longitude", "to_longitude"]].mean(axis=1)
    out = out.dropna(subset=["latitude", "longitude"]).copy()
    return out


def hazard_index_v16(
    *,
    params: HazardParams,
    q_lat: float,
    q_lon: float,
    df2: pd.DataFrame,
    window_start: Union[str, datetime, pd.Timestamp],
    window_end: Optional[Union[str, datetime, pd.Timestamp]] = None,
    return_details: bool = False,
) -> Union[float, Tuple[float, Dict]]:
    """
    Fast hazard index without NxN distances:
      - filter incidents active anytime in window
      - compute per-incident midpoint lat/lon
      - BallTree(haversine) to:
          * find seeds within R0 of q
          * expand by radius r from frontier nodes (BFS) up to L hops
    """
    if window_end is None:
        w_end = pd.Timestamp.now(tz="UTC")
    else:
        w_end = _to_utc_ts(window_end)
    w_start = _to_utc_ts(window_start)
    if w_start > w_end:
        raise ValueError("window_start must be <= window_end")

    if params.R0 <= 0 or params.r <= 0 or params.L < 0 or params.gamma <= 0 or params.alpha <= 0 or params.d0 <= 0:
        raise ValueError("Invalid params. Require R0>0, r>0, L>=0, gamma>0, alpha>0, d0>0.")

    # 1) filter + midpoints
    active = _active_anytime_in_window(df2, w_start, w_end)
    if active.empty:
        return (0.0, {"reason": "no_active_incidents"}) if return_details else 0.0

    active = _compute_midpoint_latlon(active)
    if active.empty:
        return (0.0, {"reason": "no_valid_coordinates"}) if return_details else 0.0

    pts_deg = active[["latitude", "longitude"]].to_numpy(dtype=float)

    # Convert to radians for haversine BallTree
    pts_rad = np.radians(pts_deg)
    q_rad = np.radians(np.array([[q_lat, q_lon]], dtype=float))

    # Build tree
    tree = BallTree(pts_rad, metric="haversine")

    # Convert meters to radians (Earth radius)
    R_earth = 6_371_000.0
    R0_rad = params.R0 / R_earth
    r_rad = params.r / R_earth

    # Distances to q (in meters) for w_i(q)
    # BallTree can return dist in radians; convert to meters
    d_q_rad = tree.query(q_rad, k=pts_rad.shape[0], return_distance=True)[0].ravel()
    d_q_m = d_q_rad * R_earth

    w = 1.0 / (1.0 + params.alpha * np.log(1.0 + (d_q_m / params.d0)))

    # 2) Seeds: within R0
    seed_idx = tree.query_radius(q_rad, r=R0_rad, return_distance=False)[0].astype(int)
    layers: List[np.ndarray] = [seed_idx]
    visited: Set[int] = set(seed_idx.tolist())

    # 3) BFS expansion up to L
    frontier = seed_idx
    for k in range(params.L):
        if frontier.size == 0:
            layers.append(np.array([], dtype=int))
            frontier = layers[-1]
            continue

        # Neighbors within r for all nodes in frontier
        neigh_lists = tree.query_radius(pts_rad[frontier], r=r_rad, return_distance=False)

        # Flatten + unique
        cand = np.unique(np.concatenate(neigh_lists).astype(int))
        # Remove visited
        next_nodes = np.array([j for j in cand.tolist() if j not in visited], dtype=int)

        for j in next_nodes.tolist():
            visited.add(j)

        layers.append(next_nodes)
        frontier = next_nodes

    # 4) Compute H(q)
    H = 0.0
    beta_list = []
    layer_sums = []
    for k, idx in enumerate(layers[: params.L + 1]):
        beta_k = 1.0 / (1.0 + params.gamma * np.log(1.0 + k))
        beta_list.append(float(beta_k))
        s = float(np.sum(w[idx])) if idx.size else 0.0
        layer_sums.append(s)
        H += beta_k * s

    if not return_details:
        return float(H)

    ids = active["situation_id"].to_numpy() if "situation_id" in active.columns else None
    layers_ids = [ids[layer].tolist() for layer in layers[: params.L + 1]] if ids is not None else None

    return float(H), {
        "H": float(H),
        "window_start": w_start,
        "window_end": w_end,
        "N_active_anytime": int(len(active)),
        "seed_count": int(len(layers[0])),
        "visited_count": int(len(visited)),
        "beta": beta_list,
        "layer_weight_sums": layer_sums,
        "layers_index": [layer.tolist() for layer in layers[: params.L + 1]],
        "layers_situation_id": layers_ids,
    }
