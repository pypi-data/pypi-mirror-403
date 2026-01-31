"""
Ticker Universe and Sector Mappings

Provides the built-in ticker universe with sector classifications.
Supports filtering by sector for biggest mover discovery.
"""

from __future__ import annotations

from typing import Optional


# Sector ETFs
SECTOR_ETFS = [
    {"symbol": "XLF", "name": "Financial Select Sector SPDR", "sector": "financials"},
    {"symbol": "XLE", "name": "Energy Select Sector SPDR", "sector": "energy"},
    {"symbol": "XLK", "name": "Technology Select Sector SPDR", "sector": "technology"},
    {"symbol": "XLV", "name": "Health Care Select Sector SPDR", "sector": "healthcare"},
    {"symbol": "XLI", "name": "Industrial Select Sector SPDR", "sector": "industrials"},
    {"symbol": "XLY", "name": "Consumer Discretionary SPDR", "sector": "consumer"},
    {"symbol": "XLP", "name": "Consumer Staples Select SPDR", "sector": "consumer"},
    {"symbol": "XLU", "name": "Utilities Select Sector SPDR", "sector": "utilities"},
    {"symbol": "XLB", "name": "Materials Select Sector SPDR", "sector": "materials"},
    {"symbol": "XLRE", "name": "Real Estate Select Sector SPDR", "sector": "real_estate"},
    {"symbol": "XLC", "name": "Communication Services SPDR", "sector": "communications"},
]

# Index ETFs
INDEX_ETFS = [
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "sector": "index"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust (Nasdaq-100)", "sector": "index"},
    {"symbol": "IWM", "name": "iShares Russell 2000 ETF", "sector": "index"},
    {"symbol": "DIA", "name": "SPDR Dow Jones Industrial ETF", "sector": "index"},
    {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "sector": "index"},
    {"symbol": "VTI", "name": "Vanguard Total Stock Market ETF", "sector": "index"},
]

# Thematic ETFs
THEMATIC_ETFS = [
    {"symbol": "SMH", "name": "VanEck Semiconductor ETF", "sector": "technology"},
    {"symbol": "SOXX", "name": "iShares Semiconductor ETF", "sector": "technology"},
    {"symbol": "XBI", "name": "SPDR S&P Biotech ETF", "sector": "healthcare"},
    {"symbol": "IBB", "name": "iShares Biotechnology ETF", "sector": "healthcare"},
    {"symbol": "XOP", "name": "SPDR S&P Oil & Gas Exploration ETF", "sector": "energy"},
    {"symbol": "XHB", "name": "SPDR S&P Homebuilders ETF", "sector": "real_estate"},
    {"symbol": "KRE", "name": "SPDR S&P Regional Banking ETF", "sector": "financials"},
    {"symbol": "XRT", "name": "SPDR S&P Retail ETF", "sector": "consumer"},
    {"symbol": "ARKK", "name": "ARK Innovation ETF", "sector": "technology"},
    {"symbol": "GDX", "name": "VanEck Gold Miners ETF", "sector": "materials"},
    {"symbol": "SLV", "name": "iShares Silver Trust", "sector": "materials"},
    {"symbol": "GLD", "name": "SPDR Gold Trust", "sector": "materials"},
    {"symbol": "USO", "name": "United States Oil Fund", "sector": "energy"},
    {"symbol": "UNG", "name": "United States Natural Gas Fund", "sector": "energy"},
    {"symbol": "TLT", "name": "iShares 20+ Year Treasury Bond ETF", "sector": "bonds"},
    {"symbol": "HYG", "name": "iShares iBoxx High Yield Corporate Bond ETF", "sector": "bonds"},
    {"symbol": "LQD", "name": "iShares iBoxx Investment Grade Corporate Bond ETF", "sector": "bonds"},
    {"symbol": "EEM", "name": "iShares MSCI Emerging Markets ETF", "sector": "international"},
    {"symbol": "EFA", "name": "iShares MSCI EAFE ETF", "sector": "international"},
    {"symbol": "FXI", "name": "iShares China Large-Cap ETF", "sector": "international"},
    {"symbol": "EWJ", "name": "iShares MSCI Japan ETF", "sector": "international"},
    {"symbol": "KWEB", "name": "KraneShares CSI China Internet ETF", "sector": "international"},
]

