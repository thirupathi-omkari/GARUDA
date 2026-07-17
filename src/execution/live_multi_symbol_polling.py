from dataclasses import dataclass, field
from datetime import datetime, timedelta

import time

import pandas as pd

from data.live_market_data import (
    fetch_live_intraday_data,
)


# ============================================================
# POLLING SYMBOL RESULT
# ============================================================


@dataclass
class SymbolPollingResult:
    """
    Result produced after GARUDA processes
    one symbol during one polling cycle.
    """

    cycle_number: int

    symbol: str

    instrument_token: int

    status: str

    cycle_result: object = None

    error_message: str = None


# ============================================================
# POLLING CYCLE RESULT
# ============================================================


@dataclass
class PollingCycleResult:
    """
    Result produced after GARUDA completes
    one complete multi-symbol polling cycle.
    """

    cycle_number: int

    symbol_results: list = field(
        default_factory=list
    )

    processed_symbols: int = 0

    successful_symbols: int = 0

    failed_symbols: int = 0


# ============================================================
# POLLING RUN RESULT
# ============================================================


@dataclass
class PollingRunResult:
    """
    Final result returned after GARUDA completes
    a finite multi-symbol polling run.
    """

    status: str

    requested_cycles: int

    completed_cycles: int

    total_symbol_polls: int

    successful_symbol_polls: int

    failed_symbol_polls: int

    cycle_results: list = field(
        default_factory=list
    )


# ============================================================
# LIVE MULTI-SYMBOL POLLING ENGINE
# ============================================================


