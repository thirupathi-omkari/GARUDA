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


def create_engine():

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    risk_manager = RiskManager(
        account=account,
        config=RiskConfig(
            max_portfolio_exposure_pct=100.0,
        ),
    )

    order_manager = PaperOrderManager()

    position_manager = PaperPositionManager()

    equity_curve = EquityCurve(
        initial_equity=100000.00
    )

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=order_manager,
        broker=SimulatedBroker(),
        position_manager=position_manager,
        equity_curve=equity_curve,
    )

    engine = PaperTradingSessionEngine(
        executor=executor
    )

    return (
        engine,
        account,
        position_manager,
        equity_curve,
    )


def create_strategy_result(
    signal="BUY",
    symbol="INFY",
    entry_price=100.00,
):

    return StrategyResult(
        symbol=symbol,
        strategy_name="ORB_VWAP",
        signal=signal,
        entry_price=entry_price,
        reason="GARUDA automatic exit test",
    )


def create_candle(
    high,
    low,
    close,
):

    return {
        "high": high,
        "low": low,
        "close": close,
    }


def test_existing_exit_rules_are_calculated():

    (
        engine,
        _,
        _,
        _,
    ) = create_engine()

    result = engine.process_entry(
        strategy_result=create_strategy_result(),
        market_price=100.00,
        lot_size=1,
    )

    assert result.status == "POSITION_OPEN"

    assert result.strategy_result.stop_loss == 99.00

    assert result.strategy_result.target_price == 102.00

    exit_levels = engine.get_exit_levels(
        symbol="INFY"
    )

    assert exit_levels[
        "direction"
    ] == "BUY"

    assert exit_levels[
        "stop_loss_price"
    ] == 99.00

    assert exit_levels[
        "target_price"
    ] == 102.00


def test_long_position_remains_open_between_exit_levels():

    (
        engine,
        account,
        position_manager,
        equity_curve,
    ) = create_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(),
        market_price=100.00,
        lot_size=1,
    )

    result = engine.process_market_candle(
        symbol="INFY",
        candle=create_candle(
            high=101.00,
            low=99.50,
            close=100.50,
        ),
    )

    assert result.status == "POSITION_OPEN"

    assert result.exit_reason is None

    assert result.exit_result is None

    assert position_manager.position_count == 1

    assert account.current_capital == 100000.00

    assert equity_curve.trade_count == 0


def test_long_position_automatically_exits_at_target():

    (
        engine,
        account,
        position_manager,
        equity_curve,
    ) = create_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(),
        market_price=100.00,
        lot_size=1,
    )

    result = engine.process_market_candle(
        symbol="INFY",
        candle=create_candle(
            high=102.00,
            low=100.00,
            close=101.50,
        ),
    )

    assert result.status == "POSITION_CLOSED"

    assert result.exit_reason == "TARGET"

    assert result.exit_result.status == "CLOSED"

    assert result.exit_result.exit_price == 102.00

    assert result.exit_result.realized_pnl == 2000.00

    assert account.current_capital == 102000.00

    assert position_manager.position_count == 0

    assert equity_curve.trade_count == 1


def test_long_position_automatically_exits_at_stop_loss():

    (
        engine,
        account,
        position_manager,
        equity_curve,
    ) = create_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(),
        market_price=100.00,
        lot_size=1,
    )

    result = engine.process_market_candle(
        symbol="INFY",
        candle=create_candle(
            high=100.50,
            low=99.00,
            close=99.50,
        ),
    )

    assert result.status == "POSITION_CLOSED"

    assert result.exit_reason == "STOP_LOSS"

    assert result.exit_result.exit_price == 99.00

    assert result.exit_result.realized_pnl == -1000.00

    assert account.current_capital == 99000.00

    assert position_manager.position_count == 0

    assert equity_curve.trade_count == 1


def test_short_position_automatically_exits_at_target():

    (
        engine,
        account,
        position_manager,
        equity_curve,
    ) = create_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(
            signal="SELL",
            symbol="TCS",
        ),
        market_price=100.00,
        lot_size=1,
    )

    exit_levels = engine.get_exit_levels(
        symbol="TCS"
    )

    assert exit_levels[
        "direction"
    ] == "SELL"

    assert exit_levels[
        "stop_loss_price"
    ] == 101.00

    assert exit_levels[
        "target_price"
    ] == 98.00

    result = engine.process_market_candle(
        symbol="TCS",
        candle=create_candle(
            high=100.00,
            low=98.00,
            close=98.50,
        ),
    )

    assert result.status == "POSITION_CLOSED"

    assert result.exit_reason == "TARGET"

    assert result.exit_result.realized_pnl == 2000.00

    assert account.current_capital == 102000.00

    assert position_manager.position_count == 0

    assert equity_curve.trade_count == 1


def test_short_position_automatically_exits_at_stop_loss():

    (
        engine,
        account,
        position_manager,
        equity_curve,
    ) = create_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(
            signal="SELL",
            symbol="TCS",
        ),
        market_price=100.00,
        lot_size=1,
    )

    result = engine.process_market_candle(
        symbol="TCS",
        candle=create_candle(
            high=101.00,
            low=99.50,
            close=100.50,
        ),
    )

    assert result.status == "POSITION_CLOSED"

    assert result.exit_reason == "STOP_LOSS"

    assert result.exit_result.realized_pnl == -1000.00

    assert account.current_capital == 99000.00

    assert position_manager.position_count == 0

    assert equity_curve.trade_count == 1


def test_explicit_strategy_exit_levels_are_preserved():

    (
        engine,
        _,
        _,
        _,
    ) = create_engine()

    strategy_result = StrategyResult(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        signal="BUY",
        entry_price=100.00,
        stop_loss=98.00,
        target_price=104.00,
        reason="Explicit strategy exit levels",
    )

    result = engine.process_entry(
        strategy_result=strategy_result,
        market_price=100.00,
        lot_size=1,
    )

    assert result.status == "POSITION_OPEN"

    exit_levels = engine.get_exit_levels(
        symbol="INFY"
    )

    assert exit_levels[
        "stop_loss_price"
    ] == 98.00

    assert exit_levels[
        "target_price"
    ] == 104.00


def test_exit_levels_removed_after_position_closes():

    (
        engine,
        _,
        _,
        _,
    ) = create_engine()

    engine.process_entry(
        strategy_result=create_strategy_result(),
        market_price=100.00,
        lot_size=1,
    )

    engine.process_market_candle(
        symbol="INFY",
        candle=create_candle(
            high=102.00,
            low=100.00,
            close=101.50,
        ),
    )

    with pytest.raises(ValueError):

        engine.get_exit_levels(
            symbol="INFY"
        )