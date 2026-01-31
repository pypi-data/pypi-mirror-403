# Flux-RX Dashboard Module: Interactive Dash application
from __future__ import annotations

from typing import Optional

import pandas as pd
from dash import Dash, html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc

from flux_rx.data import fetch, get_info, fetch_multiple, align_dataframes
from flux_rx.analytics import compute_metrics, format_metrics
from flux_rx.charts import (
    price_chart,
    drawdown_chart,
    rolling_vol_chart,
    rolling_sharpe_chart,
    monthly_heatmap,
    performance_chart,
    risk_return_scatter,
    correlation_matrix,
    cumulative_returns_chart,
)
from flux_rx.themes import get_theme, DEFAULT_THEME

GLASS_THEME_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-surface: #21262d;
    --text-primary: #c9d1d9;
    --text-muted: #8b949e;
    --border-color: #30363d;
    --accent-blue: #58a6ff;
    --accent-green: #3fb950;
    --accent-red: #f85149;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    margin: 0;
    padding: 0;
    min-height: 100vh;
}

.dashboard-container {
    max-width: 1600px;
    margin: 0 auto;
    padding: 24px;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);
}

.logo {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, #58a6ff, #7ee787);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.logo-subtitle {
    font-size: 12px;
    color: var(--text-muted);
    font-weight: 400;
}

