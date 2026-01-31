# Flux-RX Data Module: Fetching, caching, and metadata handling
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union

import pandas as pd
import yfinance as yf

_CACHE_DIR = Path.home() / ".flux_rx_cache"
_CACHE_EXPIRY_HOURS = 4

PERIOD_MAP = {
    "1d": 1,
    "5d": 5,
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
    "10y": 3650,
    "ytd": None,
    "max": None,
}


def _ensure_cache_dir() -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def _cache_key(ticker: str, period: str, interval: str) -> str:
    raw = f"{ticker.upper()}_{period}_{interval}"
    return hashlib.md5(raw.encode()).hexdigest()


def _cache_path(key: str, suffix: str = ".parquet") -> Path:
    return _ensure_cache_dir() / f"{key}{suffix}"


def _is_cache_valid(path: Path, max_age_hours: float = _CACHE_EXPIRY_HOURS) -> bool:
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - mtime < timedelta(hours=max_age_hours)


def clear_cache() -> int:
    cache_dir = _ensure_cache_dir()
    count = 0
    for f in cache_dir.glob("*"):
        f.unlink()
        count += 1
    return count


def fetch(
    ticker: str,
    period: str = "5y",
    interval: str = "1d",
    use_cache: bool = True,
) -> pd.DataFrame:
    ticker = ticker.upper()
    key = _cache_key(ticker, period, interval)
    cache_file = _cache_path(key)

    if use_cache and _is_cache_valid(cache_file):
        df = pd.read_parquet(cache_file)
        df.index = pd.to_datetime(df.index)
        return df

    yf_ticker = yf.Ticker(ticker)
    df = yf_ticker.history(period=period, interval=interval, auto_adjust=True)
    
    if df.empty:
        raise ValueError(f"No data found for ticker: {ticker}")

    df.index = pd.to_datetime(df.index)
    df.index.name = "Date"
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    if use_cache:
        df.to_parquet(cache_file)

    return df


def fetch_multiple(
    tickers: list[str],
    period: str = "5y",
    interval: str = "1d",
    use_cache: bool = True,
) -> dict[str, pd.DataFrame]:
    return {t: fetch(t, period, interval, use_cache) for t in tickers}


def get_info(ticker: str, use_cache: bool = True) -> dict:
    ticker = ticker.upper()
    key = f"info_{ticker}"
    cache_file = _cache_path(key, suffix=".json")

    if use_cache and _is_cache_valid(cache_file, max_age_hours=24):
        with open(cache_file, "r") as f:
            return json.load(f)

    yf_ticker = yf.Ticker(ticker)
    info = yf_ticker.info

    clean_info = {
        "ticker": ticker,
        "name": info.get("longName") or info.get("shortName") or ticker,
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "country": info.get("country", "N/A"),
        "market_cap": info.get("marketCap"),
        "market_cap_fmt": _format_market_cap(info.get("marketCap")),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange", "N/A"),
        "quote_type": info.get("quoteType", "EQUITY"),
        "description": info.get("longBusinessSummary", ""),
        "website": info.get("website", ""),
        "employees": info.get("fullTimeEmployees"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "avg_volume": info.get("averageVolume"),
        "avg_volume_10d": info.get("averageDailyVolume10Day"),
    }

    if use_cache:
        with open(cache_file, "w") as f:
            json.dump(clean_info, f, indent=2, default=str)

    return clean_info


def _format_market_cap(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    if value >= 1e12:
        return f"${value / 1e12:.2f}T"
    if value >= 1e9:
        return f"${value / 1e9:.2f}B"
    if value >= 1e6:
        return f"${value / 1e6:.2f}M"
    return f"${value:,.0f}"


def get_benchmark_data(
    benchmark: str = "SPY",
    period: str = "5y",
    interval: str = "1d",
) -> pd.DataFrame:
    return fetch(benchmark, period, interval)


def align_dataframes(
    dfs: dict[str, pd.DataFrame],
    column: str = "Close",
) -> pd.DataFrame:
    aligned = pd.DataFrame()
    for ticker, df in dfs.items():
        aligned[ticker] = df[column]
    aligned = aligned.dropna()
    return aligned


def normalize_prices(df: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    return df / df.iloc[0] * base
