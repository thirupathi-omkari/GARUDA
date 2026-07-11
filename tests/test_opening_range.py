import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from strategy.session_utils import get_opening_range_data


def main():

    print("=" * 60)
    print("GARUDA OPENING RANGE TEST")
    print("=" * 60)

    sample_data = pd.DataFrame(
        {
            "datetime": [
                "2026-07-01 09:10:00",
                "2026-07-01 09:15:00",
                "2026-07-01 09:20:00",
                "2026-07-01 09:25:00",
                "2026-07-01 09:30:00",
                "2026-07-01 09:35:00",
            ],

            "open": [
                99,
                100,
                101,
                102,
                103,
                104,
            ],

            "high": [
                101,
                102,
                103,
                104,
                105,
                106,
            ],

            "low": [
                98,
                99,
                100,
                101,
                102,
                103,
            ],

            "close": [
                100,
                101,
                102,
                103,
                104,
                105,
            ],

            "volume": [
                500,
                1000,
                1200,
                1500,
                1800,
                2000,
            ],
        }
    )

    opening_data = get_opening_range_data(
        session_data=sample_data,
        start_time="09:15",
        end_time="09:30",
    )

    print("\nOpening Range Candles")
    print("-" * 60)

    print(
        opening_data[
            [
                "datetime",
                "open",
                "high",
                "low",
                "close",
            ]
        ]
    )

    print("-" * 60)

    actual_times = (
        opening_data["datetime"]
        .dt.strftime("%H:%M")
        .tolist()
    )

    expected_times = [
        "09:15",
        "09:20",
        "09:25",
    ]

    print("Expected :", expected_times)
    print("Actual   :", actual_times)

    if actual_times == expected_times:
        print("Opening Range Test : SUCCESS")
    else:
        print("Opening Range Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()