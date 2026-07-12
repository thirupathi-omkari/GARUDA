from backtesting.transaction_costs import (
    calculate_transaction_costs,
)


def calculate_trade_pnl(
    trade,
    cost_rate_pct=0.10,
):
    """Calculate gross P&L, costs, and net P&L."""

    if trade is None:
        return None

    if trade.exit_price is None:
        return trade

    if trade.direction == "BUY":

        gross_pnl = (
            trade.exit_price
            - trade.entry_price
        ) * trade.quantity

    elif trade.direction == "SELL":

        gross_pnl = (
            trade.entry_price
            - trade.exit_price
        ) * trade.quantity

    else:
        return trade

    costs = calculate_transaction_costs(
        entry_price=trade.entry_price,
        exit_price=trade.exit_price,
        quantity=trade.quantity,
        cost_rate_pct=cost_rate_pct,
    )

    net_pnl = gross_pnl - costs

    trade.gross_pnl = gross_pnl
    trade.costs = costs
    trade.net_pnl = net_pnl

    return trade