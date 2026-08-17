"""GARUDA Strategy #2: moving-average crossover."""

from strategy.base_strategy import BaseStrategy
from strategy.strategy_result import StrategyResult
import pandas as pd
from indicators.moving_average import add_moving_averages


class MovingAverageStrategy(BaseStrategy):
    """Fast/slow MA crossover strategy.

    The signal is generated only on the crossover candle.
    Existing execution/backtesting code is responsible for next-candle entry.
    """

    def __init__(self, fast_period=9, slow_period=21, ma_type="EMA"):
        if fast_period <= 0 or slow_period <= 0:
            raise ValueError("MA periods must be positive")
        if fast_period >= slow_period:
            raise ValueError("fast_period must be less than slow_period")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type.upper()

    @property
    def name(self):
        return "MA"

    def evaluate(self, symbol, dataframe):
        if dataframe is None or dataframe.empty:
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="NO_SIGNAL",
                reason="Market data unavailable",
            )

        if len(dataframe) < self.slow_period + 1:
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="NO_SIGNAL",
                reason="Insufficient candles for MA crossover",
            )

        data = add_moving_averages(
            dataframe,
            fast_period=self.fast_period,
            slow_period=self.slow_period,
            ma_type=self.ma_type,
        )

        previous = data.iloc[-2]
        latest = data.iloc[-1]

        if any(
            pd.isna(value)
            for value in (
                previous["fast_ma"],
                previous["slow_ma"],
                latest["fast_ma"],
                latest["slow_ma"],
            )
        ):
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="NO_SIGNAL",
                reason="MA warm-up incomplete",
            )

        buy_cross = (
            previous["fast_ma"] <= previous["slow_ma"]
            and latest["fast_ma"] > latest["slow_ma"]
        )
        sell_cross = (
            previous["fast_ma"] >= previous["slow_ma"]
            and latest["fast_ma"] < latest["slow_ma"]
        )

        diagnostics = {
            "ma_type": self.ma_type,
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "previous_fast_ma": previous["fast_ma"],
            "previous_slow_ma": previous["slow_ma"],
            "latest_fast_ma": latest["fast_ma"],
            "latest_slow_ma": latest["slow_ma"],
            "latest_close": latest["close"],
            "crossover_time": latest["datetime"],
        }

        if buy_cross:
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="BUY",
                entry_price=latest["close"],
                reason="Fast MA crossed above slow MA",
                diagnostics=diagnostics,
            )

        if sell_cross:
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="SELL",
                entry_price=latest["close"],
                reason="Fast MA crossed below slow MA",
                diagnostics=diagnostics,
            )

        return StrategyResult(
            symbol=symbol,
            strategy_name=self.name,
            signal="NO_SIGNAL",
            reason="No MA crossover",
            diagnostics=diagnostics,
        )
