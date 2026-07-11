import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from strategy.orb_vwap_strategy import ORBVWAPStrategy


def main():

    print("=" * 70)
    print("GARUDA STRATEGY DIAGNOSTICS TEST")
    print("=" * 70)

    sample_data = pd.DataFrame(
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
                108,
            ],

            "low": [
                99,
                100,
                101,
                96,
            ],

            "close": [
                101,
                102,
                103,
                96,
            ],

            "volume": [
                1000,
                1200,
                1500,
                3000,
            ],
        }
    )

    strategy = ORBVWAPStrategy(
        opening_start_time="09:15",
        opening_end_time="09:30",
    )

    result = strategy.evaluate(
        symbol="TEST_STOCK",
        dataframe=sample_data,
    )

    diagnostics = result.diagnostics

    print(f"\nSymbol       : {result.symbol}")
    print(f"Signal       : {result.signal}")

    print("-" * 70)

    print(
        f"Opening High : "
        f"{diagnostics['opening_high']:.2f}"
    )

    print(
        f"Opening Low  : "
        f"{diagnostics['opening_low']:.2f}"
    )

    print(
        f"Latest Close : "
        f"{diagnostics['latest_close']:.2f}"
    )

    print(
        f"Latest VWAP  : "
        f"{diagnostics['latest_vwap']:.2f}"
    )

    print("-" * 70)

    print(
        "BUY Breakout      :",
        diagnostics["buy_breakout"],
    )

    print(
        "BUY VWAP Confirm  :",
        diagnostics["buy_vwap_confirmation"],
    )

    print(
        "SELL Breakdown    :",
        diagnostics["sell_breakdown"],
    )

    print(
        "SELL VWAP Confirm :",
        diagnostics["sell_vwap_confirmation"],
    )

    print("-" * 70)

    test_passed = (
        result.signal == "SELL"
        and diagnostics["opening_high"] == 104
        and diagnostics["opening_low"] == 99
        and diagnostics["latest_close"] == 96
        and diagnostics["sell_breakdown"]
        and diagnostics["sell_vwap_confirmation"]
    )

    if test_passed:
        print("Strategy Diagnostics Test : SUCCESS")
    else:
        print("Strategy Diagnostics Test : FAILED")

    print("=" * 70)


if __name__ == "__main__":
    main()