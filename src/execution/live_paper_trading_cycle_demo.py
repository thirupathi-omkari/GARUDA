import pandas as pd

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

from risk.account import TradingAccount

from risk.risk_config import RiskConfig

from risk.risk_manager import RiskManager

from strategy.strategy_result import StrategyResult


# ============================================================
# DEMO STRATEGY
# ============================================================


class DemoBuyStrategy:
    """
    Deterministic BUY strategy used only
    to demonstrate GARUDA's orchestration flow.

    This does not replace GARUDA's real
    ORB + VWAP strategy.
    """

    def evaluate(
        self,
        symbol,
        dataframe,
    ):
        latest_close = (
            dataframe.iloc[-1]["close"]
        )

        return StrategyResult(
            symbol=symbol,
            strategy_name="DEMO_BUY_STRATEGY",
            signal="BUY",
            entry_price=latest_close,
            reason=(
                "Deterministic BUY signal for "
                "GARUDA orchestration demo."
            ),
        )


# ============================================================
# MARKET DATA
# ============================================================


def create_entry_market_data():
    """
    Entry candle.

    Entry Price = 500

    With GARUDA demo settings:

    Stop Loss = 495
    Target    = 510
    """

    return pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp(
                    "2026-07-10 10:00:00"
                )
            ],
            "open": [
                498.0
            ],
            "high": [
                503.0
            ],
            "low": [
                497.0
            ],
            "close": [
                500.0
            ],
            "volume": [
                10000
            ],
        }
    )


def create_hold_market_data():
    """
    Second candle.

    Neither stop loss nor target is hit.
    """

    return pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp(
                    "2026-07-10 10:05:00"
                )
            ],
            "open": [
                500.0
            ],
            "high": [
                507.0
            ],
            "low": [
                499.0
            ],
            "close": [
                505.0
            ],
            "volume": [
                12000
            ],
        }
    )


def create_target_market_data():
    """
    Third candle.

    Target = 510

    Candle high reaches 512.

    GARUDA must automatically
    exit at the target price.
    """

    return pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp(
                    "2026-07-10 10:10:00"
                )
            ],
            "open": [
                505.0
            ],
            "high": [
                512.0
            ],
            "low": [
                504.0
            ],
            "close": [
                511.0
            ],
            "volume": [
                15000
            ],
        }
    )


# ============================================================
# COMPONENT CREATION
# ============================================================


