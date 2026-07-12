import sys
from pathlib import Path


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

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=order_manager,
        broker=broker,
        position_manager=position_manager,
    )

    return (
        executor,
        account,
        order_manager,
        position_manager,
    )


def test_approved_trade_is_executed():

    (
        executor,
        account,
        order_manager,
        position_manager,
    ) = create_executor()

    result = executor.execute_trade(
        symbol="INFY",
        side="BUY",
        entry_price=500.00,
        stop_loss_price=480.00,
        market_price=501.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.status == "EXECUTED"

    assert result.risk_decision.approved is True

    assert result.order is not None

    assert result.position is not None

    assert result.order.status == "FILLED"

    assert result.position.symbol == "INFY"

    assert result.position.side == "LONG"

    assert order_manager.order_count == 1

    assert position_manager.position_count == 1

    assert account.current_capital == 100000.00


def test_approved_quantity_comes_from_risk_manager():

    (
        executor,
        _,
        _,
        _,
    ) = create_executor()

    result = executor.execute_trade(
        symbol="INFY",
        side="BUY",
        entry_price=500.00,
        stop_loss_price=480.00,
        market_price=501.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert (
        result.order.quantity
        == result.risk_decision.approved_quantity
    )

    assert result.order.quantity == 50


def test_buy_order_creates_long_position():

    (
        executor,
        _,
        _,
        _,
    ) = create_executor()

    result = executor.execute_trade(
        symbol="INFY",
        side="BUY",
        entry_price=500.00,
        stop_loss_price=480.00,
        market_price=501.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.order.side == "BUY"

    assert result.position.side == "LONG"


def test_sell_order_creates_short_position():

    (
        executor,
        _,
        _,
        _,
    ) = create_executor()

    result = executor.execute_trade(
        symbol="INFY",
        side="SELL",
        entry_price=500.00,
        stop_loss_price=520.00,
        market_price=499.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.status == "EXECUTED"

    assert result.order.side == "SELL"

    assert result.position.side == "SHORT"


def test_risk_rejected_trade_creates_no_order():

    (
        executor,
        _,
        order_manager,
        position_manager,
    ) = create_executor()

    result = executor.execute_trade(
        symbol="INFY",
        side="BUY",
        entry_price=500.00,
        stop_loss_price=480.00,
        market_price=501.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=5,
        daily_realized_pnl=0.00,
    )

    assert result.status == "REJECTED"

    assert result.risk_decision.approved is False

    assert (
        result.risk_decision.reason
        == "MAX_OPEN_POSITIONS"
    )

    assert result.order is None

    assert result.position is None

    assert order_manager.order_count == 0

    assert position_manager.position_count == 0


def test_daily_loss_rejection_creates_no_order():

    (
        executor,
        _,
        order_manager,
        position_manager,
    ) = create_executor()

    result = executor.execute_trade(
        symbol="INFY",
        side="BUY",
        entry_price=500.00,
        stop_loss_price=480.00,
        market_price=501.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=-4000.00,
    )

    assert result.status == "REJECTED"

    assert result.risk_decision.approved is False

    assert (
        result.risk_decision.reason
        == "DAILY_LOSS_LIMIT"
    )

    assert order_manager.order_count == 0

    assert position_manager.position_count == 0


def test_execution_fill_price_comes_from_market_price():

    (
        executor,
        _,
        _,
        _,
    ) = create_executor()

    result = executor.execute_trade(
        symbol="INFY",
        side="BUY",
        entry_price=500.00,
        stop_loss_price=480.00,
        market_price=502.50,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.order.fill_price == 502.50

    assert result.position.entry_price == 502.50


def test_risk_evaluation_uses_current_account_capital():

    (
        executor,
        account,
        _,
        _,
    ) = create_executor(
        initial_capital=200000.00
    )

    result = executor.execute_trade(
        symbol="INFY",
        side="BUY",
        entry_price=500.00,
        stop_loss_price=480.00,
        market_price=501.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.status == "EXECUTED"

    assert result.risk_decision.risk_amount == 2000.00

    assert result.order.quantity == 100

    assert account.current_capital == 200000.00