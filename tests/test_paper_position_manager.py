import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from execution.paper_order_manager import (
    PaperOrderManager,
)

from execution.paper_position_manager import (
    PaperPositionManager,
)

from execution.simulated_broker import (
    SimulatedBroker,
)


def create_filled_order(
    symbol="INFY",
    side="BUY",
    quantity=50,
    market_price=1500.00,
):

    order_manager = PaperOrderManager()

    order = order_manager.create_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type="MARKET",
    )

    order_manager.submit_order(
        order_id=order.order_id
    )

    broker = SimulatedBroker()

    broker.execute_market_order(
        order=order,
        market_price=market_price,
    )

    return order


def test_position_manager_starts_empty():

    manager = PaperPositionManager()

    assert manager.position_count == 0

    assert manager.positions == []

    assert manager.total_unrealized_pnl == 0.00


def test_filled_buy_order_opens_long_position():

    order = create_filled_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        market_price=1500.00,
    )

    manager = PaperPositionManager()

    position = manager.open_position_from_order(
        order=order
    )

    assert position.symbol == "INFY"

    assert position.side == "LONG"

    assert position.quantity == 50

    assert position.entry_price == 1500.00

    assert position.current_price == 1500.00

    assert manager.position_count == 1


def test_filled_sell_order_opens_short_position():

    order = create_filled_order(
        symbol="TCS",
        side="SELL",
        quantity=25,
        market_price=3000.00,
    )

    manager = PaperPositionManager()

    position = manager.open_position_from_order(
        order=order
    )

    assert position.symbol == "TCS"

    assert position.side == "SHORT"

    assert position.quantity == 25

    assert position.entry_price == 3000.00


def test_pending_order_cannot_open_position():

    order_manager = PaperOrderManager()

    order = order_manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    manager = PaperPositionManager()

    with pytest.raises(ValueError):

        manager.open_position_from_order(
            order=order
        )


def test_submitted_order_cannot_open_position():

    order_manager = PaperOrderManager()

    order = order_manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    order_manager.submit_order(
        order_id=order.order_id
    )

    manager = PaperPositionManager()

    with pytest.raises(ValueError):

        manager.open_position_from_order(
            order=order
        )


def test_get_position():

    order = create_filled_order()

    manager = PaperPositionManager()

    created_position = (
        manager.open_position_from_order(
            order=order
        )
    )

    retrieved_position = manager.get_position(
        symbol="INFY"
    )

    assert retrieved_position is created_position


def test_get_position_normalizes_symbol():

    order = create_filled_order()

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=order
    )

    position = manager.get_position(
        symbol="infy"
    )

    assert position.symbol == "INFY"


def test_unknown_position_raises_error():

    manager = PaperPositionManager()

    with pytest.raises(ValueError):

        manager.get_position(
            symbol="INFY"
        )


def test_duplicate_position_is_rejected():

    first_order = create_filled_order(
        symbol="INFY"
    )

    second_order = create_filled_order(
        symbol="INFY"
    )

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=first_order
    )

    with pytest.raises(ValueError):

        manager.open_position_from_order(
            order=second_order
        )


def test_update_long_position_market_price():

    order = create_filled_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        market_price=1500.00,
    )

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=order
    )

    position = manager.update_market_price(
        symbol="INFY",
        market_price=1520.00,
    )

    assert position.current_price == 1520.00

    assert position.unrealized_pnl == 1000.00


def test_update_short_position_market_price():

    order = create_filled_order(
        symbol="INFY",
        side="SELL",
        quantity=50,
        market_price=1500.00,
    )

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=order
    )

    position = manager.update_market_price(
        symbol="INFY",
        market_price=1480.00,
    )

    assert position.current_price == 1480.00

    assert position.unrealized_pnl == 1000.00


def test_total_unrealized_pnl():

    first_order = create_filled_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        market_price=1500.00,
    )

    second_order = create_filled_order(
        symbol="TCS",
        side="SELL",
        quantity=10,
        market_price=3000.00,
    )

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=first_order
    )

    manager.open_position_from_order(
        order=second_order
    )

    manager.update_market_price(
        symbol="INFY",
        market_price=1520.00,
    )

    manager.update_market_price(
        symbol="TCS",
        market_price=2950.00,
    )

    assert manager.total_unrealized_pnl == 1500.00

    assert manager.position_count == 2


def test_positions_preserve_creation_order():

    first_order = create_filled_order(
        symbol="INFY"
    )

    second_order = create_filled_order(
        symbol="TCS"
    )

    manager = PaperPositionManager()

    first_position = (
        manager.open_position_from_order(
            order=first_order
        )
    )

    second_position = (
        manager.open_position_from_order(
            order=second_order
        )
    )

    assert manager.positions == [
        first_position,
        second_position,
    ]


def test_close_profitable_long_position():

    order = create_filled_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        market_price=1500.00,
    )

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=order
    )

    position, realized_pnl = (
        manager.close_position(
            symbol="INFY",
            exit_price=1520.00,
        )
    )

    assert position.symbol == "INFY"

    assert realized_pnl == 1000.00

    assert manager.position_count == 0


def test_close_losing_long_position():

    order = create_filled_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        market_price=1500.00,
    )

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=order
    )

    _, realized_pnl = manager.close_position(
        symbol="INFY",
        exit_price=1480.00,
    )

    assert realized_pnl == -1000.00

    assert manager.position_count == 0


def test_close_profitable_short_position():

    order = create_filled_order(
        symbol="INFY",
        side="SELL",
        quantity=50,
        market_price=1500.00,
    )

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=order
    )

    _, realized_pnl = manager.close_position(
        symbol="INFY",
        exit_price=1480.00,
    )

    assert realized_pnl == 1000.00

    assert manager.position_count == 0


def test_close_losing_short_position():

    order = create_filled_order(
        symbol="INFY",
        side="SELL",
        quantity=50,
        market_price=1500.00,
    )

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=order
    )

    _, realized_pnl = manager.close_position(
        symbol="INFY",
        exit_price=1520.00,
    )

    assert realized_pnl == -1000.00

    assert manager.position_count == 0


def test_close_position_requires_positive_exit_price():

    order = create_filled_order()

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=order
    )

    with pytest.raises(ValueError):

        manager.close_position(
            symbol="INFY",
            exit_price=0.00,
        )


def test_closed_position_cannot_be_retrieved():

    order = create_filled_order()

    manager = PaperPositionManager()

    manager.open_position_from_order(
        order=order
    )

    manager.close_position(
        symbol="INFY",
        exit_price=1520.00,
    )

    with pytest.raises(ValueError):

        manager.get_position(
            symbol="INFY"
        )