import pandas as pd


def fetch_historical_data(
    kite,
    instrument_token,
    from_date,
    to_date,
    interval,
):
    """Fetch historical market data from Kite."""

    print("\nFetching historical market data...")
    print("-" * 60)

    candles = kite.historical_data(
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
    )

    dataframe = pd.DataFrame(candles)

    print(f"Candles received : {len(dataframe)}")

    if dataframe.empty:
        print("No historical candles received.")
        return dataframe

    print("Historical market data fetched successfully.")
    print("-" * 60)

    return dataframe

def standardize_historical_data(dataframe):
    """Convert Kite historical data into GARUDA standard format."""

    print("\nStandardizing historical market data...")
    print("-" * 60)

    if dataframe.empty:
        print("Cannot standardize an empty DataFrame.")
        return dataframe

    standardized_data = dataframe.copy()

    standardized_data = standardized_data.rename(
        columns={
            "date": "datetime",
        }
    )

    required_columns = [
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    standardized_data = standardized_data[required_columns]

    print("Market data standardized successfully.")
    print(f"Columns : {list(standardized_data.columns)}")
    print("-" * 60)

    return standardized_data