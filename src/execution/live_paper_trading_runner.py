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


class LivePaperTradingRunner:
    """
    GARUDA live paper-trading runner.

    Part 13E responsibilities:

    - Maintain multi-symbol runtime state.
    - Detect new market candles.
    - Prevent duplicate candle processing.
    - Prevent duplicate entries.
    - Track open and closed positions.
    - Track executed and rejected trades.
    - Enforce trading-session timing.
    - Provide visible runtime summaries.

    Later integration:

    Kite Market Data
        ↓
    New Candle Detection
        ↓
    Existing ORB + VWAP Strategy
        ↓
    Existing Risk Manager
        ↓
    Existing Paper Trading Session Engine
        ↓
    Automatic SL / Target Exit
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

        Entry is blocked when:

        - Position is already open.
        - Same candle already created an entry.
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