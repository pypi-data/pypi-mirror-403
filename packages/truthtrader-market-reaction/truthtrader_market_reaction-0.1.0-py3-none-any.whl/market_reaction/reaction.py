"""
Core Reaction Computation

Computes market reactions with proper bar alignment using barvault.

Key principle: Event inside a bar → use next bar's OPEN as T0.
You cannot trade on information until the next bar opens.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import pandas as pd

from market_data import MarketDataClient

from market_reaction.types import REACTION_WINDOWS
from market_reaction.volume import compute_volume_metrics

logger = logging.getLogger("market_reaction.reaction")


def to_utc_naive(dt: datetime) -> datetime:
    """Convert an aware datetime to naive UTC."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def iso_z(dt_utc_naive: datetime) -> str:
    """Serialize a naive UTC datetime as ISO 8601 with Z suffix."""
    return dt_utc_naive.replace(microsecond=0).isoformat() + "Z"


def is_market_hours(dt: datetime, market: str = "NYSE") -> bool:
    """
    Check if datetime is during regular market hours.

    NYSE Market hours: 9:30 AM - 4:00 PM ET (14:30 - 21:00 UTC)

    Args:
        dt: Datetime to check (should be naive UTC)
        market: Market to check (currently only NYSE supported)

    Returns:
        True if during market hours
    """
    if market != "NYSE":
        logger.warning(f"Unknown market {market}, assuming NYSE hours")

    weekday = dt.weekday()
    if weekday >= 5:  # Weekend
        return False

    # Market hours in UTC: 14:30 - 21:00
    if dt.hour < 14 or dt.hour >= 21:
        return False
    if dt.hour == 14 and dt.minute < 30:
        return False

    return True


def find_market_open_after(dt: datetime, market: str = "NYSE") -> datetime:
    """
    Find the next market open after the given datetime.

    Args:
        dt: Datetime (naive UTC)
        market: Market (currently only NYSE supported)

    Returns:
        Next market open datetime (naive UTC)
    """
    current = dt
    for _ in range(10):
        weekday = current.weekday()

        if weekday >= 5:  # Weekend
            days_until_monday = (7 - weekday) % 7
            if days_until_monday == 0:
                days_until_monday = 1
            current = (current + timedelta(days=days_until_monday)).replace(
                hour=14, minute=30, second=0, microsecond=0
            )
            continue

        if current.hour < 14 or (current.hour == 14 and current.minute < 30):
            return current.replace(hour=14, minute=30, second=0, microsecond=0)

        current = (current + timedelta(days=1)).replace(
            hour=14, minute=30, second=0, microsecond=0
        )

    return (dt + timedelta(days=1)).replace(hour=14, minute=30, second=0, microsecond=0)


def find_t0_bar(
    bars: pd.DataFrame,
    event_time: datetime,
) -> Optional[dict[str, Any]]:
    """
    Find the T0 bar - the first bar we can trade on.

    CRITICAL: Event inside a bar means we use the NEXT bar's open.

    Args:
        bars: DataFrame with bars (must have 'ts' column and OHLCV data)
        event_time: Event timestamp (naive UTC)

    Returns:
        Dict with T0 bar info, or None if not found
    """
    if bars is None or bars.empty:
        return None

    # Ensure we have timestamps to search
    if "ts" not in bars.columns:
        logger.warning("Bars DataFrame missing 'ts' column")
        return None

    # Convert timestamps to comparable format
    bars = bars.copy()
    bars["ts_dt"] = pd.to_datetime(bars["ts"]).dt.tz_localize(None)

    # Find the first bar that starts AFTER the event
    # This is the bar whose OPEN we can actually trade at
    event_naive = to_utc_naive(event_time)

    mask = bars["ts_dt"] > event_naive
    future_bars = bars[mask]

    if future_bars.empty:
        return None

    t0_bar = future_bars.iloc[0]
    t0_idx = future_bars.index[0]
    t0_timestamp = t0_bar["ts_dt"]

    # Calculate gap between event and T0
    gap_seconds = int((t0_timestamp - event_naive).total_seconds())

    return {
        "timestamp": iso_z(t0_timestamp),
        "open": float(t0_bar["open"]),
        "close": float(t0_bar["close"]),
        "high": float(t0_bar["high"]),
        "low": float(t0_bar["low"]),
        "volume": int(t0_bar["volume"]),
        "index": t0_idx,
        "gap_seconds": gap_seconds,
        "alignment_method": "next_bar_open",
    }


