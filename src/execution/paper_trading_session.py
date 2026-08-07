from dataclasses import dataclass

from backtesting.exit_rules import (
    calculate_exit_levels,
)

from backtesting.trade_lifecycle import (
    evaluate_trade_candle,
)

from strategy.strategy_result import (
    StrategyResult,
)

from execution.risk_managed_paper_executor import (
    PaperExecutionResult,
    PaperExitResult,
    RiskManagedPaperExecutor,
)

from execution.trade_csv_journal import (
    TradeCSVJournal,
)

from risk.break_even_engine import (
    calculate_break_even,
)

from risk.trailing_stop_engine import (
    calculate_trailing_stop,
)

from risk.risk_config import (
    RiskConfig,
)

risk_config = RiskConfig()


@dataclass
class PaperTradingSessionResult:
    """
    Final result returned by GARUDA's
    paper trading session engine.
    """

    status: str

    strategy_result: StrategyResult

    reason: str = None

    execution_result: PaperExecutionResult = None

    exit_result: PaperExitResult = None

    stop_loss_price: float = 0.0


@dataclass
class PaperPositionUpdateResult:
    """
    Result returned when GARUDA updates
    the market price of an open paper position.
    """

    status: str

    symbol: str

    position: object

    current_price: float

    unrealized_pnl: float


@dataclass
class PaperMarketCandleResult:
    """
    Result returned when GARUDA processes
    a live market candle for an open
    paper position.
    """

    status: str

    symbol: str

    position: object

    current_price: float

    unrealized_pnl: float

    stop_loss_price: float

    target_price: float

    holding_time: object = None

    pnl_percentage: float = 0.0

    exit_reason: str = None

    exit_result: PaperExitResult = None


