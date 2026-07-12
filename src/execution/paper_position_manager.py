from execution.paper_order import PaperOrder
from execution.paper_position import PaperPosition


class PaperPositionManager:
    """
    Manages open virtual positions inside
    GARUDA's paper trading system.

    The manager converts filled paper orders
    into virtual positions, maintains current
    market prices, calculates unrealized P&L,
    and closes positions with realized P&L.
    """

    def __init__(self):

        self._positions = {}


    def open_position_from_order(
        self,
        order: PaperOrder,
    ):
        """
        Create an open paper position from
        a successfully filled paper order.
        """

        if order.status != "FILLED":

            raise ValueError(
                "Only filled orders can open positions."
            )

        if order.fill_price is None:

            raise ValueError(
                "Filled order must have a fill price."
            )

        if order.symbol in self._positions:

            raise ValueError(
                "Position already exists for symbol."
            )

        if order.side == "BUY":

            position_side = "LONG"

        elif order.side == "SELL":

            position_side = "SHORT"

        else:

            raise ValueError(
                "Unsupported order side."
            )

        position = PaperPosition.create(
            symbol=order.symbol,
            side=position_side,
            quantity=order.quantity,
            entry_price=order.fill_price,
        )

        self._positions[
            order.symbol
        ] = position

        return position


    def get_position(
        self,
        symbol: str,
    ):
        """
        Retrieve an open position by symbol.
        """

        normalized_symbol = symbol.upper()

        if normalized_symbol not in self._positions:

            raise ValueError(
                "Position not found."
            )

        return self._positions[
            normalized_symbol
        ]


    def update_market_price(
        self,
        symbol: str,
        market_price: float,
    ):
        """
        Update the latest market price
        for an open position.
        """

        position = self.get_position(
            symbol=symbol
        )

        position.update_market_price(
            market_price=market_price
        )

        return position


    def close_position(
        self,
        symbol: str,
        exit_price: float,
    ):
        """
        Close an open virtual position and
        return the position with its realized P&L.

        The returned tuple contains:

        position
        realized_pnl
        """

        if exit_price <= 0:

            raise ValueError(
                "Exit price must be positive."
            )

        position = self.get_position(
            symbol=symbol
        )

        if position.side == "LONG":

            realized_pnl = (
                exit_price
                - position.entry_price
            ) * position.quantity

        elif position.side == "SHORT":

            realized_pnl = (
                position.entry_price
                - exit_price
            ) * position.quantity

        else:

            raise ValueError(
                "Unsupported position side."
            )

        del self._positions[
            position.symbol
        ]

        return position, realized_pnl


    @property
    def position_count(self):
        """
        Return total number of currently
        open paper positions.
        """

        return len(self._positions)


    @property
    def positions(self):
        """
        Return all open positions.
        """

        return list(
            self._positions.values()
        )


    @property
    def total_unrealized_pnl(self):
        """
        Calculate total unrealized P&L
        across all open positions.
        """

        return sum(
            position.unrealized_pnl
            for position in self._positions.values()
        )