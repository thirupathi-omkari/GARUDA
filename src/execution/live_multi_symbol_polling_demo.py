from broker.session_manager import (
    create_authenticated_session,
)

from data.instrument_resolver import (
    resolve_instrument_token,
)

from execution.live_multi_symbol_polling import (
    LiveMultiSymbolPollingEngine,
)

from execution.live_paper_trading_runner import (
    LivePaperTradingRunner,
)

from execution.paper_order_manager import (
    PaperOrderManager,
)

from execution.paper_position_manager import (
    PaperPositionManager,
)

from execution.paper_trading_session import (
    PaperTradingSessionEngine,
)

from execution.risk_managed_paper_executor import (
    RiskManagedPaperExecutor,
)

from execution.simulated_broker import (
    SimulatedBroker,
)

from risk.account import (
    TradingAccount,
)

from risk.risk_config import (
    RiskConfig,
)

from risk.risk_manager import (
    RiskManager,
)

from strategy.orb_vwap_strategy import (
    ORBVWAPStrategy,
)


# ============================================================
# DEMO CONFIGURATION
# ============================================================


SYMBOLS = [
    "INFY",
    "TCS",
    "RELIANCE",
    "HDFCBANK",
    "ICICIBANK",
]

INITIAL_CAPITAL = 100000.0

INTERVAL = "5minute"

LOOKBACK_DAYS = 5

POLLING_CYCLES = 1

POLL_INTERVAL_SECONDS = 5.0


# ============================================================
# GARUDA COMPONENT FACTORY
# ============================================================


def create_garuda_components():
    """
    Create GARUDA's existing paper-trading
    components for the real Kite polling demo.
    """

    account = TradingAccount.create(
        initial_capital=INITIAL_CAPITAL
    )

    risk_config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=100.0,
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    risk_manager = RiskManager(
        account=account,
        config=risk_config,
    )

    order_manager = PaperOrderManager()

    broker = SimulatedBroker()

    position_manager = (
        PaperPositionManager()
    )

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=order_manager,
        broker=broker,
        position_manager=position_manager,
    )

    session_engine = (
        PaperTradingSessionEngine(
            executor=executor
        )
    )

    runner = LivePaperTradingRunner()

    strategy = ORBVWAPStrategy()

    return (
        account,
        order_manager,
        position_manager,
        session_engine,
        runner,
        strategy,
    )


# ============================================================
# SYMBOL REGISTRATION
# ============================================================


def register_symbols(
    kite,
    runner,
):
    """
    Resolve Kite instrument tokens and register
    the configured NSE symbols with GARUDA.
    """

    print("\n" + "=" * 70)

    print(
        "GARUDA SYMBOL REGISTRATION"
    )

    print("=" * 70)

    registered_symbols = []

    failed_symbols = []

    for symbol in SYMBOLS:

        print(
            f"\nResolving {symbol}..."
        )

        try:

            instrument_token = (
                resolve_instrument_token(
                    kite=kite,
                    tradingsymbol=symbol,
                    exchange="NSE",
                )
            )

            if instrument_token is None:

                failed_symbols.append(
                    symbol
                )

                print(
                    f"Registration Failed : "
                    f"{symbol}"
                )

                continue

            runner.register_symbol(
                symbol=symbol,
                instrument_token=instrument_token,
            )

            registered_symbols.append(
                symbol
            )

            print(
                f"Registered          : "
                f"{symbol}"
            )

            print(
                f"Instrument Token    : "
                f"{instrument_token}"
            )

        except Exception as error:

            failed_symbols.append(
                symbol
            )

            print(
                f"Registration Failed : "
                f"{symbol}"
            )

            print(
                f"Reason              : "
                f"{error}"
            )

    print("\n" + "-" * 70)

    print(
        f"Requested Symbols   : "
        f"{len(SYMBOLS)}"
    )

    print(
        f"Registered Symbols  : "
        f"{len(registered_symbols)}"
    )

    print(
        f"Failed Symbols      : "
        f"{len(failed_symbols)}"
    )

    return (
        registered_symbols,
        failed_symbols,
    )


# ============================================================
# POLLING RESULT DISPLAY
# ============================================================


