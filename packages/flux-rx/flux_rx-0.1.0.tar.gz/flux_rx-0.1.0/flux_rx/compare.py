# Flux-RX Compare Module: Multi-ticker analysis and comparison utilities
from __future__ import annotations

from typing import Optional

import pandas as pd
import numpy as np

from flux_rx.data import fetch_multiple, align_dataframes, normalize_prices, get_info
from flux_rx.analytics import (
    compute_metrics,
    daily_returns,
    correlation_matrix,
    cagr,
    volatility,
    max_drawdown,
    sharpe_ratio,
    beta,
    alpha,
)
from flux_rx.charts import (
    performance_chart,
    risk_return_scatter,
    correlation_matrix as correlation_chart,
)
from flux_rx.themes import DEFAULT_THEME


class ComparisonResult:
    def __init__(
        self,
        tickers: list[str],
        prices: pd.DataFrame,
        metrics: dict[str, dict],
        correlation: pd.DataFrame,
        period: str,
    ):
        self.tickers = tickers
        self.prices = prices
        self.metrics = metrics
        self.correlation = correlation
        self.period = period
    
    def summary(self) -> pd.DataFrame:
        rows = []
        for ticker in self.tickers:
            m = self.metrics[ticker]
            rows.append({
                "Ticker": ticker,
                "CAGR": f"{m['cagr'] * 100:.2f}%",
                "Volatility": f"{m['volatility'] * 100:.2f}%",
                "Max Drawdown": f"{m['max_drawdown'] * 100:.2f}%",
                "Sharpe": f"{m['sharpe_ratio']:.2f}",
                "Sortino": f"{m['sortino_ratio']:.2f}",
                "Calmar": f"{m['calmar_ratio']:.2f}",
            })
        return pd.DataFrame(rows).set_index("Ticker")
    
    def best_performer(self, metric: str = "sharpe_ratio") -> str:
        return max(self.tickers, key=lambda t: self.metrics[t].get(metric, 0))
    
    def lowest_risk(self) -> str:
        return min(self.tickers, key=lambda t: self.metrics[t]["volatility"])
    
    def highest_return(self) -> str:
        return max(self.tickers, key=lambda t: self.metrics[t]["cagr"])
    
    def rank_by(self, metric: str = "sharpe_ratio", ascending: bool = False) -> list[str]:
        return sorted(
            self.tickers,
            key=lambda t: self.metrics[t].get(metric, 0),
            reverse=not ascending,
        )


def compare_tickers(
    tickers: list[str],
    period: str = "5y",
    benchmark: Optional[str] = None,
) -> ComparisonResult:
    all_tickers = list(tickers)
    if benchmark and benchmark not in all_tickers:
        all_tickers.append(benchmark)
    
    data = fetch_multiple(all_tickers, period=period)
    prices_df = align_dataframes(data)
    
    benchmark_prices = prices_df[benchmark] if benchmark else None
    
    metrics = {}
    for ticker in tickers:
        metrics[ticker] = compute_metrics(
            prices_df[ticker],
            benchmark_prices if ticker != benchmark else None,
        )
    
    corr = correlation_matrix(prices_df[tickers])
    
    return ComparisonResult(
        tickers=tickers,
        prices=prices_df[tickers],
        metrics=metrics,
        correlation=corr,
        period=period,
    )


def performance_attribution(
    ticker: str,
    benchmark: str,
    period: str = "5y",
) -> dict:
    from flux_rx.data import fetch
    
    ticker_df = fetch(ticker, period=period)
    bench_df = fetch(benchmark, period=period)
    
    aligned_idx = ticker_df.index.intersection(bench_df.index)
    ticker_prices = ticker_df["Close"].loc[aligned_idx]
    bench_prices = bench_df["Close"].loc[aligned_idx]
    
    ticker_cagr = cagr(ticker_prices)
    bench_cagr = cagr(bench_prices)
    ticker_vol = volatility(ticker_prices)
    bench_vol = volatility(bench_prices)
    b = beta(ticker_prices, bench_prices)
    a = alpha(ticker_prices, bench_prices)
    
    excess_return = ticker_cagr - bench_cagr
    
    returns_t = daily_returns(ticker_prices)
    returns_b = daily_returns(bench_prices)
    tracking_error = (returns_t - returns_b).std() * np.sqrt(252)
    
    information_ratio = excess_return / tracking_error if tracking_error != 0 else 0
    
    r_squared = returns_t.corr(returns_b) ** 2
    
    return {
        "ticker": ticker,
        "benchmark": benchmark,
        "ticker_cagr": ticker_cagr,
        "benchmark_cagr": bench_cagr,
        "excess_return": excess_return,
        "beta": b,
        "alpha": a,
        "ticker_volatility": ticker_vol,
        "benchmark_volatility": bench_vol,
        "tracking_error": tracking_error,
        "information_ratio": information_ratio,
        "r_squared": r_squared,
    }


