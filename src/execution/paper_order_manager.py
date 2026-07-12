from execution.paper_order import PaperOrder


class PaperOrderManager:
    """
    Manages virtual orders inside GARUDA's
    paper trading execution system.

    The manager is intentionally independent
    from any specific broker or asset class.
    """

    def __init__(self):

        self._orders = {}

        self._order_sequence = 0


    def _generate_order_id(self):
        """
        Generate the next unique GARUDA
        paper order ID.
        """

        self._order_sequence += 1

        return (
            f"GARUDA-{self._order_sequence:06d}"
        )


    def create_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        order_type: str,
    ):
        """
        Create and store a new paper order.
        """

        order_id = self._generate_order_id()

        order = PaperOrder.create(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
        )

        self._orders[order_id] = order

        return order


    def submit_order(
        self,
        order_id: str,
    ):
        """
        Submit an existing pending order.
        """

        order = self.get_order(
            order_id=order_id
        )

        order.submit()

        return order


    def reject_order(
        self,
        order_id: str,
        reason: str,
    ):
        """
        Reject an existing order.
        """

        order = self.get_order(
            order_id=order_id
        )

        order.reject(
            reason=reason
        )

        return order


    def cancel_order(
        self,
        order_id: str,
    ):
        """
        Cancel an existing order.
        """

        order = self.get_order(
            order_id=order_id
        )

        order.cancel()

        return order


    def get_order(
        self,
        order_id: str,
    ):
        """
        Retrieve an order by its GARUDA
        order ID.
        """

        if order_id not in self._orders:

            raise ValueError(
                "Order not found."
            )

        return self._orders[order_id]


    @property
    def order_count(self):
        """
        Return total number of orders
        created by the manager.
        """

        return len(self._orders)


    @property
    def orders(self):
        """
        Return all orders in creation order.
        """

        return list(
            self._orders.values()
        )