def display_symbol_result(
    symbol_result,
):
    """
    Display one real polling result.
    """

    print("\n" + "-" * 70)

    print(
        f"Symbol              : "
        f"{symbol_result.symbol}"
    )

    print(
        f"Instrument Token    : "
        f"{symbol_result.instrument_token}"
    )

    print(
        f"Status              : "
        f"{symbol_result.status}"
    )

    if symbol_result.error_message:

        print(
            f"Error               : "
            f"{symbol_result.error_message}"
        )

    cycle_result = (
        symbol_result.cycle_result
    )

    if cycle_result is None:

        return

    if cycle_result.candle_time is not None:

        print(
            f"Candle Time         : "
            f"{cycle_result.candle_time}"
        )

    if cycle_result.reason:

        print(
            f"Reason              : "
            f"{cycle_result.reason}"
        )

    strategy_result = (
        cycle_result.strategy_result
    )

    if strategy_result is not None:

        print(
            f"Strategy            : "
            f"{strategy_result.strategy_name}"
        )

        print(
            f"Signal              : "
            f"{strategy_result.signal}"
        )

        if (
            strategy_result.entry_price
            is not None
        ):

            print(
                f"Entry Price         : "
                f"{strategy_result.entry_price:,.2f}"
            )

        print(
            f"Strategy Reason     : "
            f"{strategy_result.reason}"
        )

    session_result = (
        cycle_result.session_result
    )

    if session_result is not None:

        print(
            f"Session Status      : "
            f"{session_result.status}"
        )

        execution_result = (
            session_result.execution_result
        )

        if execution_result is not None:

            risk_decision = (
                execution_result.risk_decision
            )

            print(
                f"Risk Decision       : "
                f"{risk_decision.reason}"
            )

            print(
                f"Risk Amount         : "
                f"{risk_decision.risk_amount:,.2f}"
            )

            print(
                f"Approved Quantity   : "
                f"{risk_decision.approved_quantity}"
            )

            print(
                f"Proposed Exposure   : "
                f"{risk_decision.proposed_exposure:,.2f}"
            )

            if execution_result.order is not None:

                print(
                    f"Order ID            : "
                    f"{execution_result.order.order_id}"
                )

                print(
                    f"Order Status        : "
                    f"{execution_result.order.status}"
                )

                print(
                    f"Fill Price          : "
                    f"{execution_result.order.fill_price:,.2f}"
                )

    market_candle_result = (
        cycle_result.market_candle_result
    )

    if market_candle_result is not None:

        print(
            f"Position Status     : "
            f"{market_candle_result.status}"
        )

        print(
            f"Current Price       : "
            f"{market_candle_result.current_price:,.2f}"
        )

        print(
            f"Unrealized P&L      : "
            f"{market_candle_result.unrealized_pnl:,.2f}"
        )

        if (
            market_candle_result.exit_reason
            is not None
        ):

            print(
                f"Exit Reason         : "
                f"{market_candle_result.exit_reason}"
            )


def display_polling_result(
    polling_result,
):
    """
    Display the complete finite polling run.
    """

    print("\n" + "=" * 70)

    print(
        "GARUDA REAL KITE MULTI-SYMBOL "
        "POLLING RESULT"
    )

    print("=" * 70)

    print("\n[POLLING SUMMARY]")

    print("-" * 70)

    print(
        f"Status              : "
        f"{polling_result.status}"
    )

    print(
        f"Requested Cycles    : "
        f"{polling_result.requested_cycles}"
    )

    print(
        f"Completed Cycles    : "
        f"{polling_result.completed_cycles}"
    )

    print(
        f"Total Symbol Polls  : "
        f"{polling_result.total_symbol_polls}"
    )

    print(
        f"Successful Polls    : "
        f"{polling_result.successful_symbol_polls}"
    )

    print(
        f"Failed Polls        : "
        f"{polling_result.failed_symbol_polls}"
    )

    for cycle_result in polling_result.cycle_results:

        print("\n" + "=" * 70)

        print(
            f"POLLING CYCLE "
            f"{cycle_result.cycle_number}"
        )

        print("=" * 70)

        print(
            f"Processed Symbols   : "
            f"{cycle_result.processed_symbols}"
        )

        print(
            f"Successful Symbols  : "
            f"{cycle_result.successful_symbols}"
        )

        print(
            f"Failed Symbols      : "
            f"{cycle_result.failed_symbols}"
        )

        for symbol_result in (
            cycle_result.symbol_results
        ):

            display_symbol_result(
                symbol_result
            )


# ============================================================
# FINAL ACCOUNT SUMMARY
# ============================================================


