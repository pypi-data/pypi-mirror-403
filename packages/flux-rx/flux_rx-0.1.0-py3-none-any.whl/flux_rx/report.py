# Flux-RX Report Module: Publication-quality interactive HTML report generation
from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from flux_rx.analytics import (
    compute_metrics,
    format_metrics,
    monthly_returns,
    drawdown_series,
    rolling_volatility,
    rolling_sharpe,
    daily_returns,
    cumulative_returns,
)
from flux_rx.data import get_info, fetch
from flux_rx.themes import get_theme, DEFAULT_THEME


def _create_main_chart(df: pd.DataFrame, ticker: str, theme_config: dict) -> go.Figure:
    colors = theme_config["colors"]
    palette = theme_config["palette"]
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.6, 0.2, 0.2],
        specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}]]
    )
    
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="OHLC",
            increasing={"line": {"color": colors["positive"], "width": 1}, "fillcolor": colors["positive"]},
            decreasing={"line": {"color": colors["negative"], "width": 1}, "fillcolor": colors["negative"]},
            showlegend=False,
        ),
        row=1, col=1
    )
    
    for i, window in enumerate([20, 50, 200]):
        if len(df) >= window:
            ma = df["Close"].rolling(window=window).mean()
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=ma,
                    mode="lines",
                    name=f"MA{window}",
                    line={"color": palette[i], "width": 1.5},
                    hovertemplate=f"MA{window}: $%{{y:.2f}}<extra></extra>",
                ),
                row=1, col=1
            )
    
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
            showlegend=False,
            hovertemplate="Vol: %{y:,.0f}<extra></extra>",
        ),
        row=2, col=1
    )
    
    dd = drawdown_series(df["Close"])
    fig.add_trace(
        go.Scatter(
            x=dd.index,
            y=dd * 100,
            mode="lines",
            name="Drawdown",
            fill="tozeroy",
            line={"color": colors["negative"], "width": 1},
            fillcolor=f"rgba({int(colors['negative'][1:3], 16)}, {int(colors['negative'][3:5], 16)}, {int(colors['negative'][5:7], 16)}, 0.4)",
            showlegend=False,
            hovertemplate="DD: %{y:.2f}%<extra></extra>",
        ),
        row=3, col=1
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=650,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        font={"family": "Inter, sans-serif", "color": colors["text"]},
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"size": 11}
        },
        hovermode="x unified",
        hoverlabel={"bgcolor": colors["surface"], "bordercolor": colors["border"], "font": {"size": 12}},
        xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        xaxis2={"showgrid": False, "zeroline": False, "showticklabels": False},
        xaxis3={"showgrid": True, "gridcolor": colors["grid"], "zeroline": False, "rangeslider": {"visible": False}},
        yaxis={"showgrid": True, "gridcolor": colors["grid"], "zeroline": False, "side": "right", "tickformat": "$,.0f"},
        yaxis2={"showgrid": False, "zeroline": False, "side": "right", "tickformat": ".2s"},
        yaxis3={"showgrid": True, "gridcolor": colors["grid"], "zeroline": True, "zerolinecolor": colors["grid"], "side": "right", "ticksuffix": "%"},
        dragmode="zoom",
        modebar={"bgcolor": "rgba(0,0,0,0)", "color": colors["text_muted"], "activecolor": colors["primary"]},
    )
    
    fig.update_xaxes(
        rangeselector={
            "buttons": [
                {"count": 1, "label": "1M", "step": "month", "stepmode": "backward"},
                {"count": 3, "label": "3M", "step": "month", "stepmode": "backward"},
                {"count": 6, "label": "6M", "step": "month", "stepmode": "backward"},
                {"count": 1, "label": "1Y", "step": "year", "stepmode": "backward"},
                {"count": 2, "label": "2Y", "step": "year", "stepmode": "backward"},
                {"step": "all", "label": "ALL"}
            ],
            "bgcolor": colors["surface"],
            "activecolor": colors["primary"],
            "bordercolor": colors["border"],
            "font": {"color": colors["text"], "size": 10},
            "x": 0,
            "y": 1.08,
        },
        row=1, col=1
    )
    
    return fig


