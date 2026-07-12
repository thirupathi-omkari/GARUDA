class EquityCurve:

    def __init__(self, initial_equity: float):

        if initial_equity <= 0:
            raise ValueError("Initial equity must be positive.")

        self.initial_equity = initial_equity
        self.current_equity = initial_equity
        self.equity_history = [initial_equity]

    def record_trade(self, pnl: float):

        self.current_equity += pnl
        self.equity_history.append(self.current_equity)

    @property
    def trade_count(self):

        return len(self.equity_history) - 1

    @property
    def net_pnl(self):

        return self.current_equity - self.initial_equity

    @property
    def return_percentage(self):

        return (self.net_pnl / self.initial_equity) * 100

    @property
    def peak_equity(self):

        return max(self.equity_history)

    @property
    def lowest_equity(self):

        return min(self.equity_history)