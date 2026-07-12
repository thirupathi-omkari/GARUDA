import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.quantity_rules import (
    adjust_quantity_to_lot_size,
)


def test_quantity_adjustment_to_lot_size():

    adjusted_quantity = (
        adjust_quantity_to_lot_size(
            position_size=137,
            lot_size=25,
        )
    )

    assert adjusted_quantity == 125


def test_quantity_smaller_than_lot_size():

    adjusted_quantity = (
        adjust_quantity_to_lot_size(
            position_size=20,
            lot_size=25,
        )
    )

    assert adjusted_quantity == 0


def test_exact_lot_size_quantity():

    adjusted_quantity = (
        adjust_quantity_to_lot_size(
            position_size=100,
            lot_size=25,
        )
    )

    assert adjusted_quantity == 100


def test_invalid_lot_size():

    with pytest.raises(ValueError):

        adjust_quantity_to_lot_size(
            position_size=100,
            lot_size=0,
        )


def test_negative_position_size():

    with pytest.raises(ValueError):

        adjust_quantity_to_lot_size(
            position_size=-10,
            lot_size=25,
        )