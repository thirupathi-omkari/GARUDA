import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from strategy.strategy_result import StrategyResult


def main():

    print("=" * 60)
    print("GARUDA STRATEGY RESULT TEST")
    print("=" * 60)

    result = StrategyResult(
        symbol="RELIANCE",
        strategy_name="TEST_STRATEGY",
        signal="BUY",
        entry_price=1500.00,
        stop_loss=1485.00,
        target_price=1530.00,
        reason="Test strategy signal",
    )

    print(f"\nSymbol        : {result.symbol}")
    print(f"Strategy      : {result.strategy_name}")
    print(f"Signal        : {result.signal}")
    print(f"Entry Price   : {result.entry_price}")
    print(f"Stop Loss     : {result.stop_loss}")
    print(f"Target Price  : {result.target_price}")
    print(f"Reason        : {result.reason}")

    print("-" * 60)

    if (
        result.symbol == "RELIANCE"
        and result.strategy_name == "TEST_STRATEGY"
        and result.signal == "BUY"
        and result.entry_price == 1500.00
    ):
        print("Strategy Result Test : SUCCESS")
    else:
        print("Strategy Result Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()