from datetime import datetime, timedelta

from broker.session_manager import (
    create_authenticated_session,
)

from backtesting.exit_rules import (
    calculate_exit_levels,
)

from data.instrument_resolver import (
    resolve_instrument_token,
)

from data.live_market_data import (
    fetch_live_intraday_data,
    get_latest_market_price,
)

from execution.paper_order_manager import (
    PaperOrderManager,
)

from execution.paper_position_manager import (
    PaperPositionManager,
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

from risk.equity_curve import (
    EquityCurve,
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


def display_no_signal(
    symbol,
    strategy_result,
):
    """
    Display GARUDA no-signal result.
    """

    print("\n" + "=" * 70)
    print("GARUDA QUANT LAB - LIVE PAPER EXECUTION DEMO")
    print("=" * 70)

    print("\n[STRATEGY RESULT]")
    print("-" * 70)

    print(
        f"Symbol              : "
        f"{symbol}"
    )

    print(
        f"Strategy            : "
        f"{strategy_result.strategy_name}"
    )

    print(
        f"Signal              : "
        f"{strategy_result.signal}"
    )

    print(
        f"Reason              : "
        f"{strategy_result.reason}"
    )

    print("\n[GARUDA DECISION]")
    print("-" * 70)

    print(
        "Action              : "
        "NO PAPER ORDER CREATED"
    )

    print("\n" + "=" * 70)
    print("GARUDA LIVE PAPER EXECUTION DEMO COMPLETED")
    print("=" * 70)


def display_risk_rejection(
    symbol,
    strategy_result,
    exit_levels,
    execution_result,
):
    """
    Display GARUDA risk rejection.
    """

    risk_decision = execution_result.risk_decision

    print("\n" + "=" * 70)
    print("GARUDA QUANT LAB - LIVE PAPER EXECUTION DEMO")
    print("=" * 70)

    print("\n[STRATEGY SIGNAL]")
    print("-" * 70)

    print(
        f"Symbol              : "
        f"{symbol}"
    )

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
        f"{strategy_result.entry_price:.2f}"
    )

    print(
        f"Stop Loss           : "
        f"{exit_levels['stop_loss']:.2f}"
    )

    print(
        f"Target              : "
        f"{exit_levels['target']:.2f}"
    )

    print("\n[RISK EVALUATION]")
    print("-" * 70)

    print(
        f"Decision            : "
        f"{risk_decision.reason}"
    )

    print(
        f"Risk Amount         : "
        f"{risk_decision.risk_amount:,.2f}"
    )

    print(
        f"Raw Position Size   : "
        f"{risk_decision.raw_position_size}"
    )

    print(
        f"Approved Quantity   : "
        f"{risk_decision.approved_quantity}"
    )

    print(
        f"Proposed Exposure   : "
        f"{risk_decision.proposed_exposure:,.2f}"
    )

    print("\n[GARUDA DECISION]")
    print("-" * 70)

    print(
        "Action              : "
        "PAPER TRADE REJECTED"
    )

    print("\n" + "=" * 70)
    print("GARUDA LIVE PAPER EXECUTION DEMO COMPLETED")
    print("=" * 70)


def display_execution_result(
    symbol,
    strategy_result,
    exit_levels,
    execution_result,
    account,
    equity_curve,
):
    """
    Display GARUDA successful paper execution.
    """

    risk_decision = execution_result.risk_decision

    order = execution_result.order

    position = execution_result.position

    print("\n" + "=" * 70)
    print("GARUDA QUANT LAB - LIVE PAPER EXECUTION DEMO")
    print("=" * 70)

    print("\n[STRATEGY SIGNAL]")
    print("-" * 70)

    print(
        f"Symbol              : "
        f"{symbol}"
    )

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
        f"{strategy_result.entry_price:.2f}"
    )

    print(
        f"Stop Loss           : "
        f"{exit_levels['stop_loss']:.2f}"
    )

    print(
        f"Target              : "
        f"{exit_levels['target']:.2f}"
    )

    print(
        f"Reason              : "
        f"{strategy_result.reason}"
    )

    print("\n[RISK EVALUATION]")
    print("-" * 70)

    print(
        "Decision            : "
        "APPROVED"
    )

    print(
        f"Risk Amount         : "
        f"{risk_decision.risk_amount:,.2f}"
    )

    print(
        f"Raw Position Size   : "
        f"{risk_decision.raw_position_size}"
    )

    print(
        f"Approved Quantity   : "
        f"{risk_decision.approved_quantity}"
    )

    print(
        f"Proposed Exposure   : "
        f"{risk_decision.proposed_exposure:,.2f}"
    )

    print("\n[PAPER ORDER]")
    print("-" * 70)

    print(
        f"Order ID            : "
        f"{order.order_id}"
    )

    print(
        f"Symbol              : "
        f"{order.symbol}"
    )

    print(
        f"Side                : "
        f"{order.side}"
    )

    print(
        f"Quantity            : "
        f"{order.quantity}"
    )

    print(
        f"Order Type          : "
        f"{order.order_type}"
    )

    print(
        f"Status              : "
        f"{order.status}"
    )

    print(
        f"Fill Price          : "
        f"{order.fill_price:.2f}"
    )

    print("\n[VIRTUAL POSITION]")
    print("-" * 70)

    print(
        f"Symbol              : "
        f"{position.symbol}"
    )

    print(
        f"Position Side       : "
        f"{position.side}"
    )

    print(
        f"Quantity            : "
        f"{position.quantity}"
    )

    print(
        f"Entry Price         : "
        f"{position.entry_price:.2f}"
    )

    print(
        f"Current Price       : "
        f"{position.current_price:.2f}"
    )

    print(
        f"Unrealized P&L      : "
        f"{position.unrealized_pnl:,.2f}"
    )

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
        f"Equity Trade Count  : "
        f"{equity_curve.trade_count}"
    )

    print("\n[GARUDA STATUS]")
    print("-" * 70)

    print(
        "Real Market Data    : CONNECTED"
    )

    print(
        "Strategy            : EXECUTED"
    )

    print(
        "Risk Manager        : APPROVED"
    )

    print(
        "Real Broker Order   : NOT SENT"
    )

    print(
        "Paper Order         : FILLED"
    )

    print(
        "Virtual Position    : OPEN"
    )

    print("\n" + "=" * 70)
    print("GARUDA LIVE PAPER EXECUTION DEMO COMPLETED")
    print("=" * 70)