def _create_analytics_charts(prices: pd.Series, benchmark_prices: Optional[pd.Series], theme_config: dict) -> go.Figure:
    colors = theme_config["colors"]
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Cumulative Returns", "Rolling Volatility (21D)", "Rolling Sharpe (63D)", "Returns Distribution"),
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )
    
    cum_ret = cumulative_returns(prices) * 100
    fig.add_trace(
        go.Scatter(
            x=cum_ret.index,
            y=cum_ret,
            mode="lines",
            name="Asset",
            line={"color": colors["primary"], "width": 2},
            fill="tozeroy",
            fillcolor=f"rgba({int(colors['primary'][1:3], 16)}, {int(colors['primary'][3:5], 16)}, {int(colors['primary'][5:7], 16)}, 0.15)",
            hovertemplate="%{y:.2f}%<extra></extra>",
        ),
        row=1, col=1
    )
    if benchmark_prices is not None:
        bench_cum = cumulative_returns(benchmark_prices) * 100
        fig.add_trace(
            go.Scatter(
                x=bench_cum.index,
                y=bench_cum,
                mode="lines",
                name="Benchmark",
                line={"color": colors["text_muted"], "width": 1.5, "dash": "dash"},
                hovertemplate="Bench: %{y:.2f}%<extra></extra>",
            ),
            row=1, col=1
        )
    
    roll_vol = rolling_volatility(prices, window=21) * 100
    avg_vol = float(roll_vol.mean())
    fig.add_trace(
        go.Scatter(
            x=roll_vol.index,
            y=roll_vol,
            mode="lines",
            name="Volatility",
            line={"color": colors["secondary"], "width": 1.5},
            fill="tozeroy",
            fillcolor=f"rgba({int(colors['secondary'][1:3], 16)}, {int(colors['secondary'][3:5], 16)}, {int(colors['secondary'][5:7], 16)}, 0.2)",
            showlegend=False,
            hovertemplate="%{y:.1f}%<extra></extra>",
        ),
        row=1, col=2
    )
    fig.add_shape(type="line", y0=avg_vol, y1=avg_vol, x0=0, x1=1, xref="x2 domain", yref="y2",
                  line={"dash": "dot", "color": colors["text_muted"], "width": 1})
    
    roll_sh = rolling_sharpe(prices, window=63)
    pos_sharpe = roll_sh.copy()
    pos_sharpe[pos_sharpe < 0] = np.nan
    neg_sharpe = roll_sh.copy()
    neg_sharpe[neg_sharpe >= 0] = np.nan
    
    fig.add_trace(
        go.Scatter(x=pos_sharpe.index, y=pos_sharpe, mode="lines", line={"color": colors["positive"], "width": 1.5},
                   fill="tozeroy", fillcolor=f"rgba({int(colors['positive'][1:3], 16)}, {int(colors['positive'][3:5], 16)}, {int(colors['positive'][5:7], 16)}, 0.3)",
                   showlegend=False, hovertemplate="%{y:.2f}<extra></extra>"),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=neg_sharpe.index, y=neg_sharpe, mode="lines", line={"color": colors["negative"], "width": 1.5},
                   fill="tozeroy", fillcolor=f"rgba({int(colors['negative'][1:3], 16)}, {int(colors['negative'][3:5], 16)}, {int(colors['negative'][5:7], 16)}, 0.3)",
                   showlegend=False, hovertemplate="%{y:.2f}<extra></extra>"),
        row=2, col=1
    )
    fig.add_shape(type="line", y0=0, y1=0, x0=0, x1=1, xref="x3 domain", yref="y3",
                  line={"color": colors["grid"], "width": 1})
    fig.add_shape(type="line", y0=1, y1=1, x0=0, x1=1, xref="x3 domain", yref="y3",
                  line={"dash": "dot", "color": colors["text_muted"], "width": 1})
    
    rets = daily_returns(prices) * 100
    fig.add_trace(
        go.Histogram(
            x=rets,
            nbinsx=80,
            name="Returns",
            marker_color=colors["primary"],
            opacity=0.7,
            showlegend=False,
            hovertemplate="Return: %{x:.2f}%<br>Count: %{y}<extra></extra>",
        ),
        row=2, col=2
    )
    mean_ret = float(rets.mean())
    fig.add_shape(type="line", x0=mean_ret, x1=mean_ret, y0=0, y1=1, xref="x4", yref="y4 domain",
                  line={"dash": "dash", "color": colors["positive"], "width": 2})
    fig.add_shape(type="line", x0=0, x1=0, y0=0, y1=1, xref="x4", yref="y4 domain",
                  line={"color": colors["text_muted"], "width": 1})
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=500,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        font={"family": "Inter, sans-serif", "color": colors["text"], "size": 11},
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.08, "xanchor": "left", "x": 0, "bgcolor": "rgba(0,0,0,0)"},
        hovermode="x unified",
    )
    
    for i in range(1, 5):
        fig.update_xaxes(showgrid=True, gridcolor=colors["grid"], zeroline=False, row=(i-1)//2+1, col=(i-1)%2+1)
        fig.update_yaxes(showgrid=True, gridcolor=colors["grid"], zeroline=False, row=(i-1)//2+1, col=(i-1)%2+1)
    
    fig.update_annotations(font_size=12, font_color=colors["text_muted"])
    
    return fig


def _create_heatmap(prices: pd.Series, theme_config: dict) -> go.Figure:
    colors = theme_config["colors"]
    
    monthly_df = monthly_returns(prices)
    z_values = monthly_df.values * 100
    x_labels = monthly_df.columns.tolist()
    y_labels = [str(y) for y in monthly_df.index.tolist()]
    
    text_matrix = [[f"{val:.1f}" if not np.isnan(val) else "" for val in row] for row in z_values]
    
    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            z=z_values,
            x=x_labels,
            y=y_labels,
            text=text_matrix,
            texttemplate="%{text}%",
            textfont={"size": 11, "color": "#ffffff"},
            colorscale=[
                [0.0, "#dc2626"],
                [0.25, "#991b1b"],
                [0.45, "#1f2937"],
                [0.55, "#1f2937"],
                [0.75, "#166534"],
                [1.0, "#22c55e"],
            ],
            zmid=0,
            zmin=-20,
            zmax=20,
            colorbar={
                "title": {"text": "Return", "font": {"color": colors["text"], "size": 11}},
                "tickfont": {"color": colors["text_muted"], "size": 10},
                "ticksuffix": "%",
                "thickness": 15,
                "len": 0.9,
            },
            hovertemplate="%{y} %{x}: %{z:.2f}%<extra></extra>",
            xgap=2,
            ygap=2,
        )
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin={"l": 0, "r": 60, "t": 0, "b": 0},
        font={"family": "Inter, sans-serif", "color": colors["text"]},
        xaxis={"side": "top", "tickfont": {"size": 11}},
        yaxis={"autorange": "reversed", "tickfont": {"size": 11}},
    )
    
    return fig


