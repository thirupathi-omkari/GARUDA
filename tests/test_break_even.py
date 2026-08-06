import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.break_even.risk_reward_break_even import (
    calculate_break_even_stop,
)


def main():

    print("=" * 60)
    print("GARUDA BREAK-EVEN TEST")
    print("=" * 60)

    # BUY

    buy_stop = calculate_break_even_stop(
        signal="BUY",
        entry_price=100,
        current_stop=95,
        latest_price=105,
        initial_risk=5,
        trigger_multiple=1,
    )

    print(f"BUY Break-even : {buy_stop:.2f}")

    assert buy_stop == 100

    # SELL

    sell_stop = calculate_break_even_stop(
        signal="SELL",
        entry_price=100,
        current_stop=105,
        latest_price=95,
        initial_risk=5,
        trigger_multiple=1,
    )

    print(f"SELL Break-even: {sell_stop:.2f}")

    assert sell_stop == 100

    print("-" * 60)
    print("Break-even Tests : SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()