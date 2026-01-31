# Flux-RX API Module: Main user-facing functions
from __future__ import annotations

from typing import Optional, Union, Literal

import plotly.graph_objects as go

from flux_rx.data import fetch, get_info, fetch_multiple, align_dataframes
from flux_rx.analytics import compute_metrics, format_metrics, monthly_returns
from flux_rx.charts import (
    price_chart,
    volume_chart,
    drawdown_chart,
    rolling_vol_chart,
    rolling_sharpe_chart,
    monthly_heatmap,
    performance_chart,
    risk_return_scatter,
    correlation_matrix,
    cumulative_returns_chart,
    candlestick_chart,
)
from flux_rx.report import generate_report, generate_comparison_report
from flux_rx.compare import compare_tickers, ComparisonResult
from flux_rx.themes import DEFAULT_THEME

ChartKind = Literal[
    "price",
    "volume",
    "drawdown",
    "volatility",
    "sharpe",
    "monthly",
    "cumulative",
    "candlestick",
    "performance",
]


def quick(
    ticker: str,
    period: str = "5y",
    benchmark: Optional[str] = None,
    theme: str = DEFAULT_THEME,
    save: Optional[str] = None,
    show: bool = True,
) -> str:
    """
    Generate a complete analysis report for a single ticker.
    
    This is the primary one-liner API for Flux-RX. It fetches data,
    computes all metrics, generates charts, and produces a beautiful
    interactive HTML report.
    
    Args:
        ticker: Stock symbol (e.g., "AAPL", "SPY")
        period: Time period ("1y", "2y", "5y", "10y", "max")
        benchmark: Optional benchmark ticker for comparison
        theme: Visual theme ("glass", "midnight", "light", "terminal")
        save: Path to save HTML report (e.g., "AAPL.html")
        show: Whether to open report in browser
    
    Returns:
        HTML string of the generated report
    """
    html = generate_report(
        ticker=ticker,
        period=period,
        benchmark=benchmark,
        theme=theme,
        save=save,
    )
    
    if show and save:
        import webbrowser
        import os
        webbrowser.open(f"file://{os.path.abspath(save)}")
    
    return html


def chart(
    ticker: str,
    kind: ChartKind = "price",
    period: str = "5y",
    theme: str = DEFAULT_THEME,
    height: int = 500,
    **kwargs,
) -> go.Figure:
    """
    Generate a single chart for a ticker.
    
    Args:
        ticker: Stock symbol
        kind: Chart type - "price", "volume", "drawdown", "volatility", 
              "sharpe", "monthly", "cumulative", "candlestick", "performance"
        period: Time period
        theme: Visual theme
        height: Chart height in pixels
        **kwargs: Additional arguments passed to chart functions
    
    Returns:
        Plotly Figure object
    """
    df = fetch(ticker, period=period)
    prices = df["Close"]
    
    chart_map = {
        "price": lambda: price_chart(
            df, ticker=ticker, theme=theme, height=height,
            show_volume=kwargs.get("show_volume", False),
            ma_windows=kwargs.get("ma_windows"),
        ),
        "volume": lambda: volume_chart(df, ticker=ticker, theme=theme, height=height),
        "drawdown": lambda: drawdown_chart(prices, ticker=ticker, theme=theme, height=height),
        "volatility": lambda: rolling_vol_chart(
            prices, 
            window=kwargs.get("window", 21),
            ticker=ticker, 
            theme=theme, 
            height=height,
        ),
        "sharpe": lambda: rolling_sharpe_chart(
            prices,
            window=kwargs.get("window", 63),
            ticker=ticker,
            theme=theme,
            height=height,
        ),
        "monthly": lambda: monthly_heatmap(prices, ticker=ticker, theme=theme, height=height),
        "cumulative": lambda: cumulative_returns_chart(
            prices,
            ticker=ticker,
            theme=theme,
            height=height,
        ),
        "candlestick": lambda: candlestick_chart(df, ticker=ticker, theme=theme, height=height),
        "performance": lambda: _single_performance_chart(ticker, period, theme, height),
    }
    
    if kind not in chart_map:
        available = ", ".join(chart_map.keys())
        raise ValueError(f"Unknown chart kind: {kind}. Available: {available}")
    
    return chart_map[kind]()


