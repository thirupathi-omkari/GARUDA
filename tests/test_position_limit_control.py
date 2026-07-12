import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.position_limit_control import (
    is_new_position_allowed,
)


def test_position_below_limit():

    allowed = is_new_position_allowed(
        current_open_positions=4,
        max_open_positions=5,
    )

    assert allowed is True


def test_position_exactly_at_limit():

    allowed = is_new_position_allowed(
        current_open_positions=5,
        max_open_positions=5,
    )

    assert allowed is False


def test_position_above_limit():

    allowed = is_new_position_allowed(
        current_open_positions=6,
        max_open_positions=5,
    )

    assert allowed is False


def test_zero_open_positions():

    allowed = is_new_position_allowed(
        current_open_positions=0,
        max_open_positions=5,
    )

    assert allowed is True


def test_negative_open_positions():

    with pytest.raises(ValueError):

        is_new_position_allowed(
            current_open_positions=-1,
            max_open_positions=5,
        )


def test_invalid_max_open_positions():

    with pytest.raises(ValueError):

        is_new_position_allowed(
            current_open_positions=0,
            max_open_positions=0,
        )