# Leveraged ETFs
LEVERAGED_ETFS = [
    {"symbol": "TQQQ", "name": "ProShares UltraPro QQQ (3x)", "sector": "leveraged"},
    {"symbol": "SQQQ", "name": "ProShares UltraPro Short QQQ (-3x)", "sector": "leveraged"},
    {"symbol": "SPXL", "name": "Direxion Daily S&P 500 Bull 3X", "sector": "leveraged"},
    {"symbol": "SPXS", "name": "Direxion Daily S&P 500 Bear 3X", "sector": "leveraged"},
    {"symbol": "SOXL", "name": "Direxion Daily Semiconductor Bull 3X", "sector": "leveraged"},
    {"symbol": "SOXS", "name": "Direxion Daily Semiconductor Bear 3X", "sector": "leveraged"},
    {"symbol": "UVXY", "name": "ProShares Ultra VIX Short-Term Futures", "sector": "volatility"},
    {"symbol": "VXX", "name": "iPath Series B S&P 500 VIX Short-Term Futures", "sector": "volatility"},
]

# Tech Stocks
TECH_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "technology"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc. Class A", "sector": "technology"},
    {"symbol": "GOOG", "name": "Alphabet Inc. Class C", "sector": "technology"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "technology"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "technology"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "technology"},
    {"symbol": "TSM", "name": "Taiwan Semiconductor", "sector": "technology"},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "sector": "technology"},
    {"symbol": "ASML", "name": "ASML Holding N.V.", "sector": "technology"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "technology"},
    {"symbol": "INTC", "name": "Intel Corporation", "sector": "technology"},
    {"symbol": "QCOM", "name": "Qualcomm Inc.", "sector": "technology"},
    {"symbol": "TXN", "name": "Texas Instruments", "sector": "technology"},
    {"symbol": "MU", "name": "Micron Technology", "sector": "technology"},
    {"symbol": "AMAT", "name": "Applied Materials", "sector": "technology"},
    {"symbol": "LRCX", "name": "Lam Research", "sector": "technology"},
    {"symbol": "KLAC", "name": "KLA Corporation", "sector": "technology"},
    {"symbol": "MRVL", "name": "Marvell Technology", "sector": "technology"},
    {"symbol": "ON", "name": "ON Semiconductor", "sector": "technology"},
    {"symbol": "ADI", "name": "Analog Devices", "sector": "technology"},
    {"symbol": "NXPI", "name": "NXP Semiconductors", "sector": "technology"},
    {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "technology"},
    {"symbol": "ORCL", "name": "Oracle Corporation", "sector": "technology"},
    {"symbol": "NOW", "name": "ServiceNow Inc.", "sector": "technology"},
    {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "technology"},
    {"symbol": "IBM", "name": "IBM Corporation", "sector": "technology"},
    {"symbol": "CSCO", "name": "Cisco Systems", "sector": "technology"},
    {"symbol": "ACN", "name": "Accenture plc", "sector": "technology"},
    {"symbol": "INTU", "name": "Intuit Inc.", "sector": "technology"},
    {"symbol": "SNPS", "name": "Synopsys Inc.", "sector": "technology"},
    {"symbol": "CDNS", "name": "Cadence Design Systems", "sector": "technology"},
    {"symbol": "PANW", "name": "Palo Alto Networks", "sector": "technology"},
    {"symbol": "CRWD", "name": "CrowdStrike Holdings", "sector": "technology"},
    {"symbol": "PLTR", "name": "Palantir Technologies", "sector": "technology"},
    {"symbol": "NET", "name": "Cloudflare Inc.", "sector": "technology"},
    {"symbol": "DDOG", "name": "Datadog Inc.", "sector": "technology"},
    {"symbol": "ZS", "name": "Zscaler Inc.", "sector": "technology"},
    {"symbol": "SNOW", "name": "Snowflake Inc.", "sector": "technology"},
    {"symbol": "MDB", "name": "MongoDB Inc.", "sector": "technology"},
]

