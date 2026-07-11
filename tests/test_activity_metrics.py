import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from scanner.activity_metrics import calculate_activity_metrics


def main():

    print("=" * 60)
    print("GARUDA ACTIVITY METRICS TEST")
    print("=" * 60)

    sample_data = pd.DataFrame(
        {
            "datetime": [
                "2026-07-01 09:15:00",
                "2026-07-01 09:20:00",
                "2026-07-01 09:25:00",
                "2026-07-01 09:30:00",
                "2026-07-01 09:35:00",
                "2026-07-01 09:40:00",
            ],
            "open": [
                100,
                101,
                102,
                103,
                104,
                105,
            ],
            "high": [
                102,
                103,
                104,
                105,
                106,
                108,
            ],
            "low": [
                99,
                100,
                101,
                102,
                103,
                104,
            ],
            "close": [
                101,
                102,
                103,
                104,
                105,
                107,
            ],
            "volume": [
                1000,
                1200,
                1500,
                1800,
                2500,
                3000,
            ],
        }
    )

    metrics = calculate_activity_metrics(sample_data)

    print("\nCalculated Metrics")
    print("-" * 60)

    for metric_name, metric_value in metrics.items():

        print(
            f"{metric_name:<30} "
            f"{metric_value:.4f}"
        )

    print("-" * 60)

    if metrics is not None:
        print("Activity Metrics Test : SUCCESS")
    else:
        print("Activity Metrics Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()