"""
Volume Metrics Calculator

Computes volume-based metrics for market reaction analysis:
- Volume Z-score: How unusual is this bar's volume compared to recent history
- Relative Volume: Volume compared to typical volume at this time of day
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import numpy as np

from market_reaction.types import VolumeMetrics

logger = logging.getLogger("market_reaction.volume")


# Default lookback for rolling calculations
DEFAULT_LOOKBACK_BARS = 20
DEFAULT_TIME_OF_DAY_LOOKBACK_DAYS = 20


def compute_volume_zscore(
    volumes: pd.Series,
    target_idx: int,
    lookback: int = DEFAULT_LOOKBACK_BARS,
) -> float:
    """
    Compute volume z-score for a specific bar.

    Z-score = (volume - mean) / std

    Args:
        volumes: Series of volume values
        target_idx: Index of the target bar
        lookback: Number of bars to use for rolling stats

    Returns:
        Z-score (0 if insufficient data or std is 0)
    """
    if target_idx < lookback:
        # Not enough history, use what we have
        lookback = target_idx

    if lookback < 2:
        return 0.0

    # Get lookback window (excluding target bar)
    start_idx = target_idx - lookback
    window = volumes.iloc[start_idx:target_idx]

    mean = window.mean()
    std = window.std()

    if std == 0 or pd.isna(std):
        return 0.0

    target_volume = volumes.iloc[target_idx]
    zscore = (target_volume - mean) / std

    return round(float(zscore), 4)


def compute_relative_volume(
    df: pd.DataFrame,
    target_idx: int,
    lookback_days: int = DEFAULT_TIME_OF_DAY_LOOKBACK_DAYS,
) -> float:
    """
    Compute relative volume compared to typical volume at same time of day.

    Args:
        df: DataFrame with timestamp index and 'volume' column
        target_idx: Index position of the target bar
        lookback_days: Days to look back for same-time-of-day comparison

    Returns:
        Relative volume (1.0 = average, 2.0 = 2x average, etc.)
    """
    if df.empty or target_idx >= len(df):
        return 1.0

    target_ts = df.index[target_idx]
    target_volume = df.iloc[target_idx]["volume"]

    # Get time of day (hour and minute)
    target_hour = target_ts.hour
    target_minute = target_ts.minute

    # Find bars at same time of day in history
    same_time_volumes = []

    for i in range(target_idx):
        ts = df.index[i]
        # Same hour and minute (or within 5 minutes)
        if ts.hour == target_hour and abs(ts.minute - target_minute) <= 2:
            same_time_volumes.append(df.iloc[i]["volume"])

    if not same_time_volumes:
        # Fall back to simple rolling average
        start_idx = max(0, target_idx - DEFAULT_LOOKBACK_BARS)
        avg_vol = df.iloc[start_idx:target_idx]["volume"].mean()
        if avg_vol > 0:
            return round(float(target_volume / avg_vol), 4)
        return 1.0

    avg_same_time = np.mean(same_time_volumes)

    if avg_same_time <= 0:
        return 1.0

    return round(float(target_volume / avg_same_time), 4)


def compute_volume_percentile(
    volumes: pd.Series,
    target_idx: int,
    lookback: int = 100,
) -> float:
    """
    Compute what percentile the target volume is in vs recent history.

    Args:
        volumes: Series of volume values
        target_idx: Index of the target bar
        lookback: Number of bars to compare against

    Returns:
        Percentile (0-100)
    """
    start_idx = max(0, target_idx - lookback)
    window = volumes.iloc[start_idx : target_idx + 1]

    if len(window) < 2:
        return 50.0

    target_volume = volumes.iloc[target_idx]
    percentile = (window < target_volume).sum() / len(window) * 100

    return round(float(percentile), 2)


def compute_volume_metrics(
    df: pd.DataFrame,
    target_idx: int,
    lookback_bars: int = DEFAULT_LOOKBACK_BARS,
    lookback_days: int = DEFAULT_TIME_OF_DAY_LOOKBACK_DAYS,
) -> VolumeMetrics:
    """
    Compute all volume metrics for a specific bar.

    Args:
        df: DataFrame with timestamp index and 'volume' column
        target_idx: Index position of the target bar
        lookback_bars: Bars for rolling z-score calculation
        lookback_days: Days for time-of-day comparison

    Returns:
        VolumeMetrics dataclass with all computed metrics
    """
    if df.empty or target_idx >= len(df) or target_idx < 0:
        return VolumeMetrics(
            volume=0,
            volume_zscore=0.0,
            relative_volume=1.0,
            avg_volume_20bar=0.0,
            volume_percentile=50.0,
        )

    volumes = df["volume"]
    target_volume = int(volumes.iloc[target_idx])

    # Compute z-score
    zscore = compute_volume_zscore(volumes, target_idx, lookback_bars)

    # Compute relative volume
    rel_vol = compute_relative_volume(df, target_idx, lookback_days)

    # Compute rolling average
    start_idx = max(0, target_idx - lookback_bars)
    avg_vol = (
        volumes.iloc[start_idx:target_idx].mean() if target_idx > 0 else target_volume
    )

    # Compute percentile
    percentile = compute_volume_percentile(volumes, target_idx)

    return VolumeMetrics(
        volume=target_volume,
        volume_zscore=zscore,
        relative_volume=rel_vol,
        avg_volume_20bar=round(float(avg_vol), 2),
        volume_percentile=percentile,
    )


def compute_volume_metrics_for_bars(
    df: pd.DataFrame,
    bar_indices: list[int],
) -> dict[int, VolumeMetrics]:
    """
    Compute volume metrics for multiple bars efficiently.

    Args:
        df: DataFrame with timestamp index and 'volume' column
        bar_indices: List of bar indices to compute metrics for

    Returns:
        Dict mapping bar index to VolumeMetrics
    """
    results = {}

    for idx in bar_indices:
        results[idx] = compute_volume_metrics(df, idx)

    return results


def is_unusual_volume(
    metrics: VolumeMetrics,
    zscore_threshold: float = 2.0,
    relative_threshold: float = 2.0,
) -> bool:
    """
    Check if volume metrics indicate unusual activity.

    Args:
        metrics: Computed volume metrics
        zscore_threshold: Z-score threshold for unusual (default 2.0 = 2 std devs)
        relative_threshold: Relative volume threshold (default 2.0 = 2x normal)

    Returns:
        True if volume is unusually high
    """
    return (
        abs(metrics.volume_zscore) >= zscore_threshold
        or metrics.relative_volume >= relative_threshold
    )


def classify_volume_activity(metrics: VolumeMetrics) -> str:
    """
    Classify volume activity level.

    Args:
        metrics: Computed volume metrics

    Returns:
        Classification string: 'very_low', 'low', 'normal', 'high', 'very_high', 'extreme'
    """
    zscore = metrics.volume_zscore

    if zscore < -2.0:
        return "very_low"
    elif zscore < -1.0:
        return "low"
    elif zscore < 1.0:
        return "normal"
    elif zscore < 2.0:
        return "high"
    elif zscore < 3.0:
        return "very_high"
    else:
        return "extreme"
