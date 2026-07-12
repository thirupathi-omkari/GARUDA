class TradeLedger:
    """Store completed backtest trades."""

    def __init__(self):
        self.trades = []

    def add_trade(self, trade):
        """Add a completed trade to the ledger."""

        if trade is None:
            return

        self.trades.append(trade)

    def get_trades(self):
        """Return all recorded trades."""

        return self.trades

    def trade_count(self):
        """Return number of recorded trades."""

        return len(self.trades)