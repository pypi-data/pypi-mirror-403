"""
Correlation Calculator

Computes correlations between tickers for detecting "unexpected" movers.
Uses on-demand correlation computation from historical bar data via barvault.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd
import numpy as np

from market_data import MarketDataClient

logger = logging.getLogger("market_reaction.correlation")


# Default lookback for correlation calculation
DEFAULT_CORRELATION_LOOKBACK_DAYS = 30
DEFAULT_MIN_OBSERVATIONS = 100  # Minimum bars needed for reliable correlation


def _resample_to_daily_returns(
    bars: pd.DataFrame,
) -> pd.Series:
    """
    Convert minute bars to daily returns for correlation calculation.

    Args:
        bars: DataFrame with OHLCV data

    Returns:
        Series of daily returns
    """
    if bars.empty:
        return pd.Series()

    # Ensure we have a timestamp column
    if "ts" in bars.columns:
        bars = bars.copy()
        bars["date"] = pd.to_datetime(bars["ts"]).dt.date
    else:
        return pd.Series()

    # Get daily close prices (last bar of each day)
    daily = bars.groupby("date")["close"].last()

    # Calculate returns
    returns = daily.pct_change().dropna()

    return returns


def _align_returns(
    returns_dict: dict[str, pd.Series],
) -> pd.DataFrame:
    """
    Align multiple return series to common dates.

    Args:
        returns_dict: Dict mapping ticker to return series

    Returns:
        DataFrame with aligned returns, tickers as columns
    """
    if not returns_dict:
        return pd.DataFrame()

    # Create DataFrame from all series
    df = pd.DataFrame(returns_dict)

    # Drop rows with any NaN (only keep dates where all tickers have data)
    df = df.dropna()

    return df


def compute_correlation_matrix(
    client: MarketDataClient,
    tickers: list[str],
    as_of: datetime,
    lookback_days: int = DEFAULT_CORRELATION_LOOKBACK_DAYS,
) -> pd.DataFrame:
    """
    Compute correlation matrix from historical returns.

    Args:
        client: MarketDataClient instance for accessing market data
        tickers: List of ticker symbols
        as_of: Calculate correlations as of this datetime
        lookback_days: Number of trading days to look back

    Returns:
        DataFrame with correlation matrix (tickers x tickers)
    """
    if not tickers:
        return pd.DataFrame()

    # Calculate date range
    end = as_of
    start = as_of - timedelta(days=lookback_days + 10)  # Add buffer for non-trading days

    # Collect returns for each ticker
    returns_dict = {}

    for ticker in tickers:
        ticker = ticker.upper()

        try:
            bars = client.get_bars([ticker], start=start, end=end, timeframe="1min")

            if bars is None or bars.empty:
                logger.debug(f"No bars available for {ticker}")
                continue

            returns = _resample_to_daily_returns(bars)

            if len(returns) >= DEFAULT_MIN_OBSERVATIONS / 10:  # At least some data
                returns_dict[ticker] = returns
            else:
                logger.debug(f"Insufficient data for {ticker}: {len(returns)} days")

        except Exception as e:
            logger.warning(f"Error getting bars for {ticker}: {e}")

    if not returns_dict:
        logger.warning("No return data available for any tickers")
        return pd.DataFrame()

    # Align returns to common dates
    aligned = _align_returns(returns_dict)

    if aligned.empty or len(aligned) < 5:
        logger.warning(f"Insufficient aligned data: {len(aligned)} observations")
        return pd.DataFrame()

    # Compute correlation matrix
    corr_matrix = aligned.corr()

    logger.debug(
        f"Computed correlation matrix: {len(corr_matrix)} tickers, "
        f"{len(aligned)} observations"
    )

    return corr_matrix


def get_correlation(
    corr_matrix: pd.DataFrame,
    ticker1: str,
    ticker2: str,
) -> Optional[float]:
    """
    Get correlation between two tickers from a correlation matrix.

    Args:
        corr_matrix: Correlation matrix DataFrame
        ticker1: First ticker
        ticker2: Second ticker

    Returns:
        Correlation coefficient, or None if not available
    """
    ticker1 = ticker1.upper()
    ticker2 = ticker2.upper()

    if corr_matrix.empty:
        return None

    if ticker1 not in corr_matrix.columns or ticker2 not in corr_matrix.columns:
        return None

    return float(corr_matrix.loc[ticker1, ticker2])


def get_average_correlation_to_group(
    corr_matrix: pd.DataFrame,
    ticker: str,
    group: list[str],
) -> Optional[float]:
    """
    Get average correlation of a ticker to a group of other tickers.

    Args:
        corr_matrix: Correlation matrix DataFrame
        ticker: Ticker to check
        group: List of tickers in the group

    Returns:
        Average correlation to group, or None if not available
    """
    ticker = ticker.upper()
    group = [t.upper() for t in group if t.upper() != ticker]

    if not group or corr_matrix.empty:
        return None

    if ticker not in corr_matrix.columns:
        return None

    correlations = []
    for other in group:
        if other in corr_matrix.columns:
            corr = corr_matrix.loc[ticker, other]
            if not pd.isna(corr):
                correlations.append(corr)

    if not correlations:
        return None

    return round(float(np.mean(correlations)), 4)


def find_low_correlation_movers(
    watchlist: list[str],
    universe: list[str],
    corr_matrix: pd.DataFrame,
    threshold: float = 0.3,
) -> list[dict[str, Any]]:
    """
    Find tickers in universe with low correlation to watchlist.

    These are potential "unexpected" movers - tickers that moved
    with the event despite not being typically correlated to the
    watchlist tickers.

    Args:
        watchlist: Tickers from the event's market hypothesis
        universe: Full universe of tickers to check
        corr_matrix: Pre-computed correlation matrix
        threshold: Maximum average correlation to be considered "low"

    Returns:
        List of dicts with ticker and correlation info
    """
    watchlist = [t.upper() for t in watchlist]
    universe = [t.upper() for t in universe]

    # Remove watchlist tickers from universe for this analysis
    candidates = [t for t in universe if t not in watchlist]

    low_corr_tickers = []

    for ticker in candidates:
        avg_corr = get_average_correlation_to_group(corr_matrix, ticker, watchlist)

        if avg_corr is not None and abs(avg_corr) <= threshold:
            low_corr_tickers.append(
                {
                    "ticker": ticker,
                    "avg_correlation_to_watchlist": avg_corr,
                    "correlation_category": _categorize_correlation(avg_corr),
                }
            )

    # Sort by lowest absolute correlation first
    low_corr_tickers.sort(key=lambda x: abs(x["avg_correlation_to_watchlist"]))

    return low_corr_tickers


def _categorize_correlation(corr: float) -> str:
    """
    Categorize correlation strength.

    Args:
        corr: Correlation coefficient

    Returns:
        Category string
    """
    abs_corr = abs(corr)

    if abs_corr < 0.1:
        return "uncorrelated"
    elif abs_corr < 0.3:
        return "weak"
    elif abs_corr < 0.5:
        return "moderate"
    elif abs_corr < 0.7:
        return "strong"
    else:
        return "very_strong"


def find_highly_correlated_tickers(
    ticker: str,
    corr_matrix: pd.DataFrame,
    threshold: float = 0.7,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Find tickers highly correlated to a given ticker.

    Useful for identifying potential spillover effects.

    Args:
        ticker: Base ticker
        corr_matrix: Correlation matrix
        threshold: Minimum correlation to include
        limit: Maximum number of results

    Returns:
        List of correlated tickers with correlation values
    """
    ticker = ticker.upper()

    if corr_matrix.empty or ticker not in corr_matrix.columns:
        return []

    correlations = corr_matrix[ticker].drop(ticker)  # Exclude self

    # Filter by threshold
    high_corr = correlations[correlations.abs() >= threshold]

    # Sort by absolute correlation (highest first)
    high_corr = high_corr.reindex(high_corr.abs().sort_values(ascending=False).index)

    results = []
    for other_ticker, corr in high_corr.head(limit).items():
        results.append(
            {
                "ticker": other_ticker,
                "correlation": round(float(corr), 4),
                "direction": "positive" if corr > 0 else "negative",
                "category": _categorize_correlation(corr),
            }
        )

    return results


