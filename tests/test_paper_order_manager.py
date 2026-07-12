import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from execution.paper_order_manager import (
    PaperOrderManager,
)


def create_order_manager():

    return PaperOrderManager()


def test_order_manager_starts_empty():

    manager = create_order_manager()

    assert manager.order_count == 0

    assert manager.orders == []


def test_create_order():

    manager = create_order_manager()

    order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    assert order.order_id == "GARUDA-000001"

    assert order.symbol == "INFY"

    assert order.side == "BUY"

    assert order.quantity == 50

    assert order.order_type == "MARKET"

    assert order.status == "PENDING"

    assert manager.order_count == 1


def test_order_ids_are_unique_and_sequential():

    manager = create_order_manager()

    first_order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    second_order = manager.create_order(
        symbol="TCS",
        side="SELL",
        quantity=25,
        order_type="MARKET",
    )

    third_order = manager.create_order(
        symbol="RELIANCE",
        side="BUY",
        quantity=10,
        order_type="LIMIT",
    )

    assert (
        first_order.order_id
        == "GARUDA-000001"
    )

    assert (
        second_order.order_id
        == "GARUDA-000002"
    )

    assert (
        third_order.order_id
        == "GARUDA-000003"
    )

    assert manager.order_count == 3


def test_get_order():

    manager = create_order_manager()

    created_order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    retrieved_order = manager.get_order(
        order_id=created_order.order_id
    )

    assert retrieved_order is created_order


def test_get_unknown_order_raises_error():

    manager = create_order_manager()

    with pytest.raises(ValueError):

        manager.get_order(
            order_id="GARUDA-999999"
        )


def test_submit_order():

    manager = create_order_manager()

    order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    submitted_order = manager.submit_order(
        order_id=order.order_id
    )

    assert submitted_order.status == "SUBMITTED"

    assert (
        manager.get_order(
            order_id=order.order_id
        ).status
        == "SUBMITTED"
    )


def test_reject_order():

    manager = create_order_manager()

    order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    rejected_order = manager.reject_order(
        order_id=order.order_id,
        reason="RISK_REJECTED",
    )

    assert rejected_order.status == "REJECTED"

    assert (
        rejected_order.rejection_reason
        == "RISK_REJECTED"
    )


def test_cancel_order():

    manager = create_order_manager()

    order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    cancelled_order = manager.cancel_order(
        order_id=order.order_id
    )

    assert cancelled_order.status == "CANCELLED"


def test_orders_preserve_creation_order():

    manager = create_order_manager()

    first_order = manager.create_order(
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )

    second_order = manager.create_order(
        symbol="TCS",
        side="SELL",
        quantity=25,
        order_type="MARKET",
    )

    assert manager.orders == [
        first_order,
        second_order,
    ]


def test_invalid_order_is_not_stored():

    manager = create_order_manager()

    with pytest.raises(ValueError):

        manager.create_order(
            symbol="INFY",
            side="BUY",
            quantity=0,
            order_type="MARKET",
        )

    assert manager.order_count == 0

    assert manager.orders == []