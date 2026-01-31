"""
Type definitions for market reaction engine.

Dataclasses for reaction results, mover data, and volume metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional


@dataclass
class VolumeMetrics:
    """Volume metrics for a single bar."""

    volume: int
    volume_zscore: float  # (vol - rolling_mean) / rolling_std
    relative_volume: float  # vol / avg_vol_same_time_of_day
    avg_volume_20bar: float  # Rolling average for context
    volume_percentile: Optional[float] = None  # Percentile vs recent history

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MoverData:
    """Data for a single mover."""

    ticker: str
    change_pct: float
    price: float
    volume_metrics: Optional[dict[str, Any]] = None
    sector: Optional[str] = None
    correlation_to_watchlist: Optional[float] = None
    bar_timestamp: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CategorizedMovers:
    """All mover categories for a reaction."""

    watchlist: list[MoverData] = field(default_factory=list)
    biggest_movers: list[MoverData] = field(default_factory=list)
    sector_spillovers: list[MoverData] = field(default_factory=list)
    unexpected: list[MoverData] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "watchlist": [m.to_dict() for m in self.watchlist],
            "biggest_movers": [m.to_dict() for m in self.biggest_movers],
            "sector_spillovers": [m.to_dict() for m in self.sector_spillovers],
            "unexpected": [m.to_dict() for m in self.unexpected],
        }


@dataclass
class T0BarInfo:
    """Information about the T0 bar (first tradeable bar after event)."""

    timestamp: str
    open_price: float
    close_price: float
    volume: int
    alignment_method: str  # "next_bar_open" or "market_open"
    event_bar_gap_seconds: int  # Time between event and T0 bar

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ReactionSummary:
    """Summary statistics for the reaction."""

    biggest_mover: Optional[str] = None
    biggest_move_pct: float = 0.0
    biggest_move_window: Optional[str] = None
    biggest_move_category: Optional[str] = None
    direction_confirmed: Optional[bool] = None
    avg_move_pct: float = 0.0
    positive_movers: int = 0
    negative_movers: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ReactionResult:
    """Complete result from get_market_reaction()."""

    event_time: str
    computed_at: str
    market: str
    data_status: str  # "ok", "partial", "unavailable"
    data_issues: list[str] = field(default_factory=list)

    t0_bar: Optional[dict[str, Any]] = None
    baseline: Optional[dict[str, Any]] = None

    # Reaction data per window
    reactions: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)

    # Categorized movers
    watchlist: list[dict[str, Any]] = field(default_factory=list)
    biggest_movers: list[dict[str, Any]] = field(default_factory=list)

    # Sector impact analysis
    sector_impact: dict[str, Any] = field(default_factory=dict)

    # Summary
    summary: dict[str, Any] = field(default_factory=dict)

    # Market status
    market_status: str = "open_during_event"
    baseline_adjusted: bool = False
    baseline_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


# Time windows to compute (in minutes)
REACTION_WINDOWS = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "1d": 1440,
}

# Valid sector names
VALID_SECTORS = {
    "technology",
    "financials",
    "healthcare",
    "energy",
    "consumer",
    "industrials",
    "defense",
    "communications",
    "crypto",
    "real_estate",
    "utilities",
    "materials",
    "bonds",
    "international",
    "index",
    "leveraged",
    "volatility",
}
