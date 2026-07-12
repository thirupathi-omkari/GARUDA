from dataclasses import dataclass


@dataclass
class TradingAccount:
    """
    Represents the trading account used by GARUDA.
    """

    initial_capital: float
    current_capital: float


    @classmethod
    def create(cls, initial_capital: float):
        """
        Create a new trading account.
        """

        return cls(
            initial_capital=initial_capital,
            current_capital=initial_capital,
        )