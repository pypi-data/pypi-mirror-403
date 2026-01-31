# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Stock Data MCP Server is a Python-based Model Context Protocol (MCP) server providing stock market data (Chinese A-stocks, HK, US), cryptocurrency analytics (OKX, Binance), and financial news. Built on FastMCP framework with **multi-source data provider** supporting automatic failover.

## Development Commands

```bash
# Install dependencies
uv sync

# Run the server (stdio mode - default)
uv run stock-data-mcp

# Run as module
uv run -m stock_data_mcp

# Run with HTTP transport
uv run stock-data-mcp --http --host 0.0.0.0 --port 8808

# Docker deployment
docker-compose up -d
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `TRANSPORT` | Protocol mode: `http`, `sse`, or `stdio` (default) |
| `TUSHARE_TOKEN` | Tushare API token (enables high-priority Tushare data source) |
| `OKX_BASE_URL` | Custom OKX API proxy endpoint |
| `BINANCE_BASE_URL` | Custom Binance API proxy endpoint |
| `NEWSNOW_BASE_URL` | News aggregator endpoint |
| `NEWSNOW_CHANNELS` | Comma-separated news source channels |

## Architecture

### Module Structure

```
stock_data_mcp/
├── __init__.py           # Core MCP server, tools, entry point
├── __main__.py           # Entry point launcher
├── cache.py              # Dual-tier caching (TTLCache + DiskCache)
└── data_provider/        # Multi-source data layer
    ├── __init__.py       # Exports
    ├── types.py          # UnifiedRealtimeQuote, ChipDistribution, CircuitBreaker
    ├── base.py           # BaseFetcher, DataFetcherManager
    ├── efinance_fetcher.py   # Priority 0 - 东方财富
    ├── akshare_fetcher.py    # Priority 1 - 多源(东财/新浪/腾讯)
    ├── tushare_fetcher.py    # Priority 0/2 - Tushare Pro
    ├── baostock_fetcher.py   # Priority 3 - Baostock
    └── yfinance_fetcher.py   # Priority 4 - Yahoo Finance
```

### Multi-Source Data Provider

The `data_provider` module implements automatic failover across multiple data sources:

| Priority | Fetcher | Condition | Markets |
|----------|---------|-----------|---------|
| 0 | TushareFetcher | Has TUSHARE_TOKEN | A-shares |
| 0 | EfinanceFetcher | Default | A-shares, ETF |
| 1 | AkshareFetcher | Default | A-shares, ETF, HK |
| 3 | BaostockFetcher | Default | A-shares |
| 4 | YfinanceFetcher | Default | Global |

**Key Features:**
- **CircuitBreaker**: Automatic source isolation on failures (5min cooldown)
- **Retry with exponential backoff**: Configurable per fetcher
- **Rate limiting**: Anti-blocking with random sleep
- **Unified column names**: Internal English (`date`, `open`, `close`), output Chinese (`日期`, `开盘`, `收盘`)

### Tool Pattern

All MCP tools follow the decorator pattern:
```python
@mcp.tool()
def tool_name(param: str, ...) -> str:
    # For A-shares, use multi-source manager
    manager = get_data_manager()
    df = manager.get_daily_data(symbol, days=30)
    # Process and return CSV-formatted string
```

### Data Flow

```
MCP Request → Tool Function → DataFetcherManager
           → Try Fetchers by Priority → CircuitBreaker Check
           → Fetch Data (with retry) → Normalize to English columns
           → Technical Indicators (optional) → Convert to Chinese columns
           → CSV Response
```

### Tool Categories (27+ tools)

1. **Stock Search/Info**: `search`, `stock_info`, `stock_prices`, `stock_indicators_a/_hk/_us`, `trading_suggest`
2. **A-Stock Market**: `get_current_time`, `stock_zt_pool_em`, `stock_zt_pool_strong_em`, `stock_lhb_ggtj_sina`, `stock_sector_fund_flow_rank`
3. **News**: `stock_news`, `stock_news_global`
4. **Cryptocurrency**: `okx_prices`, `okx_loan_ratios`, `okx_taker_volume`, `binance_ai_report`
5. **Real-time & Analytics** (NEW): `stock_realtime`, `stock_chip`, `stock_batch_realtime`, `data_source_status`

### Technical Indicators

Computed server-side in `__init__.py`:
- MACD (12, 26, 9 EMA periods)
- KDJ (9-period RSV)
- RSI (14-period)
- Bollinger Bands (20-period, 2 std dev)

### External Data Sources

- **Efinance** - Primary A-share data (Priority 0)
- **Akshare** - Multi-source: 东财/新浪/腾讯 (Priority 1)
- **Tushare** - Pro API with token (Priority 0 when configured)
- **Baostock** - Free A-share historical data (Priority 3)
- **YFinance** - International stocks fallback (Priority 4)
- **OKX API** - Crypto market K-lines, margin ratios
- **Binance API** - AI analysis reports
- **Eastmoney** - Financial news scraping

## CI/CD Workflows

- **`.github/workflows/pypi.yaml`** - Publishes to PyPI on release/main push
- **`.github/workflows/docker.yaml`** - Multi-arch Docker builds (amd64/arm64) to GHCR
- **`.github/workflows/release.yaml`** - Publishes to official MCP registry

## Adding New Data Source

1. Create new fetcher in `data_provider/xxx_fetcher.py`:
```python
class XxxFetcher(BaseFetcher):
    name = "XxxFetcher"
    priority = N  # Lower = higher priority

    def _fetch_raw_data(self, stock_code, start_date, end_date):
        # Fetch data from source
        pass

    def _normalize_data(self, df, stock_code):
        # Map columns to STANDARD_COLUMNS
        pass
```

2. Register in `data_provider/__init__.py`
3. Add to `DataFetcherManager._init_default_fetchers()` in `base.py`

## Adding New MCP Tools

1. Add function with `@mcp.tool()` decorator in `__init__.py`
2. Use typed parameters for MCP schema generation
3. For A-shares, use `get_data_manager()` for multi-source support
4. Return CSV string via `df.to_csv()` for DataFrame results