def display_final_summary(
    account,
    order_manager,
    position_manager,
    runner,
    polling_engine,
):
    """
    Display GARUDA's final state after the
    controlled real Kite polling demo.
    """

    portfolio_state = (
        polling_engine.get_portfolio_state()
    )

    print("\n" + "=" * 70)

    print(
        "GARUDA FINAL PAPER TRADING STATE"
    )

    print("=" * 70)

    print("\n[ACCOUNT]")

    print("-" * 70)

    print(
        f"Initial Capital     : "
        f"{account.initial_capital:,.2f}"
    )

    print(
        f"Current Capital     : "
        f"{account.current_capital:,.2f}"
    )

    print(
        f"Net Realized P&L    : "
        f"{account.current_capital - account.initial_capital:,.2f}"
    )

    print("\n[PORTFOLIO]")

    print("-" * 70)

    print(
        f"Current Exposure    : "
        f"{portfolio_state['current_exposure']:,.2f}"
    )

    print(
        f"Current Open Risk   : "
        f"{portfolio_state['current_open_risk']:,.2f}"
    )

    print(
        f"Open Positions      : "
        f"{portfolio_state['current_open_positions']}"
    )

    print(
        f"Daily Realized P&L  : "
        f"{portfolio_state['daily_realized_pnl']:,.2f}"
    )

    print("\n[EXECUTION]")

    print("-" * 70)

    print(
        f"Orders Created      : "
        f"{order_manager.order_count}"
    )

    print(
        f"Positions Open      : "
        f"{position_manager.position_count}"
    )

    runner.display_summary()


# ============================================================
# MAIN DEMO
# ============================================================


def run_demo():
    """
    Run one controlled finite real Kite
    multi-symbol polling demonstration.
    """

    print("\n" + "=" * 70)

    print(
        "GARUDA QUANT LAB - "
        "REAL KITE MULTI-SYMBOL POLLING DEMO"
    )

    print("=" * 70)

    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------

    print("\nCreating authenticated Kite session...")

    kite = create_authenticated_session()

    if kite is None:

        print(
            "\nGARUDA Real Kite Polling Demo Failed."
        )

        print(
            "Reason: Authenticated Kite "
            "session unavailable."
        )

        return

    # --------------------------------------------------------
    # GARUDA COMPONENTS
    # --------------------------------------------------------

    (
        account,
        order_manager,
        position_manager,
        session_engine,
        runner,
        strategy,
    ) = create_garuda_components()

    # --------------------------------------------------------
    # SYMBOL REGISTRATION
    # --------------------------------------------------------

    (
        registered_symbols,
        failed_symbols,
    ) = register_symbols(
        kite=kite,
        runner=runner,
    )

    if not registered_symbols:

        print(
            "\nGARUDA Real Kite Polling Demo Failed."
        )

        print(
            "Reason: No symbols were registered."
        )

        return

    # --------------------------------------------------------
    # START RUNNER
    # --------------------------------------------------------

    runner.start()

    # --------------------------------------------------------
    # CREATE POLLING ENGINE
    # --------------------------------------------------------

    polling_engine = (
        LiveMultiSymbolPollingEngine(
            kite=kite,
            runner=runner,
            strategy=strategy,
            session_engine=session_engine,
            interval=INTERVAL,
            lookback_days=LOOKBACK_DAYS,
            poll_interval_seconds=(
                POLL_INTERVAL_SECONDS
            ),
        )
    )

    # --------------------------------------------------------
    # RUN ONE FINITE POLLING CYCLE
    # --------------------------------------------------------

    print("\n" + "=" * 70)

    print(
        "STARTING CONTROLLED REAL KITE POLLING"
    )

    print("=" * 70)

    print(
        f"Registered Symbols  : "
        f"{len(registered_symbols)}"
    )

    print(
        f"Polling Cycles      : "
        f"{POLLING_CYCLES}"
    )

    print(
        f"Interval            : "
        f"{INTERVAL}"
    )

    print(
        f"Lookback Days       : "
        f"{LOOKBACK_DAYS}"
    )

    polling_result = (
        polling_engine.run(
            cycles=POLLING_CYCLES
        )
    )

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    display_polling_result(
        polling_result
    )

    display_final_summary(
        account=account,
        order_manager=order_manager,
        position_manager=position_manager,
        runner=runner,
        polling_engine=polling_engine,
    )

    # --------------------------------------------------------
    # STOP RUNNER
    # --------------------------------------------------------

    runner.stop()

    print("\n" + "=" * 70)

    print(
        "GARUDA REAL KITE MULTI-SYMBOL "
        "POLLING DEMO COMPLETED"
    )

    print("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================


if __name__ == "__main__":

    run_demo()