def portfolio_metrics(
    tickers: list[str],
    weights: list[float],
    period: str = "5y",
) -> dict:
    if abs(sum(weights) - 1.0) > 0.001:
        raise ValueError("Weights must sum to 1.0")
    
    if len(tickers) != len(weights):
        raise ValueError("Number of tickers must match number of weights")
    
    data = fetch_multiple(tickers, period=period)
    prices_df = align_dataframes(data)
    returns_df = prices_df.pct_change().dropna()
    
    weights_arr = np.array(weights)
    portfolio_returns = (returns_df * weights_arr).sum(axis=1)
    
    portfolio_prices = (1 + portfolio_returns).cumprod()
    portfolio_prices = portfolio_prices / portfolio_prices.iloc[0] * 100
    
    port_cagr = cagr(portfolio_prices)
    port_vol = portfolio_returns.std() * np.sqrt(252)
    
    cummax = portfolio_prices.cummax()
    drawdown = (portfolio_prices - cummax) / cummax
    port_mdd = drawdown.min()
    
    excess_returns = portfolio_returns - 0.04 / 252
    port_sharpe = (excess_returns.mean() / portfolio_returns.std()) * np.sqrt(252)
    
    cov_matrix = returns_df.cov() * 252
    portfolio_variance = np.dot(weights_arr, np.dot(cov_matrix, weights_arr))
    
    individual_contributions = []
    for i, ticker in enumerate(tickers):
        marginal_contrib = np.dot(cov_matrix.iloc[i], weights_arr) / np.sqrt(portfolio_variance)
        contrib = weights[i] * marginal_contrib
        individual_contributions.append({
            "ticker": ticker,
            "weight": weights[i],
            "marginal_contribution": marginal_contrib,
            "risk_contribution": contrib,
        })
    
    return {
        "cagr": port_cagr,
        "volatility": port_vol,
        "max_drawdown": port_mdd,
        "sharpe_ratio": port_sharpe,
        "total_variance": portfolio_variance,
        "portfolio_prices": portfolio_prices,
        "portfolio_returns": portfolio_returns,
        "risk_contributions": individual_contributions,
    }


def optimal_weights_minvol(
    tickers: list[str],
    period: str = "5y",
) -> dict[str, float]:
    data = fetch_multiple(tickers, period=period)
    prices_df = align_dataframes(data)
    returns_df = prices_df.pct_change().dropna()
    
    cov_matrix = returns_df.cov().values
    inv_cov = np.linalg.inv(cov_matrix)
    ones = np.ones(len(tickers))
    
    weights = np.dot(inv_cov, ones) / np.dot(ones, np.dot(inv_cov, ones))
    weights = np.maximum(weights, 0)
    weights = weights / weights.sum()
    
    return {ticker: weight for ticker, weight in zip(tickers, weights)}


def rolling_correlation(
    ticker1: str,
    ticker2: str,
    period: str = "5y",
    window: int = 63,
) -> pd.Series:
    from flux_rx.data import fetch
    
    df1 = fetch(ticker1, period=period)
    df2 = fetch(ticker2, period=period)
    
    aligned_idx = df1.index.intersection(df2.index)
    returns1 = daily_returns(df1["Close"].loc[aligned_idx])
    returns2 = daily_returns(df2["Close"].loc[aligned_idx])
    
    return returns1.rolling(window=window).corr(returns2)


def sector_exposure(tickers: list[str]) -> pd.DataFrame:
    sectors = {}
    for ticker in tickers:
        info = get_info(ticker)
        sector = info.get("sector", "Unknown")
        sectors[ticker] = sector
    
    df = pd.DataFrame.from_dict(sectors, orient="index", columns=["Sector"])
    df.index.name = "Ticker"
    return df


def diversification_ratio(
    tickers: list[str],
    weights: list[float],
    period: str = "5y",
) -> float:
    data = fetch_multiple(tickers, period=period)
    prices_df = align_dataframes(data)
    returns_df = prices_df.pct_change().dropna()
    
    weights_arr = np.array(weights)
    
    individual_vols = returns_df.std() * np.sqrt(252)
    weighted_avg_vol = np.dot(weights_arr, individual_vols)
    
    cov_matrix = returns_df.cov() * 252
    portfolio_vol = np.sqrt(np.dot(weights_arr, np.dot(cov_matrix, weights_arr)))
    
    return weighted_avg_vol / portfolio_vol if portfolio_vol != 0 else 1.0
