from datetime import datetime

import pandas as pd
import pytest


from data.live_market_data import (
    GARUDA_MARKET_COLUMNS,
    fetch_live_intraday_data,
    get_latest_market_candle,
    get_latest_market_price,
)


class FakeKiteClient:
    """
    Fake Kite client used to test GARUDA's
    live market data adapter without making
    real network requests.
    """

    def __init__(
        self,
        candles=None,
    ):

        self.candles = (
            candles
            if candles is not None
            else []
        )

        self.last_request = None


    def historical_data(
        self,
        instrument_token,
        from_date,
        to_date,
        interval,
    ):

        self.last_request = {
            "instrument_token": instrument_token,
            "from_date": from_date,
            "to_date": to_date,
            "interval": interval,
        }

        return self.candles


def create_test_candles():

    return [
        {
            "date": "2026-07-12 09:15:00",
            "open": 100.00,
            "high": 101.00,
            "low": 99.50,
            "close": 100.50,
            "volume": 1000,
        },
        {
            "date": "2026-07-12 09:20:00",
            "open": 100.50,
            "high": 102.00,
            "low": 100.00,
            "close": 101.50,
            "volume": 1500,
        },
    ]


def test_fetch_live_intraday_data():

    kite = FakeKiteClient(
        candles=create_test_candles()
    )

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=123456,
        from_date="2026-07-12",
        to_date="2026-07-12",
        interval="5minute",
    )

    assert isinstance(
        dataframe,
        pd.DataFrame,
    )

    assert list(
        dataframe.columns
    ) == GARUDA_MARKET_COLUMNS

    assert len(dataframe) == 2


def test_kite_request_parameters_are_preserved():

    kite = FakeKiteClient(
        candles=create_test_candles()
    )

    fetch_live_intraday_data(
        kite=kite,
        instrument_token=123456,
        from_date="2026-07-12",
        to_date="2026-07-12",
        interval="5minute",
    )

    assert (
        kite.last_request["instrument_token"]
        == 123456
    )

    assert (
        kite.last_request["interval"]
        == "5minute"
    )

    assert (
        kite.last_request["from_date"]
        == datetime(
            2026,
            7,
            12,
        )
    )

    assert (
        kite.last_request["to_date"]
        == datetime(
            2026,
            7,
            12,
        )
    )


def test_date_column_is_standardized():

    kite = FakeKiteClient(
        candles=create_test_candles()
    )

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=123456,
        from_date="2026-07-12",
        to_date="2026-07-12",
    )

    assert "datetime" in dataframe.columns

    assert "date" not in dataframe.columns

    assert pd.api.types.is_datetime64_any_dtype(
        dataframe["datetime"]
    )


def test_market_data_is_sorted_by_datetime():

    candles = list(
        reversed(
            create_test_candles()
        )
    )

    kite = FakeKiteClient(
        candles=candles
    )

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=123456,
        from_date="2026-07-12",
        to_date="2026-07-12",
    )

    assert dataframe.iloc[0][
        "datetime"
    ] < dataframe.iloc[1][
        "datetime"
    ]


def test_duplicate_candles_are_removed():

    candles = create_test_candles()

    candles.append(
        candles[-1].copy()
    )

    kite = FakeKiteClient(
        candles=candles
    )

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=123456,
        from_date="2026-07-12",
        to_date="2026-07-12",
    )

    assert len(dataframe) == 2


def test_empty_market_data_returns_standard_dataframe():

    kite = FakeKiteClient()

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=123456,
        from_date="2026-07-12",
        to_date="2026-07-12",
    )

    assert dataframe.empty

    assert list(
        dataframe.columns
    ) == GARUDA_MARKET_COLUMNS


def test_missing_required_column_raises_error():

    candles = create_test_candles()

    for candle in candles:

        candle.pop("volume")

    kite = FakeKiteClient(
        candles=candles
    )

    with pytest.raises(
        ValueError,
        match="missing required columns",
    ):

        fetch_live_intraday_data(
            kite=kite,
            instrument_token=123456,
            from_date="2026-07-12",
            to_date="2026-07-12",
        )


def test_kite_client_is_required():

    with pytest.raises(
        ValueError,
        match="Authenticated Kite client is required",
    ):

        fetch_live_intraday_data(
            kite=None,
            instrument_token=123456,
            from_date="2026-07-12",
            to_date="2026-07-12",
        )


def test_instrument_token_is_required():

    kite = FakeKiteClient()

    with pytest.raises(
        ValueError,
        match="Instrument token is required",
    ):

        fetch_live_intraday_data(
            kite=kite,
            instrument_token=None,
            from_date="2026-07-12",
            to_date="2026-07-12",
        )


def test_latest_market_candle():

    kite = FakeKiteClient(
        candles=create_test_candles()
    )

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=123456,
        from_date="2026-07-12",
        to_date="2026-07-12",
    )

    latest_candle = get_latest_market_candle(
        dataframe
    )

    assert latest_candle["close"] == 101.50


def test_empty_dataframe_has_no_latest_candle():

    dataframe = pd.DataFrame(
        columns=GARUDA_MARKET_COLUMNS
    )

    assert (
        get_latest_market_candle(
            dataframe
        )
        is None
    )


def test_latest_market_price():

    kite = FakeKiteClient(
        candles=create_test_candles()
    )

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=123456,
        from_date="2026-07-12",
        to_date="2026-07-12",
    )

    market_price = get_latest_market_price(
        dataframe
    )

    assert market_price == 101.50