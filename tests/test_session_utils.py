import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from strategy.session_utils import get_latest_trading_session


def main():

    print("=" * 60)
    print("GARUDA TRADING SESSION TEST")
    print("=" * 60)

    sample_data = pd.DataFrame(
        {
            "datetime": [
                "2026-07-01 09:15:00",
                "2026-07-01 09:20:00",
                "2026-07-01 09:25:00",

                "2026-07-02 09:15:00",
                "2026-07-02 09:20:00",
                "2026-07-02 09:25:00",
                "2026-07-02 09:30:00",
            ],

            "open": [
                100,
                101,
                102,
                200,
                201,
                202,
                203,
            ],

            "high": [
                102,
                103,
                104,
                202,
                203,
                204,
                205,
            ],

            "low": [
                99,
                100,
                101,
                199,
                200,
                201,
                202,
            ],

            "close": [
                101,
                102,
                103,
                201,
                202,
                203,
                204,
            ],

            "volume": [
                1000,
                1200,
                1500,
                2000,
                2200,
                2500,
                3000,
            ],
        }
    )

    session_data = get_latest_trading_session(
        sample_data
    )

    print("\nLatest Session Data")
    print("-" * 60)

    print(session_data)

    print("-" * 60)

    session_dates = (
        session_data["datetime"]
        .dt.date
        .unique()
    )

    test_passed = (
        len(session_data) == 4
        and len(session_dates) == 1
        and str(session_dates[0]) == "2026-07-02"
    )

    if test_passed:
        print("Trading Session Test : SUCCESS")
    else:
        print("Trading Session Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()