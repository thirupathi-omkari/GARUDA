import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.exposure_control import (
    calculate_max_exposure,
    is_exposure_allowed,
)


def test_max_exposure_calculation():

    max_exposure = calculate_max_exposure(
        current_capital=100000.00,
        max_portfolio_exposure_pct=50.0,
    )

    assert max_exposure == 50000.00


def test_exposure_within_limit():

    allowed = is_exposure_allowed(
        current_capital=100000.00,
        max_portfolio_exposure_pct=50.0,
        current_exposure=30000.00,
        proposed_exposure=15000.00,
    )

    assert allowed is True


def test_exposure_exactly_at_limit():

    allowed = is_exposure_allowed(
        current_capital=100000.00,
        max_portfolio_exposure_pct=50.0,
        current_exposure=30000.00,
        proposed_exposure=20000.00,
    )

    assert allowed is True


def test_exposure_above_limit():

    allowed = is_exposure_allowed(
        current_capital=100000.00,
        max_portfolio_exposure_pct=50.0,
        current_exposure=40000.00,
        proposed_exposure=15000.00,
    )

    assert allowed is False