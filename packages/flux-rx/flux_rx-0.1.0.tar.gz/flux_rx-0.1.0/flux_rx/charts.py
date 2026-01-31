# Flux-RX Charts Module: Plotly visualization components
from __future__ import annotations

from typing import Optional, Union

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from flux_rx.analytics import (
    cumulative_returns,
    daily_returns,
    drawdown_series,
    monthly_returns as calc_monthly_returns,
    rolling_sharpe as calc_rolling_sharpe,
    rolling_volatility as calc_rolling_volatility,
    correlation_matrix as calc_correlation_matrix,
)
from flux_rx.themes import create_layout, get_theme, get_heatmap_colorscale, DEFAULT_THEME


def price_chart(
    df: pd.DataFrame,
    ticker: str = "",
    ma_windows: Optional[list[int]] = None,
    theme: str = DEFAULT_THEME,
    height: int = 450,
    show_volume: bool = False,
) -> go.Figure:
    if ma_windows is None:
        ma_windows = [20, 50, 200]
    
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    palette = theme_config["palette"]
    
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.75, 0.25],
        )
    else:
        fig = go.Figure()
    
    row = 1 if show_volume else None
    
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name="Price",
            line={"color": colors["primary"], "width": 2},
            hovertemplate="%{y:$.2f}<extra></extra>",
        ),
        row=row, col=1 if show_volume else None,
    )
    
    for i, window in enumerate(ma_windows):
        if len(df) >= window:
            ma = df["Close"].rolling(window=window).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=ma,
                    mode="lines",
                    name=f"{window}D MA",
                    line={"color": palette[i + 1], "width": 1.5, "dash": "dot"},
                    hovertemplate=f"{window}D MA: %{{y:$.2f}}<extra></extra>",
                ),
                row=row, col=1 if show_volume else None,
            )
    
    if show_volume and "Volume" in df.columns:
        volume_colors = [
            colors["positive"] if df["Close"].iloc[i] >= df["Open"].iloc[i] else colors["negative"]
            for i in range(len(df))
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["Volume"],
                name="Volume",
                marker_color=volume_colors,
                opacity=0.7,
                hovertemplate="Vol: %{y:,.0f}<extra></extra>",
            ),
            row=2, col=1,
        )
    
    layout = create_layout(
        theme_config,
        title=f"{ticker} Price" if ticker else "Price",
        height=height,
        y_title="Price ($)",
    )
    fig.update_layout(**layout)
    
    if show_volume:
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig


def volume_chart(
    df: pd.DataFrame,
    ticker: str = "",
    theme: str = DEFAULT_THEME,
    height: int = 300,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    
    volume_colors = [
        colors["positive"] if df["Close"].iloc[i] >= df["Open"].iloc[i] else colors["negative"]
        for i in range(len(df))
    ]
    
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color=volume_colors,
            opacity=0.8,
            hovertemplate="Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>",
        )
    )
    
    layout = create_layout(
        theme_config,
        title=f"{ticker} Volume" if ticker else "Volume",
        height=height,
        show_legend=False,
        y_title="Volume",
    )
    fig.update_layout(**layout)
    
    return fig


def drawdown_chart(
    prices: pd.Series,
    ticker: str = "",
    theme: str = DEFAULT_THEME,
    height: int = 350,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    
    dd = drawdown_series(prices)
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dd.index,
            y=dd * 100,
            mode="lines",
            name="Drawdown",
            fill="tozeroy",
            line={"color": colors["negative"], "width": 1.5},
            fillcolor=f"rgba({int(colors['negative'][1:3], 16)}, {int(colors['negative'][3:5], 16)}, {int(colors['negative'][5:7], 16)}, 0.3)",
            hovertemplate="Drawdown: %{y:.2f}%<extra></extra>",
        )
    )
    
    max_dd_idx = dd.idxmin()
    max_dd_val = dd.min() * 100
    
    fig.add_trace(
        go.Scatter(
            x=[max_dd_idx],
            y=[max_dd_val],
            mode="markers+text",
            name="Max Drawdown",
            marker={"color": colors["accent"], "size": 10, "symbol": "diamond"},
            text=[f"{max_dd_val:.1f}%"],
            textposition="bottom center",
            textfont={"color": colors["text"], "size": 11},
            hovertemplate=f"Max Drawdown: {max_dd_val:.2f}%<extra></extra>",
        )
    )
    
    layout = create_layout(
        theme_config,
        title=f"{ticker} Drawdown" if ticker else "Drawdown",
        height=height,
        show_legend=False,
        y_title="Drawdown (%)",
    )
    fig.update_layout(**layout)
    fig.update_yaxes(range=[min(dd * 100) * 1.2, 5])
    
    return fig


