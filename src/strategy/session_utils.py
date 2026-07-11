import pandas as pd


def get_latest_trading_session(dataframe):
    """Return market data for the latest trading session."""

    if dataframe is None or dataframe.empty:
        return None

    data = dataframe.copy()

    data["datetime"] = pd.to_datetime(
        data["datetime"]
    )

    latest_session_date = (
        data["datetime"].dt.date.max()
    )

    session_data = data[
        data["datetime"].dt.date
        == latest_session_date
    ].copy()

    session_data = session_data.sort_values(
        "datetime"
    ).reset_index(drop=True)

    return session_data


def get_opening_range_data(
    session_data,
    start_time="09:15",
    end_time="09:30",
):
    """Return candles belonging to the opening range period."""

    if session_data is None or session_data.empty:
        return None

    data = session_data.copy()

    data["datetime"] = pd.to_datetime(
        data["datetime"]
    )

    candle_times = data[
        "datetime"
    ].dt.strftime("%H:%M")

    opening_data = data[
        (candle_times >= start_time)
        & (candle_times < end_time)
    ].copy()

    opening_data = opening_data.sort_values(
        "datetime"
    ).reset_index(drop=True)

    return opening_data