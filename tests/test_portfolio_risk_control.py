import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.portfolio_risk_control import (
    calculate_max_portfolio_risk,
    is_portfolio_risk_allowed,
)


def test_max_portfolio_risk_calculation():

    max_risk = calculate_max_portfolio_risk(
        current_capital=100000.00,
        max_portfolio_risk_pct=5.0,
    )

    assert max_risk == 5000.00


def test_portfolio_risk_within_limit():

    allowed = is_portfolio_risk_allowed(
        current_capital=100000.00,
        max_portfolio_risk_pct=5.0,
        current_open_risk=3200.00,
        proposed_trade_risk=1000.00,
    )

    assert allowed is True


def test_portfolio_risk_exactly_at_limit():

    allowed = is_portfolio_risk_allowed(
        current_capital=100000.00,
        max_portfolio_risk_pct=5.0,
        current_open_risk=4000.00,
        proposed_trade_risk=1000.00,
    )

    assert allowed is True


def test_portfolio_risk_above_limit():

    allowed = is_portfolio_risk_allowed(
        current_capital=100000.00,
        max_portfolio_risk_pct=5.0,
        current_open_risk=4500.00,
        proposed_trade_risk=1000.00,
    )

    assert allowed is False