import pandas as pd


GARUDA_MARKET_COLUMNS = [
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "volume",
]


def fetch_live_intraday_data(
    kite,
    instrument_token,
    from_date,
    to_date,
    interval="5minute",
):
    """
    Fetch the latest available intraday candles
    from Kite and convert them into GARUDA's
    standard OHLCV market-data format.

    This adapter is the bridge between:

    Kite Market Data
        ↓
    GARUDA Strategy Engine
        ↓
    GARUDA Risk Manager
        ↓
    GARUDA Paper Trading Engine
    """

    # --------------------------------------------------
    # VALIDATE KITE CLIENT
    # --------------------------------------------------

    if kite is None:

        raise ValueError(
            "Authenticated Kite client is required."
        )

    # --------------------------------------------------
    # VALIDATE INSTRUMENT TOKEN
    # --------------------------------------------------

    if instrument_token is None:

        raise ValueError(
            "Instrument token is required."
        )

    # --------------------------------------------------
    # VALIDATE DATE RANGE
    # --------------------------------------------------

    if from_date is None:

        raise ValueError(
            "From date is required."
        )

    if to_date is None:

        raise ValueError(
            "To date is required."
        )

    # --------------------------------------------------
    # VALIDATE INTERVAL
    # --------------------------------------------------

    if not interval:

        raise ValueError(
            "Interval is required."
        )

    # --------------------------------------------------
    # FETCH INTRADAY MARKET DATA
    # --------------------------------------------------

    candles = kite.historical_data(
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
    )

    # --------------------------------------------------
    # CONVERT TO DATAFRAME
    # --------------------------------------------------

    dataframe = pd.DataFrame(candles)

    # --------------------------------------------------
    # EMPTY MARKET DATA
    # --------------------------------------------------

    if dataframe.empty:

        return pd.DataFrame(
            columns=GARUDA_MARKET_COLUMNS
        )

    # --------------------------------------------------
    # STANDARDIZE DATETIME COLUMN
    # --------------------------------------------------

    if "date" in dataframe.columns:

        dataframe = dataframe.rename(
            columns={
                "date": "datetime",
            }
        )

    # --------------------------------------------------
    # VALIDATE REQUIRED MARKET COLUMNS
    # --------------------------------------------------

    missing_columns = [
        column
        for column in GARUDA_MARKET_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:

        raise ValueError(
            "Kite market data missing required columns: "
            + ", ".join(missing_columns)
        )

    # --------------------------------------------------
    # KEEP GARUDA STANDARD COLUMNS
    # --------------------------------------------------

    dataframe = dataframe[
        GARUDA_MARKET_COLUMNS
    ].copy()

    # --------------------------------------------------
    # STANDARDIZE DATETIME VALUES
    # --------------------------------------------------

    dataframe["datetime"] = pd.to_datetime(
        dataframe["datetime"]
    )

    # --------------------------------------------------
    # SORT MARKET DATA
    # --------------------------------------------------

    dataframe = dataframe.sort_values(
        by="datetime"
    )

    # --------------------------------------------------
    # REMOVE DUPLICATE CANDLES
    # --------------------------------------------------

    dataframe = dataframe.drop_duplicates(
        subset=["datetime"],
        keep="last",
    )

    # --------------------------------------------------
    # RESET DATAFRAME INDEX
    # --------------------------------------------------

    dataframe = dataframe.reset_index(
        drop=True
    )

    # --------------------------------------------------
    # RETURN GARUDA MARKET DATA
    # --------------------------------------------------

    return dataframe


def get_latest_market_candle(
    dataframe,
):
    """
    Return the latest available GARUDA
    market candle.
    """

    # --------------------------------------------------
    # VALIDATE DATAFRAME
    # --------------------------------------------------

    if dataframe is None:

        raise ValueError(
            "Market dataframe is required."
        )

    # --------------------------------------------------
    # EMPTY DATAFRAME
    # --------------------------------------------------

    if dataframe.empty:

        return None

    # --------------------------------------------------
    # RETURN LATEST CANDLE
    # --------------------------------------------------

    return dataframe.iloc[-1]


def get_latest_market_price(
    dataframe,
):
    """
    Return the latest available market price
    from GARUDA intraday data.
    """

    latest_candle = get_latest_market_candle(
        dataframe
    )

    if latest_candle is None:

        return None

    return float(
        latest_candle["close"]
    )