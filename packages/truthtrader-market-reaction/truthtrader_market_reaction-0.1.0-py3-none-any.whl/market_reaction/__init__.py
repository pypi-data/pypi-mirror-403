"""
Market Reaction Engine

Compute market reactions at a given datetime with automatic biggest mover
discovery by sector or market-wide.

Usage:
    from datetime import datetime, timezone
    from market_reaction import get_market_reaction
    from market_data import ArchiveConfig

    result = get_market_reaction(
        event_datetime=datetime(2025, 1, 15, 14, 30, tzinfo=timezone.utc),
        tickers=["TSLA"],
        include_biggest_movers="technology",  # or "market", "financials", etc.
        biggest_movers_limit=10,
        market="NYSE",
        barvault_config=ArchiveConfig.s3(bucket="...", prefix="..."),
        polygon_api_key="..."  # optional
    )

    # result contains:
    # - watchlist: reactions for your specified tickers
    # - biggest_movers: top movers from the sector/market
    # - reactions: per-window reactions (1m, 5m, 15m, 1h, 4h, 1d)
    # - summary: overall statistics
"""

from market_reaction.engine import get_market_reaction
from market_reaction.types import (
    MoverData,
    VolumeMetrics,
    CategorizedMovers,
    ReactionResult,
    ReactionSummary,
    T0BarInfo,
    REACTION_WINDOWS,
    VALID_SECTORS,
)
from market_reaction.universe import (
    get_all_symbols,
    get_sector_for_symbol,
    get_symbols_by_sector,
    get_symbols_for_biggest_movers,
    get_ticker_info,
    DEFAULT_INDICES,
)

__version__ = "0.1.0"

__all__ = [
    # Main API
    "get_market_reaction",
    # Types
    "MoverData",
    "VolumeMetrics",
    "CategorizedMovers",
    "ReactionResult",
    "ReactionSummary",
    "T0BarInfo",
    # Constants
    "REACTION_WINDOWS",
    "VALID_SECTORS",
    "DEFAULT_INDICES",
    # Universe functions
    "get_all_symbols",
    "get_sector_for_symbol",
    "get_symbols_by_sector",
    "get_symbols_for_biggest_movers",
    "get_ticker_info",
]
