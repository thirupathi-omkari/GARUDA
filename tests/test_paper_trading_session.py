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

from risk.equity_curve import (
    EquityCurve,
)

from risk.risk_config import (
    RiskConfig,
)

from risk.risk_manager import (
    RiskManager,
)

from strategy.strategy_result import (
    StrategyResult,
)


def create_session_engine(
    initial_capital=100000.00,
):

    account = TradingAccount.create(
        initial_capital=initial_capital
    )

    risk_manager = RiskManager(
        account=account,
        config=RiskConfig(),
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

    engine = PaperTradingSessionEngine(
        executor=executor
    )

    return (
        engine,
        account,
        order_manager,
        position_manager,
        equity_curve,
    )


def create_strategy_result(
    signal="BUY",
    symbol="INFY",
    entry_price=500.00,
):

    return StrategyResult(
        symbol=symbol,
        strategy_name="ORB_VWAP",
        signal=signal,
        entry_price=entry_price,
        reason="GARUDA test signal",
    )


def test_no_signal_returns_no_trade():

    (
        engine,
        account,
        order_manager,
        position_manager,
        equity_curve,
    ) = create_session_engine()

    result = engine.process_entry(
        strategy_result=create_strategy_result(
            signal="NO_SIGNAL",
            entry_price=None,
        ),
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.status == "NO_TRADE"

    assert result.execution_result is None

    assert account.current_capital == 100000.00

    assert order_manager.order_count == 0

    assert position_manager.position_count == 0

    assert equity_curve.trade_count == 0


def test_buy_entry_opens_long_position():

    (
        engine,
        account,
        order_manager,
        position_manager,
        equity_curve,
    ) = create_session_engine()

    result = engine.process_entry(
        strategy_result=create_strategy_result(
            signal="BUY",
            symbol="INFY",
            entry_price=500.00,
        ),
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.status == "POSITION_OPEN"

    assert result.execution_result.status == "EXECUTED"

    assert result.execution_result.order.side == "BUY"

    assert result.execution_result.position.side == "LONG"

    assert order_manager.order_count == 1

    assert position_manager.position_count == 1

    assert account.current_capital == 100000.00

    assert equity_curve.trade_count == 0


def test_sell_entry_opens_short_position():

    (
        engine,
        _,
        _,
        position_manager,
        _,
    ) = create_session_engine()

    result = engine.process_entry(
        strategy_result=create_strategy_result(
            signal="SELL",
            symbol="TCS",
            entry_price=500.00,
        ),
        stop_loss_price=520.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.status == "POSITION_OPEN"

    assert result.execution_result.order.side == "SELL"

    assert result.execution_result.position.side == "SHORT"

    assert position_manager.position_count == 1


def test_risk_rejection_opens_no_position():

    (
        engine,
        account,
        order_manager,
        position_manager,
        equity_curve,
    ) = create_session_engine()

    result = engine.process_entry(
        strategy_result=create_strategy_result(),
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=5,
        daily_realized_pnl=0.00,
    )

    assert result.status == "REJECTED"

    assert order_manager.order_count == 0

    assert position_manager.position_count == 0

    assert account.current_capital == 100000.00

    assert equity_curve.trade_count == 0


def test_update_long_position_tracks_unrealized_profit():

    (
        engine,
        account,
        _,
        position_manager,
        equity_curve,
    ) = create_session_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(),
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    result = engine.update_position(
        symbol="INFY",
        market_price=510.00,
    )

    assert result.status == "POSITION_UPDATED"

    assert result.current_price == 510.00

    assert result.unrealized_pnl == 500.00

    assert position_manager.position_count == 1

    assert account.current_capital == 100000.00

    assert equity_curve.trade_count == 0


def test_update_long_position_tracks_unrealized_loss():

    (
        engine,
        account,
        _,
        _,
        equity_curve,
    ) = create_session_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(),
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    result = engine.update_position(
        symbol="INFY",
        market_price=490.00,
    )

    assert result.unrealized_pnl == -500.00

    assert account.current_capital == 100000.00

    assert equity_curve.trade_count == 0


def test_update_short_position_tracks_unrealized_profit():

    (
        engine,
        account,
        _,
        _,
        equity_curve,
    ) = create_session_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(
            signal="SELL",
            symbol="TCS",
        ),
        stop_loss_price=520.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    result = engine.update_position(
        symbol="TCS",
        market_price=490.00,
    )

    assert result.unrealized_pnl == 500.00

    assert account.current_capital == 100000.00

    assert equity_curve.trade_count == 0


def test_process_exit_realizes_profit():

    (
        engine,
        account,
        _,
        position_manager,
        equity_curve,
    ) = create_session_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(),
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    engine.update_position(
        symbol="INFY",
        market_price=505.00,
    )

    result = engine.process_exit(
        symbol="INFY",
        exit_price=510.00,
    )

    assert result.status == "CLOSED"

    assert result.realized_pnl == 500.00

    assert account.current_capital == 100500.00

    assert position_manager.position_count == 0

    assert equity_curve.trade_count == 1

    assert equity_curve.current_equity == 100500.00


def test_process_exit_realizes_loss():

    (
        engine,
        account,
        _,
        position_manager,
        equity_curve,
    ) = create_session_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(),
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    result = engine.process_exit(
        symbol="INFY",
        exit_price=490.00,
    )

    assert result.realized_pnl == -500.00

    assert account.current_capital == 99500.00

    assert position_manager.position_count == 0

    assert equity_curve.trade_count == 1

    assert equity_curve.current_equity == 99500.00


def test_position_remains_open_until_explicit_exit():

    (
        engine,
        account,
        _,
        position_manager,
        equity_curve,
    ) = create_session_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(),
        stop_loss_price=480.00,
        market_price=500.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    engine.update_position(
        symbol="INFY",
        market_price=505.00,
    )

    engine.update_position(
        symbol="INFY",
        market_price=507.00,
    )

    engine.update_position(
        symbol="INFY",
        market_price=509.00,
    )

    assert position_manager.position_count == 1

    assert account.current_capital == 100000.00

    assert equity_curve.trade_count == 0

    position = position_manager.get_position(
        symbol="INFY"
    )

    assert position.current_price == 509.00

    assert position.unrealized_pnl == 450.00


def test_invalid_signal_raises_error():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_session_engine()

    with pytest.raises(ValueError):

        engine.process_entry(
            strategy_result=create_strategy_result(
                signal="HOLD",
            ),
            stop_loss_price=480.00,
            market_price=500.00,
            lot_size=1,
            current_exposure=0.00,
            current_open_risk=0.00,
            current_open_positions=0,
            daily_realized_pnl=0.00,
        )


def test_trade_signal_requires_entry_price():

    (
        engine,
        _,
        _,
        _,
        _,
    ) = create_session_engine()

    with pytest.raises(ValueError):

        engine.process_entry(
            strategy_result=create_strategy_result(
                signal="BUY",
                entry_price=None,
            ),
            stop_loss_price=480.00,
            market_price=500.00,
            lot_size=1,
            current_exposure=0.00,
            current_open_risk=0.00,
            current_open_positions=0,
            daily_realized_pnl=0.00,
        )


def test_existing_run_session_remains_compatible():

    (
        engine,
        account,
        _,
        position_manager,
        equity_curve,
    ) = create_session_engine()

    result = engine.run_session(
        strategy_result=create_strategy_result(),
        stop_loss_price=480.00,
        market_price=500.00,
        exit_price=510.00,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.status == "COMPLETED"

    assert result.execution_result.status == "EXECUTED"

    assert result.exit_result.status == "CLOSED"

    assert account.current_capital == 100500.00

    assert position_manager.position_count == 0

    assert equity_curve.trade_count == 1