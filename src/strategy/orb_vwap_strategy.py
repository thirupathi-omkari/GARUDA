from strategy.base_strategy import BaseStrategy
from strategy.strategy_result import StrategyResult
from strategy.session_utils import (
    get_latest_trading_session,
    get_opening_range_data,
)
from indicators.vwap import calculate_vwap

from risk.stop_loss_engine import (
    calculate_stop_loss,
)

from risk.target_engine import (
    calculate_target,
)

from risk.risk_config import RiskConfig

risk_config = RiskConfig()

class ORBVWAPStrategy(BaseStrategy):
    """Opening Range Breakout with VWAP confirmation."""

    def __init__(
        self,
        opening_start_time="09:15",
        opening_end_time="09:30",
    ):
        self.opening_start_time = opening_start_time
        self.opening_end_time = opening_end_time

    @property
    def name(self):
        return "ORB_VWAP"

    def evaluate(self, symbol, dataframe):
        """Evaluate time-aware ORB breakout with VWAP confirmation."""

        if dataframe is None or dataframe.empty:
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="NO_SIGNAL",
                reason="Market data unavailable",
            )

        # Step 1: Extract latest trading session
        session_data = get_latest_trading_session(
            dataframe
        )

        if session_data is None or session_data.empty:
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="NO_SIGNAL",
                reason="Trading session unavailable",
            )

        # Step 2: Extract opening-range candles by time
        opening_data = get_opening_range_data(
            session_data=session_data,
            start_time=self.opening_start_time,
            end_time=self.opening_end_time,
        )

        if opening_data is None or opening_data.empty:
            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="NO_SIGNAL",
                reason="Opening range data unavailable",
            )

        # Step 3: Calculate VWAP using latest session data
        data_with_vwap = calculate_vwap(
            session_data
        )

        # Step 4: Calculate opening-range boundaries
        opening_high = opening_data["high"].max()
        opening_low = opening_data["low"].min()

        # Step 5: Get latest candle
        latest_candle = data_with_vwap.iloc[-1]

        latest_close = latest_candle["close"]
        latest_vwap = latest_candle["vwap"]

        # Step 6: Evaluate individual conditions
        buy_breakout = latest_close > opening_high

        buy_vwap_confirmation = (
            latest_close > latest_vwap
        )

        sell_breakdown = latest_close < opening_low

        sell_vwap_confirmation = (
            latest_close < latest_vwap
        )

        # Step 7: Store decision evidence
        diagnostics = {
            "opening_high": opening_high,
            "opening_low": opening_low,
            "latest_close": latest_close,
            "latest_vwap": latest_vwap,
            "buy_breakout": buy_breakout,
            "buy_vwap_confirmation": (
                buy_vwap_confirmation
            ),
            "sell_breakdown": sell_breakdown,
            "sell_vwap_confirmation": (
                sell_vwap_confirmation
            ),
        }

        # Step 8: BUY decision
        if (
            buy_breakout
            and buy_vwap_confirmation
        ):

            stop_loss = calculate_stop_loss(
                mode=risk_config.active_stop_loss_mode,
                signal="BUY",
                entry_price=latest_close,
                opening_high=opening_high,
                opening_low=opening_low,
                candles=dataframe,
            )

            target = calculate_target(
                mode=risk_config.active_target_mode,
                signal="BUY",
                entry_price=latest_close,
                stop_loss=stop_loss,
                candles=dataframe,
                risk_reward_ratio=(
                    risk_config.risk_reward_ratio
                ),
            )

            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="BUY",
                entry_price=latest_close,
                stop_loss=stop_loss,
                target_price=target,
                reason=(
                    "Time-aware ORB breakout "
                    "confirmed above VWAP"
                ),
                diagnostics=diagnostics,
            )

        # Step 9: SELL decision
        if (
            sell_breakdown
            and sell_vwap_confirmation
        ):

            stop_loss = calculate_stop_loss(
                mode=risk_config.active_stop_loss_mode,
                signal="SELL",
                entry_price=latest_close,
                opening_high=opening_high,
                opening_low=opening_low,
                candles=dataframe,
            )

            target = calculate_target(
                mode=risk_config.active_target_mode,
                signal="SELL",
                entry_price=latest_close,
                stop_loss=stop_loss,
                candles=dataframe,
                risk_reward_ratio=(
                    risk_config.risk_reward_ratio
                ),
            )

            return StrategyResult(
                symbol=symbol,
                strategy_name=self.name,
                signal="SELL",
                entry_price=latest_close,
                stop_loss=stop_loss,
                target_price=target,
                reason=(
                    "Time-aware ORB breakdown "
                    "confirmed below VWAP"
                ),
                diagnostics=diagnostics,
            )

        # Step 10: NO SIGNAL decision
        return StrategyResult(
            symbol=symbol,
            strategy_name=self.name,
            signal="NO_SIGNAL",
            reason=(
                "Time-aware ORB and VWAP "
                "conditions not confirmed"
            ),
            diagnostics=diagnostics,
        )