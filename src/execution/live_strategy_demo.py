from datetime import datetime, timedelta

from broker.session_manager import (
    create_authenticated_session,
)

from data.instrument_resolver import (
    resolve_instrument_token,
)

from data.live_market_data import (
    fetch_live_intraday_data,
)

from strategy.orb_vwap_strategy import (
    ORBVWAPStrategy,
)


def display_strategy_result(
    symbol,
    dataframe,
    strategy_result,
):
    """
    Display GARUDA's real-market
    strategy evaluation result.
    """

    print("\n" + "=" * 70)
    print("GARUDA QUANT LAB - LIVE STRATEGY DEMO")
    print("=" * 70)

    print("\n[MARKET DATA]")
    print("-" * 70)

    print(
        f"Symbol              : "
        f"{symbol}"
    )

    print(
        f"Candles Available   : "
        f"{len(dataframe)}"
    )

    if dataframe.empty:

        print(
            "Status              : "
            "NO MARKET DATA"
        )

        print("\n" + "=" * 70)
        print(
            "GARUDA LIVE STRATEGY DEMO COMPLETED"
        )
        print("=" * 70)

        return

    latest_candle = dataframe.iloc[-1]

    print(
        f"Latest Candle Time  : "
        f"{latest_candle['datetime']}"
    )

    print(
        f"Latest Close        : "
        f"{latest_candle['close']:.2f}"
    )

    print("\n[STRATEGY EVALUATION]")
    print("-" * 70)

    print(
        f"Strategy            : "
        f"{strategy_result.strategy_name}"
    )

    print(
        f"Signal              : "
        f"{strategy_result.signal}"
    )

    if strategy_result.entry_price is not None:

        print(
            f"Entry Price         : "
            f"{strategy_result.entry_price:.2f}"
        )

    else:

        print(
            "Entry Price         : "
            "N/A"
        )

    print(
        f"Reason              : "
        f"{strategy_result.reason}"
    )

    print("\n[STRATEGY DIAGNOSTICS]")
    print("-" * 70)

    diagnostics = strategy_result.diagnostics

    if not diagnostics:

        print(
            "Diagnostics         : "
            "NOT AVAILABLE"
        )

    else:

        print(
            f"Opening High        : "
            f"{diagnostics['opening_high']:.2f}"
        )

        print(
            f"Opening Low         : "
            f"{diagnostics['opening_low']:.2f}"
        )

        print(
            f"Latest Close        : "
            f"{diagnostics['latest_close']:.2f}"
        )

        print(
            f"Latest VWAP         : "
            f"{diagnostics['latest_vwap']:.2f}"
        )

        print(
            f"BUY Breakout        : "
            f"{diagnostics['buy_breakout']}"
        )

        print(
            f"BUY VWAP Confirm    : "
            f"{diagnostics['buy_vwap_confirmation']}"
        )

        print(
            f"SELL Breakdown      : "
            f"{diagnostics['sell_breakdown']}"
        )

        print(
            f"SELL VWAP Confirm   : "
            f"{diagnostics['sell_vwap_confirmation']}"
        )

    print("\n[GARUDA DECISION]")
    print("-" * 70)

    if strategy_result.signal == "BUY":

        print(
            "Action              : "
            "BUY SIGNAL GENERATED"
        )

        print(
            "Next Stage          : "
            "RISK MANAGER EVALUATION"
        )

    elif strategy_result.signal == "SELL":

        print(
            "Action              : "
            "SELL SIGNAL GENERATED"
        )

        print(
            "Next Stage          : "
            "RISK MANAGER EVALUATION"
        )

    else:

        print(
            "Action              : "
            "NO PAPER TRADE"
        )

        print(
            "Next Stage          : "
            "WAIT FOR NEW MARKET DATA"
        )

    print("\n" + "=" * 70)

    print(
        "GARUDA LIVE STRATEGY DEMO COMPLETED"
    )

    print("=" * 70)


def main():
    """
    Run GARUDA's real-market strategy demo.

    Flow:

    Authenticated Kite Session
        ↓
    Instrument Resolution
        ↓
    Real Intraday Market Data
        ↓
    GARUDA Standard DataFrame
        ↓
    Existing ORB + VWAP Strategy
        ↓
    StrategyResult
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
    # AUTHENTICATED KITE SESSION
    # --------------------------------------------------

    print(
        "\nCreating authenticated Kite session..."
    )

    kite = create_authenticated_session()

    if kite is None:

        print(
            "\nGARUDA Live Strategy Demo Failed."
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
            "\nGARUDA Live Strategy Demo Failed."
        )

        print(
            f"Reason: Instrument token unavailable "
            f"for {symbol}."
        )

        return

    # --------------------------------------------------
    # DEFINE MARKET DATA PERIOD
    # --------------------------------------------------

    current_time = datetime.now()

    from_date = (
        current_time - timedelta(days=5)
    )

    to_date = current_time

    # --------------------------------------------------
    # FETCH REAL MARKET DATA
    # --------------------------------------------------

    print(
        "\nFetching real Kite market data..."
    )

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval=interval,
    )

    # --------------------------------------------------
    # CREATE EXISTING GARUDA STRATEGY
    # --------------------------------------------------

    strategy = ORBVWAPStrategy()

    # --------------------------------------------------
    # EVALUATE REAL MARKET DATA
    # --------------------------------------------------

    print(
        "\nEvaluating real market data..."
    )

    strategy_result = strategy.evaluate(
        symbol=symbol,
        dataframe=dataframe,
    )

    # --------------------------------------------------
    # DISPLAY VISIBLE OUTPUT
    # --------------------------------------------------

    display_strategy_result(
        symbol=symbol,
        dataframe=dataframe,
        strategy_result=strategy_result,
    )


if __name__ == "__main__":

    main()