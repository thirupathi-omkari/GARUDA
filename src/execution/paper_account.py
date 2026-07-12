from dataclasses import dataclass


@dataclass
class PaperTradingAccount:
    """
    Represents GARUDA's virtual paper trading account.
    """

    initial_capital: float

    current_capital: float

    available_cash: float

    realized_pnl: float = 0.0


    @classmethod
    def create(
        cls,
        initial_capital: float,
    ):
        """
        Create a new paper trading account.
        """

        if initial_capital <= 0:

            raise ValueError(
                "Initial capital must be positive."
            )

        return cls(
            initial_capital=initial_capital,
            current_capital=initial_capital,
            available_cash=initial_capital,
            realized_pnl=0.0,
        )


    def record_realized_pnl(
        self,
        pnl: float,
    ):
        """
        Record realized trade P&L and update
        virtual account capital.
        """

        self.realized_pnl += pnl

        self.current_capital += pnl

        self.available_cash += pnl