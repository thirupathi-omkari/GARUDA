from dataclasses import dataclass
from datetime import datetime


VALID_POSITION_SIDES = {
    "LONG",
    "SHORT",
}


@dataclass
class PaperPosition:
    """
    Represents an open position in GARUDA's
    paper trading system.

    The model is intentionally asset-neutral
    so it can later support equities, F&O,
    and crypto instruments.
    """

    symbol: str

    side: str

    quantity: int

    entry_price: float

    current_price: float

    entry_time: datetime


    @classmethod
    def create(
        cls,
        symbol: str,
        side: str,
        quantity: int,
        entry_price: float,
        entry_time: datetime = None,
    ):
        """
        Create and validate a new paper position.
        """

        if not symbol:

            raise ValueError(
                "Symbol is required."
            )

        side = side.upper()

        if side not in VALID_POSITION_SIDES:

            raise ValueError(
                "Position side must be LONG or SHORT."
            )

        if quantity <= 0:

            raise ValueError(
                "Quantity must be positive."
            )

        if entry_price <= 0:

            raise ValueError(
                "Entry price must be positive."
            )

        if entry_time is None:

            entry_time = datetime.now()

        return cls(
            symbol=symbol.upper(),
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            entry_time=entry_time
        )


    def update_market_price(
        self,
        market_price: float,
    ):
        """
        Update the latest market price
        for the open position.
        """

        if market_price <= 0:

            raise ValueError(
                "Market price must be positive."
            )

        self.current_price = market_price


    @property
    def market_value(self):
        """
        Calculate the current position value.
        """

        return (
            self.quantity
            * self.current_price
        )


    @property
    def unrealized_pnl(self):
        """
        Calculate unrealized P&L.

        LONG:
        Current Price - Entry Price

        SHORT:
        Entry Price - Current Price
        """

        if self.side == "LONG":

            return (
                self.current_price
                - self.entry_price
            ) * self.quantity

        return (
            self.entry_price
            - self.current_price
        ) * self.quantity

    @property
    def holding_time(self):
        return datetime.now() - self.entry_time

    @property
    def pnl_percentage(self):

        if self.side == "LONG":

            return (
                (self.current_price - self.entry_price)
                / self.entry_price
            ) * 100

        return (
            (self.entry_price - self.current_price)
            / self.entry_price
        ) * 100