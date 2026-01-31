# Flux-RX Analytics Module: Financial metrics and calculations
from __future__ import annotations

from typing import Optional, Union

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.04


def daily_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().dropna()


def cumulative_returns(prices: pd.Series) -> pd.Series:
    returns = daily_returns(prices)
    return (1 + returns).cumprod() - 1


def total_return(prices: pd.Series) -> float:
    return (prices.iloc[-1] / prices.iloc[0]) - 1


def cagr(prices: pd.Series) -> float:
    total_days = (prices.index[-1] - prices.index[0]).days
    if total_days <= 0:
        return 0.0
    years = total_days / 365.25
    total_ret = total_return(prices)
    return (1 + total_ret) ** (1 / years) - 1


def volatility(prices: pd.Series, annualize: bool = True) -> float:
    returns = daily_returns(prices)
    vol = returns.std()
    if annualize:
        vol *= np.sqrt(TRADING_DAYS_PER_YEAR)
    return vol


def max_drawdown(prices: pd.Series) -> float:
    cummax = prices.cummax()
    drawdown = (prices - cummax) / cummax
    return drawdown.min()


def drawdown_series(prices: pd.Series) -> pd.Series:
    cummax = prices.cummax()
    return (prices - cummax) / cummax


def sharpe_ratio(
    prices: pd.Series,
    risk_free_rate: float = RISK_FREE_RATE,
) -> float:
    returns = daily_returns(prices)
    excess_returns = returns - risk_free_rate / TRADING_DAYS_PER_YEAR
    if returns.std() == 0:
        return 0.0
    return (excess_returns.mean() / returns.std()) * np.sqrt(TRADING_DAYS_PER_YEAR)


def sortino_ratio(
    prices: pd.Series,
    risk_free_rate: float = RISK_FREE_RATE,
) -> float:
    returns = daily_returns(prices)
    excess_returns = returns - risk_free_rate / TRADING_DAYS_PER_YEAR
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0.0
    return (excess_returns.mean() / downside_returns.std()) * np.sqrt(TRADING_DAYS_PER_YEAR)


def calmar_ratio(prices: pd.Series) -> float:
    ann_return = cagr(prices)
    mdd = abs(max_drawdown(prices))
    if mdd == 0:
        return 0.0
    return ann_return / mdd


def rolling_volatility(
    prices: pd.Series,
    window: int = 21,
    annualize: bool = True,
) -> pd.Series:
    returns = daily_returns(prices)
    roll_vol = returns.rolling(window=window).std()
    if annualize:
        roll_vol *= np.sqrt(TRADING_DAYS_PER_YEAR)
    return roll_vol


def rolling_sharpe(
    prices: pd.Series,
    window: int = 63,
    risk_free_rate: float = RISK_FREE_RATE,
) -> pd.Series:
    returns = daily_returns(prices)
    excess_returns = returns - risk_free_rate / TRADING_DAYS_PER_YEAR
    roll_mean = excess_returns.rolling(window=window).mean()
    roll_std = returns.rolling(window=window).std()
    return (roll_mean / roll_std) * np.sqrt(TRADING_DAYS_PER_YEAR)


