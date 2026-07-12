def calculate_max_daily_loss(
    current_capital: float,
    max_daily_loss_pct: float,
) -> float:
    """
    Calculate the maximum permitted loss
    for a trading day.
    """

    return (
        current_capital
        * max_daily_loss_pct
        / 100.0
    )


def is_daily_loss_limit_reached(
    current_capital: float,
    max_daily_loss_pct: float,
    daily_realized_pnl: float,
) -> bool:
    """
    Check whether the maximum daily loss
    limit has been reached or exceeded.
    """

    max_daily_loss = calculate_max_daily_loss(
        current_capital=current_capital,
        max_daily_loss_pct=max_daily_loss_pct,
    )

    return daily_realized_pnl <= -max_daily_loss


def is_trading_allowed_by_daily_loss(
    current_capital: float,
    max_daily_loss_pct: float,
    daily_realized_pnl: float,
) -> bool:
    """
    Check whether new trades are allowed
    under the daily loss rule.
    """

    return not is_daily_loss_limit_reached(
        current_capital=current_capital,
        max_daily_loss_pct=max_daily_loss_pct,
        daily_realized_pnl=daily_realized_pnl,
    )