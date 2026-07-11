import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from strategy.orb_vwap_strategy import ORBVWAPStrategy
from strategy.strategy_engine import evaluate_candidates


def create_data(latest_close):

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
                latest_close,
            ],
            "volume": [
                1000,
                1200,
                1500,
                3000,
            ],
        }
    )


def main():

    print("=" * 60)
    print("GARUDA STRATEGY ENGINE TEST")
    print("=" * 60)

    ranked_candidates = [
        {
            "symbol": "STOCK_A",
            "score": 5.0,
        },
        {
            "symbol": "STOCK_B",
            "score": 4.0,
        },
        {
            "symbol": "STOCK_C",
            "score": 3.0,
        },
    ]

    universe_data = {
        "STOCK_A": create_data(
            latest_close=108
        ),
        "STOCK_B": create_data(
            latest_close=96
        ),
        "STOCK_C": create_data(
            latest_close=102
        ),
    }

    strategy = ORBVWAPStrategy(
        opening_start_time="09:15",
        opening_end_time="09:30",
    )

    strategy_results = evaluate_candidates(
        strategy=strategy,
        ranked_candidates=ranked_candidates,
        universe_data=universe_data,
    )

    print("\nStrategy Results")
    print("-" * 60)

    for result in strategy_results:

        print(
            f"{result.symbol:<15} "
            f"{result.signal:<12} "
            f"{result.reason}"
        )

    print("-" * 60)

    actual_signals = {
        result.symbol: result.signal
        for result in strategy_results
    }

    expected_signals = {
        "STOCK_A": "BUY",
        "STOCK_B": "SELL",
        "STOCK_C": "NO_SIGNAL",
    }

    print("Expected :", expected_signals)
    print("Actual   :", actual_signals)

    if actual_signals == expected_signals:
        print("Strategy Engine Test : SUCCESS")
    else:
        print("Strategy Engine Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()