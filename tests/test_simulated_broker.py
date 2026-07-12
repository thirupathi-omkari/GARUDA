import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from execution.paper_order_manager import (
    PaperOrderManager,
)

from execution.simulated_broker import (
    SimulatedBroker,
)


def create_submitted_market_order():

    manager = PaperOrderManager()

    order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    manager.submit_order(
        order_id=order.order_id
    )

    return order


def test_simulated_broker_executes_market_order():

    broker = SimulatedBroker()

    order = create_submitted_market_order()

    executed_order = broker.execute_market_order(
        order=order,
        market_price=1501.50,
    )

    assert executed_order is order

    assert order.status == "FILLED"

    assert order.fill_price == 1501.50


def test_buy_market_order_can_be_executed():

    broker = SimulatedBroker()

    order = create_submitted_market_order()

    broker.execute_market_order(
        order=order,
        market_price=1500.00,
    )

    assert order.side == "BUY"

    assert order.status == "FILLED"

    assert order.fill_price == 1500.00


def test_sell_market_order_can_be_executed():

    manager = PaperOrderManager()

    order = manager.create_order(
        symbol="INFY",
        side="SELL",
        quantity=50,
        order_type="MARKET",
    )

    manager.submit_order(
        order_id=order.order_id
    )

    broker = SimulatedBroker()

    broker.execute_market_order(
        order=order,
        market_price=1500.00,
    )

    assert order.side == "SELL"

    assert order.status == "FILLED"

    assert order.fill_price == 1500.00


def test_pending_order_cannot_be_executed():

    manager = PaperOrderManager()

    order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    broker = SimulatedBroker()

    with pytest.raises(ValueError):

        broker.execute_market_order(
            order=order,
            market_price=1500.00,
        )


def test_limit_order_cannot_be_executed_as_market_order():

    manager = PaperOrderManager()

    order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="LIMIT",
    )

    manager.submit_order(
        order_id=order.order_id
    )

    broker = SimulatedBroker()

    with pytest.raises(ValueError):

        broker.execute_market_order(
            order=order,
            market_price=1500.00,
        )


def test_market_price_must_be_positive():

    broker = SimulatedBroker()

    order = create_submitted_market_order()

    with pytest.raises(ValueError):

        broker.execute_market_order(
            order=order,
            market_price=0.00,
        )


def test_filled_order_cannot_be_executed_again():

    broker = SimulatedBroker()

    order = create_submitted_market_order()

    broker.execute_market_order(
        order=order,
        market_price=1500.00,
    )

    with pytest.raises(ValueError):

        broker.execute_market_order(
            order=order,
            market_price=1510.00,
        )


def test_execution_updates_order_stored_by_manager():

    manager = PaperOrderManager()

    order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    manager.submit_order(
        order_id=order.order_id
    )

    broker = SimulatedBroker()

    broker.execute_market_order(
        order=order,
        market_price=1501.50,
    )

    stored_order = manager.get_order(
        order_id=order.order_id
    )

    assert stored_order.status == "FILLED"

    assert stored_order.fill_price == 1501.50