# Financial Stocks
FINANCIAL_STOCKS = [
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "financials"},
    {"symbol": "BAC", "name": "Bank of America", "sector": "financials"},
    {"symbol": "WFC", "name": "Wells Fargo & Company", "sector": "financials"},
    {"symbol": "GS", "name": "Goldman Sachs Group", "sector": "financials"},
    {"symbol": "MS", "name": "Morgan Stanley", "sector": "financials"},
    {"symbol": "C", "name": "Citigroup Inc.", "sector": "financials"},
    {"symbol": "BLK", "name": "BlackRock Inc.", "sector": "financials"},
    {"symbol": "SCHW", "name": "Charles Schwab", "sector": "financials"},
    {"symbol": "AXP", "name": "American Express", "sector": "financials"},
    {"symbol": "USB", "name": "U.S. Bancorp", "sector": "financials"},
    {"symbol": "PNC", "name": "PNC Financial Services", "sector": "financials"},
    {"symbol": "TFC", "name": "Truist Financial", "sector": "financials"},
    {"symbol": "COF", "name": "Capital One Financial", "sector": "financials"},
    {"symbol": "BK", "name": "Bank of New York Mellon", "sector": "financials"},
    {"symbol": "V", "name": "Visa Inc.", "sector": "financials"},
    {"symbol": "MA", "name": "Mastercard Inc.", "sector": "financials"},
    {"symbol": "PYPL", "name": "PayPal Holdings", "sector": "financials"},
    {"symbol": "SQ", "name": "Block Inc. (Square)", "sector": "financials"},
]

# Healthcare Stocks
HEALTHCARE_STOCKS = [
    {"symbol": "UNH", "name": "UnitedHealth Group", "sector": "healthcare"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "sector": "healthcare"},
    {"symbol": "LLY", "name": "Eli Lilly and Company", "sector": "healthcare"},
    {"symbol": "PFE", "name": "Pfizer Inc.", "sector": "healthcare"},
    {"symbol": "ABBV", "name": "AbbVie Inc.", "sector": "healthcare"},
    {"symbol": "MRK", "name": "Merck & Co.", "sector": "healthcare"},
    {"symbol": "TMO", "name": "Thermo Fisher Scientific", "sector": "healthcare"},
    {"symbol": "ABT", "name": "Abbott Laboratories", "sector": "healthcare"},
    {"symbol": "DHR", "name": "Danaher Corporation", "sector": "healthcare"},
    {"symbol": "BMY", "name": "Bristol-Myers Squibb", "sector": "healthcare"},
    {"symbol": "AMGN", "name": "Amgen Inc.", "sector": "healthcare"},
    {"symbol": "GILD", "name": "Gilead Sciences", "sector": "healthcare"},
    {"symbol": "VRTX", "name": "Vertex Pharmaceuticals", "sector": "healthcare"},
    {"symbol": "REGN", "name": "Regeneron Pharmaceuticals", "sector": "healthcare"},
    {"symbol": "ISRG", "name": "Intuitive Surgical", "sector": "healthcare"},
    {"symbol": "CVS", "name": "CVS Health Corporation", "sector": "healthcare"},
    {"symbol": "CI", "name": "The Cigna Group", "sector": "healthcare"},
    {"symbol": "ELV", "name": "Elevance Health", "sector": "healthcare"},
    {"symbol": "HUM", "name": "Humana Inc.", "sector": "healthcare"},
    {"symbol": "MRNA", "name": "Moderna Inc.", "sector": "healthcare"},
    {"symbol": "BIIB", "name": "Biogen Inc.", "sector": "healthcare"},
]

