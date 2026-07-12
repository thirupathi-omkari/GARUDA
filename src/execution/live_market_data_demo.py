from datetime import datetime, timedelta

from broker.session_manager import (
    create_authenticated_session,
)

from data.instrument_resolver import (
    resolve_instrument_token,
)

from data.live_market_data import (
    fetch_live_intraday_data,
    get_latest_market_candle,
    get_latest_market_price,
)


def display_market_data(
    symbol,
    instrument_token,
    dataframe,
):
    """
    Display GARUDA live intraday
    market-data information.
    """

    print("\n" + "=" * 70)
    print("GARUDA QUANT LAB - LIVE MARKET DATA DEMO")
    print("=" * 70)

    print("\n[INSTRUMENT]")
    print("-" * 70)

    print(
        f"Symbol              : "
        f"{symbol}"
    )

    print(
        f"Instrument Token    : "
        f"{instrument_token}"
    )

    print("\n[MARKET DATA]")
    print("-" * 70)

    print(
        f"Candles Available   : "
        f"{len(dataframe)}"
    )

    if dataframe.empty:

        print(
            "Status              : "
            "NO MARKET DATA"
        )

        print("=" * 70)

        return

    latest_candle = (
        get_latest_market_candle(
            dataframe
        )
    )

    latest_price = (
        get_latest_market_price(
            dataframe
        )
    )

    print(
        f"Latest Candle Time  : "
        f"{latest_candle['datetime']}"
    )

    print(
        f"Open                : "
        f"{latest_candle['open']:.2f}"
    )

    print(
        f"High                : "
        f"{latest_candle['high']:.2f}"
    )

    print(
        f"Low                 : "
        f"{latest_candle['low']:.2f}"
    )

    print(
        f"Close               : "
        f"{latest_candle['close']:.2f}"
    )

    print(
        f"Volume              : "
        f"{latest_candle['volume']}"
    )

    print(
        f"Latest Market Price : "
        f"{latest_price:.2f}"
    )

    print("\n[LATEST 5 CANDLES]")
    print("-" * 70)

    print(
        dataframe.tail(5).to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)

    print(
        "GARUDA LIVE MARKET DATA DEMO COMPLETED"
    )

    print("=" * 70)


def main():
    """
    Run GARUDA's real Kite market-data demo.

    Current purpose:

    Authenticated Kite Session
        ↓
    Resolve Instrument
        ↓
    Fetch Latest Intraday Candles
        ↓
    GARUDA Standard DataFrame
        ↓
    Visible Terminal Output
    """

    # --------------------------------------------------
    # DEMO CONFIGURATION
    # --------------------------------------------------

    symbol = "INFY"

    exchange = "NSE"

    interval = "5minute"

    # --------------------------------------------------
    # CREATE AUTHENTICATED KITE SESSION
    # --------------------------------------------------

    print("\nCreating authenticated Kite session...")

    kite = create_authenticated_session()

    if kite is None:

        print(
            "\nGARUDA Live Market Data Demo Failed."
        )

        print(
            "Reason: Authenticated Kite session "
            "unavailable."
        )

        return

    # --------------------------------------------------
    # RESOLVE INSTRUMENT TOKEN
    # --------------------------------------------------

    instrument_token = (
        resolve_instrument_token(
            kite=kite,
            tradingsymbol=symbol,
            exchange=exchange,
        )
    )

    if instrument_token is None:

        print(
            "\nGARUDA Live Market Data Demo Failed."
        )

        print(
            f"Reason: Instrument token unavailable "
            f"for {symbol}."
        )

        return

    # --------------------------------------------------
    # DEFINE INTRADAY DATA PERIOD
    # --------------------------------------------------

    current_time = datetime.now()

    from_date = (
        current_time - timedelta(days=5)
    )

    to_date = current_time

    # --------------------------------------------------
    # FETCH REAL KITE MARKET DATA
    # --------------------------------------------------

    print("\nFetching real Kite market data...")

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
    )

    # --------------------------------------------------
    # DISPLAY VISIBLE OUTPUT
    # --------------------------------------------------

    display_market_data(
        symbol=symbol,
        instrument_token=instrument_token,
        dataframe=dataframe,
    )


if __name__ == "__main__":

    main()