def rolling_vol_chart(
    prices: pd.Series,
    window: int = 21,
    ticker: str = "",
    theme: str = DEFAULT_THEME,
    height: int = 350,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    
    roll_vol = calc_rolling_volatility(prices, window=window) * 100
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=roll_vol.index,
            y=roll_vol,
            mode="lines",
            name=f"{window}D Rolling Volatility",
            line={"color": colors["secondary"], "width": 2},
            fill="tozeroy",
            fillcolor=f"rgba({int(colors['secondary'][1:3], 16)}, {int(colors['secondary'][3:5], 16)}, {int(colors['secondary'][5:7], 16)}, 0.2)",
            hovertemplate="Volatility: %{y:.1f}%<extra></extra>",
        )
    )
    
    avg_vol = roll_vol.mean()
    fig.add_hline(
        y=avg_vol,
        line_dash="dash",
        line_color=colors["text_muted"],
        annotation_text=f"Avg: {avg_vol:.1f}%",
        annotation_position="right",
        annotation_font_color=colors["text_muted"],
    )
    
    layout = create_layout(
        theme_config,
        title=f"{ticker} Rolling Volatility ({window}D)" if ticker else f"Rolling Volatility ({window}D)",
        height=height,
        show_legend=False,
        y_title="Annualized Volatility (%)",
    )
    fig.update_layout(**layout)
    
    return fig


def rolling_sharpe_chart(
    prices: pd.Series,
    window: int = 63,
    ticker: str = "",
    theme: str = DEFAULT_THEME,
    height: int = 350,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    
    roll_sharpe = calc_rolling_sharpe(prices, window=window)
    
    fig = go.Figure()
    
    positive_sharpe = roll_sharpe.copy()
    positive_sharpe[positive_sharpe < 0] = np.nan
    negative_sharpe = roll_sharpe.copy()
    negative_sharpe[negative_sharpe >= 0] = np.nan
    
    fig.add_trace(
        go.Scatter(
            x=positive_sharpe.index,
            y=positive_sharpe,
            mode="lines",
            name="Positive",
            line={"color": colors["positive"], "width": 2},
            fill="tozeroy",
            fillcolor=f"rgba({int(colors['positive'][1:3], 16)}, {int(colors['positive'][3:5], 16)}, {int(colors['positive'][5:7], 16)}, 0.3)",
            hovertemplate="Sharpe: %{y:.2f}<extra></extra>",
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=negative_sharpe.index,
            y=negative_sharpe,
            mode="lines",
            name="Negative",
            line={"color": colors["negative"], "width": 2},
            fill="tozeroy",
            fillcolor=f"rgba({int(colors['negative'][1:3], 16)}, {int(colors['negative'][3:5], 16)}, {int(colors['negative'][5:7], 16)}, 0.3)",
            hovertemplate="Sharpe: %{y:.2f}<extra></extra>",
        )
    )
    
    fig.add_hline(y=0, line_color=colors["grid"], line_width=1)
    fig.add_hline(y=1, line_dash="dash", line_color=colors["text_muted"], line_width=1, opacity=0.5)
    
    layout = create_layout(
        theme_config,
        title=f"{ticker} Rolling Sharpe Ratio ({window}D)" if ticker else f"Rolling Sharpe Ratio ({window}D)",
        height=height,
        show_legend=False,
        y_title="Sharpe Ratio",
    )
    fig.update_layout(**layout)
    
    return fig


def monthly_heatmap(
    prices: pd.Series,
    ticker: str = "",
    theme: str = DEFAULT_THEME,
    height: int = 400,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    
    monthly_df = calc_monthly_returns(prices)
    
    z_values = monthly_df.values * 100
    x_labels = monthly_df.columns.tolist()
    y_labels = monthly_df.index.tolist()
    
    text_matrix = [[f"{val:.1f}%" if not np.isnan(val) else "" for val in row] for row in z_values]
    
    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            z=z_values,
            x=x_labels,
            y=y_labels,
            text=text_matrix,
            texttemplate="%{text}",
            textfont={"size": 10, "color": colors["text"]},
            colorscale=get_heatmap_colorscale(),
            zmid=0,
            zmin=-15,
            zmax=15,
            colorbar={
                "title": {"text": "Return %", "font": {"color": colors["text"]}},
                "tickfont": {"color": colors["text_muted"]},
                "ticksuffix": "%",
            },
            hovertemplate="Year: %{y}<br>Month: %{x}<br>Return: %{z:.2f}%<extra></extra>",
        )
    )
    
    layout = create_layout(
        theme_config,
        title=f"{ticker} Monthly Returns" if ticker else "Monthly Returns",
        height=height,
        show_legend=False,
    )
    layout["xaxis"]["dtick"] = 1
    layout["yaxis"]["dtick"] = 1
    layout["yaxis"]["autorange"] = "reversed"
    fig.update_layout(**layout)
    
    return fig


