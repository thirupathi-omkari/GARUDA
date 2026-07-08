import pandas as pd


REQUIRED_COLUMNS = [
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


def validate_market_data(dataframe):
    """Validate OHLCV market data."""

    print("\nValidating market data...")
    print("-" * 60)

    # Check 1: Empty DataFrame
    if dataframe.empty:
        print("❌ Validation Failed: DataFrame is empty")
        return False

    # Check 2: Required Columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        print(f"❌ Validation Failed: Missing columns {missing_columns}")
        return False

    # Check 3: Missing Values
    if dataframe.isnull().values.any():
        print("❌ Validation Failed: Missing values detected")
        return False

    # Check 4: Duplicate Candles
    if dataframe["datetime"].duplicated().any():
        print("❌ Validation Failed: Duplicate candles detected")
        return False

    # Check 5: Invalid High Prices
    invalid_high = (
        (dataframe["high"] < dataframe["open"])
        | (dataframe["high"] < dataframe["close"])
        | (dataframe["high"] < dataframe["low"])
    )

    if invalid_high.any():
        print("❌ Validation Failed: Invalid HIGH price detected")
        return False

    # Check 6: Invalid Low Prices
    invalid_low = (
        (dataframe["low"] > dataframe["open"])
        | (dataframe["low"] > dataframe["close"])
        | (dataframe["low"] > dataframe["high"])
    )

    if invalid_low.any():
        print("❌ Validation Failed: Invalid LOW price detected")
        return False

    # Check 7: Negative Volume
    if (dataframe["volume"] < 0).any():
        print("❌ Validation Failed: Negative volume detected")
        return False

    print("✅ DataFrame is not empty")
    print("✅ Required columns available")
    print("✅ No missing values")
    print("✅ No duplicate candles")
    print("✅ OHLC prices valid")
    print("✅ Volume valid")

    print("-" * 60)
    print("GARUDA Data Validation: PASSED")

    return True