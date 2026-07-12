from dataclasses import dataclass


VALID_SIDES = {
    "BUY",
    "SELL",
}

VALID_ORDER_TYPES = {
    "MARKET",
    "LIMIT",
}

VALID_ORDER_STATUSES = {
    "PENDING",
    "SUBMITTED",
    "FILLED",
    "REJECTED",
    "CANCELLED",
}


@dataclass
class PaperOrder:
    """
    Represents an order submitted to
    GARUDA's paper trading system.

    The order model is intentionally kept
    independent from any specific broker or
    asset class so GARUDA can later support
    equities, F&O, and crypto execution.
    """

    order_id: str

    symbol: str

    side: str

    quantity: int

    order_type: str

    status: str = "PENDING"

    fill_price: float | None = None

    rejection_reason: str | None = None


    @classmethod
    def create(
        cls,
        order_id: str,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str,
    ):
        """
        Create and validate a new paper order.
        """

        if not order_id:

            raise ValueError(
                "Order ID is required."
            )

        if not symbol:

            raise ValueError(
                "Symbol is required."
            )

        side = side.upper()

        if side not in VALID_SIDES:

            raise ValueError(
                "Side must be BUY or SELL."
            )

        if quantity <= 0:

            raise ValueError(
                "Quantity must be positive."
            )

        order_type = order_type.upper()

        if order_type not in VALID_ORDER_TYPES:

            raise ValueError(
                "Order type must be MARKET or LIMIT."
            )

        return cls(
            order_id=order_id,
            symbol=symbol.upper(),
            side=side,
            quantity=quantity,
            order_type=order_type,
            status="PENDING",
            fill_price=None,
            rejection_reason=None,
        )


    def submit(self):
        """
        Submit a pending order to GARUDA's
        execution layer.
        """

        if self.status != "PENDING":

            raise ValueError(
                "Only pending orders can be submitted."
            )

        self.status = "SUBMITTED"


    def fill(
        self,
        fill_price: float,
    ):
        """
        Fill a submitted order at the
        simulated execution price.
        """

        if self.status != "SUBMITTED":

            raise ValueError(
                "Only submitted orders can be filled."
            )

        if fill_price <= 0:

            raise ValueError(
                "Fill price must be positive."
            )

        self.fill_price = fill_price

        self.status = "FILLED"


    def reject(
        self,
        reason: str,
    ):
        """
        Reject an order before execution.
        """

        if self.status not in {
            "PENDING",
            "SUBMITTED",
        }:

            raise ValueError(
                "Order cannot be rejected "
                "from its current status."
            )

        if not reason:

            raise ValueError(
                "Rejection reason is required."
            )

        self.rejection_reason = reason

        self.status = "REJECTED"


    def cancel(self):
        """
        Cancel an order before execution.
        """

        if self.status not in {
            "PENDING",
            "SUBMITTED",
        }:

            raise ValueError(
                "Order cannot be cancelled "
                "from its current status."
            )

        self.status = "CANCELLED"