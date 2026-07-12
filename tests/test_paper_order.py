import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from execution.paper_order import (
    PaperOrder,
)


def create_test_order():

    return PaperOrder.create(
        order_id="GARUDA-0001",
        symbol="INFY",
        side="BUY",
        quantity=50,
        order_type="MARKET",
    )


def test_create_buy_market_order():

    order = create_test_order()

    assert order.order_id == "GARUDA-0001"

    assert order.symbol == "INFY"

    assert order.side == "BUY"

    assert order.quantity == 50

    assert order.order_type == "MARKET"

    assert order.status == "PENDING"

    assert order.fill_price is None

    assert order.rejection_reason is None


def test_create_sell_limit_order():

    order = PaperOrder.create(
        order_id="GARUDA-0002",
        symbol="TCS",
        side="SELL",
        quantity=25,
        order_type="LIMIT",
    )

    assert order.symbol == "TCS"

    assert order.side == "SELL"

    assert order.quantity == 25

    assert order.order_type == "LIMIT"

    assert order.status == "PENDING"


def test_order_values_are_normalized():

    order = PaperOrder.create(
        order_id="GARUDA-0003",
        symbol="infy",
        side="buy",
        quantity=50,
        order_type="market",
    )

    assert order.symbol == "INFY"

    assert order.side == "BUY"

    assert order.order_type == "MARKET"


def test_order_requires_order_id():

    with pytest.raises(ValueError):

        PaperOrder.create(
            order_id="",
            symbol="INFY",
            side="BUY",
            quantity=50,
            order_type="MARKET",
        )


def test_order_requires_symbol():

    with pytest.raises(ValueError):

        PaperOrder.create(
            order_id="GARUDA-0001",
            symbol="",
            side="BUY",
            quantity=50,
            order_type="MARKET",
        )


def test_order_requires_valid_side():

    with pytest.raises(ValueError):

        PaperOrder.create(
            order_id="GARUDA-0001",
            symbol="INFY",
            side="INVALID",
            quantity=50,
            order_type="MARKET",
        )


def test_order_requires_positive_quantity():

    with pytest.raises(ValueError):

        PaperOrder.create(
            order_id="GARUDA-0001",
            symbol="INFY",
            side="BUY",
            quantity=0,
            order_type="MARKET",
        )

    with pytest.raises(ValueError):

        PaperOrder.create(
            order_id="GARUDA-0001",
            symbol="INFY",
            side="BUY",
            quantity=-50,
            order_type="MARKET",
        )


def test_order_requires_valid_order_type():

    with pytest.raises(ValueError):

        PaperOrder.create(
            order_id="GARUDA-0001",
            symbol="INFY",
            side="BUY",
            quantity=50,
            order_type="INVALID",
        )


def test_pending_order_can_be_submitted():

    order = create_test_order()

    order.submit()

    assert order.status == "SUBMITTED"


def test_submitted_order_can_be_filled():

    order = create_test_order()

    order.submit()

    order.fill(
        fill_price=1501.50
    )

    assert order.status == "FILLED"

    assert order.fill_price == 1501.50


def test_pending_order_cannot_be_filled():

    order = create_test_order()

    with pytest.raises(ValueError):

        order.fill(
            fill_price=1501.50
        )


def test_fill_price_must_be_positive():

    order = create_test_order()

    order.submit()

    with pytest.raises(ValueError):

        order.fill(
            fill_price=0.00
        )


def test_pending_order_can_be_rejected():

    order = create_test_order()

    order.reject(
        reason="RISK_REJECTED"
    )

    assert order.status == "REJECTED"

    assert (
        order.rejection_reason
        == "RISK_REJECTED"
    )


def test_submitted_order_can_be_rejected():

    order = create_test_order()

    order.submit()

    order.reject(
        reason="EXECUTION_REJECTED"
    )

    assert order.status == "REJECTED"

    assert (
        order.rejection_reason
        == "EXECUTION_REJECTED"
    )


def test_rejection_requires_reason():

    order = create_test_order()

    with pytest.raises(ValueError):

        order.reject(
            reason=""
        )


def test_pending_order_can_be_cancelled():

    order = create_test_order()

    order.cancel()

    assert order.status == "CANCELLED"


def test_submitted_order_can_be_cancelled():

    order = create_test_order()

    order.submit()

    order.cancel()

    assert order.status == "CANCELLED"


def test_filled_order_cannot_be_cancelled():

    order = create_test_order()

    order.submit()

    order.fill(
        fill_price=1501.50
    )

    with pytest.raises(ValueError):

        order.cancel()


def test_filled_order_cannot_be_rejected():

    order = create_test_order()

    order.submit()

    order.fill(
        fill_price=1501.50
    )

    with pytest.raises(ValueError):

        order.reject(
            reason="INVALID"
        )


def test_submitted_order_cannot_be_submitted_again():

    order = create_test_order()

    order.submit()

    with pytest.raises(ValueError):

        order.submit()