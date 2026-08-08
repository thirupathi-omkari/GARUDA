from dataclasses import dataclass, field
from datetime import datetime, time


@dataclass
class SymbolTradingState:
    """
    Runtime state maintained by GARUDA
    for one paper-trading symbol.
    """

    symbol: str

    instrument_token: int

    last_processed_candle_time: object = None

    last_entry_candle_time: object = None

    position_open: bool = False

    processed_candle_count: int = 0

    generated_signal_count: int = 0

    executed_trade_count: int = 0

    rejected_trade_count: int = 0

    closed_trade_count: int = 0


@dataclass
class LivePaperTradingRunnerState:
    """
    Overall runtime state maintained by
    GARUDA's live paper-trading runner.
    """

    symbols: dict = field(
        default_factory=dict
    )

    started_at: object = None

    stopped_at: object = None

    running: bool = False


@dataclass
class LivePaperTradingCycleResult:
    """
    Result returned after GARUDA processes
    one live paper-trading symbol cycle.
    """

    status: str

    symbol: str

    candle_time: object = None

    strategy_result: object = None

    session_result: object = None

    market_candle_result: object = None

    reason: str = None


class LivePaperTradingRunner:
    """
    GARUDA live paper-trading runner.

    Responsibilities:

    - Maintain multi-symbol runtime state.
    - Detect new market candles.
    - Prevent duplicate candle processing.
    - Prevent duplicate entries.
    - Track open and closed positions.
    - Track executed and rejected trades.
    - Enforce trading-session timing.
    - Coordinate one complete symbol cycle.
    - Provide visible runtime summaries.
    """

    def __init__(
        self,
        market_open_time=time(9, 15),
        new_entry_cutoff_time=time(15, 0),
        market_close_time=time(15, 30),
    ):
        """
        Create GARUDA live paper-trading runner.
        """

        self.market_open_time = (
            market_open_time
        )

        self.new_entry_cutoff_time = (
            new_entry_cutoff_time
        )

        self.market_close_time = (
            market_close_time
        )

        self.state = (
            LivePaperTradingRunnerState()
        )


    # --------------------------------------------------
    # SYMBOL REGISTRATION
    # --------------------------------------------------

    def register_symbol(
        self,
        symbol,
        instrument_token,
    ):
        """
        Register one symbol with GARUDA's
        live paper-trading runner.
        """

        if not symbol:

            raise ValueError(
                "Symbol is required."
            )

        if instrument_token is None:

            raise ValueError(
                "Instrument token is required."
            )

        normalized_symbol = (
            symbol.upper()
        )

        if normalized_symbol in self.state.symbols:

            raise ValueError(
                f"Symbol already registered: "
                f"{normalized_symbol}"
            )

        symbol_state = SymbolTradingState(
            symbol=normalized_symbol,
            instrument_token=instrument_token,
        )

        self.state.symbols[
            normalized_symbol
        ] = symbol_state

        return symbol_state


    def get_symbol_state(
        self,
        symbol,
    ):
        """
        Return runtime state for one symbol.
        """

        normalized_symbol = (
            symbol.upper()
        )

        if normalized_symbol not in self.state.symbols:

            raise ValueError(
                f"Symbol not registered: "
                f"{normalized_symbol}"
            )

        return self.state.symbols[
            normalized_symbol
        ]


    # --------------------------------------------------
    # RUNNER LIFECYCLE
    # --------------------------------------------------

    def start(
        self,
        started_at=None,
    ):
        """
        Start GARUDA live paper-trading runner.
        """

        if self.state.running:

            raise ValueError(
                "GARUDA live paper-trading runner "
                "is already running."
            )

        if started_at is None:

            started_at = datetime.now()

        self.state.started_at = started_at

        self.state.stopped_at = None

        self.state.running = True

        return self.state


    def stop(
        self,
        stopped_at=None,
    ):
        """
        Stop GARUDA live paper-trading runner.
        """

        if not self.state.running:

            raise ValueError(
                "GARUDA live paper-trading runner "
                "is not running."
            )

        if stopped_at is None:

            stopped_at = datetime.now()

        self.state.stopped_at = stopped_at

        self.state.running = False

        return self.state


    # --------------------------------------------------
    # MARKET TIMING
    # --------------------------------------------------

    def is_market_session_active(
        self,
        current_datetime,
    ):
        """
        Return True when current time is within
        GARUDA's configured market session.
        """

        current_time = (
            current_datetime.time()
        )

        return (
            self.market_open_time
            <= current_time
            <= self.market_close_time
        )


    def is_new_entry_allowed_by_time(
        self,
        current_datetime,
    ):
        """
        Return True when GARUDA may create
        a new paper position.
        """

        current_time = (
            current_datetime.time()
        )

        return (
            self.market_open_time
            <= current_time
            <= self.new_entry_cutoff_time
        )


    # --------------------------------------------------
    # NEW CANDLE DETECTION
    # --------------------------------------------------

    def is_new_candle(
        self,
        symbol,
        candle_time,
    ):
        """
        Return True only when candle_time has
        not already been processed.
        """

        symbol_state = (
            self.get_symbol_state(
                symbol
            )
        )

        if candle_time is None:

            raise ValueError(
                "Candle time is required."
            )

        if (
            symbol_state.last_processed_candle_time
            is None
        ):

            return True

        return (
            candle_time
            > symbol_state.last_processed_candle_time
        )


    def mark_candle_processed(
        self,
        symbol,
        candle_time,
    ):
        """
        Mark one candle as processed.
        """

        symbol_state = (
            self.get_symbol_state(
                symbol
            )
        )

        if candle_time is None:

            raise ValueError(
                "Candle time is required."
            )

        if not self.is_new_candle(
            symbol=symbol,
            candle_time=candle_time,
        ):

            raise ValueError(
                "Candle has already been processed."
            )

        symbol_state.last_processed_candle_time = (
            candle_time
        )

        symbol_state.processed_candle_count += 1

        return symbol_state


    # --------------------------------------------------
    # ENTRY CONTROL
    # --------------------------------------------------

    def can_create_entry(
        self,
        symbol,
        candle_time,
    ):
        """
        Return True when GARUDA may create
        a new entry for the symbol.
        """

        symbol_state = (
            self.get_symbol_state(
                symbol
            )
        )

        if symbol_state.position_open:

            return False

        if (
            symbol_state.last_entry_candle_time
            == candle_time
        ):

            return False

        return True


    def record_signal(
        self,
        symbol,
    ):
        """
        Record one actionable GARUDA signal.
        """

        symbol_state = (
            self.get_symbol_state(
                symbol
            )
        )

        symbol_state.generated_signal_count += 1

        return symbol_state


    def record_execution(
        self,
        symbol,
        candle_time,
    ):
        """
        Record successful paper execution.
        """

        symbol_state = (
            self.get_symbol_state(
                symbol
            )
        )

        if symbol_state.position_open:

            raise ValueError(
                f"Position already open: "
                f"{symbol_state.symbol}"
            )

        symbol_state.position_open = True

        symbol_state.last_entry_candle_time = (
            candle_time
        )

        symbol_state.executed_trade_count += 1

        return symbol_state


    def record_rejection(
        self,
        symbol,
    ):
        """
        Record one RiskManager rejection.
        """

        symbol_state = (
            self.get_symbol_state(
                symbol
            )
        )

        symbol_state.rejected_trade_count += 1

        return symbol_state


    # --------------------------------------------------
    # POSITION CONTROL
    # --------------------------------------------------

    def record_position_closed(
        self,
        symbol,
    ):
        """
        Record successful paper-position exit.
        """

        symbol_state = (
            self.get_symbol_state(
                symbol
            )
        )

        if not symbol_state.position_open:

            raise ValueError(
                f"No open position: "
                f"{symbol_state.symbol}"
            )

        symbol_state.position_open = False

        symbol_state.closed_trade_count += 1

        return symbol_state


    def replay_missed_candles(
        self,
        symbol,
        dataframe,
        session_engine,
    ):
        """
        Replay candles that were not processed while
        GARUDA was stopped.

        Candles are processed chronologically so that
        SL, target, break-even and trailing-stop state
        evolve exactly as they would during continuous
        operation.
        """

        normalized_symbol = symbol.upper()

        symbol_state = self.get_symbol_state(
            normalized_symbol
        )

        if dataframe is None or dataframe.empty:

            return None

        # --------------------------------------------------
        # SELECT UNPROCESSED CANDLES
        # --------------------------------------------------

        if (
            symbol_state.last_processed_candle_time
            is None
        ):

            missed_candles = dataframe.copy()

        else:

            missed_candles = dataframe[
                dataframe["datetime"]
                > symbol_state.last_processed_candle_time
            ].copy()

        missed_candles = (
            missed_candles
            .sort_values("datetime")
            .reset_index(drop=True)
        )

        if missed_candles.empty:

            return None

        # --------------------------------------------------
        # REPLAY CHRONOLOGICALLY
        # --------------------------------------------------

        for _, candle in missed_candles.iterrows():

            candle_time = candle["datetime"]

            # ------------------------------------------------
            # OPEN POSITION
            # ------------------------------------------------

            if symbol_state.position_open:

                candle_dataframe = dataframe[
                    dataframe["datetime"]
                    <= candle_time
                ].copy()

                market_candle_result = (
                    session_engine.process_market_candle(
                        symbol=normalized_symbol,
                        candle=candle,
                        dataframe=candle_dataframe,
                    )
                )

                # --------------------------------------------
                # EXIT DURING OFFLINE PERIOD
                # --------------------------------------------

                if (
                    market_candle_result.status
                    == "POSITION_CLOSED"
                ):

                    self.record_position_closed(
                        normalized_symbol
                    )

                    self.mark_candle_processed(
                        symbol=normalized_symbol,
                        candle_time=candle_time,
                    )

                    return market_candle_result

            # ------------------------------------------------
            # MARK THIS CANDLE AS PROCESSED
            # ------------------------------------------------

            self.mark_candle_processed(
                symbol=normalized_symbol,
                candle_time=candle_time,
            )

        return None


    # --------------------------------------------------
    # SINGLE-CYCLE ORCHESTRATION
    # --------------------------------------------------

    def process_symbol_cycle(
        self,
        symbol,
        dataframe,
        strategy,
        session_engine,
        lot_size=1,
        current_exposure=0.0,
        current_open_risk=0.0,
        current_open_positions=0,
        daily_realized_pnl=0.0,
        stop_loss_pct=1.0,
        target_pct=2.0,
    ):
        """
        Process one complete GARUDA live
        paper-trading cycle for one symbol.

        Flow:

        Validate Runner
            ↓
        Validate Market Data
            ↓
        Detect Latest Candle
            ↓
        Market Session Check
            ↓
        Duplicate Candle Check
            ↓
        Mark Candle Processed
            ↓
        Existing Position?
            ↓
        Automatic Exit Evaluation
            OR
        Strategy Evaluation
            ↓
        Risk-Managed Paper Entry
        """

        normalized_symbol = (
            symbol.upper()
        )

        # --------------------------------------------------
        # RUNNER MUST BE ACTIVE
        # --------------------------------------------------

        if not self.state.running:

            return LivePaperTradingCycleResult(
                status="RUNNER_NOT_ACTIVE",
                symbol=normalized_symbol,
                reason=(
                    "GARUDA live paper-trading "
                    "runner is not active."
                ),
            )

        # --------------------------------------------------
        # VALIDATE REGISTERED SYMBOL
        # --------------------------------------------------

        symbol_state = self.get_symbol_state(
            normalized_symbol
        )

        # --------------------------------------------------
        # VALIDATE MARKET DATA
        # --------------------------------------------------

        if dataframe is None or dataframe.empty:

            return LivePaperTradingCycleResult(
                status="NO_MARKET_DATA",
                symbol=normalized_symbol,
                reason="Market data unavailable.",
            )

        # --------------------------------------------------
        # GET LATEST CANDLE
        # --------------------------------------------------

        latest_candle = dataframe.iloc[-1]

        candle_time = latest_candle["datetime"]

        # --------------------------------------------------
        # MARKET SESSION CHECK
        # --------------------------------------------------

        if not self.is_market_session_active(
            candle_time
        ):

            return LivePaperTradingCycleResult(
                status="MARKET_SESSION_INACTIVE",
                symbol=normalized_symbol,
                candle_time=candle_time,
                reason=(
                    "Latest candle is outside "
                    "the configured market session."
                ),
            )

        # --------------------------------------------------
        # DUPLICATE CANDLE CHECK
        # --------------------------------------------------

        if not self.is_new_candle(
            symbol=normalized_symbol,
            candle_time=candle_time,
        ):

            return LivePaperTradingCycleResult(
                status="DUPLICATE_CANDLE",
                symbol=normalized_symbol,
                candle_time=candle_time,
                reason=(
                    "Latest candle was already processed."
                ),
            )

        # --------------------------------------------------
        # MARK CANDLE PROCESSED
        # --------------------------------------------------

        self.mark_candle_processed(
            symbol=normalized_symbol,
            candle_time=candle_time,
        )

        # --------------------------------------------------
        # EXISTING OPEN POSITION
        # --------------------------------------------------

        if symbol_state.position_open:

            market_candle_result = (
                session_engine.process_market_candle(
                    symbol=normalized_symbol,
                    candle=latest_candle,
                    dataframe=dataframe,
                )
            )

            if (
                market_candle_result.status
                == "POSITION_CLOSED"
            ):

                self.record_position_closed(
                    normalized_symbol
                )

            return LivePaperTradingCycleResult(
                status=market_candle_result.status,
                symbol=normalized_symbol,
                candle_time=candle_time,
                market_candle_result=market_candle_result,
                reason=(
                    market_candle_result.reason
                    if hasattr(market_candle_result, "reason")
                    else None
                ),
            )

        # --------------------------------------------------
        # NEW ENTRY TIME CHECK
        # --------------------------------------------------

        if not self.is_new_entry_allowed_by_time(
            candle_time
        ):

            return LivePaperTradingCycleResult(
                status="ENTRY_TIME_CLOSED",
                symbol=normalized_symbol,
                candle_time=candle_time,
                reason=(
                    "New paper entries are no "
                    "longer allowed by time."
                ),
            )

        # --------------------------------------------------
        # STRATEGY EVALUATION
        # --------------------------------------------------

        strategy_result = strategy.evaluate(
            symbol=normalized_symbol,
            dataframe=dataframe,
        )

        # --------------------------------------------------
        # NO SIGNAL
        # --------------------------------------------------

        if strategy_result.signal == "NO_SIGNAL":

            return LivePaperTradingCycleResult(
                status="NO_SIGNAL",
                symbol=normalized_symbol,
                candle_time=candle_time,
                strategy_result=strategy_result,
                reason=(
                    strategy_result.reason
                    if hasattr(strategy_result, "reason")
                    else "Strategy generated no signal."
                ),
            )

        # --------------------------------------------------
        # RECORD ACTIONABLE SIGNAL
        # --------------------------------------------------

        self.record_signal(
            normalized_symbol
        )

        # --------------------------------------------------
        # DUPLICATE ENTRY CHECK
        # --------------------------------------------------

        if not self.can_create_entry(
            symbol=normalized_symbol,
            candle_time=candle_time,
        ):

            return LivePaperTradingCycleResult(
                status="ENTRY_BLOCKED",
                symbol=normalized_symbol,
                candle_time=candle_time,
                strategy_result=strategy_result,
                reason=(
                    "GARUDA entry controls "
                    "blocked the trade."
                ),
            )

        # --------------------------------------------------
        # PROCESS RISK-MANAGED ENTRY
        # --------------------------------------------------

        session_result = (
            session_engine.process_entry(
                strategy_result=strategy_result,
                market_price=(
                    latest_candle["close"]
                ),
                lot_size=lot_size,
                current_exposure=current_exposure,
                current_open_risk=current_open_risk,
                current_open_positions=(
                    current_open_positions
                ),
                daily_realized_pnl=(
                    daily_realized_pnl
                ),
                stop_loss_pct=stop_loss_pct,
                target_pct=target_pct,
            )
        )

        # --------------------------------------------------
        # RISK REJECTION
        # --------------------------------------------------

        if session_result.status == "REJECTED":

            self.record_rejection(
                normalized_symbol
            )

            return LivePaperTradingCycleResult(
                status="REJECTED",
                symbol=normalized_symbol,
                candle_time=candle_time,
                strategy_result=strategy_result,
                session_result=session_result,
                reason=session_result.reason
            )

        # --------------------------------------------------
        # SUCCESSFUL EXECUTION
        # --------------------------------------------------

        if session_result.status == "POSITION_OPEN":

            self.record_execution(
                symbol=normalized_symbol,
                candle_time=candle_time,
            )

            return LivePaperTradingCycleResult(
                status="POSITION_OPEN",
                symbol=normalized_symbol,
                candle_time=candle_time,
                strategy_result=strategy_result,
                session_result=session_result,
                reason=session_result.reason
            )

        # --------------------------------------------------
        # FALLBACK RESULT
        # --------------------------------------------------

        return LivePaperTradingCycleResult(
            status=session_result.status,
            symbol=normalized_symbol,
            candle_time=candle_time,
            strategy_result=strategy_result,
            session_result=session_result,
        )

    # --------------------------------------------------
    # PERSISTENCE
    # --------------------------------------------------

    def save_state(
        self,
        state_store,
        session_engine,
    ):
        """
        Persist complete live paper-trading state.
        """

        state_store.save(
            account=session_engine.executor.account,
            position_manager=(
                session_engine
                .executor
                .position_manager
            ),
            runner=self,
            session_engine=session_engine,
        )


    def restore_state(
        self,
        state_store,
        session_engine,
    ):
        """
        Restore complete live paper-trading state.
        """

        state_store.restore_account(
            session_engine.executor.account
        )

        state_store.restore_positions(
            session_engine
            .executor
            .position_manager
        )

        state_store.restore_runner(
            self
        )

        state_store.restore_exit_levels(
            session_engine
        )


    # --------------------------------------------------
    # RUNNER SUMMARY
    # --------------------------------------------------

    def get_summary(
        self,
    ):
        """
        Return GARUDA live paper-trading
        runtime summary.
        """

        symbol_states = list(
            self.state.symbols.values()
        )

        return {
            "registered_symbols": len(
                symbol_states
            ),
            "processed_candles": sum(
                state.processed_candle_count
                for state in symbol_states
            ),
            "generated_signals": sum(
                state.generated_signal_count
                for state in symbol_states
            ),
            "executed_trades": sum(
                state.executed_trade_count
                for state in symbol_states
            ),
            "rejected_trades": sum(
                state.rejected_trade_count
                for state in symbol_states
            ),
            "open_positions": sum(
                1
                for state in symbol_states
                if state.position_open
            ),
            "closed_trades": sum(
                state.closed_trade_count
                for state in symbol_states
            ),
            "running": self.state.running,
        }


    def display_summary(
        self,
    ):
        """
        Display visible GARUDA runtime summary.
        """

        summary = self.get_summary()

        print("\n" + "=" * 70)

        print(
            "GARUDA QUANT LAB - "
            "LIVE PAPER TRADING RUNNER"
        )

        print("=" * 70)

        print("\n[RUNTIME SUMMARY]")

        print("-" * 70)

        print(
            f"Runner Status       : "
            f"{'RUNNING' if summary['running'] else 'STOPPED'}"
        )

        print(
            f"Registered Symbols  : "
            f"{summary['registered_symbols']}"
        )

        print(
            f"Processed Candles   : "
            f"{summary['processed_candles']}"
        )

        print(
            f"Generated Signals   : "
            f"{summary['generated_signals']}"
        )

        print(
            f"Executed Trades     : "
            f"{summary['executed_trades']}"
        )

        print(
            f"Rejected Trades     : "
            f"{summary['rejected_trades']}"
        )

        print(
            f"Open Positions      : "
            f"{summary['open_positions']}"
        )

        print(
            f"Closed Trades       : "
            f"{summary['closed_trades']}"
        )

        print("\n" + "=" * 70)