# Energy Stocks
ENERGY_STOCKS = [
    {"symbol": "XOM", "name": "Exxon Mobil Corporation", "sector": "energy"},
    {"symbol": "CVX", "name": "Chevron Corporation", "sector": "energy"},
    {"symbol": "COP", "name": "ConocoPhillips", "sector": "energy"},
    {"symbol": "EOG", "name": "EOG Resources", "sector": "energy"},
    {"symbol": "SLB", "name": "Schlumberger Limited", "sector": "energy"},
    {"symbol": "MPC", "name": "Marathon Petroleum", "sector": "energy"},
    {"symbol": "PSX", "name": "Phillips 66", "sector": "energy"},
    {"symbol": "VLO", "name": "Valero Energy", "sector": "energy"},
    {"symbol": "OXY", "name": "Occidental Petroleum", "sector": "energy"},
    {"symbol": "PXD", "name": "Pioneer Natural Resources", "sector": "energy"},
    {"symbol": "DVN", "name": "Devon Energy", "sector": "energy"},
    {"symbol": "HAL", "name": "Halliburton Company", "sector": "energy"},
    {"symbol": "BKR", "name": "Baker Hughes Company", "sector": "energy"},
    {"symbol": "FANG", "name": "Diamondback Energy", "sector": "energy"},
    {"symbol": "KMI", "name": "Kinder Morgan", "sector": "energy"},
    {"symbol": "WMB", "name": "Williams Companies", "sector": "energy"},
    {"symbol": "LNG", "name": "Cheniere Energy", "sector": "energy"},
]

# Consumer Stocks
CONSUMER_STOCKS = [
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "consumer"},
    {"symbol": "HD", "name": "The Home Depot", "sector": "consumer"},
    {"symbol": "MCD", "name": "McDonald's Corporation", "sector": "consumer"},
    {"symbol": "NKE", "name": "Nike Inc.", "sector": "consumer"},
    {"symbol": "SBUX", "name": "Starbucks Corporation", "sector": "consumer"},
    {"symbol": "TGT", "name": "Target Corporation", "sector": "consumer"},
    {"symbol": "LOW", "name": "Lowe's Companies", "sector": "consumer"},
    {"symbol": "COST", "name": "Costco Wholesale", "sector": "consumer"},
    {"symbol": "WMT", "name": "Walmart Inc.", "sector": "consumer"},
    {"symbol": "PG", "name": "Procter & Gamble", "sector": "consumer"},
    {"symbol": "KO", "name": "The Coca-Cola Company", "sector": "consumer"},
    {"symbol": "PEP", "name": "PepsiCo Inc.", "sector": "consumer"},
    {"symbol": "PM", "name": "Philip Morris International", "sector": "consumer"},
    {"symbol": "MO", "name": "Altria Group", "sector": "consumer"},
    {"symbol": "CL", "name": "Colgate-Palmolive", "sector": "consumer"},
    {"symbol": "EL", "name": "Estée Lauder Companies", "sector": "consumer"},
    {"symbol": "LULU", "name": "Lululemon Athletica", "sector": "consumer"},
    {"symbol": "ROST", "name": "Ross Stores", "sector": "consumer"},
    {"symbol": "TJX", "name": "TJX Companies", "sector": "consumer"},
    {"symbol": "DG", "name": "Dollar General", "sector": "consumer"},
    {"symbol": "DLTR", "name": "Dollar Tree", "sector": "consumer"},
    {"symbol": "CMG", "name": "Chipotle Mexican Grill", "sector": "consumer"},
    {"symbol": "YUM", "name": "Yum! Brands", "sector": "consumer"},
    {"symbol": "DPZ", "name": "Domino's Pizza", "sector": "consumer"},
]

