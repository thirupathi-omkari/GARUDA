import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from execution.paper_position import (
    PaperPosition,
)


def test_create_long_position():

    position = PaperPosition.create(
        symbol="INFY",
        side="LONG",
        quantity=50,
        entry_price=1500.00,
    )

    assert position.symbol == "INFY"

    assert position.side == "LONG"

    assert position.quantity == 50

    assert position.entry_price == 1500.00

    assert position.current_price == 1500.00


def test_create_short_position():

    position = PaperPosition.create(
        symbol="TCS",
        side="SHORT",
        quantity=25,
        entry_price=3000.00,
    )

    assert position.symbol == "TCS"

    assert position.side == "SHORT"

    assert position.quantity == 25

    assert position.entry_price == 3000.00

    assert position.current_price == 3000.00


def test_position_values_are_normalized():

    position = PaperPosition.create(
        symbol="infy",
        side="long",
        quantity=50,
        entry_price=1500.00,
    )

    assert position.symbol == "INFY"

    assert position.side == "LONG"


def test_long_position_profit():

    position = PaperPosition.create(
        symbol="INFY",
        side="LONG",
        quantity=50,
        entry_price=1500.00,
    )

    position.update_market_price(
        market_price=1520.00
    )

    assert position.current_price == 1520.00

    assert position.unrealized_pnl == 1000.00


def test_long_position_loss():

    position = PaperPosition.create(
        symbol="INFY",
        side="LONG",
        quantity=50,
        entry_price=1500.00,
    )

    position.update_market_price(
        market_price=1480.00
    )

    assert position.unrealized_pnl == -1000.00


def test_short_position_profit():

    position = PaperPosition.create(
        symbol="INFY",
        side="SHORT",
        quantity=50,
        entry_price=1500.00,
    )

    position.update_market_price(
        market_price=1480.00
    )

    assert position.unrealized_pnl == 1000.00


def test_short_position_loss():

    position = PaperPosition.create(
        symbol="INFY",
        side="SHORT",
        quantity=50,
        entry_price=1500.00,
    )

    position.update_market_price(
        market_price=1520.00
    )

    assert position.unrealized_pnl == -1000.00


def test_position_market_value():

    position = PaperPosition.create(
        symbol="INFY",
        side="LONG",
        quantity=50,
        entry_price=1500.00,
    )

    position.update_market_price(
        market_price=1520.00
    )

    assert position.market_value == 76000.00


def test_position_requires_symbol():

    with pytest.raises(ValueError):

        PaperPosition.create(
            symbol="",
            side="LONG",
            quantity=50,
            entry_price=1500.00,
        )


def test_position_requires_valid_side():

    with pytest.raises(ValueError):

        PaperPosition.create(
            symbol="INFY",
            side="INVALID",
            quantity=50,
            entry_price=1500.00,
        )


def test_position_requires_positive_quantity():

    with pytest.raises(ValueError):

        PaperPosition.create(
            symbol="INFY",
            side="LONG",
            quantity=0,
            entry_price=1500.00,
        )

    with pytest.raises(ValueError):

        PaperPosition.create(
            symbol="INFY",
            side="LONG",
            quantity=-50,
            entry_price=1500.00,
        )


def test_position_requires_positive_entry_price():

    with pytest.raises(ValueError):

        PaperPosition.create(
            symbol="INFY",
            side="LONG",
            quantity=50,
            entry_price=0.00,
        )


def test_market_price_must_be_positive():

    position = PaperPosition.create(
        symbol="INFY",
        side="LONG",
        quantity=50,
        entry_price=1500.00,
    )

    with pytest.raises(ValueError):

        position.update_market_price(
            market_price=0.00
        )