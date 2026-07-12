import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.exit_rules import calculate_exit_levels


def test_buy_exit_levels():

    levels = calculate_exit_levels(
        direction="BUY",
        entry_price=100.00,
        stop_loss_pct=1.0,
        target_pct=2.0,
    )

    assert round(
        levels["stop_loss"],
        2,
    ) == 99.00

    assert round(
        levels["target"],
        2,
    ) == 102.00


def test_sell_exit_levels():

    levels = calculate_exit_levels(
        direction="SELL",
        entry_price=100.00,
        stop_loss_pct=1.0,
        target_pct=2.0,
    )

    assert round(
        levels["stop_loss"],
        2,
    ) == 101.00

    assert round(
        levels["target"],
        2,
    ) == 98.00