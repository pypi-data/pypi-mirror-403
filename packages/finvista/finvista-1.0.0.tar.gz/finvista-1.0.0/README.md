# FinVista

[English](README.md) | [中文](README_zh.md)

> A powerful Python library for global financial data with multi-source failover.

[![PyPI version](https://badge.fury.io/py/finvista.svg)](https://badge.fury.io/py/finvista)
[![Python Version](https://img.shields.io/pypi/pyversions/finvista.svg)](https://pypi.org/project/finvista/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/finvfamily/finvista/actions/workflows/tests.yml/badge.svg)](https://github.com/finvfamily/finvista/actions)
[![Documentation](https://img.shields.io/badge/docs-online-blue.svg)](https://finvfamily.github.io/finvista/)

📖 **[Documentation](https://finvfamily.github.io/finvista/)** | 🐛 **[Issues](https://github.com/finvfamily/finvista/issues)** | 💬 **[Discussions](https://github.com/finvfamily/finvista/discussions)**

## Features

- 🔄 **Multi-Source Failover**: Automatically switches to backup data sources when primary fails
- ⚡ **Circuit Breaker Pattern**: Prevents cascade failures with smart circuit breaking
- 💾 **Built-in Caching**: LRU cache reduces redundant API calls
- 🚦 **Rate Limiting**: Intelligent rate limiting to avoid being blocked
- 🔒 **Type Safe**: Full type hints support for better IDE experience
- 🎯 **Easy to Use**: Simple functional API design
- 🌍 **Global Markets**: Support for China, US, Hong Kong and more markets
- 📊 **Comprehensive Data**: Stocks, indices, funds, futures, options, bonds, and macroeconomic data

## Installation

```bash
pip install finvista
```

## Quick Start

### China A-Share Stocks

```python
import finvista as fv

# Get daily historical data
df = fv.get_cn_stock_daily("000001", start_date="2024-01-01")
print(df.head())

# Get real-time quotes
df = fv.get_cn_stock_quote(["000001", "600519"])
print(df)

# List all stocks
df = fv.list_cn_stock_symbols(market="main")
print(f"Found {len(df)} stocks")

# Search stocks by keyword
df = fv.search_cn_stock("银行")
print(df)
```

### Financial Statements

```python
# Income statement
df = fv.get_cn_income_statement("000001")

# Balance sheet
df = fv.get_cn_balance_sheet("000001")

# Cash flow statement
df = fv.get_cn_cash_flow("000001")

# Dividend history
df = fv.get_cn_dividend_history("000001")

# Performance forecast
df = fv.get_cn_performance_forecast()
```

### Money Flow

```python
# Stock money flow (last 30 days)
df = fv.get_cn_stock_moneyflow("000001", days=30)

# Real-time money flow
df = fv.get_cn_stock_moneyflow_realtime("000001")

# Industry money flow
df = fv.get_cn_industry_moneyflow()
```

### Minute-Level Data

```python
# 5-minute K-line data
df = fv.get_cn_stock_minute("000001", period="5", days=5)

# 1-minute data
df = fv.get_cn_stock_minute("000001", period="1", days=1)

# Supported periods: "1", "5", "15", "30", "60"
```

### Futures

```python
# List all futures contracts
df = fv.list_cn_futures_symbols()

# Get CFFEX contracts only
df = fv.list_cn_futures_symbols(exchange="CFFEX")

# Get futures daily data
df = fv.get_cn_futures_daily("IF2401", start_date="2024-01-01")

# Get position ranking
df = fv.get_cn_futures_positions("IF")
```

### Convertible Bonds

```python
# List all convertible bonds
df = fv.list_cn_convertible_symbols()

# Get convertible bond daily data
df = fv.get_cn_convertible_daily("113008", start_date="2024-01-01")

# Get convertible bond information
info = fv.get_cn_convertible_info("113008")
```

### Dragon Tiger List (龙虎榜)

```python
# Get latest dragon tiger list
df = fv.get_cn_lhb_list()

# Get specific date
df = fv.get_cn_lhb_list(date="2024-01-15")

# Get trading details
df = fv.get_cn_lhb_detail("000001", "2024-01-15")

# Get institution trading
df = fv.get_cn_lhb_institution()
```

### Options

```python
# List option contracts
df = fv.list_cn_option_contracts("510050")

# Get option daily data
df = fv.get_cn_option_daily("10004456", start_date="2024-01-01")
```

### Shareholders & Stock Pledge

```python
# Get top 10 shareholders
df = fv.get_cn_top_shareholders("000001")

# Get stock pledge data
df = fv.get_cn_stock_pledge("000001")

# Get unlock schedule
df = fv.get_cn_stock_unlock_schedule("2024-01-01", "2024-01-31")
```

### Index Data

```python
# Get index daily data
df = fv.get_cn_index_daily("000300", start_date="2024-01-01")

# Get index constituents
df = fv.get_cn_index_constituents("000300")

# Get index weights
df = fv.get_cn_index_weights("000300")

# List major indices
df = fv.list_cn_major_indices()
```

### ETF Data

```python
# Get ETF share changes
df = fv.get_cn_etf_share_change("510050", days=30)

# Get ETF premium/discount
df = fv.get_cn_etf_premium_discount("510050")
```

### China Funds

```python
# Get fund NAV history
df = fv.get_cn_fund_nav("110011", start_date="2024-01-01")

# Get real-time fund estimates
df = fv.get_cn_fund_quote(["110011", "000001"])

# List all funds by type
df = fv.list_cn_fund_symbols(fund_type="stock")

# Search funds
df = fv.search_cn_fund("沪深300")

# Get fund information
info = fv.get_cn_fund_info("110011")
```

### US Stocks

```python
# Get US stock daily data
df = fv.get_us_stock_daily("AAPL", start_date="2024-01-01")

# Get real-time quotes
df = fv.get_us_stock_quote(["AAPL", "MSFT", "GOOGL"])

# Get company information
info = fv.get_us_stock_info("AAPL")

# Search US stocks
df = fv.search_us_stock("Apple")
```

### Foreign Exchange

```python
# Get current exchange rate
df = fv.get_exchange_rate("USD", "CNY")

# Get historical exchange rates
df = fv.get_exchange_rate_history("USD", "CNY", start_date="2024-01-01")
```

### Macroeconomic Data

```python
# China GDP
df = fv.get_cn_macro_gdp()

# China CPI
df = fv.get_cn_macro_cpi()

# China PPI
df = fv.get_cn_macro_ppi()

# China PMI
df = fv.get_cn_macro_pmi()

# Money Supply (M0, M1, M2)
df = fv.get_cn_macro_money_supply()

# Social Financing
df = fv.get_cn_macro_social_financing()
```

## Command Line Interface

```bash
# Get real-time quotes
finvista quote 000001 600519

# Get US stock quotes
finvista quote AAPL MSFT --market us

# Get historical data
finvista history 000001 --start 2024-01-01 --format csv

# Search stocks
finvista search 银行

# Check data source health
finvista health

# Get macroeconomic data
finvista macro gdp
```

## Configuration

```python
import finvista as fv

# Set HTTP proxy
fv.set_proxies({"http": "http://127.0.0.1:7890"})

# Set request timeout
fv.set_timeout(60)

# Configure caching
fv.set_cache(enabled=True, ttl=300)

# Check data source health
health = fv.get_source_health()
print(health)

# Reset circuit breaker for a source
fv.reset_source_circuit("cn_stock_daily", "eastmoney")

# Set custom source priority
fv.set_source_priority("cn_stock_daily", ["sina", "eastmoney"])
```

## Data Source Failover

FinVista automatically handles data source failures:

```python
import finvista as fv

# Automatic failover - if eastmoney fails, tries sina, then tencent
df = fv.get_cn_stock_daily("000001")

# Check which source was used
print(f"Data from: {df.attrs.get('source')}")

# Force specific source (no failover)
df = fv.get_cn_stock_daily("000001", source="eastmoney")
```

## Data Sources

| Data Type | Primary Source | Backup Sources |
|-----------|---------------|----------------|
| China Stock Daily | East Money | Sina, Tencent |
| China Stock Quote | Sina | Tencent, East Money |
| China Index | East Money | Sina |
| China Fund | Tiantian Fund | - |
| China Financial | East Money | - |
| China Money Flow | East Money | - |
| China Futures | East Money | - |
| China Convertible | East Money | - |
| China Options | East Money | - |
| US Stock | Yahoo Finance | - |
| Forex | East Money | - |
| China Macro | East Money | - |

## API Reference

### China Stocks

| Function | Description |
|----------|-------------|
| `get_cn_stock_daily()` | Get daily historical data |
| `get_cn_stock_quote()` | Get real-time quotes |
| `list_cn_stock_symbols()` | List all stock symbols |
| `search_cn_stock()` | Search stocks by keyword |
| `get_cn_stock_minute()` | Get minute-level K-line data |

### China Financial Data

| Function | Description |
|----------|-------------|
| `get_cn_income_statement()` | Get income statement data |
| `get_cn_balance_sheet()` | Get balance sheet data |
| `get_cn_cash_flow()` | Get cash flow statement data |
| `get_cn_performance_forecast()` | Get performance forecast |
| `get_cn_dividend_history()` | Get dividend history |

### China Money Flow

| Function | Description |
|----------|-------------|
| `get_cn_stock_moneyflow()` | Get historical money flow |
| `get_cn_stock_moneyflow_realtime()` | Get real-time money flow |
| `get_cn_industry_moneyflow()` | Get industry money flow |

### China Indices

| Function | Description |
|----------|-------------|
| `get_cn_index_daily()` | Get daily index data |
| `get_cn_index_quote()` | Get real-time index quotes |
| `list_cn_major_indices()` | List major indices |
| `get_cn_index_constituents()` | Get index constituent stocks |
| `get_cn_index_weights()` | Get index constituent weights |

### China Futures

| Function | Description |
|----------|-------------|
| `list_cn_futures_symbols()` | List all futures contracts |
| `get_cn_futures_daily()` | Get futures daily data |
| `get_cn_futures_positions()` | Get position ranking |

### China Convertible Bonds

| Function | Description |
|----------|-------------|
| `list_cn_convertible_symbols()` | List all convertible bonds |
| `get_cn_convertible_daily()` | Get convertible bond daily data |
| `get_cn_convertible_info()` | Get convertible bond information |

### China Dragon Tiger List

| Function | Description |
|----------|-------------|
| `get_cn_lhb_list()` | Get dragon tiger list |
| `get_cn_lhb_detail()` | Get trading details |
| `get_cn_lhb_institution()` | Get institution trading data |

### China Options

| Function | Description |
|----------|-------------|
| `list_cn_option_contracts()` | List option contracts |
| `get_cn_option_quote()` | Get option quotes |
| `get_cn_option_daily()` | Get option daily data |

### China Shareholders

| Function | Description |
|----------|-------------|
| `get_cn_top_shareholders()` | Get top 10 shareholders |
| `get_cn_stock_pledge()` | Get stock pledge data |
| `get_cn_stock_unlock_schedule()` | Get unlock schedule |

### China ETF

| Function | Description |
|----------|-------------|
| `get_cn_etf_share_change()` | Get ETF share changes |
| `get_cn_etf_premium_discount()` | Get ETF premium/discount |

### China Funds

| Function | Description |
|----------|-------------|
| `get_cn_fund_nav()` | Get fund NAV history |
| `get_cn_fund_quote()` | Get real-time fund estimates |
| `list_cn_fund_symbols()` | List all funds |
| `search_cn_fund()` | Search funds by keyword |
| `get_cn_fund_info()` | Get fund information |

### US Stocks

| Function | Description |
|----------|-------------|
| `get_us_stock_daily()` | Get daily historical data |
| `get_us_stock_quote()` | Get real-time quotes |
| `get_us_stock_info()` | Get company information |
| `search_us_stock()` | Search stocks by keyword |

### Foreign Exchange

| Function | Description |
|----------|-------------|
| `get_exchange_rate()` | Get current exchange rate |
| `get_exchange_rate_history()` | Get historical exchange rates |

### Macroeconomic Data

| Function | Description |
|----------|-------------|
| `get_cn_macro_gdp()` | China GDP data |
| `get_cn_macro_cpi()` | China CPI data |
| `get_cn_macro_ppi()` | China PPI data |
| `get_cn_macro_pmi()` | China PMI data |
| `get_cn_macro_money_supply()` | Money supply (M0/M1/M2) |
| `get_cn_macro_social_financing()` | Social financing data |

### Configuration

| Function | Description |
|----------|-------------|
| `set_proxies()` | Set HTTP proxy |
| `set_timeout()` | Set request timeout |
| `set_cache()` | Configure caching |
| `get_source_health()` | Get data source health status |
| `reset_source_circuit()` | Reset circuit breaker |
| `set_source_priority()` | Set source priority order |

## Requirements

- Python >= 3.10
- pandas >= 2.0.0
- requests >= 2.28.0
- httpx >= 0.24.0

## Contributors

<a href="https://github.com/finvfamily/finvista/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=finvfamily/finvista" />
</a>

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

FinVista is designed for reliable financial data access with automatic failover capabilities, serving quantitative researchers, traders, and financial analysts.

## Star History

<a href="https://github.com/finvfamily/finvista/stargazers">
  <img src="https://starchart.cc/finvfamily/finvista.svg?variant=adaptive" alt="Star History Chart" width="600">
</a>