def performance_chart(
    prices_dict: dict[str, pd.Series],
    normalize: bool = True,
    theme: str = DEFAULT_THEME,
    height: int = 500,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    palette = theme_config["palette"]
    
    fig = go.Figure()
    
    for i, (ticker, prices) in enumerate(prices_dict.items()):
        if normalize:
            y_data = (prices / prices.iloc[0] - 1) * 100
            suffix = "%"
        else:
            y_data = prices
            suffix = ""
        
        fig.add_trace(
            go.Scatter(
                x=prices.index,
                y=y_data,
                mode="lines",
                name=ticker,
                line={"color": palette[i % len(palette)], "width": 2},
                hovertemplate=f"{ticker}: %{{y:.2f}}{suffix}<extra></extra>",
            )
        )
    
    layout = create_layout(
        theme_config,
        title="Performance Comparison",
        height=height,
        y_title="Return (%)" if normalize else "Price ($)",
    )
    fig.update_layout(**layout)
    
    if normalize:
        fig.add_hline(y=0, line_color=colors["grid"], line_width=1)
    
    return fig


def risk_return_scatter(
    metrics: dict[str, dict],
    theme: str = DEFAULT_THEME,
    height: int = 500,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    palette = theme_config["palette"]
    
    fig = go.Figure()
    
    tickers = list(metrics.keys())
    vols = [metrics[t]["volatility"] * 100 for t in tickers]
    cagrs = [metrics[t]["cagr"] * 100 for t in tickers]
    sharpes = [metrics[t]["sharpe_ratio"] for t in tickers]
    
    marker_sizes = [max(20, min(50, s * 20)) if s > 0 else 20 for s in sharpes]
    
    for i, ticker in enumerate(tickers):
        fig.add_trace(
            go.Scatter(
                x=[vols[i]],
                y=[cagrs[i]],
                mode="markers+text",
                name=ticker,
                marker={
                    "color": palette[i % len(palette)],
                    "size": marker_sizes[i],
                    "line": {"color": colors["text"], "width": 1},
                },
                text=[ticker],
                textposition="top center",
                textfont={"color": colors["text"], "size": 12},
                hovertemplate=(
                    f"<b>{ticker}</b><br>"
                    f"CAGR: {cagrs[i]:.2f}%<br>"
                    f"Volatility: {vols[i]:.2f}%<br>"
                    f"Sharpe: {sharpes[i]:.2f}<extra></extra>"
                ),
            )
        )
    
    min_vol, max_vol = min(vols), max(vols)
    vol_range = np.linspace(min_vol * 0.8, max_vol * 1.2, 50)
    for sharpe in [0.5, 1.0, 1.5]:
        returns_line = sharpe * vol_range / 100 * 100 + 4
        fig.add_trace(
            go.Scatter(
                x=vol_range,
                y=returns_line,
                mode="lines",
                name=f"Sharpe={sharpe}",
                line={"color": colors["grid"], "width": 1, "dash": "dot"},
                showlegend=False,
                hoverinfo="skip",
            )
        )
    
    layout = create_layout(
        theme_config,
        title="Risk-Return Analysis",
        height=height,
        x_title="Annualized Volatility (%)",
        y_title="CAGR (%)",
    )
    layout["yaxis"]["side"] = "left"
    fig.update_layout(**layout)
    
    return fig


def correlation_matrix(
    prices_df: pd.DataFrame,
    theme: str = DEFAULT_THEME,
    height: int = 500,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    
    corr = calc_correlation_matrix(prices_df)
    
    z_values = corr.values
    labels = corr.columns.tolist()
    
    text_matrix = [[f"{val:.2f}" for val in row] for row in z_values]
    
    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            z=z_values,
            x=labels,
            y=labels,
            text=text_matrix,
            texttemplate="%{text}",
            textfont={"size": 12, "color": colors["text"]},
            colorscale=[
                [0.0, colors["negative"]],
                [0.5, colors["surface"]],
                [1.0, colors["positive"]],
            ],
            zmin=-1,
            zmax=1,
            colorbar={
                "title": {"text": "Correlation", "font": {"color": colors["text"]}},
                "tickfont": {"color": colors["text_muted"]},
            },
            hovertemplate="%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>",
        )
    )
    
    layout = create_layout(
        theme_config,
        title="Correlation Matrix",
        height=height,
        show_legend=False,
    )
    fig.update_layout(**layout)
    
    return fig


def cumulative_returns_chart(
    prices: pd.Series,
    benchmark_prices: Optional[pd.Series] = None,
    ticker: str = "",
    benchmark_ticker: str = "",
    theme: str = DEFAULT_THEME,
    height: int = 400,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    
    cum_ret = cumulative_returns(prices) * 100
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=cum_ret.index,
            y=cum_ret,
            mode="lines",
            name=ticker or "Asset",
            line={"color": colors["primary"], "width": 2},
            fill="tozeroy",
            fillcolor=f"rgba({int(colors['primary'][1:3], 16)}, {int(colors['primary'][3:5], 16)}, {int(colors['primary'][5:7], 16)}, 0.15)",
            hovertemplate="Return: %{y:.2f}%<extra></extra>",
        )
    )
    
    if benchmark_prices is not None:
        bench_cum_ret = cumulative_returns(benchmark_prices) * 100
        fig.add_trace(
            go.Scatter(
                x=bench_cum_ret.index,
                y=bench_cum_ret,
                mode="lines",
                name=benchmark_ticker or "Benchmark",
                line={"color": colors["text_muted"], "width": 1.5, "dash": "dash"},
                hovertemplate="Benchmark: %{y:.2f}%<extra></extra>",
            )
        )
    
    fig.add_hline(y=0, line_color=colors["grid"], line_width=1)
    
    layout = create_layout(
        theme_config,
        title=f"{ticker} Cumulative Returns" if ticker else "Cumulative Returns",
        height=height,
        y_title="Cumulative Return (%)",
    )
    fig.update_layout(**layout)
    
    return fig


def candlestick_chart(
    df: pd.DataFrame,
    ticker: str = "",
    theme: str = DEFAULT_THEME,
    height: int = 500,
) -> go.Figure:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
            increasing={"line": {"color": colors["positive"]}, "fillcolor": colors["positive"]},
            decreasing={"line": {"color": colors["negative"]}, "fillcolor": colors["negative"]},
        )
    )
    
    layout = create_layout(
        theme_config,
        title=f"{ticker} Candlestick" if ticker else "Candlestick",
        height=height,
        show_legend=False,
        y_title="Price ($)",
    )
    layout["xaxis"]["rangeslider"] = {"visible": False}
    fig.update_layout(**layout)
    
    return fig