# Industrial Stocks
INDUSTRIAL_STOCKS = [
    {"symbol": "CAT", "name": "Caterpillar Inc.", "sector": "industrials"},
    {"symbol": "DE", "name": "Deere & Company", "sector": "industrials"},
    {"symbol": "UNP", "name": "Union Pacific Corporation", "sector": "industrials"},
    {"symbol": "UPS", "name": "United Parcel Service", "sector": "industrials"},
    {"symbol": "FDX", "name": "FedEx Corporation", "sector": "industrials"},
    {"symbol": "HON", "name": "Honeywell International", "sector": "industrials"},
    {"symbol": "MMM", "name": "3M Company", "sector": "industrials"},
    {"symbol": "GE", "name": "General Electric", "sector": "industrials"},
    {"symbol": "BA", "name": "The Boeing Company", "sector": "industrials"},
    {"symbol": "LMT", "name": "Lockheed Martin", "sector": "defense"},
    {"symbol": "RTX", "name": "RTX Corporation (Raytheon)", "sector": "defense"},
    {"symbol": "NOC", "name": "Northrop Grumman", "sector": "defense"},
    {"symbol": "GD", "name": "General Dynamics", "sector": "defense"},
    {"symbol": "LHX", "name": "L3Harris Technologies", "sector": "defense"},
    {"symbol": "HII", "name": "Huntington Ingalls Industries", "sector": "defense"},
]

# Communications Stocks
COMMUNICATIONS_STOCKS = [
    {"symbol": "NFLX", "name": "Netflix Inc.", "sector": "communications"},
    {"symbol": "DIS", "name": "The Walt Disney Company", "sector": "communications"},
    {"symbol": "CMCSA", "name": "Comcast Corporation", "sector": "communications"},
    {"symbol": "T", "name": "AT&T Inc.", "sector": "communications"},
    {"symbol": "VZ", "name": "Verizon Communications", "sector": "communications"},
    {"symbol": "TMUS", "name": "T-Mobile US", "sector": "communications"},
    {"symbol": "CHTR", "name": "Charter Communications", "sector": "communications"},
    {"symbol": "WBD", "name": "Warner Bros. Discovery", "sector": "communications"},
    {"symbol": "PARA", "name": "Paramount Global", "sector": "communications"},
    {"symbol": "EA", "name": "Electronic Arts", "sector": "communications"},
    {"symbol": "TTWO", "name": "Take-Two Interactive", "sector": "communications"},
    {"symbol": "ATVI", "name": "Activision Blizzard", "sector": "communications"},
]

# Crypto Stocks
CRYPTO_STOCKS = [
    {"symbol": "COIN", "name": "Coinbase Global", "sector": "crypto"},
    {"symbol": "MSTR", "name": "MicroStrategy", "sector": "crypto"},
    {"symbol": "RIOT", "name": "Riot Platforms", "sector": "crypto"},
    {"symbol": "MARA", "name": "Marathon Digital Holdings", "sector": "crypto"},
    {"symbol": "CLSK", "name": "CleanSpark Inc.", "sector": "crypto"},
    {"symbol": "BITF", "name": "Bitfarms Ltd.", "sector": "crypto"},
    {"symbol": "HUT", "name": "Hut 8 Mining Corp.", "sector": "crypto"},
    {"symbol": "CIFR", "name": "Cipher Mining", "sector": "crypto"},
]

# Real Estate Stocks
REAL_ESTATE_STOCKS = [
    {"symbol": "PLD", "name": "Prologis Inc.", "sector": "real_estate"},
    {"symbol": "AMT", "name": "American Tower Corporation", "sector": "real_estate"},
    {"symbol": "CCI", "name": "Crown Castle Inc.", "sector": "real_estate"},
    {"symbol": "EQIX", "name": "Equinix Inc.", "sector": "real_estate"},
    {"symbol": "SPG", "name": "Simon Property Group", "sector": "real_estate"},
    {"symbol": "O", "name": "Realty Income Corporation", "sector": "real_estate"},
    {"symbol": "WELL", "name": "Welltower Inc.", "sector": "real_estate"},
    {"symbol": "DLR", "name": "Digital Realty Trust", "sector": "real_estate"},
    {"symbol": "AVB", "name": "AvalonBay Communities", "sector": "real_estate"},
    {"symbol": "EQR", "name": "Equity Residential", "sector": "real_estate"},
]

