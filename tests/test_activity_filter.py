import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from scanner.activity_filter import filter_active_instruments


def main():

    print("=" * 60)
    print("GARUDA ACTIVITY FILTER TEST")
    print("=" * 60)

    sample_metrics = {

        "STOCK_A": {
            "volume_ratio": 1.50,
            "volatility_pct": 0.10,
        },

        "STOCK_B": {
            "volume_ratio": 0.80,
            "volatility_pct": 0.12,
        },

        "STOCK_C": {
            "volume_ratio": 1.30,
            "volatility_pct": 0.03,
        },

        "STOCK_D": {
            "volume_ratio": 1.20,
            "volatility_pct": 0.08,
        },
    }

    active_instruments = filter_active_instruments(
        universe_metrics=sample_metrics,
        min_volume_ratio=1.0,
        min_volatility_pct=0.05,
    )

    expected_symbols = {
        "STOCK_A",
        "STOCK_D",
    }

    actual_symbols = set(
        active_instruments.keys()
    )

    print("\nExpected :", expected_symbols)
    print("Actual   :", actual_symbols)

    print("-" * 60)

    if actual_symbols == expected_symbols:
        print("Activity Filter Test : SUCCESS")
    else:
        print("Activity Filter Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()