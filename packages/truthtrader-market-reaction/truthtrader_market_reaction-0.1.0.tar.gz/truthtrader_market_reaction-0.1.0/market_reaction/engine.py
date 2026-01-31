"""
Market Reaction Engine

Main public API for computing market reactions.

Usage:
    from datetime import datetime, timezone
    from market_reaction import get_market_reaction
    from market_data import ArchiveConfig

    result = get_market_reaction(
        event_datetime=datetime(2025, 1, 15, 14, 30, tzinfo=timezone.utc),
        tickers=["TSLA"],
        include_biggest_movers="technology",
        biggest_movers_limit=10,
        market="NYSE",
        barvault_config=ArchiveConfig.s3(bucket="...", prefix="..."),
        polygon_api_key="..."
    )
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime as dt
from typing import Any, Optional

from market_data import ArchiveConfig, MarketDataClient, PolygonConfig

from market_reaction.types import (
    ReactionResult,
    ReactionSummary,
    CategorizedMovers,
    VALID_SECTORS,
)
from market_reaction.universe import (
    get_symbols_for_biggest_movers,
    DEFAULT_INDICES,
    SECTOR_ETFS,
)
from market_reaction.reaction import (
    compute_all_reactions,
    get_reference_t0,
    to_utc_naive,
    iso_z,
    is_market_hours,
    find_market_open_after,
)
from market_reaction.categorizer import (
    categorize_movers,
    compute_category_summary,
    identify_sector_impact,
)
from market_reaction.correlation import CorrelationCalculator


logger = logging.getLogger("market_reaction.engine")


def get_market_reaction(
    event_datetime: dt,
    tickers: list[str],
    *,
    include_biggest_movers: Optional[str] = None,
    biggest_movers_limit: int = 10,
    market: str = "NYSE",
    barvault_config: Optional[ArchiveConfig] = None,
    polygon_api_key: Optional[str] = None,
    compute_correlations: bool = True,
) -> dict[str, Any]:
    """
    Compute market reaction for a given datetime and tickers.

    Args:
        event_datetime: Event datetime (UTC)
        tickers: List of tickers to analyze (your "watchlist")
        include_biggest_movers: Sector name (e.g., "technology"), "market" for all, or None
        biggest_movers_limit: Maximum number of biggest movers to return
        market: Market for calendar purposes (currently only "NYSE" supported)
        barvault_config: ArchiveConfig for barvault (required)
        polygon_api_key: Polygon API key for fetching missing data (optional)
        compute_correlations: Whether to compute correlations for "unexpected" movers

    Returns:
        Dict with reaction results including:
        - event_time: Event timestamp
        - market: Market
        - t0_bar: T0 bar info
        - watchlist: Reactions for watchlist tickers
        - biggest_movers: Top movers from specified sector/market
        - reactions: Reactions per time window
        - summary: Summary statistics

    Raises:
        ValueError: If barvault_config is not provided or include_biggest_movers is invalid
    """
    # Validate inputs
    if barvault_config is None:
        raise ValueError("barvault_config is required")

    if include_biggest_movers is not None:
        sector = include_biggest_movers.lower()
        if sector not in ("market", "all") and sector not in VALID_SECTORS:
            raise ValueError(
                f"Invalid include_biggest_movers: {include_biggest_movers}. "
                f"Must be 'market', 'all', or one of: {sorted(VALID_SECTORS)}"
            )

    # Create MarketDataClient
    if polygon_api_key:
        client = MarketDataClient(barvault_config, polygon=PolygonConfig(api_key=polygon_api_key))
    else:
        # Create a provider that will fail on fetch (read-only mode)
        # This requires a stub provider
        from market_data.providers.base import BaseProvider
        from market_data.types import Bar

        class NoopProvider(BaseProvider):
            def fetch_1m_bars(self, symbol: str, *, start, end) -> list[Bar]:
                raise RuntimeError("No polygon_api_key provided - cannot fetch missing data")

        client = MarketDataClient(barvault_config, provider=NoopProvider())

    # Normalize event time
    event_time = to_utc_naive(event_datetime)
    original_event_time = event_time

    # Check market status
    market_was_closed = not is_market_hours(event_time, market)
    if market_was_closed:
        event_time = find_market_open_after(event_time, market)
        logger.info(
            f"Event at {iso_z(original_event_time)} occurred when market was closed. "
            f"Using next market open at {iso_z(event_time)}."
        )

    # Build ticker list
    tickers = [t.upper() for t in tickers]
    watchlist = tickers.copy()

    # Add sector ETFs and indices for broader analysis
    sector_etf_symbols = [e["symbol"] for e in SECTOR_ETFS]
    all_tickers = list(set(tickers + DEFAULT_INDICES + sector_etf_symbols))

    # Add biggest movers universe if requested
    if include_biggest_movers:
        biggest_mover_symbols = get_symbols_for_biggest_movers(include_biggest_movers)
        all_tickers = list(set(all_tickers + biggest_mover_symbols))

    logger.info(f"Computing reaction for {len(all_tickers)} tickers at {iso_z(event_time)}")

    # Get reference T0 bar (SPY)
    reference_t0 = get_reference_t0(client, event_time)

    if reference_t0 is None:
        return _error_result(
            original_event_time,
            market,
            "Could not find T0 bar - no market data available",
        )

    # Compute reactions for all tickers
    reactions, baseline, data_issues = compute_all_reactions(
        client, all_tickers, event_time, market
    )

    if not reactions:
        return _error_result(
            original_event_time,
            market,
            "No reactions computed - market data unavailable",
            data_issues=data_issues,
        )

    # Get the last window reactions for categorization
    # (typically the 1d window, or whatever is available)
    last_window = list(reactions.keys())[-1] if reactions else "1m"
    all_ticker_reactions = reactions.get(last_window, {})

    # Compute correlations for "unexpected" mover detection
    low_corr_tickers = []
    if compute_correlations and watchlist and all_ticker_reactions:
        try:
            corr_calc = CorrelationCalculator(client)
            low_corr_tickers = corr_calc.find_unexpected_movers(
                watchlist=watchlist,
                universe=list(all_ticker_reactions.keys()),
                as_of=event_time,
                threshold=0.3,
            )
        except Exception as e:
            logger.warning(f"Failed to compute correlations: {e}")

    # Categorize movers
    categorized = categorize_movers(
        watchlist=watchlist,
        ticker_reactions=all_ticker_reactions,
        include_biggest_movers=include_biggest_movers,
        biggest_movers_limit=biggest_movers_limit,
        low_correlation_tickers=low_corr_tickers,
    )

    # Compute summary
    category_summary = compute_category_summary(categorized)
    summary = _compute_summary(categorized, category_summary)

    # Determine data status
    if not reactions:
        data_status = "unavailable"
    elif data_issues:
        data_status = "partial"
    else:
        data_status = "ok"

    # Build result
    result = ReactionResult(
        event_time=iso_z(original_event_time),
        computed_at=iso_z(dt.utcnow()),
        market=market,
        data_status=data_status,
        data_issues=data_issues,
        t0_bar={
            "timestamp": reference_t0["timestamp"],
            "open": reference_t0["open"],
            "alignment_method": reference_t0["alignment_method"],
            "gap_seconds": reference_t0["gap_seconds"],
        },
        baseline={
            "timestamp": reference_t0["timestamp"],
            "tickers": baseline,
        },
        reactions=reactions,
        watchlist=[m.to_dict() for m in categorized.watchlist],
        biggest_movers=[m.to_dict() for m in categorized.biggest_movers],
        sector_impact=identify_sector_impact(categorized),
        summary=asdict(summary),
        market_status="closed_during_event" if market_was_closed else "open_during_event",
        baseline_adjusted=market_was_closed,
        baseline_reason=(
            f"Event occurred at {iso_z(original_event_time)} when market was closed. "
            f"T0 set to next market open at {iso_z(event_time)}."
        ) if market_was_closed else None,
    )

    return result.to_dict()


def _compute_summary(
    categorized: CategorizedMovers,
    category_summary: dict[str, Any],
) -> ReactionSummary:
    """Compute summary statistics."""
    # Count movers
    all_movers = (
        categorized.watchlist
        + categorized.biggest_movers
        + categorized.sector_spillovers
        + categorized.unexpected
    )

    positive = sum(1 for m in all_movers if m.change_pct > 0)
    negative = sum(1 for m in all_movers if m.change_pct < 0)
    avg_move = (
        sum(m.change_pct for m in all_movers) / len(all_movers) if all_movers else 0
    )

    return ReactionSummary(
        biggest_mover=category_summary["biggest_mover"],
        biggest_move_pct=category_summary["biggest_move_pct"],
        biggest_move_window=None,  # Would need to track per-window
        biggest_move_category=category_summary["biggest_move_category"],
        direction_confirmed=None,
        avg_move_pct=round(avg_move, 4),
        positive_movers=positive,
        negative_movers=negative,
    )


def _error_result(
    event_time: dt,
    market: str,
    error: str,
    data_issues: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Generate an error response."""
    result = ReactionResult(
        event_time=iso_z(event_time),
        computed_at=iso_z(dt.utcnow()),
        market=market,
        data_status="unavailable",
        data_issues=data_issues or [error],
    )
    result_dict = result.to_dict()
    result_dict["error"] = error
    return result_dict
