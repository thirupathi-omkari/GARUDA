import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


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


def create_executor(
    initial_capital=100000.00,
):

    account = TradingAccount.create(
        initial_capital=initial_capital
    )

    config = RiskConfig()

    risk_manager = RiskManager(
        account=account,
        config=config,
    )

    order_manager = PaperOrderManager()

    broker = SimulatedBroker()

    position_manager = (
        PaperPositionManager()
    )

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

    return (
        executor,
        account,
        order_manager,
        position_manager,
        equity_curve,
    )


def execute_long_trade(
    executor,
):

    return executor.execute_trade(
        symbol="INFY",
        side="BUY",
        entry_price=500.00,
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )


def execute_short_trade(
    executor,
):

    return executor.execute_trade(
        symbol="TCS",
        side="SELL",
        entry_price=500.00,
        stop_loss_price=520.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )


def test_executor_uses_existing_equity_curve():

    (
        executor,
        _,
        _,
        _,
        equity_curve,
    ) = create_executor()

    assert executor.equity_curve is equity_curve


def test_executor_creates_equity_curve_when_not_provided():

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    risk_manager = RiskManager(
        account=account,
        config=RiskConfig(),
    )

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=PaperOrderManager(),
        broker=SimulatedBroker(),
        position_manager=PaperPositionManager(),
    )

    assert executor.equity_curve.initial_equity == 100000.00

    assert executor.equity_curve.current_equity == 100000.00


def test_profitable_long_trade_updates_account():

    (
        executor,
        account,
        _,
        position_manager,
        _,
    ) = create_executor()

    execute_long_trade(
        executor=executor
    )

    result = executor.close_trade(
        symbol="INFY",
        exit_price=510.00,
    )

    assert result.status == "CLOSED"

    assert result.realized_pnl == 500.00

    assert result.previous_capital == 100000.00

    assert result.current_capital == 100500.00

    assert account.current_capital == 100500.00

    assert position_manager.position_count == 0


def test_losing_long_trade_updates_account():

    (
        executor,
        account,
        _,
        _,
        _,
    ) = create_executor()

    execute_long_trade(
        executor=executor
    )

    result = executor.close_trade(
        symbol="INFY",
        exit_price=490.00,
    )

    assert result.realized_pnl == -500.00

    assert account.current_capital == 99500.00


def test_profitable_short_trade_updates_account():

    (
        executor,
        account,
        _,
        _,
        _,
    ) = create_executor()

    execute_short_trade(
        executor=executor
    )

    result = executor.close_trade(
        symbol="TCS",
        exit_price=490.00,
    )

    assert result.realized_pnl == 500.00

    assert account.current_capital == 100500.00


def test_losing_short_trade_updates_account():

    (
        executor,
        account,
        _,
        _,
        _,
    ) = create_executor()

    execute_short_trade(
        executor=executor
    )

    result = executor.close_trade(
        symbol="TCS",
        exit_price=510.00,
    )

    assert result.realized_pnl == -500.00

    assert account.current_capital == 99500.00


def test_profitable_trade_updates_equity_curve():

    (
        executor,
        _,
        _,
        _,
        equity_curve,
    ) = create_executor()

    execute_long_trade(
        executor=executor
    )

    executor.close_trade(
        symbol="INFY",
        exit_price=510.00,
    )

    assert equity_curve.current_equity == 100500.00

    assert equity_curve.equity_history == [
        100000.00,
        100500.00,
    ]

    assert equity_curve.trade_count == 1

    assert equity_curve.net_pnl == 500.00


def test_losing_trade_updates_equity_curve():

    (
        executor,
        _,
        _,
        _,
        equity_curve,
    ) = create_executor()

    execute_long_trade(
        executor=executor
    )

    executor.close_trade(
        symbol="INFY",
        exit_price=490.00,
    )

    assert equity_curve.current_equity == 99500.00

    assert equity_curve.equity_history == [
        100000.00,
        99500.00,
    ]

    assert equity_curve.trade_count == 1

    assert equity_curve.net_pnl == -500.00


def test_multiple_closed_trades_update_account_and_equity():

    (
        executor,
        account,
        _,
        position_manager,
        equity_curve,
    ) = create_executor()

    execute_long_trade(
        executor=executor
    )

    executor.close_trade(
        symbol="INFY",
        exit_price=510.00,
    )

    execute_short_trade(
        executor=executor
    )

    executor.close_trade(
        symbol="TCS",
        exit_price=490.00,
    )

    assert account.current_capital == 101000.00

    assert equity_curve.current_equity == 101000.00

    assert equity_curve.equity_history == [
        100000.00,
        100500.00,
        101000.00,
    ]

    assert equity_curve.trade_count == 2

    assert equity_curve.net_pnl == 1000.00

    assert position_manager.position_count == 0


def test_next_trade_uses_updated_account_capital():

    (
        executor,
        account,
        _,
        _,
        _,
    ) = create_executor()

    execute_long_trade(
        executor=executor
    )

    executor.close_trade(
        symbol="INFY",
        exit_price=510.00,
    )

    assert account.current_capital == 100500.00

    result = executor.execute_trade(
        symbol="TCS",
        side="BUY",
        entry_price=500.00,
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=500.00,
    )

    assert result.status == "EXECUTED"

    assert result.risk_decision.risk_amount == pytest.approx(
        1005.00
    )

    assert result.order.quantity == 50


def test_unknown_position_does_not_change_account_or_equity():

    (
        executor,
        account,
        _,
        _,
        equity_curve,
    ) = create_executor()

    with pytest.raises(ValueError):

        executor.close_trade(
            symbol="UNKNOWN",
            exit_price=500.00,
        )

    assert account.current_capital == 100000.00

    assert equity_curve.current_equity == 100000.00

    assert equity_curve.trade_count == 0