class PaperTradingSessionEngine:
    """
    Coordinates GARUDA's paper trading lifecycle.

    Flow:

    Strategy Result
        ↓
    Existing Exit Rules
        ↓
    Stop Loss + Target
        ↓
    Existing Risk Manager
        ↓
    Paper Execution
        ↓
    Open Position
        ↓
    Live Market Candle
        ↓
    Existing evaluate_trade_candle()
        ↓
    Position Remains Open
        OR
    Automatic SL / Target Exit
        ↓
    Account + Equity Curve Update

    Backward compatibility:

    update_position()
        continues to update unrealized P&L only.

    process_market_candle()
        performs automatic SL / target evaluation.
    """

    def __init__(
        self,
        executor: RiskManagedPaperExecutor,
    ):

        self.executor = executor

        self._active_exit_levels = {}

        self.trade_journal = TradeCSVJournal()


    def process_entry(
        self,
        strategy_result: StrategyResult,
        stop_loss_price: float = None,
        market_price: float = None,
        lot_size: int = 1,
        current_exposure: float = 0.0,
        current_open_risk: float = 0.0,
        current_open_positions: int = 0,
        daily_realized_pnl: float = 0.0,
        stop_loss_pct: float = 1.0,
        target_pct: float = 2.0,
    ):
        """
        Process a GARUDA strategy result
        through existing exit rules,
        risk evaluation, and paper entry.

        Exit-level priority:

        Stop Loss:
        1. StrategyResult.stop_loss
        2. Explicit stop_loss_price
        3. Existing calculate_exit_levels()

        Target:
        1. StrategyResult.target_price
        2. Existing calculate_exit_levels()
        """

        # --------------------------------------------------
        # NO SIGNAL
        # --------------------------------------------------

        if strategy_result.signal == "NO_SIGNAL":

            return PaperTradingSessionResult(
                status="NO_TRADE",
                strategy_result=strategy_result,
                stop_loss_price=0.0,
            )

        # --------------------------------------------------
        # VALIDATE SIGNAL
        # --------------------------------------------------

        if strategy_result.signal not in (
            "BUY",
            "SELL",
        ):

            raise ValueError(
                "Strategy signal must be BUY, SELL, or NO_SIGNAL."
            )

        # --------------------------------------------------
        # VALIDATE ENTRY PRICE
        # --------------------------------------------------

        if strategy_result.entry_price is None:

            raise ValueError(
                "Trade signal requires an entry price."
            )

        # --------------------------------------------------
        # MARKET PRICE DEFAULT
        # --------------------------------------------------

        if market_price is None:

            market_price = (
                strategy_result.entry_price
            )

        # --------------------------------------------------
        # CALCULATE EXISTING GARUDA EXIT LEVELS
        # --------------------------------------------------

        calculated_exit_levels = (
            calculate_exit_levels(
                direction=strategy_result.signal,
                entry_price=(
                    strategy_result.entry_price
                ),
                stop_loss_pct=stop_loss_pct,
                target_pct=target_pct,
            )
        )

        calculated_stop_loss = (
            calculated_exit_levels["stop_loss"]
        )

        calculated_target = (
            calculated_exit_levels["target"]
        )

        # --------------------------------------------------
        # RESOLVE STOP LOSS
        # --------------------------------------------------

        if strategy_result.stop_loss is not None:

            resolved_stop_loss = (
                strategy_result.stop_loss
            )

        elif stop_loss_price is not None:

            resolved_stop_loss = (
                stop_loss_price
            )

        else:

            resolved_stop_loss = (
                calculated_stop_loss
            )

        # --------------------------------------------------
        # RESOLVE TARGET
        # --------------------------------------------------

        if strategy_result.target_price is not None:

            resolved_target = (
                strategy_result.target_price
            )

        else:

            resolved_target = (
                calculated_target
            )

        # --------------------------------------------------
        # STORE EXIT LEVELS IN STRATEGY RESULT
        # --------------------------------------------------

        strategy_result.stop_loss = (
            resolved_stop_loss
        )

        strategy_result.target_price = (
            resolved_target
        )

        # --------------------------------------------------
        # RISK-MANAGED PAPER EXECUTION
        # --------------------------------------------------

        execution_result = (
            self.executor.execute_trade(
                symbol=strategy_result.symbol,
                side=strategy_result.signal,
                entry_price=(
                    strategy_result.entry_price
                ),
                stop_loss_price=(
                    resolved_stop_loss
                ),
                market_price=market_price,
                lot_size=lot_size,
                current_exposure=current_exposure,
                current_open_risk=current_open_risk,
                current_open_positions=(
                    current_open_positions
                ),
                daily_realized_pnl=(
                    daily_realized_pnl
                ),
            )
        )

        # --------------------------------------------------
        # RISK REJECTION
        # --------------------------------------------------

        if execution_result.status == "REJECTED":

            return PaperTradingSessionResult(
                status="REJECTED",
                strategy_result=strategy_result,
                reason=execution_result.reason,
                execution_result=execution_result,
                stop_loss_price=execution_result.stop_loss_price,
            )

        # --------------------------------------------------
        # STORE ACTIVE EXIT LEVELS
        # --------------------------------------------------

        normalized_symbol = (
            strategy_result.symbol.upper()
        )

        self._active_exit_levels[
            normalized_symbol
        ] = {

            "direction": strategy_result.signal,

            "entry_price": strategy_result.entry_price,

            "stop_loss_price": resolved_stop_loss,

            "target_price": resolved_target,

            "initial_stop_loss": resolved_stop_loss,

            "initial_risk": abs(
                strategy_result.entry_price
                - resolved_stop_loss
            ),

            "trade_state": "INITIAL",

            "break_even_done": False,

            "trailing_active": False,
        }

        # --------------------------------------------------
        # POSITION REMAINS OPEN
        # --------------------------------------------------

        return PaperTradingSessionResult(
            status="POSITION_OPEN",
            strategy_result=strategy_result,
            reason=execution_result.reason,
            execution_result=execution_result,
            stop_loss_price=execution_result.stop_loss_price,
        )


    def update_position(
        self,
        symbol: str,
        market_price: float,
    ):
        """
        Update an open paper position with
        the latest market price.

        This method preserves the existing
        Module 9 behavior.

        It updates unrealized P&L only.

        It does NOT perform automatic
        stop-loss or target exits.
        """

        position = (
            self.executor
            .position_manager
            .update_market_price(
                symbol=symbol,
                market_price=market_price,
            )
        )

        return PaperPositionUpdateResult(
            status="POSITION_UPDATED",
            symbol=position.symbol,
            position=position,
            current_price=position.current_price,
            unrealized_pnl=position.unrealized_pnl,
        )


    def process_market_candle(
        self,
        symbol: str,
        candle,
        dataframe,
    ):
        """
        Process a live market candle for
        an open paper position.

        Reuses GARUDA Module 7's existing
        evaluate_trade_candle() logic.

        Candle must provide:

        high
        low
        close
        """

        normalized_symbol = symbol.upper()

        # --------------------------------------------------
        # GET ACTIVE EXIT LEVELS
        # --------------------------------------------------

        if (
            normalized_symbol
            not in self._active_exit_levels
        ):

            raise ValueError(
                "Exit levels not found for open position."
            )

        exit_levels = (
            self._active_exit_levels[
                normalized_symbol
            ]
        )

        direction = (
            exit_levels["direction"]
        )

        stop_loss_price = (
            exit_levels["stop_loss_price"]
        )

        target_price = (
            exit_levels["target_price"]
        )

        # --------------------------------------------------
        # GET CURRENT MARKET PRICE
        # --------------------------------------------------

        current_price = candle["close"]

        # --------------------------------------------------
        # UPDATE POSITION MARKET PRICE
        # --------------------------------------------------

        position = (
            self.executor
            .position_manager
            .update_market_price(
                symbol=normalized_symbol,
                market_price=current_price,
            )
        )

        # --------------------------------------------------
        # DYNAMIC STOP MANAGEMENT
        # --------------------------------------------------

        entry_price = (
            exit_levels["entry_price"]
        )

        # NOTE:
        # This will be improved later by storing
        # initial_risk at entry time.
        # For now we'll keep the existing calculation.

        initial_risk = (
            exit_levels["initial_risk"]
        )

        if initial_risk <= 0:

            raise ValueError(
                "Initial risk must be greater than zero."
            )

        # --------------------------------------------------
        # CURRENT PROFIT
        # --------------------------------------------------

        if direction == "BUY":

            current_profit = (
                current_price
                - entry_price
            )

        else:

            current_profit = (
                entry_price
                - current_price
            )

        current_r_multiple = (
            current_profit
            / initial_risk
        )

        # --------------------------------------------------
        # BREAK-EVEN MANAGEMENT
        # --------------------------------------------------

        if (
            risk_config.break_even_enabled
            and not exit_levels["break_even_done"]
            and current_r_multiple >=
            risk_config.break_even_trigger_multiple
        ):

            stop_loss_price = calculate_break_even(
                mode=risk_config.active_break_even_mode,
                signal=direction,
                entry_price=entry_price,
                current_stop=stop_loss_price,
                latest_price=current_price,
                initial_risk=initial_risk,
                trigger_multiple=(
                    risk_config.break_even_trigger_multiple
                ),
            )

            exit_levels["stop_loss_price"] = (
                stop_loss_price
            )

            exit_levels["break_even_done"] = True

            exit_levels["trade_state"] = (
                "BREAK_EVEN"
            )

        # --------------------------------------------------
        # ATR TRAILING STOP
        # --------------------------------------------------

        if (
            risk_config.trailing_stop_enabled
            and current_r_multiple >=
            risk_config.trailing_activation_multiple
        ):

            if not exit_levels["trailing_active"]:

                exit_levels["trailing_active"] = True

                exit_levels["trade_state"] = (
                    "TRAILING"
                )

            stop_loss_price = calculate_trailing_stop(
                mode=risk_config.active_trailing_stop_mode,
                signal=direction,
                current_stop=stop_loss_price,
                candles=dataframe,
            )

            exit_levels["stop_loss_price"] = stop_loss_price

        # --------------------------------------------------
        # UPDATE ACTIVE STOP LOSS
        # --------------------------------------------------

        self._active_exit_levels[
            normalized_symbol
        ]["stop_loss_price"] = stop_loss_price

        # --------------------------------------------------
        # REUSE EXISTING GARUDA EXIT LOGIC
        # --------------------------------------------------

        exit_decision = evaluate_trade_candle(
            direction=direction,
            candle=candle,
            stop_loss=stop_loss_price,
            target=target_price,
        )

        # --------------------------------------------------
        # POSITION REMAINS OPEN
        # --------------------------------------------------

        if exit_decision is None:

            return PaperMarketCandleResult(
                status="POSITION_OPEN",
                symbol=position.symbol,
                position=position,
                current_price=position.current_price,
                unrealized_pnl=position.unrealized_pnl,
                holding_time=position.holding_time,
                pnl_percentage=position.pnl_percentage,
                stop_loss_price=stop_loss_price,
                target_price=target_price,
            )

        # --------------------------------------------------
        # AUTOMATIC PAPER EXIT
        # --------------------------------------------------

        exit_result = self.process_exit(
            symbol=normalized_symbol,
            exit_price=exit_decision["exit_price"],
            exit_reason=exit_decision["exit_reason"],
        )   

        return PaperMarketCandleResult(
            status="POSITION_CLOSED",
            symbol=position.symbol,
            position=position,
            current_price=current_price,
            unrealized_pnl=0.0,
            holding_time=position.holding_time,
            pnl_percentage=position.pnl_percentage,
            stop_loss_price=stop_loss_price,
            target_price=target_price,
            exit_reason=(
                exit_decision["exit_reason"]
            ),
            exit_result=exit_result,
        )


    def process_exit(
        self,
        symbol: str,
        exit_price: float,
        exit_reason: str,
    ):
        """
        Close an open paper position.

        Realized P&L updates GARUDA's
        TradingAccount and EquityCurve through
        RiskManagedPaperExecutor.
        """

        normalized_symbol = symbol.upper()

        exit_result = self.executor.close_trade(
            symbol=normalized_symbol,
            exit_price=exit_price,
        )

        exit_levels = self.get_exit_levels(
            normalized_symbol
        )

        position = exit_result.position

        self.trade_journal.record_trade(
            symbol=position.symbol,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            exit_price=exit_result.exit_price,
            stop_loss=exit_levels["stop_loss_price"],
            target=exit_levels["target_price"],
            holding_time=position.holding_time,
            exit_reason=exit_reason,
            realized_pnl=exit_result.realized_pnl,
        )

        # --------------------------------------------------
        # REMOVE ACTIVE EXIT LEVELS
        # --------------------------------------------------

        self._active_exit_levels.pop(
            normalized_symbol,
            None,
        )

        return exit_result

    def square_off_all_positions(
        self,
    ):
        """
        Close every remaining open paper position
        at the latest available market price.
        """

        closed_positions = []

        positions = list(
            self.executor
            .position_manager
            .positions
        )

        for position in positions:

            exit_result = self.process_exit(
                symbol=position.symbol,
                exit_price=position.current_price,
                exit_reason="MARKET_CLOSE",
            )

            closed_positions.append(exit_result)

        return closed_positions
    


    def get_exit_levels(
        self,
        symbol: str,
    ):
        """
        Return active stop-loss and target
        levels for an open paper position.
        """

        normalized_symbol = symbol.upper()

        if (
            normalized_symbol
            not in self._active_exit_levels
        ):

            raise ValueError(
                "Exit levels not found for open position."
            )

        return dict(
            self._active_exit_levels[
                normalized_symbol
            ]
        )


    def run_session(
        self,
        strategy_result: StrategyResult,
        stop_loss_price: float,
        market_price: float,
        exit_price: float,
        lot_size: int,
        current_exposure: float,
        current_open_risk: float,
        current_open_positions: int,
        daily_realized_pnl: float,
    ):
        """
        Run one complete GARUDA paper session.

        Retained for backward compatibility.
        """

        entry_result = self.process_entry(
            strategy_result=strategy_result,
            stop_loss_price=stop_loss_price,
            market_price=market_price,
            lot_size=lot_size,
            current_exposure=current_exposure,
            current_open_risk=current_open_risk,
            current_open_positions=(
                current_open_positions
            ),
            daily_realized_pnl=(
                daily_realized_pnl
            ),
        )

        if entry_result.status in (
            "NO_TRADE",
            "REJECTED",
        ):

            return entry_result

        exit_result = self.process_exit(
            symbol=strategy_result.symbol,
            exit_price=exit_price,
            exit_reason="MANUAL",
        )

        return PaperTradingSessionResult(
            status="COMPLETED",
            strategy_result=strategy_result,
            execution_result=(
                entry_result.execution_result
            ),
            exit_result=exit_result,
            stop_loss_price=(
                entry_result.execution_result.stop_loss_price
            ),
        )