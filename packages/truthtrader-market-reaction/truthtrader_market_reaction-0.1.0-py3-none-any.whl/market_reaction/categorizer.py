"""
Mover Categorizer

Categorizes market movers into different groups for analysis:
- Watchlist movers: Tickers from the user-specified watchlist
- Biggest movers: Top movers from the specified sector or market
- Sector spillovers: Sector ETFs that moved significantly
- Unexpected movers: Tickers with low correlation that moved
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from market_reaction.types import MoverData, CategorizedMovers
from market_reaction.universe import (
    get_sector_for_symbol,
    get_sector_etf_for_sector,
    SECTOR_ETFS,
)

logger = logging.getLogger("market_reaction.categorizer")


# Default sector ETF mappings (symbol -> sector)
DEFAULT_SECTOR_ETFS = {etf["symbol"]: etf["sector"] for etf in SECTOR_ETFS}


def categorize_movers(
    watchlist: list[str],
    ticker_reactions: dict[str, dict[str, Any]],
    include_biggest_movers: Optional[str] = None,
    biggest_movers_limit: int = 10,
    sector_etfs: Optional[dict[str, str]] = None,
    low_correlation_tickers: Optional[list[dict[str, Any]]] = None,
    min_move_pct: float = 0.0,  # No minimum - store all moves
) -> CategorizedMovers:
    """
    Categorize movers into different groups.

    Args:
        watchlist: Tickers from user's watchlist (always analyzed)
        ticker_reactions: Dict of ticker -> reaction data
        include_biggest_movers: Sector name, "market", or None
        biggest_movers_limit: Max biggest movers to return
        sector_etfs: Optional custom sector ETF mapping
        low_correlation_tickers: Pre-computed low correlation tickers
        min_move_pct: Minimum absolute move to include (0 = include all)

    Returns:
        CategorizedMovers with all categories populated
    """
    sector_etfs = sector_etfs or DEFAULT_SECTOR_ETFS
    watchlist = [t.upper() for t in watchlist]

    # Build sets for efficient lookup
    watchlist_set = set(watchlist)
    sector_etf_set = set(sector_etfs.keys())

    # Build lookup for low correlation tickers
    low_corr_lookup = {}
    if low_correlation_tickers:
        for item in low_correlation_tickers:
            ticker = item.get("ticker", "").upper()
            low_corr_lookup[ticker] = item.get("avg_correlation_to_watchlist", 0)

    result = CategorizedMovers()

    # Collect all movers for biggest mover sorting
    all_non_watchlist_movers: list[MoverData] = []

    for ticker, reaction in ticker_reactions.items():
        ticker = ticker.upper()
        change_pct = reaction.get("change_pct", 0)

        # Skip if below minimum threshold
        if abs(change_pct) < min_move_pct:
            continue

        # Build mover data
        mover = MoverData(
            ticker=ticker,
            change_pct=round(change_pct, 4),
            price=reaction.get("price", 0),
            volume_metrics=reaction.get("volume_metrics"),
            sector=get_sector_for_symbol(ticker),
            bar_timestamp=reaction.get("as_of"),
        )

        # Categorize
        if ticker in watchlist_set:
            result.watchlist.append(mover)
        elif ticker in sector_etf_set:
            mover.sector = sector_etfs[ticker]
            result.sector_spillovers.append(mover)
        elif ticker in low_corr_lookup:
            mover.correlation_to_watchlist = low_corr_lookup[ticker]
            result.unexpected.append(mover)
        else:
            # Candidate for biggest movers
            all_non_watchlist_movers.append(mover)

    # Sort watchlist by absolute move
    result.watchlist.sort(key=lambda m: abs(m.change_pct), reverse=True)
    result.sector_spillovers.sort(key=lambda m: abs(m.change_pct), reverse=True)
    result.unexpected.sort(key=lambda m: abs(m.change_pct), reverse=True)

    # Filter and sort biggest movers
    if include_biggest_movers:
        sector_filter = include_biggest_movers.lower()

        if sector_filter in ("market", "all"):
            # All movers
            biggest = sorted(
                all_non_watchlist_movers,
                key=lambda m: abs(m.change_pct),
                reverse=True,
            )
        else:
            # Filter by sector
            biggest = sorted(
                [m for m in all_non_watchlist_movers if m.sector == sector_filter],
                key=lambda m: abs(m.change_pct),
                reverse=True,
            )

        result.biggest_movers = biggest[:biggest_movers_limit]

    return result


def get_biggest_movers(
    categorized: CategorizedMovers,
    category: str = "all",
    limit: int = 5,
) -> list[MoverData]:
    """
    Get the biggest movers from a category.

    Args:
        categorized: CategorizedMovers instance
        category: Category to get ('watchlist', 'biggest_movers', 'sector_spillovers',
                  'unexpected', 'all')
        limit: Maximum number to return

    Returns:
        List of biggest movers
    """
    if category == "watchlist":
        movers = categorized.watchlist
    elif category == "biggest_movers":
        movers = categorized.biggest_movers
    elif category == "sector_spillovers":
        movers = categorized.sector_spillovers
    elif category == "unexpected":
        movers = categorized.unexpected
    elif category == "all":
        movers = (
            categorized.watchlist
            + categorized.biggest_movers
            + categorized.sector_spillovers
            + categorized.unexpected
        )
        movers.sort(key=lambda m: abs(m.change_pct), reverse=True)
    else:
        raise ValueError(f"Invalid category: {category}")

    return movers[:limit]


def compute_category_summary(categorized: CategorizedMovers) -> dict[str, Any]:
    """
    Compute summary statistics for categorized movers.

    Args:
        categorized: CategorizedMovers instance

    Returns:
        Summary dict with counts and aggregates
    """

    def _category_stats(movers: list[MoverData]) -> dict[str, Any]:
        if not movers:
            return {
                "count": 0,
                "positive": 0,
                "negative": 0,
                "avg_move_pct": 0.0,
                "max_move_pct": 0.0,
                "min_move_pct": 0.0,
            }

        changes = [m.change_pct for m in movers]
        return {
            "count": len(movers),
            "positive": sum(1 for c in changes if c > 0),
            "negative": sum(1 for c in changes if c < 0),
            "avg_move_pct": round(sum(changes) / len(changes), 4),
            "max_move_pct": round(max(changes), 4),
            "min_move_pct": round(min(changes), 4),
        }

    # Find overall biggest mover
    all_movers = (
        categorized.watchlist
        + categorized.biggest_movers
        + categorized.sector_spillovers
        + categorized.unexpected
    )

    biggest_mover = None
    biggest_move_pct = 0.0
    biggest_category = None

    if all_movers:
        biggest = max(all_movers, key=lambda m: abs(m.change_pct))
        biggest_mover = biggest.ticker
        biggest_move_pct = biggest.change_pct

        # Determine category
        if biggest in categorized.watchlist:
            biggest_category = "watchlist"
        elif biggest in categorized.biggest_movers:
            biggest_category = "biggest_movers"
        elif biggest in categorized.sector_spillovers:
            biggest_category = "sector_spillovers"
        else:
            biggest_category = "unexpected"

    return {
        "biggest_mover": biggest_mover,
        "biggest_move_pct": round(biggest_move_pct, 4),
        "biggest_move_category": biggest_category,
        "total_movers": len(all_movers),
        "watchlist": _category_stats(categorized.watchlist),
        "biggest_movers": _category_stats(categorized.biggest_movers),
        "sector_spillovers": _category_stats(categorized.sector_spillovers),
        "unexpected": _category_stats(categorized.unexpected),
    }


def identify_sector_impact(
    categorized: CategorizedMovers,
    threshold_pct: float = 0.5,
) -> dict[str, Any]:
    """
    Identify which sectors were impacted by the event.

    Args:
        categorized: CategorizedMovers instance
        threshold_pct: Minimum move to consider significant

    Returns:
        Dict mapping sector to impact data
    """
    sector_impact: dict[str, dict[str, Any]] = {}

    # Collect all movers with sectors
    all_movers = (
        categorized.watchlist
        + categorized.biggest_movers
        + categorized.sector_spillovers
    )

    for mover in all_movers:
        if mover.sector:
            if mover.sector not in sector_impact:
                sector_impact[mover.sector] = {
                    "movers": [],
                    "avg_move_pct": 0.0,
                    "total_movers": 0,
                    "direction": "neutral",
                }

            sector_impact[mover.sector]["movers"].append(
                {
                    "ticker": mover.ticker,
                    "change_pct": mover.change_pct,
                }
            )

    # Compute averages and determine direction
    for sector, data in sector_impact.items():
        if data["movers"]:
            changes = [m["change_pct"] for m in data["movers"]]
            avg = sum(changes) / len(changes)
            data["avg_move_pct"] = round(avg, 4)
            data["total_movers"] = len(data["movers"])

            if avg > threshold_pct:
                data["direction"] = "bullish"
            elif avg < -threshold_pct:
                data["direction"] = "bearish"
            else:
                data["direction"] = "neutral"

    return sector_impact
