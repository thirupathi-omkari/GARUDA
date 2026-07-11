from strategy.base_strategy import BaseStrategy
from strategy.strategy_result import StrategyResult


class ORBStrategy(BaseStrategy):
    """Opening Range Breakout strategy."""

    def __init__(self, opening_candles=3):
        self.opening_candles = opening_candles

    @property
    def name(self):
        return "ORB"

    def evaluate(self, symbol, dataframe):
        """Evaluate an Opening Range Breakout signal."""

        if dataframe is None or dataframe.empty:
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="NO_SIGNAL",
                reason="Market data unavailable",
            )

        if len(dataframe) <= self.opening_candles:
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="NO_SIGNAL",
                reason="Insufficient candles",
            )

        opening_data = dataframe.iloc[
            :self.opening_candles
        ]

        opening_high = opening_data["high"].max()
        opening_low = opening_data["low"].min()

        latest_candle = dataframe.iloc[-1]

        latest_close = latest_candle["close"]

        if latest_close > opening_high:

            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="BUY",
                entry_price=latest_close,
                reason=(
                    "Latest close broke above "
                    "the opening range high"
                ),
            )

        if latest_close < opening_low:

            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="SELL",
                entry_price=latest_close,
                reason=(
                    "Latest close broke below "
                    "the opening range low"
                ),
            )

        return StrategyResult(
            symbol=symbol,
            strategy_name=self.name,
            signal="NO_SIGNAL",
            reason="No opening range breakout",
        )