def generate_report(
    ticker: str,
    period: str = "5y",
    benchmark: Optional[str] = None,
    theme: str = DEFAULT_THEME,
    save: Optional[str] = None,
) -> str:
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    
    df = fetch(ticker, period=period)
    prices = df["Close"]
    info = get_info(ticker)
    
    benchmark_prices = None
    if benchmark:
        benchmark_df = fetch(benchmark, period=period)
        aligned_idx = prices.index.intersection(benchmark_df.index)
        prices = prices.loc[aligned_idx]
        benchmark_prices = benchmark_df["Close"].loc[aligned_idx]
        df = df.loc[aligned_idx]
    
    metrics = compute_metrics(prices, benchmark_prices)
    formatted = format_metrics(metrics)
    
    main_chart = _create_main_chart(df, ticker, theme_config)
    analytics_chart = _create_analytics_charts(prices, benchmark_prices, theme_config)
    heatmap_chart = _create_heatmap(prices, theme_config)
    
    main_chart_html = main_chart.to_html(full_html=False, include_plotlyjs=False, config={
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
        "displaylogo": False,
        "scrollZoom": True,
    })
    analytics_chart_html = analytics_chart.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})
    heatmap_chart_html = heatmap_chart.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})
    
    current_price = float(prices.iloc[-1])
    prev_price = float(prices.iloc[-2]) if len(prices) > 1 else current_price
    day_change = (current_price - prev_price) / prev_price * 100
    day_change_abs = current_price - prev_price
    
    start_date = prices.index[0].strftime("%b %d, %Y")
    end_date = prices.index[-1].strftime("%b %d, %Y")
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ticker} | Flux-RX Analytics</title>
    <script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #09090b;
            --bg-secondary: #18181b;
            --bg-tertiary: #27272a;
            --bg-elevated: #3f3f46;
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --border: #27272a;
            --border-hover: #3f3f46;
            --accent: #3b82f6;
            --accent-hover: #60a5fa;
            --positive: #22c55e;
            --positive-bg: rgba(34, 197, 94, 0.1);
            --negative: #ef4444;
            --negative-bg: rgba(239, 68, 68, 0.1);
            --warning: #f59e0b;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        html {{ scroll-behavior: smooth; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        .app {{
            display: flex;
            min-height: 100vh;
        }}
        
        .sidebar {{
            width: 280px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            padding: 24px 0;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            z-index: 100;
        }}
        
        .sidebar-header {{
            padding: 0 24px 24px;
            border-bottom: 1px solid var(--border);
        }}
        
        .logo {{
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.5px;
        }}
        
        .logo span {{
            color: var(--accent);
        }}
        
        .sidebar-nav {{
            padding: 16px 12px;
        }}
        
        .nav-section {{
            margin-bottom: 24px;
        }}
        
        .nav-section-title {{
            font-size: 10px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 0 12px;
            margin-bottom: 8px;
        }}
        
        .nav-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            border-radius: 8px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.15s ease;
            cursor: pointer;
        }}
        
        .nav-item:hover {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }}
        
        .nav-item.active {{
            background: var(--accent);
            color: white;
        }}
        
        .nav-icon {{
            width: 18px;
            height: 18px;
            opacity: 0.7;
        }}
        
        .main {{
            flex: 1;
            margin-left: 280px;
            min-height: 100vh;
        }}
        
        .topbar {{
            height: 64px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 32px;
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(8px);
            background: rgba(24, 24, 27, 0.9);
        }}
        
        .ticker-header {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        
        .ticker-symbol {{
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .ticker-name {{
            font-size: 14px;
            color: var(--text-secondary);
            max-width: 300px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .ticker-badge {{
            padding: 4px 10px;
            background: var(--bg-tertiary);
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
        }}
        
        .price-display {{
            text-align: right;
        }}
        
        .current-price {{
            font-size: 28px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-primary);
        }}
        
        .price-change {{
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 8px;
            margin-top: 2px;
        }}
        
        .change-value {{
            font-size: 14px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .change-badge {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .positive {{ color: var(--positive); }}
        .negative {{ color: var(--negative); }}
        .positive-bg {{ background: var(--positive-bg); }}
        .negative-bg {{ background: var(--negative-bg); }}
        
        .content {{
            padding: 24px 32px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        
        .metric-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.2s ease;
        }}
        
        .metric-card:hover {{
            border-color: var(--border-hover);
            transform: translateY(-2px);
        }}
        
        .metric-label {{
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .metric-value {{
            font-size: 24px;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .metric-subtext {{
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        
        .section {{
            margin-bottom: 24px;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }}
        
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .chart-container {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            overflow: hidden;
        }}
        
        .chart-container .js-plotly-plot {{
            width: 100% !important;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}
        
        .info-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }}
        
        .info-card-title {{
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}
        
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
        }}
        
        .info-row:last-child {{
            border-bottom: none;
        }}
        
        .info-label {{
            font-size: 13px;
            color: var(--text-secondary);
        }}
        
        .info-value {{
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .footer {{
            padding: 32px;
            text-align: center;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            font-size: 12px;
        }}
        
        .footer a {{
            color: var(--accent);
            text-decoration: none;
        }}
        
        .js-plotly-plot .plotly .modebar {{
            top: 8px !important;
            right: 8px !important;
        }}
        
        .js-plotly-plot .plotly .modebar-btn {{
            fill: var(--text-muted) !important;
        }}
        
        .js-plotly-plot .plotly .modebar-btn:hover {{
            fill: var(--text-primary) !important;
        }}
        
        @media (max-width: 1200px) {{
            .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        
        @media (max-width: 900px) {{
            .sidebar {{ display: none; }}
            .main {{ margin-left: 0; }}
            .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .info-grid {{ grid-template-columns: 1fr; }}
        }}
        
        @media (max-width: 600px) {{
            .metrics-grid {{ grid-template-columns: 1fr; }}
            .topbar {{ flex-direction: column; height: auto; padding: 16px; gap: 12px; }}
            .price-display {{ text-align: left; }}
        }}
    </style>
</head>
<body>
    <div class="app">
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="logo">Flux<span>-RX</span></div>
            </div>
            <nav class="sidebar-nav">
                <div class="nav-section">
                    <div class="nav-section-title">Analysis</div>
                    <a href="#overview" class="nav-item active">
                        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        Overview
                    </a>
                    <a href="#chart" class="nav-item">
                        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"></path></svg>
                        Price Chart
                    </a>
                    <a href="#analytics" class="nav-item">
                        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        Analytics
                    </a>
                    <a href="#returns" class="nav-item">
                        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                        Monthly Returns
                    </a>
                </div>
                <div class="nav-section">
                    <div class="nav-section-title">Details</div>
                    <a href="#company" class="nav-item">
                        <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>
                        Company Info
                    </a>
                </div>
            </nav>
        </aside>
        
        <main class="main">
            <header class="topbar">
                <div class="ticker-header">
                    <span class="ticker-symbol">{ticker}</span>
                    <span class="ticker-name">{info.get('name', ticker)}</span>
                    <span class="ticker-badge">{info.get('sector', 'Equity')}</span>
                </div>
                <div class="price-display">
                    <div class="current-price">${current_price:,.2f}</div>
                    <div class="price-change">
                        <span class="change-value {'positive' if day_change >= 0 else 'negative'}">
                            {"+" if day_change >= 0 else ""}{day_change_abs:,.2f}
                        </span>
                        <span class="change-badge {'positive positive-bg' if day_change >= 0 else 'negative negative-bg'}">
                            {"+" if day_change >= 0 else ""}{day_change:.2f}%
                        </span>
                    </div>
                </div>
            </header>
            
            <div class="content">
                <section id="overview" class="section">
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-label">CAGR</div>
                            <div class="metric-value {'positive' if metrics['cagr'] >= 0 else 'negative'}">{formatted['cagr']}</div>
                            <div class="metric-subtext">Compound Annual Growth</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Volatility</div>
                            <div class="metric-value">{formatted['volatility']}</div>
                            <div class="metric-subtext">Annualized Std Dev</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Max Drawdown</div>
                            <div class="metric-value negative">{formatted['max_drawdown']}</div>
                            <div class="metric-subtext">Peak to Trough</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Sharpe Ratio</div>
                            <div class="metric-value {'positive' if metrics['sharpe_ratio'] >= 1 else ''}">{formatted['sharpe_ratio']}</div>
                            <div class="metric-subtext">Risk-Adjusted Return</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Sortino Ratio</div>
                            <div class="metric-value">{formatted['sortino_ratio']}</div>
                            <div class="metric-subtext">Downside Risk-Adjusted</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Calmar Ratio</div>
                            <div class="metric-value">{formatted['calmar_ratio']}</div>
                            <div class="metric-subtext">Return / Max DD</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Total Return</div>
                            <div class="metric-value {'positive' if metrics['total_return'] >= 0 else 'negative'}">{formatted['total_return']}</div>
                            <div class="metric-subtext">{start_date} - {end_date}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">{'Beta' if benchmark else 'Period'}</div>
                            <div class="metric-value">{formatted.get('beta', period.upper())}</div>
                            <div class="metric-subtext">{'vs ' + benchmark if benchmark else 'Analysis Window'}</div>
                        </div>
                    </div>
                </section>
                
                <section id="chart" class="section">
                    <div class="section-header">
                        <h2 class="section-title">Price Action & Volume</h2>
                    </div>
                    <div class="chart-container">
                        {main_chart_html}
                    </div>
                </section>
                
                <section id="analytics" class="section">
                    <div class="section-header">
                        <h2 class="section-title">Performance Analytics</h2>
                    </div>
                    <div class="chart-container">
                        {analytics_chart_html}
                    </div>
                </section>
                
                <section id="returns" class="section">
                    <div class="section-header">
                        <h2 class="section-title">Monthly Returns Heatmap</h2>
                    </div>
                    <div class="chart-container">
                        {heatmap_chart_html}
                    </div>
                </section>
                
                <section id="company" class="section">
                    <div class="info-grid">
                        <div class="info-card">
                            <div class="info-card-title">Company Information</div>
                            <div class="info-row">
                                <span class="info-label">Name</span>
                                <span class="info-value">{info.get('name', 'N/A')}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Sector</span>
                                <span class="info-value">{info.get('sector', 'N/A')}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Industry</span>
                                <span class="info-value">{info.get('industry', 'N/A')}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Country</span>
                                <span class="info-value">{info.get('country', 'N/A')}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Exchange</span>
                                <span class="info-value">{info.get('exchange', 'N/A')}</span>
                            </div>
                        </div>
                        <div class="info-card">
                            <div class="info-card-title">Market Data</div>
                            <div class="info-row">
                                <span class="info-label">Market Cap</span>
                                <span class="info-value">{info.get('market_cap_fmt', 'N/A')}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">P/E Ratio</span>
                                <span class="info-value">{f"{info['pe_ratio']:.2f}" if info.get('pe_ratio') else 'N/A'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Forward P/E</span>
                                <span class="info-value">{f"{info['forward_pe']:.2f}" if info.get('forward_pe') else 'N/A'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Beta</span>
                                <span class="info-value">{f"{info['beta']:.2f}" if info.get('beta') else 'N/A'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">52W Range</span>
                                <span class="info-value">${info.get('fifty_two_week_low', 0):,.2f} - ${info.get('fifty_two_week_high', 0):,.2f}</span>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
            
            <footer class="footer">
                <p>Generated by <a href="#">Flux-RX</a> on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
                <p style="margin-top: 4px; opacity: 0.7">A Finance Python Package</p>
            </footer>
        </main>
    </div>
    
    <script>
        document.querySelectorAll('.nav-item').forEach(item => {{
            item.addEventListener('click', function(e) {{
                document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
                this.classList.add('active');
            }});
        }});
        
        window.addEventListener('scroll', function() {{
            const sections = document.querySelectorAll('section[id]');
            let current = '';
            sections.forEach(section => {{
                const sectionTop = section.offsetTop;
                if (window.scrollY >= sectionTop - 100) {{
                    current = section.getAttribute('id');
                }}
            }});
            document.querySelectorAll('.nav-item').forEach(item => {{
                item.classList.remove('active');
                if (item.getAttribute('href') === '#' + current) {{
                    item.classList.add('active');
                }}
            }});
        }});
    </script>
</body>
</html>'''
    
    if save:
        with open(save, "w", encoding="utf-8") as f:
            f.write(html)
    
    return html


def generate_comparison_report(
    tickers: list[str],
    period: str = "5y",
    theme: str = DEFAULT_THEME,
    save: Optional[str] = None,
) -> str:
    from flux_rx.data import fetch_multiple, align_dataframes
    
    theme_config = get_theme(theme)
    colors = theme_config["colors"]
    palette = theme_config["palette"]
    
    data = fetch_multiple(tickers, period=period)
    prices_df = align_dataframes(data)
    
    all_metrics = {}
    for ticker in tickers:
        all_metrics[ticker] = compute_metrics(prices_df[ticker])
    
    perf_fig = go.Figure()
    for i, ticker in enumerate(tickers):
        normalized = (prices_df[ticker] / prices_df[ticker].iloc[0] - 1) * 100
        perf_fig.add_trace(
            go.Scatter(
                x=normalized.index,
                y=normalized,
                mode="lines",
                name=ticker,
                line={"color": palette[i % len(palette)], "width": 2},
                hovertemplate=f"{ticker}: %{{y:.2f}}%<extra></extra>",
            )
        )
    
    perf_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        font={"family": "Inter, sans-serif", "color": colors["text"]},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0, "bgcolor": "rgba(0,0,0,0)"},
        hovermode="x unified",
        xaxis={"showgrid": True, "gridcolor": colors["grid"], "zeroline": False},
        yaxis={"showgrid": True, "gridcolor": colors["grid"], "zeroline": True, "zerolinecolor": colors["grid"], "side": "right", "ticksuffix": "%"},
    )
    perf_fig.add_hline(y=0, line_color=colors["grid"], line_width=1)
    
    vols = [all_metrics[t]["volatility"] * 100 for t in tickers]
    cagrs = [all_metrics[t]["cagr"] * 100 for t in tickers]
    sharpes = [all_metrics[t]["sharpe_ratio"] for t in tickers]
    
    risk_fig = go.Figure()
    for i, ticker in enumerate(tickers):
        risk_fig.add_trace(
            go.Scatter(
                x=[vols[i]],
                y=[cagrs[i]],
                mode="markers+text",
                name=ticker,
                marker={"color": palette[i % len(palette)], "size": max(20, min(50, sharpes[i] * 20)) if sharpes[i] > 0 else 20, "line": {"color": "#fff", "width": 2}},
                text=[ticker],
                textposition="top center",
                textfont={"color": colors["text"], "size": 12, "family": "Inter"},
                hovertemplate=f"<b>{ticker}</b><br>CAGR: {cagrs[i]:.2f}%<br>Vol: {vols[i]:.2f}%<br>Sharpe: {sharpes[i]:.2f}<extra></extra>",
            )
        )
    
    risk_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        font={"family": "Inter, sans-serif", "color": colors["text"]},
        showlegend=False,
        xaxis={"title": "Volatility (%)", "showgrid": True, "gridcolor": colors["grid"], "zeroline": False},
        yaxis={"title": "CAGR (%)", "showgrid": True, "gridcolor": colors["grid"], "zeroline": True, "zerolinecolor": colors["grid"]},
    )
    
    corr = prices_df.pct_change().dropna().corr()
    corr_fig = go.Figure()
    corr_fig.add_trace(
        go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            text=[[f"{v:.2f}" for v in row] for row in corr.values],
            texttemplate="%{text}",
            textfont={"size": 14, "color": "#fff"},
            colorscale=[[0, "#ef4444"], [0.5, "#1f2937"], [1, "#22c55e"]],
            zmin=-1,
            zmax=1,
            colorbar={"title": {"text": "Corr", "font": {"color": colors["text"]}}, "tickfont": {"color": colors["text_muted"]}},
            xgap=3,
            ygap=3,
        )
    )
    corr_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=350,
        margin={"l": 0, "r": 60, "t": 0, "b": 0},
        font={"family": "Inter, sans-serif", "color": colors["text"]},
        xaxis={"side": "top"},
    )
    
    perf_html = perf_fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": True, "displaylogo": False})
    risk_html = risk_fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})
    corr_html = corr_fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})
    
    metrics_rows = ""
    for i, ticker in enumerate(tickers):
        m = all_metrics[ticker]
        fm = format_metrics(m)
        metrics_rows += f'''
        <tr>
            <td><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{palette[i % len(palette)]};margin-right:8px"></span>{ticker}</td>
            <td class="{'positive' if m['cagr'] >= 0 else 'negative'}">{fm['cagr']}</td>
            <td>{fm['volatility']}</td>
            <td class="negative">{fm['max_drawdown']}</td>
            <td class="{'positive' if m['sharpe_ratio'] >= 1 else ''}">{fm['sharpe_ratio']}</td>
            <td>{fm['sortino_ratio']}</td>
            <td>{fm['calmar_ratio']}</td>
        </tr>'''
    
    start_date = prices_df.index[0].strftime("%b %d, %Y")
    end_date = prices_df.index[-1].strftime("%b %d, %Y")
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparison Analysis | Flux-RX</title>
    <script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #09090b;
            --bg-secondary: #18181b;
            --bg-tertiary: #27272a;
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --text-muted: #71717a;
            --border: #27272a;
            --accent: #3b82f6;
            --positive: #22c55e;
            --negative: #ef4444;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 32px; }}
        .header {{ margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid var(--border); }}
        .title {{ font-size: 32px; font-weight: 700; margin-bottom: 8px; }}
        .subtitle {{ color: var(--text-secondary); }}
        .tickers {{ display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }}
        .ticker-badge {{ padding: 8px 16px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; font-weight: 600; font-family: 'JetBrains Mono', monospace; }}
        .section {{ margin-bottom: 32px; }}
        .section-title {{ font-size: 18px; font-weight: 600; margin-bottom: 16px; }}
        .card {{ background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 24px; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 16px; text-align: right; border-bottom: 1px solid var(--border); }}
        th {{ font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; background: var(--bg-tertiary); }}
        td {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; }}
        td:first-child, th:first-child {{ text-align: left; }}
        .positive {{ color: var(--positive); }}
        .negative {{ color: var(--negative); }}
        .footer {{ padding: 32px 0; text-align: center; color: var(--text-muted); font-size: 12px; border-top: 1px solid var(--border); margin-top: 32px; }}
        @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1 class="title">Comparison Analysis</h1>
            <p class="subtitle">{start_date} - {end_date}</p>
            <div class="tickers">
                {"".join(f'<span class="ticker-badge" style="border-left: 3px solid {palette[i % len(palette)]}">{t}</span>' for i, t in enumerate(tickers))}
            </div>
        </header>
        
        <section class="section">
            <h2 class="section-title">Performance Metrics</h2>
            <div class="card" style="padding: 0; overflow: hidden;">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>CAGR</th>
                            <th>Volatility</th>
                            <th>Max DD</th>
                            <th>Sharpe</th>
                            <th>Sortino</th>
                            <th>Calmar</th>
                        </tr>
                    </thead>
                    <tbody>{metrics_rows}</tbody>
                </table>
            </div>
        </section>
        
        <section class="section">
            <h2 class="section-title">Normalized Performance</h2>
            <div class="card">{perf_html}</div>
        </section>
        
        <section class="section">
            <div class="grid">
                <div>
                    <h2 class="section-title">Risk-Return</h2>
                    <div class="card">{risk_html}</div>
                </div>
                <div>
                    <h2 class="section-title">Correlation Matrix</h2>
                    <div class="card">{corr_html}</div>
                </div>
            </div>
        </section>
        
        <footer class="footer">
            Generated by Flux-RX on {datetime.now().strftime('%B %d, %Y at %H:%M')}
        </footer>
    </div>
</body>
</html>'''
    
    if save:
        with open(save, "w", encoding="utf-8") as f:
            f.write(html)
    
    return html