def _single_performance_chart(
    ticker: str,
    period: str,
    theme: str,
    height: int,
) -> go.Figure:
    df = fetch(ticker, period=period)
    return performance_chart({ticker: df["Close"]}, theme=theme, height=height)


def compare(
    tickers: list[str],
    period: str = "5y",
    kind: Literal["performance", "risk_return", "correlation", "report"] = "performance",
    theme: str = DEFAULT_THEME,
    save: Optional[str] = None,
    height: int = 500,
) -> Union[go.Figure, ComparisonResult, str]:
    """
    Compare multiple tickers with various visualizations.
    
    Args:
        tickers: List of stock symbols
        period: Time period
        kind: Comparison type - "performance", "risk_return", "correlation", "report"
        theme: Visual theme
        save: Path to save (for report kind)
        height: Chart height
    
    Returns:
        Plotly Figure, ComparisonResult object, or HTML string depending on kind
    """
    if kind == "report":
        return generate_comparison_report(
            tickers=tickers,
            period=period,
            theme=theme,
            save=save,
        )
    
    comparison = compare_tickers(tickers, period=period)
    
    if kind == "performance":
        prices_dict = {t: comparison.prices[t] for t in tickers}
        return performance_chart(prices_dict, theme=theme, height=height)
    
    if kind == "risk_return":
        return risk_return_scatter(comparison.metrics, theme=theme, height=height)
    
    if kind == "correlation":
        return correlation_matrix(comparison.prices, theme=theme, height=height)
    
    return comparison


def metrics(
    ticker: str,
    period: str = "5y",
    benchmark: Optional[str] = None,
    formatted: bool = True,
) -> dict:
    """
    Compute key financial metrics for a ticker.
    
    Args:
        ticker: Stock symbol
        period: Time period
        benchmark: Optional benchmark for beta/alpha calculation
        formatted: Return formatted strings if True, raw values if False
    
    Returns:
        Dictionary of metrics
    """
    df = fetch(ticker, period=period)
    prices = df["Close"]
    
    benchmark_prices = None
    if benchmark:
        bench_df = fetch(benchmark, period=period)
        aligned_idx = prices.index.intersection(bench_df.index)
        prices = prices.loc[aligned_idx]
        benchmark_prices = bench_df["Close"].loc[aligned_idx]
    
    raw_metrics = compute_metrics(prices, benchmark_prices)
    
    if formatted:
        return format_metrics(raw_metrics)
    return raw_metrics


def info(ticker: str) -> dict:
    """
    Get company/security information.
    
    Args:
        ticker: Stock symbol
    
    Returns:
        Dictionary with name, sector, market cap, etc.
    """
    return get_info(ticker)


def app(
    tickers: Optional[list[str]] = None,
    port: int = 8050,
    debug: bool = False,
    theme: str = DEFAULT_THEME,
):
    """
    Launch the interactive Flux-RX dashboard application.
    
    Args:
        tickers: Optional list of default tickers to display
        port: Port number for the web server
        debug: Enable debug mode
        theme: Default visual theme
    """
    from flux_rx.dashboard import create_app
    
    application = create_app(default_tickers=tickers, default_theme=theme)
    application.run(port=port, debug=debug)


def help_api() -> None:
    """Print quick reference for Flux-RX API."""
    print("""
Flux-RX Quick Reference
=======================

One-liner report:
    fx.quick("AAPL", period="5y", benchmark="SPY", save="AAPL.html")

Single charts:
    fx.chart("AAPL", kind="price")
    fx.chart("AAPL", kind="drawdown")
    fx.chart("AAPL", kind="volatility")
    fx.chart("AAPL", kind="sharpe")
    fx.chart("AAPL", kind="monthly")

Comparisons:
    fx.compare(["QQQ", "SPY", "IWM"], kind="performance")
    fx.compare(["QQQ", "SPY", "IWM"], kind="risk_return")
    fx.compare(["QQQ", "SPY", "IWM"], kind="correlation")

Interactive app:
    fx.app()

Get metrics:
    fx.metrics("AAPL", benchmark="SPY")

Get info:
    fx.info("AAPL")

Available themes: glass, midnight, light, terminal
Available periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
""")
