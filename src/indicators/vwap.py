def calculate_vwap(dataframe):
    """Calculate cumulative VWAP."""

    if dataframe is None or dataframe.empty:
        return None

    data = dataframe.copy()

    typical_price = (
        data["high"]
        + data["low"]
        + data["close"]
    ) / 3

    cumulative_price_volume = (
        typical_price * data["volume"]
    ).cumsum()

    cumulative_volume = (
        data["volume"].cumsum()
    )

    data["vwap"] = (
        cumulative_price_volume
        / cumulative_volume
    )

    return data