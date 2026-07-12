import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.daily_loss_control import (
    calculate_max_daily_loss,
    is_daily_loss_limit_reached,
    is_trading_allowed_by_daily_loss,
)


def test_max_daily_loss_calculation():

    max_daily_loss = calculate_max_daily_loss(
        current_capital=100000.00,
        max_daily_loss_pct=3.0,
    )

    assert max_daily_loss == 3000.00


def test_daily_loss_below_limit():

    limit_reached = is_daily_loss_limit_reached(
        current_capital=100000.00,
        max_daily_loss_pct=3.0,
        daily_realized_pnl=-2000.00,
    )

    assert limit_reached is False


def test_daily_loss_exactly_at_limit():

    limit_reached = is_daily_loss_limit_reached(
        current_capital=100000.00,
        max_daily_loss_pct=3.0,
        daily_realized_pnl=-3000.00,
    )

    assert limit_reached is True


def test_daily_loss_above_limit():

    limit_reached = is_daily_loss_limit_reached(
        current_capital=100000.00,
        max_daily_loss_pct=3.0,
        daily_realized_pnl=-4000.00,
    )

    assert limit_reached is True


def test_trading_allowed_within_daily_loss_limit():

    allowed = is_trading_allowed_by_daily_loss(
        current_capital=100000.00,
        max_daily_loss_pct=3.0,
        daily_realized_pnl=-2000.00,
    )

    assert allowed is True


def test_trading_rejected_when_daily_loss_limit_reached():

    allowed = is_trading_allowed_by_daily_loss(
        current_capital=100000.00,
        max_daily_loss_pct=3.0,
        daily_realized_pnl=-3000.00,
    )

    assert allowed is False