def compute_ticker_reaction(
    bars: pd.DataFrame,
    t0_info: dict[str, Any],
    window_minutes: int,
) -> Optional[dict[str, Any]]:
    """
    Compute reaction for a ticker at a specific window.

    Uses OPEN prices for consistency (first tradeable price).

    Args:
        bars: DataFrame with bars
        t0_info: T0 bar info dict
        window_minutes: Window size in minutes

    Returns:
        Reaction data dict or None
    """
    if bars.empty:
        return None

    # Get T0 data
    t0_idx = t0_info["index"]
    t0_open = t0_info["open"]
    t0_time = pd.to_datetime(t0_info["timestamp"].replace("Z", "")).tz_localize(None)

    # Ensure we have timestamps
    bars = bars.copy()
    if "ts_dt" not in bars.columns:
        bars["ts_dt"] = pd.to_datetime(bars["ts"]).dt.tz_localize(None)

    # Find bar at window end
    target_time = t0_time + timedelta(minutes=window_minutes)

    # Find closest bar at or after target time
    mask = bars["ts_dt"] >= target_time
    future_bars = bars[mask]

    if future_bars.empty:
        # Try to use last available bar
        if len(bars) == 0:
            return None
        window_bar = bars.iloc[-1]
        window_time = window_bar["ts_dt"]
    else:
        window_bar = future_bars.iloc[0]
        window_idx = future_bars.index[0]
        window_time = window_bar["ts_dt"]

    # Check if bar is reasonably close to target
    delta_seconds = abs((window_time - target_time).total_seconds())
    max_delta = max(120, window_minutes * 60 * 0.25)  # 25% tolerance

    if delta_seconds > max_delta:
        return None

    # Use OPEN of window bar (consistent with T0)
    window_price = float(window_bar["open"])

    # Compute change
    change_pct = ((window_price - t0_open) / t0_open) * 100

    # Compute volume metrics - need to find the index in the full dataframe
    try:
        window_idx_full = bars.index.get_loc(window_idx) if 'window_idx' in dir() else len(bars) - 1
        vol_metrics = compute_volume_metrics(bars.reset_index(drop=True), window_idx_full)
        vol_dict = vol_metrics.to_dict()
    except Exception:
        vol_dict = None

    return {
        "price": window_price,
        "change_pct": round(change_pct, 4),
        "volume_metrics": vol_dict,
        "as_of": iso_z(window_time),
        "target": iso_z(target_time),
        "delta_seconds": int(delta_seconds),
    }


def compute_all_reactions(
    client: MarketDataClient,
    tickers: list[str],
    event_time: datetime,
    market: str = "NYSE",
) -> tuple[dict[str, dict[str, Any]], dict[str, Any], list[str]]:
    """
    Compute reactions for all tickers across all time windows.

    Args:
        client: MarketDataClient instance
        tickers: List of tickers to analyze
        event_time: Event timestamp (will be converted to naive UTC)
        market: Market (for calendar purposes)

    Returns:
        Tuple of:
        - reactions: Dict of window -> ticker -> reaction data
        - baseline: Dict of ticker -> baseline data
        - data_issues: List of issues encountered
    """
    event_time = to_utc_naive(event_time)
    original_event_time = event_time
    market_was_closed = False

    # Handle events outside market hours
    if not is_market_hours(event_time, market):
        market_was_closed = True
        market_open = find_market_open_after(event_time, market)
        logger.info(
            f"Event at {iso_z(event_time)} occurred when market was closed. "
            f"Using next market open at {iso_z(market_open)} as T0 reference."
        )
        event_time = market_open

    # Fetch bars for all tickers
    start = event_time - timedelta(days=5)
    end = event_time + timedelta(days=2)

    data_issues: list[str] = []
    ticker_bars: dict[str, pd.DataFrame] = {}
    ticker_t0: dict[str, dict[str, Any]] = {}

    logger.info(f"Fetching bars for {len(tickers)} tickers from {start} to {end}")

    try:
        all_bars = client.get_bars(tickers, start=start, end=end, timeframe="1min")
    except Exception as e:
        logger.error(f"Failed to fetch bars: {e}")
        return {}, {}, [f"Failed to fetch bars: {e}"]

    if all_bars is None or all_bars.empty:
        return {}, {}, ["No bars returned from barvault"]

    # Group bars by symbol
    for ticker in tickers:
        ticker = ticker.upper()
        ticker_data = all_bars[all_bars["symbol"] == ticker]

        if ticker_data.empty:
            data_issues.append(f"{ticker}: no data available")
            continue

        ticker_bars[ticker] = ticker_data

        # Find T0 bar for this ticker
        t0_info = find_t0_bar(ticker_data, event_time)
        if t0_info:
            ticker_t0[ticker] = t0_info
        else:
            data_issues.append(f"{ticker}: could not find T0 bar")

    if not ticker_t0:
        return {}, {}, ["No T0 bars found for any tickers"]

    # Build baseline (T0 prices for all tickers)
    baseline = {}
    for ticker, t0 in ticker_t0.items():
        baseline[ticker] = {
            "price": t0["open"],
            "timestamp": t0["timestamp"],
            "volume": t0["volume"],
        }

    # Compute reactions for each window
    reactions: dict[str, dict[str, dict[str, Any]]] = {}

    for window_name, window_minutes in REACTION_WINDOWS.items():
        window_reactions = {}

        for ticker in ticker_t0:
            bars = ticker_bars.get(ticker)
            t0_info = ticker_t0.get(ticker)

            if bars is None or t0_info is None:
                continue

            reaction = compute_ticker_reaction(bars, t0_info, window_minutes)

            if reaction:
                reaction["ticker"] = ticker
                window_reactions[ticker] = reaction

        if window_reactions:
            reactions[window_name] = window_reactions
        else:
            data_issues.append(
                f"{window_name}: no reactions computed (market closed or data gap)"
            )

    return reactions, baseline, data_issues


def get_reference_t0(
    client: MarketDataClient,
    event_time: datetime,
    reference_ticker: str = "SPY",
) -> Optional[dict[str, Any]]:
    """
    Get T0 bar info for a reference ticker (typically SPY).

    Args:
        client: MarketDataClient instance
        event_time: Event timestamp
        reference_ticker: Reference ticker symbol

    Returns:
        T0 bar info dict or None
    """
    event_time = to_utc_naive(event_time)

    # Handle market closed
    if not is_market_hours(event_time):
        event_time = find_market_open_after(event_time)

    start = event_time - timedelta(hours=2)
    end = event_time + timedelta(hours=24)

    try:
        bars = client.get_bars([reference_ticker], start=start, end=end, timeframe="1min")
        if bars is None or bars.empty:
            return None

        return find_t0_bar(bars, event_time)
    except Exception as e:
        logger.error(f"Failed to get reference T0: {e}")
        return None