def rolling_beta(
    prices: pd.Series,
    benchmark_prices: pd.Series,
    window: int = 63,
) -> pd.Series:
    returns = daily_returns(prices)
    bench_returns = daily_returns(benchmark_prices)
    aligned = pd.DataFrame({"asset": returns, "bench": bench_returns}).dropna()
    
    def calc_beta(window_data):
        if len(window_data) < 2:
            return np.nan
        cov = window_data["asset"].cov(window_data["bench"])
        var = window_data["bench"].var()
        return cov / var if var != 0 else np.nan
    
    result = aligned.rolling(window=window).apply(
        lambda x: calc_beta(pd.DataFrame({"asset": x[:len(x)//2], "bench": x[len(x)//2:]})),
        raw=False
    )
    return pd.Series(result.values, index=aligned.index)  # type: ignore[arg-type]


def beta(prices: pd.Series, benchmark_prices: pd.Series) -> float:
    returns = daily_returns(prices)
    bench_returns = daily_returns(benchmark_prices)
    aligned = pd.DataFrame({"asset": returns, "bench": bench_returns}).dropna()
    cov_val = aligned["asset"].cov(aligned["bench"])
    var_val = aligned["bench"].var()
    cov: float = cov_val  # type: ignore[assignment]
    var: float = var_val  # type: ignore[assignment]
    return cov / var if var != 0 else 0.0


def alpha(
    prices: pd.Series,
    benchmark_prices: pd.Series,
    risk_free_rate: float = RISK_FREE_RATE,
) -> float:
    asset_return = cagr(prices)
    bench_return = cagr(benchmark_prices)
    b = beta(prices, benchmark_prices)
    return asset_return - (risk_free_rate + b * (bench_return - risk_free_rate))


def monthly_returns(prices: pd.Series) -> pd.DataFrame:
    monthly = prices.resample("ME").last()
    returns = monthly.pct_change().dropna()
    # Get year and month from DatetimeIndex
    dates = pd.to_datetime(returns.index)
    df = pd.DataFrame({
        "year": dates.year,
        "month": dates.month,
        "return": returns.values,
    })
    pivot = df.pivot(index="year", columns="month", values="return")
    pivot.columns = pd.Index(["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    return pivot


def yearly_returns(prices: pd.Series) -> pd.Series:
    yearly = prices.resample("YE").last()
    return yearly.pct_change().dropna()


def correlation_matrix(prices_df: pd.DataFrame) -> pd.DataFrame:
    returns = prices_df.pct_change().dropna()
    return returns.corr()


def detect_regime(
    prices: pd.Series,
    short_window: int = 20,
    long_window: int = 50,
    vol_window: int = 21,
    vol_threshold: float = 0.25,
) -> pd.DataFrame:
    short_ma = prices.rolling(window=short_window).mean()
    long_ma = prices.rolling(window=long_window).mean()
    returns = daily_returns(prices)
    roll_vol = returns.rolling(window=vol_window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    trend = pd.Series(index=prices.index, dtype=str)
    trend[short_ma > long_ma] = "uptrend"
    trend[short_ma <= long_ma] = "downtrend"
    
    volatility_regime = pd.Series(index=prices.index, dtype=str)
    volatility_regime[roll_vol > vol_threshold] = "high_vol"
    volatility_regime[roll_vol <= vol_threshold] = "low_vol"
    
    regime = pd.DataFrame({
        "trend": trend,
        "volatility_regime": volatility_regime,
        "short_ma": short_ma,
        "long_ma": long_ma,
        "rolling_vol": roll_vol,
    })
    return regime


def compute_metrics(
    prices: pd.Series,
    benchmark_prices: Optional[pd.Series] = None,
    risk_free_rate: float = RISK_FREE_RATE,
) -> dict:
    metrics = {
        "total_return": total_return(prices),
        "cagr": cagr(prices),
        "volatility": volatility(prices),
        "max_drawdown": max_drawdown(prices),
        "sharpe_ratio": sharpe_ratio(prices, risk_free_rate),
        "sortino_ratio": sortino_ratio(prices, risk_free_rate),
        "calmar_ratio": calmar_ratio(prices),
    }
    
    if benchmark_prices is not None:
        metrics["beta"] = beta(prices, benchmark_prices)
        metrics["alpha"] = alpha(prices, benchmark_prices, risk_free_rate)
    
    return metrics


def format_metrics(metrics: dict) -> dict:
    formatters = {
        "total_return": lambda x: f"{x * 100:.2f}%",
        "cagr": lambda x: f"{x * 100:.2f}%",
        "volatility": lambda x: f"{x * 100:.2f}%",
        "max_drawdown": lambda x: f"{x * 100:.2f}%",
        "sharpe_ratio": lambda x: f"{x:.2f}",
        "sortino_ratio": lambda x: f"{x:.2f}",
        "calmar_ratio": lambda x: f"{x:.2f}",
        "beta": lambda x: f"{x:.2f}",
        "alpha": lambda x: f"{x * 100:.2f}%",
    }
    return {k: formatters.get(k, lambda x: f"{x:.2f}")(v) for k, v in metrics.items()}


def compute_rolling_metrics(
    prices: pd.Series,
    windows: Optional[dict[str, int]] = None,
) -> pd.DataFrame:
    if windows is None:
        windows = {"volatility": 21, "sharpe": 63}
    
    result = pd.DataFrame(index=prices.index)
    result["price"] = prices
    result["rolling_vol"] = rolling_volatility(prices, window=windows["volatility"])
    result["rolling_sharpe"] = rolling_sharpe(prices, window=windows["sharpe"])
    result["drawdown"] = drawdown_series(prices)
    
    return result
