from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """Abstract base class for all GARUDA strategies."""

    @property
    @abstractmethod
    def name(self):
        """Return the strategy name."""

        pass

    @abstractmethod
    def evaluate(self, symbol, dataframe):
        """Evaluate market data and return a StrategyResult."""

        pass