# Utility Stocks
UTILITY_STOCKS = [
    {"symbol": "NEE", "name": "NextEra Energy", "sector": "utilities"},
    {"symbol": "DUK", "name": "Duke Energy Corporation", "sector": "utilities"},
    {"symbol": "SO", "name": "Southern Company", "sector": "utilities"},
    {"symbol": "D", "name": "Dominion Energy", "sector": "utilities"},
    {"symbol": "AEP", "name": "American Electric Power", "sector": "utilities"},
    {"symbol": "EXC", "name": "Exelon Corporation", "sector": "utilities"},
    {"symbol": "SRE", "name": "Sempra", "sector": "utilities"},
    {"symbol": "XEL", "name": "Xcel Energy", "sector": "utilities"},
    {"symbol": "ED", "name": "Consolidated Edison", "sector": "utilities"},
    {"symbol": "WEC", "name": "WEC Energy Group", "sector": "utilities"},
]

# Complete universe
ALL_TICKERS = (
    SECTOR_ETFS
    + INDEX_ETFS
    + THEMATIC_ETFS
    + LEVERAGED_ETFS
    + TECH_STOCKS
    + FINANCIAL_STOCKS
    + HEALTHCARE_STOCKS
    + ENERGY_STOCKS
    + CONSUMER_STOCKS
    + INDUSTRIAL_STOCKS
    + COMMUNICATIONS_STOCKS
    + CRYPTO_STOCKS
    + REAL_ESTATE_STOCKS
    + UTILITY_STOCKS
)


def get_all_symbols() -> list[str]:
    """Get all symbols in the universe."""
    return [t["symbol"] for t in ALL_TICKERS]


def get_sector_for_symbol(symbol: str) -> Optional[str]:
    """
    Get the sector for a given symbol.

    Args:
        symbol: Stock symbol (case-insensitive)

    Returns:
        Sector name or None if not found
    """
    symbol = symbol.upper()
    for ticker in ALL_TICKERS:
        if ticker["symbol"] == symbol:
            return ticker["sector"]
    return None


def get_symbols_by_sector(sector: str) -> list[str]:
    """
    Get all symbols in a given sector.

    Args:
        sector: Sector name (e.g., "technology", "financials")

    Returns:
        List of symbols in that sector
    """
    sector = sector.lower()
    return [t["symbol"] for t in ALL_TICKERS if t["sector"] == sector]


def get_symbols_for_biggest_movers(include_biggest_movers: Optional[str]) -> list[str]:
    """
    Get symbols to analyze for biggest movers based on the include_biggest_movers parameter.

    Args:
        include_biggest_movers: Sector name (e.g., "technology"), "market" for all, or None

    Returns:
        List of symbols to analyze
    """
    if include_biggest_movers is None:
        return []

    if include_biggest_movers.lower() in ("market", "all"):
        return get_all_symbols()

    # Filter by sector
    return get_symbols_by_sector(include_biggest_movers)


def get_sector_etf_for_sector(sector: str) -> Optional[str]:
    """
    Get the primary sector ETF for a given sector.

    Args:
        sector: Sector name

    Returns:
        ETF symbol or None
    """
    sector = sector.lower()
    for etf in SECTOR_ETFS:
        if etf["sector"] == sector:
            return etf["symbol"]
    return None


# Build symbol-to-sector lookup for quick access
_SYMBOL_TO_SECTOR: dict[str, str] = {t["symbol"]: t["sector"] for t in ALL_TICKERS}
_SYMBOL_TO_NAME: dict[str, str] = {t["symbol"]: t["name"] for t in ALL_TICKERS}


def get_ticker_info(symbol: str) -> Optional[dict[str, str]]:
    """
    Get full ticker info.

    Args:
        symbol: Stock symbol

    Returns:
        Dict with symbol, name, sector or None
    """
    symbol = symbol.upper()
    if symbol in _SYMBOL_TO_SECTOR:
        return {
            "symbol": symbol,
            "name": _SYMBOL_TO_NAME.get(symbol, ""),
            "sector": _SYMBOL_TO_SECTOR[symbol],
        }
    return None


# Default indices to always include
DEFAULT_INDICES = ["SPY", "QQQ"]
