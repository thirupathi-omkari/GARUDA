import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.position_sizer import (
    calculate_position_size,
)


def test_position_size_calculation():

    position_size = calculate_position_size(
        risk_amount=1000.00,
        entry_price=500.00,
        stop_loss_price=490.00,
    )

    assert position_size == 100