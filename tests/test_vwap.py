import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from indicators.vwap import calculate_vwap


def main():

    print("=" * 60)
    print("GARUDA VWAP ACCURACY TEST")
    print("=" * 60)

    sample_data = pd.DataFrame(
        {
            "datetime": [
                "2026-07-01 09:15:00",
                "2026-07-01 09:20:00",
                "2026-07-01 09:25:00",
            ],
            "open": [
                100,
                102,
                104,
            ],
            "high": [
                102,
                104,
                106,
            ],
            "low": [
                98,
                100,
                102,
            ],
            "close": [
                101,
                103,
                105,
            ],
            "volume": [
                1000,
                2000,
                3000,
            ],
        }
    )

    result = calculate_vwap(sample_data)

    print("\nCalculated VWAP")
    print("-" * 60)

    print(
        result[
            [
                "datetime",
                "close",
                "volume",
                "vwap",
            ]
        ]
    )

    print("-" * 60)

    expected_vwap = [
        100.3333333333,
        101.6666666667,
        103.0,
    ]

    tolerance = 0.0001

    accuracy_passed = True

    for index, expected_value in enumerate(
        expected_vwap
    ):

        actual_value = result["vwap"].iloc[index]

        difference = abs(
            actual_value - expected_value
        )

        print(
            f"Row {index + 1}: "
            f"Expected = {expected_value:.4f}, "
            f"Actual = {actual_value:.4f}, "
            f"Difference = {difference:.6f}"
        )

        if difference > tolerance:
            accuracy_passed = False

    print("-" * 60)

    if accuracy_passed:
        print("VWAP Accuracy Test : SUCCESS")
    else:
        print("VWAP Accuracy Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()