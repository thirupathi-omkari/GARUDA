import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


import pandas as pd

from risk.trailing.atr_trailing import (
    calculate_atr_trailing_stop,
)


def create_test_dataframe():

    return pd.DataFrame(
        {
            "high": [101, 102, 103, 104, 105, 106, 107],
            "low": [99, 100, 101, 102, 103, 104, 105],
            "close": [100, 101, 102, 103, 104, 105, 106],
        }
    )


def main():

    print("=" * 60)
    print("GARUDA ATR TRAILING STOP TEST")
    print("=" * 60)

    dataframe = create_test_dataframe()

    # BUY TEST

    buy_stop = calculate_atr_trailing_stop(
        signal="BUY",
        current_stop=100.0,
        candles=dataframe,
        atr_multiplier=2.0,
    )

    print(f"BUY Trailing Stop  : {buy_stop:.2f}")

    assert buy_stop >= 100.0

    # SELL TEST

    sell_stop = calculate_atr_trailing_stop(
        signal="SELL",
        current_stop=110.0,
        candles=dataframe,
        atr_multiplier=2.0,
    )

    print(f"SELL Trailing Stop : {sell_stop:.2f}")

    assert sell_stop <= 110.0

    print("-" * 60)
    print("ATR Trailing Tests : SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()