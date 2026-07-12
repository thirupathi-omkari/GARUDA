import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.slippage import apply_slippage


def test_buy_entry_slippage():

    adjusted_price = apply_slippage(
        price=100.00,
        direction="BUY",
        slippage_pct=0.05,
        is_entry=True,
    )

    assert round(adjusted_price, 2) == 100.05


def test_buy_exit_slippage():

    adjusted_price = apply_slippage(
        price=100.00,
        direction="BUY",
        slippage_pct=0.05,
        is_entry=False,
    )

    assert round(adjusted_price, 2) == 99.95


def test_sell_entry_slippage():

    adjusted_price = apply_slippage(
        price=100.00,
        direction="SELL",
        slippage_pct=0.05,
        is_entry=True,
    )

    assert round(adjusted_price, 2) == 99.95


def test_sell_exit_slippage():

    adjusted_price = apply_slippage(
        price=100.00,
        direction="SELL",
        slippage_pct=0.05,
        is_entry=False,
    )

    assert round(adjusted_price, 2) == 100.05