.controls-row {
    display: flex;
    gap: 16px;
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.control-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.control-label {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.ticker-input {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 10px 14px;
    color: var(--text-primary);
    font-size: 14px;
    font-weight: 500;
    width: 200px;
    transition: border-color 0.2s;
}

.ticker-input:focus {
    outline: none;
    border-color: var(--accent-blue);
}

.Select-control {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    min-height: 40px !important;
}

.Select-value-label, .Select-placeholder {
    color: var(--text-primary) !important;
}

.Select-menu-outer {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
}

.analyze-btn {
    background: var(--accent-blue);
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    color: #fff;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
    align-self: flex-end;
}

.analyze-btn:hover {
    opacity: 0.9;
}

.info-bar {
    display: flex;
    gap: 24px;
    padding: 16px 20px;
    background: var(--bg-secondary);
    border-radius: 12px;
    border: 1px solid var(--border-color);
    margin-bottom: 24px;
    flex-wrap: wrap;
}

.info-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.info-label {
    font-size: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.info-value {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}

.kpi-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.kpi-label {
    font-size: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 22px;
    font-weight: 600;
}

.kpi-positive { color: var(--accent-green); }
.kpi-negative { color: var(--accent-red); }
.kpi-neutral { color: var(--text-primary); }

.chart-grid {
    display: grid;
    gap: 16px;
}

.chart-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}

.chart-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 16px;
    overflow: hidden;
}

.chart-full {
    grid-column: 1 / -1;
}

.tabs-container {
    margin-bottom: 24px;
}

.tab-list {
    display: flex;
    gap: 4px;
    padding: 4px;
    background: var(--bg-secondary);
    border-radius: 10px;
    width: fit-content;
}

.tab {
    padding: 8px 20px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.2s;
    border: none;
    background: none;
}

.tab:hover {
    color: var(--text-primary);
}

.tab.active {
    background: var(--bg-surface);
    color: var(--text-primary);
}

.compare-input {
    width: 400px;
}

.footer {
    margin-top: 48px;
    padding-top: 24px;
    border-top: 1px solid var(--border-color);
    text-align: center;
    color: var(--text-muted);
    font-size: 12px;
}

@media (max-width: 768px) {
    .chart-row {
        grid-template-columns: 1fr;
    }
    
    .controls-row {
        flex-direction: column;
    }
    
    .ticker-input, .compare-input {
        width: 100%;
    }
}
"""


def create_app(
    default_tickers: Optional[list[str]] = None,
    default_theme: str = DEFAULT_THEME,
) -> Dash:
    app = Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True,
        title="Flux-RX",
    )
    
    if default_tickers is None:
        default_tickers = ["SPY"]
    
    # Inject custom CSS via index string
    app.index_string = '''<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>''' + GLASS_THEME_CSS + '''</style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>'''
    
    app.layout = html.Div([
        
        html.Div([
            html.Div([
                html.Div([
                    html.Span("Flux-RX", className="logo"),
                    html.Div("A Finance Python Package", className="logo-subtitle"),
                ]),
            ], className="header"),
            
            html.Div([
                html.Button("Single", id="tab-single", n_clicks=0, className="tab active"),
                html.Button("Compare", id="tab-compare", n_clicks=0, className="tab"),
            ], className="tab-list"),
            
            html.Div(id="tab-content"),
            
            html.Div([
                html.P("Powered by Flux-RX"),
            ], className="footer"),
            
        ], className="dashboard-container"),
        
        dcc.Store(id="active-tab", data="single"),
        dcc.Store(id="current-data", data={}),
    ])
    
    @app.callback(
        [Output("tab-single", "className"),
         Output("tab-compare", "className"),
         Output("active-tab", "data")],
        [Input("tab-single", "n_clicks"),
         Input("tab-compare", "n_clicks")],
        [State("active-tab", "data")],
    )
    def switch_tab(single_clicks, compare_clicks, current_tab):
        from dash import ctx
        if not ctx.triggered_id:
            return "tab active", "tab", "single"
        
        if ctx.triggered_id == "tab-single":
            return "tab active", "tab", "single"
        else:
            return "tab", "tab active", "compare"
    
    @app.callback(
        Output("tab-content", "children"),
        [Input("active-tab", "data")],
    )
    def render_tab_content(active_tab):
        if active_tab == "single":
            return render_single_tab()
        else:
            return render_compare_tab()
    
    @app.callback(
        [Output("single-info-bar", "children"),
         Output("single-kpi-grid", "children"),
         Output("single-charts", "children")],
        [Input("analyze-btn", "n_clicks")],
        [State("ticker-input", "value"),
         State("period-selector", "value"),
         State("benchmark-input", "value")],
        prevent_initial_call=False,
    )
    def update_single_analysis(n_clicks, ticker, period, benchmark):
        theme = DEFAULT_THEME
        if not ticker:
            ticker = "SPY"
        
        ticker = ticker.upper().strip()
        
        try:
            df = fetch(ticker, period=period)
            info = get_info(ticker)
            prices = df["Close"]
            
            benchmark_prices = None
            if benchmark:
                bench_df = fetch(benchmark.upper().strip(), period=period)
                aligned_idx = prices.index.intersection(bench_df.index)
                prices = prices.loc[aligned_idx]
                benchmark_prices = bench_df["Close"].loc[aligned_idx]
                df = df.loc[aligned_idx]
            
            metrics = compute_metrics(prices, benchmark_prices)
            formatted = format_metrics(metrics)
            
            info_bar = create_info_bar(info, prices)
            kpi_grid = create_kpi_grid(metrics, formatted)
            charts = create_single_charts(df, prices, ticker, benchmark, benchmark_prices, theme)
            
            return info_bar, kpi_grid, charts
            
        except Exception as e:
            error_msg = html.Div([
                html.P(f"Error loading data: {str(e)}", style={"color": "#f85149"}),
            ])
            return error_msg, [], []
    
    @app.callback(
        Output("compare-charts", "children"),
        [Input("compare-btn", "n_clicks")],
        [State("compare-input", "value"),
         State("compare-period-selector", "value")],
        prevent_initial_call=True,
    )
    def update_comparison(n_clicks, tickers_str, period):
        theme = DEFAULT_THEME
        if not tickers_str:
            return html.Div("Enter tickers separated by commas", style={"color": "#8b949e"})
        
        tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
        
        if len(tickers) < 2:
            return html.Div("Enter at least 2 tickers", style={"color": "#8b949e"})
        
        try:
            data = fetch_multiple(tickers, period=period)
            prices_df = align_dataframes(data)
            
            all_metrics = {}
            for ticker in tickers:
                all_metrics[ticker] = compute_metrics(prices_df[ticker])
            
            prices_dict = {t: prices_df[t] for t in tickers}
            perf_fig = performance_chart(prices_dict, theme=theme, height=400)
            risk_fig = risk_return_scatter(all_metrics, theme=theme, height=400)
            corr_fig = correlation_matrix(prices_df, theme=theme, height=400)
            
            metrics_table = create_comparison_table(tickers, all_metrics)
            
            return html.Div([
                html.Div([metrics_table], style={"marginBottom": "24px"}),
                html.Div([
                    dcc.Graph(figure=perf_fig, config={"displayModeBar": False}),
                ], className="chart-container chart-full"),
                html.Div([
                    html.Div([
                        dcc.Graph(figure=risk_fig, config={"displayModeBar": False}),
                    ], className="chart-container"),
                    html.Div([
                        dcc.Graph(figure=corr_fig, config={"displayModeBar": False}),
                    ], className="chart-container"),
                ], className="chart-row"),
            ], className="chart-grid")
            
        except Exception as e:
            return html.Div([
                html.P(f"Error: {str(e)}", style={"color": "#f85149"}),
            ])
    
    return app


def render_single_tab():
    return html.Div([
        html.Div([
            html.Div([
                html.Label("Ticker", className="control-label"),
                dcc.Input(
                    id="ticker-input",
                    type="text",
                    value="AAPL",
                    placeholder="Enter ticker",
                    className="ticker-input",
                ),
            ], className="control-group"),
            
            html.Div([
                html.Label("Period", className="control-label"),
                dcc.Dropdown(
                    id="period-selector",
                    options=[
                        {"label": "1 Year", "value": "1y"},
                        {"label": "2 Years", "value": "2y"},
                        {"label": "5 Years", "value": "5y"},
                        {"label": "10 Years", "value": "10y"},
                        {"label": "Max", "value": "max"},
                    ],
                    value="5y",
                    clearable=False,
                    style={"width": "130px"},
                ),
            ], className="control-group"),
            
            html.Div([
                html.Label("Benchmark", className="control-label"),
                dcc.Input(
                    id="benchmark-input",
                    type="text",
                    value="",
                    placeholder="e.g., SPY",
                    className="ticker-input",
                    style={"width": "120px"},
                ),
            ], className="control-group"),
            
            html.Button("Analyze", id="analyze-btn", n_clicks=1, className="analyze-btn"),
        ], className="controls-row"),
        
        html.Div(id="single-info-bar", className="info-bar"),
        html.Div(id="single-kpi-grid", className="kpi-grid"),
        html.Div(id="single-charts", className="chart-grid"),
    ])


def render_compare_tab():
    return html.Div([
        html.Div([
            html.Div([
                html.Label("Tickers (comma separated)", className="control-label"),
                dcc.Input(
                    id="compare-input",
                    type="text",
                    value="QQQ, SPY, IWM",
                    placeholder="AAPL, MSFT, GOOGL",
                    className="ticker-input compare-input",
                ),
            ], className="control-group"),
            
            html.Div([
                html.Label("Period", className="control-label"),
                dcc.Dropdown(
                    id="compare-period-selector",
                    options=[
                        {"label": "1 Year", "value": "1y"},
                        {"label": "2 Years", "value": "2y"},
                        {"label": "5 Years", "value": "5y"},
                        {"label": "10 Years", "value": "10y"},
                    ],
                    value="5y",
                    clearable=False,
                    style={"width": "130px"},
                ),
            ], className="control-group"),
            
            html.Button("Compare", id="compare-btn", n_clicks=0, className="analyze-btn"),
        ], className="controls-row"),
        
        html.Div(id="compare-charts", className="chart-grid"),
    ])


def create_info_bar(info: dict, prices: pd.Series) -> list:
    items = [
        ("Company", info.get("name", "N/A")),
        ("Sector", info.get("sector", "N/A")),
        ("Industry", info.get("industry", "N/A")),
        ("Market Cap", info.get("market_cap_fmt", "N/A")),
        ("Exchange", info.get("exchange", "N/A")),
        ("Current Price", f"${prices.iloc[-1]:.2f}"),
    ]
    
    return [
        html.Div([
            html.Span(label, className="info-label"),
            html.Span(value, className="info-value"),
        ], className="info-item")
        for label, value in items
    ]


def create_kpi_grid(metrics: dict, formatted: dict) -> list:
    kpis = [
        ("CAGR", formatted.get("cagr", "N/A"), metrics.get("cagr", 0) >= 0),
        ("Volatility", formatted.get("volatility", "N/A"), None),
        ("Max Drawdown", formatted.get("max_drawdown", "N/A"), False),
        ("Sharpe Ratio", formatted.get("sharpe_ratio", "N/A"), metrics.get("sharpe_ratio", 0) >= 1),
        ("Sortino Ratio", formatted.get("sortino_ratio", "N/A"), metrics.get("sortino_ratio", 0) >= 1),
        ("Calmar Ratio", formatted.get("calmar_ratio", "N/A"), metrics.get("calmar_ratio", 0) >= 1),
    ]
    
    if "beta" in formatted:
        kpis.append(("Beta", formatted["beta"], None))
    if "alpha" in formatted:
        kpis.append(("Alpha", formatted["alpha"], metrics.get("alpha", 0) >= 0))
    
    cards = []
    for label, value, is_positive in kpis:
        if is_positive is None:
            value_class = "kpi-value kpi-neutral"
        elif is_positive:
            value_class = "kpi-value kpi-positive"
        else:
            value_class = "kpi-value kpi-negative"
        
        cards.append(
            html.Div([
                html.Div(label, className="kpi-label"),
                html.Div(value, className=value_class),
            ], className="kpi-card")
        )
    
    return cards


def create_single_charts(
    df: pd.DataFrame,
    prices: pd.Series,
    ticker: str,
    benchmark: str,
    benchmark_prices: Optional[pd.Series],
    theme: str,
) -> list:
    price_fig = price_chart(df, ticker=ticker, theme=theme, height=380, show_volume=True)
    cum_fig = cumulative_returns_chart(prices, benchmark_prices, ticker, benchmark or "", theme=theme, height=320)
    dd_fig = drawdown_chart(prices, ticker=ticker, theme=theme, height=280)
    vol_fig = rolling_vol_chart(prices, ticker=ticker, theme=theme, height=280)
    sharpe_fig = rolling_sharpe_chart(prices, ticker=ticker, theme=theme, height=280)
    heat_fig = monthly_heatmap(prices, ticker=ticker, theme=theme, height=320)
    
    return [
        html.Div([
            dcc.Graph(figure=price_fig, config={"displayModeBar": False}),
        ], className="chart-container chart-full"),
        
        html.Div([
            html.Div([
                dcc.Graph(figure=cum_fig, config={"displayModeBar": False}),
            ], className="chart-container"),
            html.Div([
                dcc.Graph(figure=dd_fig, config={"displayModeBar": False}),
            ], className="chart-container"),
        ], className="chart-row"),
        
        html.Div([
            html.Div([
                dcc.Graph(figure=vol_fig, config={"displayModeBar": False}),
            ], className="chart-container"),
            html.Div([
                dcc.Graph(figure=sharpe_fig, config={"displayModeBar": False}),
            ], className="chart-container"),
        ], className="chart-row"),
        
        html.Div([
            dcc.Graph(figure=heat_fig, config={"displayModeBar": False}),
        ], className="chart-container chart-full"),
    ]


def create_comparison_table(tickers: list, all_metrics: dict) -> html.Table:
    header = html.Thead(html.Tr([
        html.Th("Ticker", style={"textAlign": "left"}),
        html.Th("CAGR"),
        html.Th("Volatility"),
        html.Th("Max DD"),
        html.Th("Sharpe"),
        html.Th("Sortino"),
    ], style={"background": "#21262d", "color": "#8b949e", "fontSize": "11px", "textTransform": "uppercase"}))
    
    rows = []
    for ticker in tickers:
        m = all_metrics[ticker]
        fm = format_metrics(m)
        
        cagr_style = {"color": "#3fb950"} if m["cagr"] >= 0 else {"color": "#f85149"}
        
        rows.append(html.Tr([
            html.Td(ticker, style={"fontWeight": "600", "color": "#58a6ff"}),
            html.Td(fm["cagr"], style=cagr_style),
            html.Td(fm["volatility"]),
            html.Td(fm["max_drawdown"], style={"color": "#f85149"}),
            html.Td(fm["sharpe_ratio"]),
            html.Td(fm["sortino_ratio"]),
        ], style={"borderBottom": "1px solid #30363d"}))
    
    body = html.Tbody(rows)
    
    return html.Table([header, body], style={
        "width": "100%",
        "borderCollapse": "collapse",
        "background": "#161b22",
        "borderRadius": "12px",
        "overflow": "hidden",
        "fontSize": "14px",
    })