class LiveMultiSymbolPollingEngine:
    """
    GARUDA finite multi-symbol polling engine.

    Responsibilities:

    Registered Symbols
            ↓
    Fetch Live Intraday Data
            ↓
    Validate Market Data Freshness
            ↓
    Calculate Current Portfolio State
            ↓
    Existing LivePaperTradingRunner
            ↓
    Existing PaperTradingSessionEngine
            ↓
    Collect Polling Results
            ↓
    Wait
            ↓
    Next Finite Polling Cycle

    Important:

    This engine does NOT duplicate:

    Strategy Logic
    Risk Logic
    Order Logic
    Position Logic
    Stop-Loss Logic
    Target Logic
    P&L Logic

    Those responsibilities remain inside
    GARUDA's existing components.
    """

    def __init__(
        self,
        kite,
        runner,
        strategy,
        session_engine,
        interval="5minute",
        lookback_days=5,
        poll_interval_seconds=5.0,
        sleep_function=None,
        market_data_fetcher=None,
        current_time_provider=None,
    ):
        """
        Create the GARUDA polling engine.

        Dependencies are injected so the engine
        remains independently testable.
        """

        self.kite = kite

        self.runner = runner

        self.strategy = strategy

        self.session_engine = session_engine

        self.interval = interval

        self.lookback_days = lookback_days

        self.poll_interval_seconds = (
            poll_interval_seconds
        )

        # ----------------------------------------------------
        # SLEEP DEPENDENCY
        # ----------------------------------------------------

        if sleep_function is None:

            sleep_function = time.sleep

        self.sleep_function = sleep_function

        # ----------------------------------------------------
        # MARKET DATA DEPENDENCY
        # ----------------------------------------------------

        if market_data_fetcher is None:

            market_data_fetcher = (
                fetch_live_intraday_data
            )

        self.market_data_fetcher = (
            market_data_fetcher
        )

        # ----------------------------------------------------
        # CURRENT TIME DEPENDENCY
        # ----------------------------------------------------

        if current_time_provider is None:

            current_time_provider = (
                lambda: pd.Timestamp.now(
                    tz="Asia/Kolkata"
                )
            )

        self.current_time_provider = (
            current_time_provider
        )


    # ========================================================
    # VALIDATION
    # ========================================================


    def _validate_requested_cycles(
        self,
        cycles,
    ):
        """
        Validate finite polling-cycle count.
        """

        if not isinstance(cycles, int):

            raise TypeError(
                "cycles must be an integer."
            )

        if cycles <= 0:

            raise ValueError(
                "cycles must be greater than zero."
            )


    def _validate_registered_symbols(self):
        """
        Ensure the runner contains at least
        one registered symbol.
        """

        if len(
            self.runner.state.symbols
        ) == 0:

            raise ValueError(
                "At least one symbol must be "
                "registered before polling."
            )


    # ========================================================
    # PORTFOLIO STATE
    # ========================================================


    def _calculate_current_exposure(self):
        """
        Calculate current portfolio exposure
        from GARUDA's open paper positions.

        Exposure:

            quantity × current market price

        Current market price is used instead of
        entry price because portfolio exposure
        should reflect the latest known value
        of every open position.
        """

        position_manager = (
            self.session_engine
            .executor
            .position_manager
        )

        return sum(
            position.quantity
            * position.current_price
            for position
            in position_manager.positions
        )


    def _calculate_current_open_risk(self):
        """
        Calculate current open portfolio risk
        using GARUDA's active exit levels.

        LONG:

            entry price - stop loss

        SHORT:

            stop loss - entry price

        Result is multiplied by quantity.
        """

        position_manager = (
            self.session_engine
            .executor
            .position_manager
        )

        total_open_risk = 0.0

        for position in position_manager.positions:

            try:

                exit_levels = (
                    self.session_engine
                    .get_exit_levels(
                        position.symbol
                    )
                )

            except ValueError:

                continue

            stop_loss_price = (
                exit_levels[
                    "stop_loss_price"
                ]
            )

            if position.side == "LONG":

                risk_per_unit = max(
                    position.entry_price
                    - stop_loss_price,
                    0.0,
                )

            elif position.side == "SHORT":

                risk_per_unit = max(
                    stop_loss_price
                    - position.entry_price,
                    0.0,
                )

            else:

                continue

            total_open_risk += (
                risk_per_unit
                * position.quantity
            )

        return total_open_risk


    def _calculate_current_open_positions(self):
        """
        Return current number of open
        GARUDA paper positions.
        """

        position_manager = (
            self.session_engine
            .executor
            .position_manager
        )

        return position_manager.position_count


    def _calculate_daily_realized_pnl(self):
        """
        Calculate realized P&L from GARUDA's
        authoritative trading account.

        Current Module 9 account state:

            current capital - initial capital

        This is sufficient for the current
        single-session paper-trading architecture.

        A date-aware daily ledger can replace
        this implementation in a future module.
        """

        account = (
            self.session_engine
            .executor
            .risk_manager
            .account
        )

        return (
            account.current_capital
            - account.initial_capital
        )


    def get_portfolio_state(self):
        """
        Return the current GARUDA portfolio state.
        """

        return {
            "current_exposure": (
                self._calculate_current_exposure()
            ),
            "current_open_risk": (
                self._calculate_current_open_risk()
            ),
            "current_open_positions": (
                self._calculate_current_open_positions()
            ),
            "daily_realized_pnl": (
                self._calculate_daily_realized_pnl()
            ),
        }


    # ========================================================
    # MARKET DATA
    # ========================================================


    def _fetch_symbol_market_data(
        self,
        instrument_token,
    ):
        """
        Fetch current intraday market data
        using GARUDA's existing market-data layer.

        The date range is calculated dynamically
        from the configured lookback period.
        """

        to_date = datetime.now()

        from_date = (
            to_date
            - timedelta(
                days=self.lookback_days
            )
        )

        return self.market_data_fetcher(
            kite=self.kite,
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=self.interval,
        )


    # ========================================================
    # MARKET DATA FRESHNESS
    # ========================================================


    def _get_latest_candle_time(
        self,
        dataframe,
    ):
        """
        Return the timestamp of the latest
        available GARUDA market candle.
        """

        if dataframe is None:

            return None

        if dataframe.empty:

            return None

        latest_candle_time = pd.Timestamp(
            dataframe.iloc[-1]["datetime"]
        )

        return latest_candle_time


    def _is_market_data_stale(
        self,
        dataframe,
    ):
        """
        Determine whether the latest market candle
        belongs to an earlier calendar date.

        GARUDA must not evaluate strategy signals
        or create paper trades from old market data.

        Kite timestamps may be timezone-aware.
        Test data may be timezone-naive.

        The comparison therefore normalizes the
        current time to match the timezone behavior
        of the latest candle timestamp.
        """

        latest_candle_time = (
            self._get_latest_candle_time(
                dataframe
            )
        )

        if latest_candle_time is None:

            return False

        current_time = pd.Timestamp(
            self.current_time_provider()
        )

        # ----------------------------------------------------
        # TIMEZONE-AWARE MARKET CANDLE
        # ----------------------------------------------------

        if latest_candle_time.tzinfo is not None:

            if current_time.tzinfo is None:

                current_time = (
                    current_time.tz_localize(
                        latest_candle_time.tzinfo
                    )
                )

            else:

                current_time = (
                    current_time.tz_convert(
                        latest_candle_time.tzinfo
                    )
                )

        # ----------------------------------------------------
        # TIMEZONE-NAIVE MARKET CANDLE
        # ----------------------------------------------------

        elif current_time.tzinfo is not None:

            current_time = (
                current_time.tz_localize(None)
            )

        # ----------------------------------------------------
        # DATE COMPARISON
        # ----------------------------------------------------

        return (
            latest_candle_time.date()
            < current_time.date()
        )


    # ========================================================
    # PROCESS ONE SYMBOL
    # ========================================================


    def process_symbol(
        self,
        cycle_number,
        symbol,
        instrument_token,
    ):
        """
        Process one registered symbol through
        one GARUDA polling cycle.
        """

        try:

            # ------------------------------------------------
            # FETCH MARKET DATA
            # ------------------------------------------------

            dataframe = (
                self._fetch_symbol_market_data(
                    instrument_token=(
                        instrument_token
                    )
                )
            )

            # ------------------------------------------------
            # NONE MARKET DATA
            # ------------------------------------------------

            if dataframe is None:

                return SymbolPollingResult(
                    cycle_number=cycle_number,
                    symbol=symbol,
                    instrument_token=(
                        instrument_token
                    ),
                    status="NO_MARKET_DATA",
                )

            # ------------------------------------------------
            # EMPTY MARKET DATA
            # ------------------------------------------------

            if dataframe.empty:

                return SymbolPollingResult(
                    cycle_number=cycle_number,
                    symbol=symbol,
                    instrument_token=(
                        instrument_token
                    ),
                    status="NO_MARKET_DATA",
                )

            # ------------------------------------------------
            # STALE MARKET DATA
            # ------------------------------------------------

            if self._is_market_data_stale(
                dataframe
            ):

                return SymbolPollingResult(
                    cycle_number=cycle_number,
                    symbol=symbol,
                    instrument_token=(
                        instrument_token
                    ),
                    status="STALE_MARKET_DATA",
                )

            # ------------------------------------------------
            # CURRENT PORTFOLIO STATE
            # ------------------------------------------------

            portfolio_state = (
                self.get_portfolio_state()
            )

            # ------------------------------------------------
            # EXISTING GARUDA ORCHESTRATION
            # ------------------------------------------------

            cycle_result = (
                self.runner
                .process_symbol_cycle(
                    symbol=symbol,
                    dataframe=dataframe,
                    strategy=self.strategy,
                    session_engine=(
                        self.session_engine
                    ),
                    current_exposure=(
                        portfolio_state[
                            "current_exposure"
                        ]
                    ),
                    current_open_risk=(
                        portfolio_state[
                            "current_open_risk"
                        ]
                    ),
                    current_open_positions=(
                        portfolio_state[
                            "current_open_positions"
                        ]
                    ),
                    daily_realized_pnl=(
                        portfolio_state[
                            "daily_realized_pnl"
                        ]
                    ),
                )
            )

            # ------------------------------------------------
            # SUCCESS RESULT
            # ------------------------------------------------

            return SymbolPollingResult(
                cycle_number=cycle_number,
                symbol=symbol,
                instrument_token=(
                    instrument_token
                ),
                status=cycle_result.status,
                cycle_result=cycle_result,
            )

        except Exception as error:

            # ------------------------------------------------
            # ISOLATE SYMBOL FAILURE
            # ------------------------------------------------

            return SymbolPollingResult(
                cycle_number=cycle_number,
                symbol=symbol,
                instrument_token=(
                    instrument_token
                ),
                status="ERROR",
                error_message=str(error),
            )


    # ========================================================
    # PROCESS ONE COMPLETE POLLING CYCLE
    # ========================================================


    def process_polling_cycle(
        self,
        cycle_number,
    ):
        """
        Process all registered symbols once.
        """

        registered_symbols = self.runner.state.symbols

        from datetime import datetime

        print("\n" + "=" * 78)
        print("GARUDA LIVE PAPER TRADING")
        print("=" * 78)
        print(f"Cycle         : {cycle_number}")
        print(f"Current Time  : {datetime.now():%d-%m-%Y %H:%M:%S}")
        print(f"Symbols       : {len(registered_symbols)}")
        print("-" * 78)


        symbol_results = []

        successful_symbols = 0

        failed_symbols = 0

        registered_symbols = (
            self.runner.state.symbols
        )

        for (
            symbol,
            symbol_state,
        ) in registered_symbols.items():

            instrument_token = (
                symbol_state.instrument_token
            )

            symbol_result = (
                self.process_symbol(
                    cycle_number=cycle_number,
                    symbol=symbol,
                    instrument_token=(
                        instrument_token
                    ),
                )
            )

            symbol_results.append(
                symbol_result
            )

            print(f"{symbol:<12} Status : {symbol_result.status}")

            if symbol_result.status == "ERROR":

                failed_symbols += 1

            else:

                successful_symbols += 1

        return PollingCycleResult(
            cycle_number=cycle_number,
            symbol_results=symbol_results,
            processed_symbols=len(
                symbol_results
            ),
            successful_symbols=(
                successful_symbols
            ),
            failed_symbols=failed_symbols,
        )


    # ========================================================
    # FINITE POLLING RUN
    # ========================================================


    def run(
        self,
        cycles,
    ):
        """
        Run GARUDA for a finite number
        of polling cycles.

        The engine intentionally does not use
        an infinite while loop.

        This makes the polling architecture:

        Testable
        Deterministic
        Safer during development
        """

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        self._validate_requested_cycles(
            cycles=cycles
        )

        self._validate_registered_symbols()

        # ----------------------------------------------------
        # RESULT COUNTERS
        # ----------------------------------------------------

        cycle_results = []

        total_symbol_polls = 0

        successful_symbol_polls = 0

        failed_symbol_polls = 0

        # ----------------------------------------------------
        # FINITE POLLING LOOP
        # ----------------------------------------------------

        for cycle_number in range(
            1,
            cycles + 1,
        ):

            cycle_result = (
                self.process_polling_cycle(
                    cycle_number=cycle_number
                )
            )

            cycle_results.append(
                cycle_result
            )

            total_symbol_polls += (
                cycle_result.processed_symbols
            )

            successful_symbol_polls += (
                cycle_result.successful_symbols
            )

            failed_symbol_polls += (
                cycle_result.failed_symbols
            )

            # ------------------------------------------------
            # WAIT BETWEEN CYCLES
            # ------------------------------------------------

            if cycle_number < cycles:

                from datetime import datetime, timedelta

                completed = datetime.now()
                next_poll = completed + timedelta(
                    seconds=self.poll_interval_seconds
                )

                print("\n" + "=" * 70)
                print(f"Cycle {cycle_number} completed successfully.")
                print(f"Completed At : {completed:%d-%m-%Y %H:%M:%S}")
                print(f"Next Poll At : {next_poll:%d-%m-%Y %H:%M:%S}")
                print(f"Waiting      : {int(self.poll_interval_seconds)} seconds")
                print("=" * 70)

                self.sleep_function(
                    self.poll_interval_seconds
                )

                print("\n" + "=" * 70)
                print(f"Starting Cycle {cycle_number + 1}")
                print(f"Current Time : {datetime.now():%d-%m-%Y %H:%M:%S}")
                print("=" * 70)

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        return PollingRunResult(
            status="COMPLETED",
            requested_cycles=cycles,
            completed_cycles=len(
                cycle_results
            ),
            total_symbol_polls=(
                total_symbol_polls
            ),
            successful_symbol_polls=(
                successful_symbol_polls
            ),
            failed_symbol_polls=(
                failed_symbol_polls
            ),
            cycle_results=cycle_results,
        )