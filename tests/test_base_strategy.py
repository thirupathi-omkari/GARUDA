import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from strategy.base_strategy import BaseStrategy
from strategy.strategy_result import StrategyResult


class TestStrategy(BaseStrategy):

    @property
    def name(self):

        return "TEST_STRATEGY"

    def evaluate(self, symbol, dataframe):

        return StrategyResult(
            symbol=symbol,
            strategy_name=self.name,
            signal="NO_SIGNAL",
            reason="Base strategy interface test",
        )


def main():

    print("=" * 60)
    print("GARUDA BASE STRATEGY TEST")
    print("=" * 60)

    strategy = TestStrategy()

    result = strategy.evaluate(
        symbol="RELIANCE",
        dataframe=None,
    )

    print(f"\nStrategy Name : {strategy.name}")
    print(f"Symbol        : {result.symbol}")
    print(f"Signal        : {result.signal}")
    print(f"Reason        : {result.reason}")

    print("-" * 60)

    if (
        strategy.name == "TEST_STRATEGY"
        and isinstance(result, StrategyResult)
        and result.signal == "NO_SIGNAL"
    ):
        print("Base Strategy Test : SUCCESS")
    else:
        print("Base Strategy Test : FAILED")

    print("=" * 60)


if __name__ == "__main__":
    main()