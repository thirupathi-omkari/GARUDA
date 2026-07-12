def calculate_win_rate(trades):
    """Calculate win rate from completed backtest trades."""

    if not trades:
        return 0.0

    total_trades = len(trades)

    winning_trades = sum(
        1
        for trade in trades
        if trade.net_pnl > 0
    )

    win_rate = (
        winning_trades
        / total_trades
    ) * 100

    return win_rate

def calculate_profit_factor(trades):
    """Calculate profit factor from completed backtest trades."""

    if not trades:
        return 0.0

    gross_profit = sum(
        trade.net_pnl
        for trade in trades
        if trade.net_pnl > 0
    )

    gross_loss = abs(
        sum(
            trade.net_pnl
            for trade in trades
            if trade.net_pnl < 0
        )
    )

    if gross_loss == 0:

        if gross_profit > 0:
            return float("inf")

        return 0.0

    profit_factor = (
        gross_profit
        / gross_loss
    )

    return profit_factor

def calculate_expectancy(trades):
    """Calculate average net P&L per completed trade."""

    if not trades:
        return 0.0

    total_net_pnl = sum(
        trade.net_pnl
        for trade in trades
    )

    total_trades = len(trades)

    expectancy = (
        total_net_pnl
        / total_trades
    )

    return expectancy

def calculate_max_drawdown(trades):
    """Calculate maximum drawdown from cumulative net P&L."""

    if not trades:
        return 0.0

    cumulative_pnl = 0.0
    peak_pnl = 0.0
    max_drawdown = 0.0

    for trade in trades:

        cumulative_pnl += trade.net_pnl

        if cumulative_pnl > peak_pnl:
            peak_pnl = cumulative_pnl

        current_drawdown = (
            peak_pnl
            - cumulative_pnl
        )

        if current_drawdown > max_drawdown:
            max_drawdown = current_drawdown

    return max_drawdown


def generate_backtest_summary(trades):
    """Generate summary metrics from completed backtest trades."""

    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "total_net_pnl": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
            "max_drawdown": 0.0,
        }

    winning_trades = sum(
        1
        for trade in trades
        if trade.net_pnl > 0
    )

    losing_trades = sum(
        1
        for trade in trades
        if trade.net_pnl < 0
    )

    breakeven_trades = sum(
        1
        for trade in trades
        if trade.net_pnl == 0
    )

    total_net_pnl = sum(
        trade.net_pnl
        for trade in trades
    )

    return {
        "total_trades": len(trades),
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "breakeven_trades": breakeven_trades,
        "total_net_pnl": total_net_pnl,
        "win_rate": calculate_win_rate(trades),
        "profit_factor": calculate_profit_factor(trades),
        "expectancy": calculate_expectancy(trades),
        "max_drawdown": calculate_max_drawdown(trades),
    }