import pandas as pd


def prepare_historical_sessions(dataframe):
    """Split historical market data into trading sessions."""

    if dataframe is None or dataframe.empty:
        return []

    data = dataframe.copy()

    data["datetime"] = pd.to_datetime(
        data["datetime"]
    )

    data = data.sort_values(
        "datetime"
    ).reset_index(drop=True)

    sessions = []

    grouped_data = data.groupby(
        data["datetime"].dt.date
    )

    for session_date, session_data in grouped_data:

        prepared_session = (
            session_data
            .copy()
            .sort_values("datetime")
            .reset_index(drop=True)
        )

        sessions.append(
            {
                "session_date": session_date,
                "data": prepared_session,
            }
        )

    return sessions