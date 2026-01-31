# Flux-RX

**A Finance Python Package**

Flux-RX makes financial analysis and visualization effortless. Generate publication-quality interactive charts, reports, and dashboards for any stock, ETF, or index with minimal code.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
import flux_rx as fx

# Generate a complete analysis report
fx.quick("AAPL", period="5y", benchmark="SPY", save="AAPL.html")

# Create individual charts
fx.chart("SPY", kind="price", period="10y")
fx.chart("AAPL", kind="drawdown")
fx.chart("TSLA", kind="monthly")

# Compare multiple assets
fx.compare(["QQQ", "SPY", "IWM"], period="5y", kind="risk_return")

# Launch interactive dashboard
fx.app()
```

## Features

### Data
- Automatic data fetching via yfinance
- Local caching to avoid repeated downloads
- Company metadata and fundamentals
- Support for stocks, ETFs, and indices

### Analytics
- Daily and cumulative returns
- CAGR, volatility, max drawdown
- Sharpe, Sortino, and Calmar ratios
- Rolling volatility and rolling Sharpe
- Beta and alpha vs benchmark
- Monthly returns analysis

### Charts
- Price charts with moving averages
- Candlestick OHLC charts
- Volume analysis
- Drawdown curves
- Rolling volatility and Sharpe charts
- Monthly returns heatmaps
- Risk-return scatter plots
- Correlation matrices

### Reports
- Interactive HTML reports
- Single-ticker analysis
- Multi-ticker comparison
- All charts in one exportable file

### Dashboard
- Full web application via Dash
- Single ticker analysis mode
- Multi-ticker comparison mode

## API Reference

### `fx.quick(ticker, period, benchmark, save)`
Generate a complete analysis report.

```python
fx.quick("AAPL", period="5y", benchmark="SPY", save="report.html")
```

### `fx.chart(ticker, kind, period)`
Create individual charts.

```python
# Chart types: price, volume, drawdown, volatility, sharpe, monthly, cumulative, candlestick
fx.chart("AAPL", kind="price", period="2y")
```

### `fx.compare(tickers, period, kind)`
Compare multiple assets.

```python
# Comparison types: performance, risk_return, correlation, report
fx.compare(["AAPL", "MSFT", "GOOGL"], period="5y", kind="performance")
```

### `fx.app()`
Launch the interactive dashboard.

```python
fx.app(port=8050)
```

### `fx.metrics(ticker, period, benchmark)`
Get computed metrics as a dictionary.

```python
metrics = fx.metrics("AAPL", period="5y", benchmark="SPY")
# Returns: cagr, volatility, max_drawdown, sharpe_ratio, sortino_ratio, etc.
```

### `fx.info(ticker)`
Get company/security information.

```python
info = fx.info("AAPL")
# Returns: name, sector, industry, market_cap, pe_ratio, etc.
```

## License

MIT License