def create_garuda_components():
    """
    Create the existing GARUDA paper-trading
    components required by the orchestration demo.
    """

    account = TradingAccount.create(
        initial_capital=100000.0
    )

    config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=100.0,
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    risk_manager = RiskManager(
        account=account,
        config=config,
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

    runner.register_symbol(
        symbol="INFY",
        instrument_token=408065,
    )

    runner.start(
        started_at=pd.Timestamp(
            "2026-07-10 09:15:00"
        )
    )

    return (
        account,
        order_manager,
        position_manager,
        session_engine,
        runner,
    )


# ============================================================
# DISPLAY HELPERS
# ============================================================


def display_cycle_header(
    cycle_number,
    title,
):
    """
    Display one GARUDA cycle heading.
    """

    print("\n" + "=" * 70)

    print(
        f"CYCLE {cycle_number} - {title}"
    )

    print("=" * 70)


def display_cycle_result(
    result,
):
    """
    Display common cycle-result information.
    """

    print(
        f"Status              : "
        f"{result.status}"
    )

    print(
        f"Symbol              : "
        f"{result.symbol}"
    )

    print(
        f"Candle Time         : "
        f"{result.candle_time}"
    )


# ============================================================
# DEMO
# ============================================================


def run_demo():
    """
    Run the complete visible GARUDA
    single-cycle orchestration demonstration.

    Flow:

    Cycle 1
        Signal
        Risk Evaluation
        Paper Execution
        Position Open

    Cycle 2
        Position Monitoring
        Unrealized P&L Update
        Hold Position

    Cycle 3
        Target Detection
        Automatic Exit
        Realized P&L
        Capital Update

    Final
        Runner Summary
    """

    print("\n" + "=" * 70)

    print(
        "GARUDA QUANT LAB - "
        "SINGLE-CYCLE ORCHESTRATION DEMO"
    )

    print("=" * 70)

    (
        account,
        order_manager,
        position_manager,
        session_engine,
        runner,
    ) = create_garuda_components()

    strategy = DemoBuyStrategy()

    # ========================================================
    # INITIAL STATE
    # ========================================================

    print("\n[INITIAL ACCOUNT]")

    print("-" * 70)

    print(
        f"Initial Capital     : "
        f"{account.initial_capital:,.2f}"
    )

    print(
        f"Current Capital     : "
        f"{account.current_capital:,.2f}"
    )

    # ========================================================
    # CYCLE 1
    # NEW SIGNAL AND PAPER ENTRY
    # ========================================================

    display_cycle_header(
        cycle_number=1,
        title="NEW SIGNAL AND PAPER ENTRY",
    )

    entry_result = (
        runner.process_symbol_cycle(
            symbol="INFY",
            dataframe=(
                create_entry_market_data()
            ),
            strategy=strategy,
            session_engine=session_engine,
        )
    )

    display_cycle_result(
        entry_result
    )

    # --------------------------------------------------------
    # STRATEGY RESULT
    # --------------------------------------------------------

    if entry_result.strategy_result is not None:

        strategy_result = (
            entry_result.strategy_result
        )

        print("\n[STRATEGY]")

        print("-" * 70)

        print(
            f"Strategy            : "
            f"{strategy_result.strategy_name}"
        )

        print(
            f"Signal              : "
            f"{strategy_result.signal}"
        )

        print(
            f"Entry Price         : "
            f"{strategy_result.entry_price:,.2f}"
        )

        print(
            f"Reason              : "
            f"{strategy_result.reason}"
        )

    # --------------------------------------------------------
    # PAPER EXECUTION RESULT
    # --------------------------------------------------------

    if entry_result.session_result is not None:

        session_result = (
            entry_result.session_result
        )

        print("\n[PAPER EXECUTION]")

        print("-" * 70)

        print(
            f"Execution Status    : "
            f"{session_result.status}"
        )

        if (
            session_result.execution_result
            is not None
        ):

            execution_result = (
                session_result.execution_result
            )

            print(
                f"Risk Decision       : "
                f"{execution_result.risk_decision.reason}"
            )

            print(
                f"Risk Amount         : "
                f"{execution_result.risk_decision.risk_amount:,.2f}"
            )

            print(
                f"Raw Position Size   : "
                f"{execution_result.risk_decision.raw_position_size}"
            )

            print(
                f"Approved Quantity   : "
                f"{execution_result.risk_decision.approved_quantity}"
            )

            print(
                f"Proposed Exposure   : "
                f"{execution_result.risk_decision.proposed_exposure:,.2f}"
            )

            print(
                f"Order ID            : "
                f"{execution_result.order.order_id}"
            )

            print(
                f"Order Side          : "
                f"{execution_result.order.side}"
            )

            print(
                f"Order Quantity      : "
                f"{execution_result.order.quantity}"
            )

            print(
                f"Order Status        : "
                f"{execution_result.order.status}"
            )

            print(
                f"Fill Price          : "
                f"{execution_result.order.fill_price:,.2f}"
            )

    # --------------------------------------------------------
    # EXIT LEVELS
    # --------------------------------------------------------

    exit_levels = (
        session_engine.get_exit_levels(
            "INFY"
        )
    )

    print("\n[EXIT LEVELS]")

    print("-" * 70)

    print(
        f"Direction           : "
        f"{exit_levels['direction']}"
    )

    print(
        f"Stop Loss           : "
        f"{exit_levels['stop_loss_price']:,.2f}"
    )

    print(
        f"Target              : "
        f"{exit_levels['target_price']:,.2f}"
    )

    # --------------------------------------------------------
    # OPEN POSITION
    # --------------------------------------------------------

    position = (
        position_manager.get_position(
            "INFY"
        )
    )

    print("\n[OPEN POSITION]")

    print("-" * 70)

    print(
        f"Symbol              : "
        f"{position.symbol}"
    )

    print(
        f"Side                : "
        f"{position.side}"
    )

    print(
        f"Quantity            : "
        f"{position.quantity}"
    )

    print(
        f"Entry Price         : "
        f"{position.entry_price:,.2f}"
    )

    print(
        f"Current Price       : "
        f"{position.current_price:,.2f}"
    )

    print(
        f"Unrealized P&L      : "
        f"{position.unrealized_pnl:,.2f}"
    )

    # ========================================================
    # CYCLE 2
    # OPEN POSITION MONITORING
    # ========================================================

    display_cycle_header(
        cycle_number=2,
        title="OPEN POSITION MONITORING",
    )

    hold_result = (
        runner.process_symbol_cycle(
            symbol="INFY",
            dataframe=(
                create_hold_market_data()
            ),
            strategy=strategy,
            session_engine=session_engine,
        )
    )

    display_cycle_result(
        hold_result
    )

    # --------------------------------------------------------
    # MARKET CANDLE RESULT
    # --------------------------------------------------------

    if (
        hold_result.market_candle_result
        is not None
    ):

        market_result = (
            hold_result.market_candle_result
        )

        print("\n[MARKET CANDLE EVALUATION]")

        print("-" * 70)

        print(
            f"Current Price       : "
            f"{market_result.current_price:,.2f}"
        )

        print(
            f"Stop Loss           : "
            f"{market_result.stop_loss_price:,.2f}"
        )

        print(
            f"Target              : "
            f"{market_result.target_price:,.2f}"
        )

        print(
            f"Unrealized P&L      : "
            f"{market_result.unrealized_pnl:,.2f}"
        )

        print(
            "Action              : "
            "HOLD POSITION"
        )

    # --------------------------------------------------------
    # UPDATED POSITION
    # --------------------------------------------------------

    position = (
        position_manager.get_position(
            "INFY"
        )
    )

    print("\n[POSITION UPDATE]")

    print("-" * 70)

    print(
        f"Current Price       : "
        f"{position.current_price:,.2f}"
    )

    print(
        f"Unrealized P&L      : "
        f"{position.unrealized_pnl:,.2f}"
    )

    # ========================================================
    # CYCLE 3
    # AUTOMATIC TARGET EXIT
    # ========================================================

    display_cycle_header(
        cycle_number=3,
        title="AUTOMATIC TARGET EXIT",
    )

    target_result = (
        runner.process_symbol_cycle(
            symbol="INFY",
            dataframe=(
                create_target_market_data()
            ),
            strategy=strategy,
            session_engine=session_engine,
        )
    )

    display_cycle_result(
        target_result
    )

    # --------------------------------------------------------
    # AUTOMATIC EXIT RESULT
    # --------------------------------------------------------

    if (
        target_result.market_candle_result
        is not None
    ):

        market_result = (
            target_result.market_candle_result
        )

        print("\n[AUTOMATIC EXIT]")

        print("-" * 70)

        print(
            f"Current Market Price: "
            f"{market_result.current_price:,.2f}"
        )

        print(
            f"Stop Loss           : "
            f"{market_result.stop_loss_price:,.2f}"
        )

        print(
            f"Target              : "
            f"{market_result.target_price:,.2f}"
        )

        print(
            f"Exit Reason         : "
            f"{market_result.exit_reason}"
        )

        if market_result.exit_result is not None:

            paper_exit_result = (
                market_result.exit_result
            )

            print(
                f"Exit Price          : "
                f"{paper_exit_result.exit_price:,.2f}"
            )

            print(
                f"Realized P&L        : "
                f"{paper_exit_result.realized_pnl:,.2f}"
            )

    # ========================================================
    # FINAL ACCOUNT
    # ========================================================

    print("\n[FINAL ACCOUNT]")

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
        f"Net P&L             : "
        f"{account.current_capital - account.initial_capital:,.2f}"
    )

    print(
        f"Return              : "
        f"{(
            (
                account.current_capital
                - account.initial_capital
            )
            / account.initial_capital
        ) * 100:,.2f}%"
    )

    print(
        f"Orders Created      : "
        f"{order_manager.order_count}"
    )

    print(
        f"Open Positions      : "
        f"{position_manager.position_count}"
    )

    # ========================================================
    # RUNNER SUMMARY
    # ========================================================

    runner.display_summary()

    # ========================================================
    # FINAL MESSAGE
    # ========================================================

    print(
        "\nGARUDA SINGLE-CYCLE "
        "ORCHESTRATION DEMO COMPLETED"
    )

    print("=" * 70)


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================


if __name__ == "__main__":

    run_demo()