def main():
    """
    Run GARUDA's real-market-to-paper-execution demo.

    Flow:

    Authenticated Kite Session
        ↓
    Real Market Data
        ↓
    Existing ORB + VWAP Strategy
        ↓
    Existing Exit Rules
        ↓
    Existing Risk Manager
        ↓
    Existing Position Sizing
        ↓
    Paper Order
        ↓
    Simulated Broker
        ↓
    Virtual Position
    """

    # --------------------------------------------------
    # DEMO CONFIGURATION
    # --------------------------------------------------

    symbol = "INFY"

    exchange = "NSE"

    interval = "5minute"

    initial_capital = 100000.00

    stop_loss_pct = 1.0

    target_pct = 2.0

    lot_size = 1

    # --------------------------------------------------
    # AUTHENTICATED KITE SESSION
    # --------------------------------------------------

    print(
        "\nCreating authenticated Kite session..."
    )

    kite = create_authenticated_session()

    if kite is None:

        print(
            "\nGARUDA Live Paper Execution Demo Failed."
        )

        print(
            "Reason: Authenticated Kite session unavailable."
        )

        return

    # --------------------------------------------------
    # RESOLVE INSTRUMENT
    # --------------------------------------------------

    instrument_token = resolve_instrument_token(
        kite=kite,
        tradingsymbol=symbol,
        exchange=exchange,
    )

    if instrument_token is None:

        print(
            "\nGARUDA Live Paper Execution Demo Failed."
        )

        print(
            f"Reason: Instrument token unavailable "
            f"for {symbol}."
        )

        return

    # --------------------------------------------------
    # FETCH REAL MARKET DATA
    # --------------------------------------------------

    current_time = datetime.now()

    dataframe = fetch_live_intraday_data(
        kite=kite,
        instrument_token=instrument_token,
        from_date=(
            current_time - timedelta(days=5)
        ),
        to_date=current_time,
        interval=interval,
    )

    if dataframe.empty:

        print(
            "\nGARUDA Live Paper Execution Demo Failed."
        )

        print(
            "Reason: No market data available."
        )

        return

    # --------------------------------------------------
    # EXISTING STRATEGY
    # --------------------------------------------------

    strategy = ORBVWAPStrategy()

    strategy_result = strategy.evaluate(
        symbol=symbol,
        dataframe=dataframe,
    )

    # --------------------------------------------------
    # NO SIGNAL
    # --------------------------------------------------

    if strategy_result.signal == "NO_SIGNAL":

        display_no_signal(
            symbol=symbol,
            strategy_result=strategy_result,
        )

        return

    # --------------------------------------------------
    # EXISTING EXIT RULES
    # --------------------------------------------------

    exit_levels = calculate_exit_levels(
        direction=strategy_result.signal,
        entry_price=strategy_result.entry_price,
        stop_loss_pct=stop_loss_pct,
        target_pct=target_pct,
    )

    # --------------------------------------------------
    # EXISTING TRADING ACCOUNT
    # --------------------------------------------------

    account = TradingAccount.create(
        initial_capital=initial_capital
    )

    # --------------------------------------------------
    # EXISTING RISK MANAGER
    # --------------------------------------------------

    risk_manager = RiskManager(
        account=account,
        config=RiskConfig(),
    )

    # --------------------------------------------------
    # EXISTING PAPER COMPONENTS
    # --------------------------------------------------

    order_manager = PaperOrderManager()

    broker = SimulatedBroker()

    position_manager = PaperPositionManager()

    equity_curve = EquityCurve(
        initial_equity=initial_capital
    )

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=order_manager,
        broker=broker,
        position_manager=position_manager,
        equity_curve=equity_curve,
    )

    # --------------------------------------------------
    # LATEST REAL MARKET PRICE
    # --------------------------------------------------

    market_price = get_latest_market_price(
        dataframe
    )

    # --------------------------------------------------
    # EXECUTE THROUGH EXISTING GARUDA PIPELINE
    # --------------------------------------------------

    execution_result = executor.execute_trade(
        symbol=symbol,
        side=strategy_result.signal,
        entry_price=strategy_result.entry_price,
        stop_loss_price=exit_levels["stop_loss"],
        market_price=market_price,
        lot_size=lot_size,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    # --------------------------------------------------
    # RISK REJECTION
    # --------------------------------------------------

    if execution_result.status == "REJECTED":

        display_risk_rejection(
            symbol=symbol,
            strategy_result=strategy_result,
            exit_levels=exit_levels,
            execution_result=execution_result,
        )

        return

    # --------------------------------------------------
    # SUCCESSFUL PAPER EXECUTION
    # --------------------------------------------------

    display_execution_result(
        symbol=symbol,
        strategy_result=strategy_result,
        exit_levels=exit_levels,
        execution_result=execution_result,
        account=account,
        equity_curve=equity_curve,
    )


if __name__ == "__main__":

    main()