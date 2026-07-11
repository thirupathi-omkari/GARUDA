import pandas as pd


def calculate_activity_metrics(dataframe):
    """Calculate activity metrics for one instrument."""

    if dataframe.empty:
        return None

    data = dataframe.copy()

    # Average volume across all candles
    average_volume = data["volume"].mean()

    # Recent volume: average of last 5 candles
    recent_volume = data["volume"].tail(5).mean()

    # Volume ratio
    if average_volume > 0:
        volume_ratio = recent_volume / average_volume
    else:
        volume_ratio = 0

    # Candle range percentage
    data["candle_range_pct"] = (
        (data["high"] - data["low"])
        / data["open"]
        * 100
    )

    average_candle_range_pct = (
        data["candle_range_pct"].mean()
    )

    # Recent price change percentage
    first_close = data["close"].iloc[0]
    latest_close = data["close"].iloc[-1]

    if first_close > 0:
        price_change_pct = (
            (latest_close - first_close)
            / first_close
            * 100
        )
    else:
        price_change_pct = 0

    # Volatility based on close-to-close returns
    returns = data["close"].pct_change()

    volatility_pct = returns.std() * 100

    metrics = {
        "average_volume": average_volume,
        "recent_volume": recent_volume,
        "volume_ratio": volume_ratio,
        "average_candle_range_pct": average_candle_range_pct,
        "price_change_pct": price_change_pct,
        "volatility_pct": volatility_pct,
    }

    return metrics

def calculate_universe_metrics(universe_data):
    """Calculate activity metrics for all instruments."""

    universe_metrics = {}

    for symbol, dataframe in universe_data.items():

        metrics = calculate_activity_metrics(dataframe)

        if metrics is None:
            print(f"Skipping {symbol}: Metrics unavailable.")
            continue

        universe_metrics[symbol] = metrics

    return universe_metrics