class CorrelationCalculator:
    """
    Calculator for on-demand correlation computation.

    Caches correlation matrices to avoid recomputation.
    """

    def __init__(
        self,
        client: MarketDataClient,
        cache_ttl_minutes: int = 60,
    ):
        """
        Initialize the correlation calculator.

        Args:
            client: MarketDataClient instance for accessing market data
            cache_ttl_minutes: How long to cache correlation matrices
        """
        self.client = client
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)

        self._cache: dict[str, tuple[datetime, pd.DataFrame]] = {}

    def _cache_key(self, tickers: list[str], as_of_date: str) -> str:
        """Generate cache key."""
        sorted_tickers = sorted([t.upper() for t in tickers])
        return f"{as_of_date}:{','.join(sorted_tickers)}"

    def get_correlation_matrix(
        self,
        tickers: list[str],
        as_of: datetime,
        lookback_days: int = DEFAULT_CORRELATION_LOOKBACK_DAYS,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """
        Get correlation matrix, using cache if available.

        Args:
            tickers: List of tickers
            as_of: As-of datetime
            lookback_days: Lookback period
            use_cache: Whether to use cached results

        Returns:
            Correlation matrix DataFrame
        """
        as_of_date = as_of.strftime("%Y-%m-%d")
        cache_key = self._cache_key(tickers, as_of_date)

        # Check cache
        if use_cache and cache_key in self._cache:
            cached_at, matrix = self._cache[cache_key]
            if datetime.utcnow() - cached_at < self.cache_ttl:
                logger.debug(f"Using cached correlation matrix for {cache_key}")
                return matrix

        # Compute fresh
        matrix = compute_correlation_matrix(
            self.client,
            tickers,
            as_of,
            lookback_days,
        )

        # Cache result
        self._cache[cache_key] = (datetime.utcnow(), matrix)

        return matrix

    def find_unexpected_movers(
        self,
        watchlist: list[str],
        universe: list[str],
        as_of: datetime,
        threshold: float = 0.3,
    ) -> list[dict[str, Any]]:
        """
        Find unexpected movers (low correlation to watchlist).

        Args:
            watchlist: Event's primary tickers
            universe: Full universe to check
            as_of: As-of datetime
            threshold: Correlation threshold

        Returns:
            List of low-correlation tickers
        """
        all_tickers = list(set(watchlist + universe))

        corr_matrix = self.get_correlation_matrix(all_tickers, as_of)

        return find_low_correlation_movers(
            watchlist,
            universe,
            corr_matrix,
            threshold,
        )

    def clear_cache(self):
        """Clear the correlation cache."""
        self._cache.clear()
