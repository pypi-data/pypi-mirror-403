# Flux-RX: A Finance Python Package
from flux_rx.api import quick, chart, compare, app, metrics, info
from flux_rx.data import fetch, get_info, clear_cache
from flux_rx.analytics import (
    daily_returns,
    cumulative_returns,
    cagr,
    volatility,
    max_drawdown,
    sharpe_ratio,
    rolling_volatility,
    rolling_sharpe,
    monthly_returns,
    compute_metrics,
)
from flux_rx.charts import (
    price_chart,
    volume_chart,
    drawdown_chart,
    rolling_vol_chart,
    rolling_sharpe_chart,
    monthly_heatmap,
    risk_return_scatter,
    correlation_matrix,
)
from flux_rx.report import generate_report
from flux_rx.themes import get_theme

__version__ = "0.1.0"
__all__ = [
    "quick",
    "chart",
    "compare",
    "app",
    "fetch",
    "get_info",
    "clear_cache",
    "daily_returns",
    "cumulative_returns",
    "cagr",
    "volatility",
    "max_drawdown",
    "sharpe_ratio",
    "rolling_volatility",
    "rolling_sharpe",
    "monthly_returns",
    "compute_metrics",
    "price_chart",
    "volume_chart",
    "drawdown_chart",
    "rolling_vol_chart",
    "rolling_sharpe_chart",
    "monthly_heatmap",
    "risk_return_scatter",
    "correlation_matrix",
    "generate_report",
    "get_theme",
]
