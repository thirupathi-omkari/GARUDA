def calculate_risk_amount(
    current_capital: float,
    risk_per_trade_pct: float,
) -> float:
    """
    Calculate the maximum capital amount
    that may be risked on a single trade.
    """

    risk_amount = (
        current_capital
        * risk_per_trade_pct
        / 100.0
    )

    return risk_amount