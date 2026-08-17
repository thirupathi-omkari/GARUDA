"""Moving-average indicator helpers for GARUDA Strategy #2."""

import pandas as pd


def calculate_moving_average(
    dataframe: pd.DataFrame,
    period: int,
    ma_type: str = "EMA",
    price_column: str = "close",
) -> pd.Series:
    """Calculate an SMA or EMA using only data available through each candle."""
    if dataframe is None or dataframe.empty:
        return pd.Series(dtype="float64")

    if period <= 0:
        raise ValueError("period must be greater than zero")

    if price_column not in dataframe.columns:
        raise ValueError(f"Missing price column: {price_column}")

    prices = pd.to_numeric(dataframe[price_column], errors="coerce")
    mode = ma_type.upper()

    if mode == "EMA":
        return prices.ewm(span=period, adjust=False, min_periods=period).mean()

    if mode == "SMA":
        return prices.rolling(window=period, min_periods=period).mean()

    raise ValueError("ma_type must be EMA or SMA")


def add_moving_averages(
    dataframe: pd.DataFrame,
    fast_period: int = 9,
    slow_period: int = 21,
    ma_type: str = "EMA",
    price_column: str = "close",
) -> pd.DataFrame:
    """Return a copy containing fast_ma and slow_ma."""
    if fast_period >= slow_period:
        raise ValueError("fast_period must be less than slow_period")

    result = dataframe.copy()
    result["fast_ma"] = calculate_moving_average(
        result, fast_period, ma_type, price_column
    )
    result["slow_ma"] = calculate_moving_average(
        result, slow_period, ma_type, price_column
    )
    return result
