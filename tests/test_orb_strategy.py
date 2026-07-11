import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from strategy.orb_strategy import ORBStrategy


def create_data(latest_close):
    """Create controlled market data for ORB testing."""

    return pd.DataFrame(
        {
            "datetime": [
                "2026-07-01 09:15:00",
                "2026-07-01 09:20:00",
                "2026-07-01 09:25:00",
                "2026-07-01 09:30:00",
            ],
            "open": [
                100,
                101,
                102,
                103,
            ],
            "high": [
                102,
                103,
                104,
                105,
            ],
            "low": [
                99,
                100,
                101,
                98,
            ],
            "close": [
                101,
                102,
                103,
                latest_close,
            ],
            "volume": [
                1000,
                1200,
                1500,
                1800,
            ],
        }
    )


def main():

    print("=" * 60)
    print("GARUDA ORB STRATEGY OUTCOME TEST")
    print("=" * 60)

    strategy = ORBStrategy(opening_candles=3)

    # BUY TEST
    buy_data = create_data(
        latest_close=107
    )

    buy_result = strategy.evaluate(
        symbol="BUY_STOCK",
        dataframe=buy_data,
    )

    print(f"\nBUY Test       : {buy_result.signal}")

    # SELL TEST
    sell_data = create_data(
        latest_close=97
    )

    sell_result = strategy.evaluate(
        symbol="SELL_STOCK",
        dataframe=sell_data,
    )

    print(f"SELL Test      : {sell_result.signal}")

    # NO SIGNAL TEST
    no_signal_data = create_data(
        latest_close=102
    )

    no_signal_result = strategy.evaluate(
        symbol="NO_SIGNAL_STOCK",
        dataframe=no_signal_data,
    )

    print(
        f"NO SIGNAL Test : "
        f"{no_signal_result.signal}"
    )

    # EMPTY DATA TEST
    empty_data = pd.DataFrame()

    empty_result = strategy.evaluate(
        symbol="EMPTY_STOCK",
        dataframe=empty_data,
    )

    print(f"Empty Data     : {empty_result.signal}")

    # INSUFFICIENT DATA TEST
    insufficient_data = create_data(
        latest_close=107
    ).iloc[:3]

    insufficient_result = strategy.evaluate(
        symbol="SHORT_DATA",
        dataframe=insufficient_data,
    )

    print(
        f"Insufficient   : "
        f"{insufficient_result.signal}"
    )

    print("-" * 60)

    all_tests_passed = (
        buy_result.signal == "BUY"
        and sell_result.signal == "SELL"
        and no_signal_result.signal == "NO_SIGNAL"
        and empty_result.signal == "NO_SIGNAL"
        and insufficient_result.signal == "NO_SIGNAL"
    )

    if all_tests_passed:
        print("ORB Outcome Tests : SUCCESS")
    else:
        print("ORB Outcome Tests : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()