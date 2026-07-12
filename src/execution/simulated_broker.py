from execution.paper_order import PaperOrder


class SimulatedBroker:
    """
    GARUDA's simulated execution broker.

    Executes virtual orders without sending
    orders to a real broker or exchange.

    The broker is intentionally independent
    from any specific asset class so GARUDA
    can later support equities, F&O,
    and crypto execution.
    """

    def execute_market_order(
        self,
        order: PaperOrder,
        market_price: float,
    ):
        """
        Execute a submitted MARKET order
        at the supplied simulated market price.
        """

        if order.status != "SUBMITTED":

            raise ValueError(
                "Only submitted orders can be executed."
            )

        if order.order_type != "MARKET":

            raise ValueError(
                "Only MARKET orders are currently supported."
            )

        if market_price <= 0:

            raise ValueError(
                "Market price must be positive."
            )

        order.fill(
            fill_price=market_price
        )

        return order