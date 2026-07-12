import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.account import TradingAccount
from risk.risk_config import RiskConfig
from risk.risk_manager import RiskManager


def create_risk_manager():

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=50.0,
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    return RiskManager(
        account=account,
        config=config,
    )


def test_risk_manager_approves_valid_trade():

    manager = create_risk_manager()

    decision = manager.evaluate_trade(
        entry_price=500.00,
        stop_loss_price=490.00,
        lot_size=25,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert decision.approved is True

    assert decision.reason == "APPROVED"

    assert decision.risk_amount == 1000.00

    assert decision.raw_position_size == 100

    assert decision.approved_quantity == 100

    assert decision.proposed_exposure == 50000.00


def test_risk_manager_rejects_daily_loss_limit():

    manager = create_risk_manager()

    decision = manager.evaluate_trade(
        entry_price=500.00,
        stop_loss_price=490.00,
        lot_size=25,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=-3000.00,
    )

    assert decision.approved is False

    assert decision.reason == "DAILY_LOSS_LIMIT"

    assert decision.approved_quantity == 0


def test_risk_manager_rejects_max_open_positions():

    manager = create_risk_manager()

    decision = manager.evaluate_trade(
        entry_price=500.00,
        stop_loss_price=490.00,
        lot_size=25,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=5,
        daily_realized_pnl=0.00,
    )

    assert decision.approved is False

    assert decision.reason == "MAX_OPEN_POSITIONS"

    assert decision.approved_quantity == 0


def test_risk_manager_rejects_quantity_below_minimum_lot():

    manager = create_risk_manager()

    decision = manager.evaluate_trade(
        entry_price=500.00,
        stop_loss_price=450.00,
        lot_size=25,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert decision.approved is False

    assert (
        decision.reason
        == "QUANTITY_BELOW_MINIMUM_LOT"
    )

    assert decision.risk_amount == 1000.00

    assert decision.raw_position_size == 20

    assert decision.approved_quantity == 0


def test_risk_manager_rejects_max_portfolio_exposure():

    manager = create_risk_manager()

    decision = manager.evaluate_trade(
        entry_price=500.00,
        stop_loss_price=490.00,
        lot_size=25,
        current_exposure=10000.00,
        current_open_risk=0.00,
        current_open_positions=1,
        daily_realized_pnl=0.00,
    )

    assert decision.approved is False

    assert (
        decision.reason
        == "MAX_PORTFOLIO_EXPOSURE"
    )

    assert decision.risk_amount == 1000.00

    assert decision.raw_position_size == 100

    assert decision.approved_quantity == 100

    assert decision.proposed_exposure == 50000.00


def test_risk_manager_rejects_max_portfolio_risk():

    manager = create_risk_manager()

    decision = manager.evaluate_trade(
        entry_price=250.00,
        stop_loss_price=245.00,
        lot_size=25,
        current_exposure=0.00,
        current_open_risk=4500.00,
        current_open_positions=4,
        daily_realized_pnl=0.00,
    )

    assert decision.approved is False

    assert decision.reason == "MAX_PORTFOLIO_RISK"

    assert decision.risk_amount == 1000.00

    assert decision.raw_position_size == 200

    assert decision.approved_quantity == 200

    assert decision.proposed_exposure == 50000.00