def calculate_max_portfolio_risk(
    current_capital: float,
    max_portfolio_risk_pct: float,
) -> float:
    """
    Calculate the maximum permitted portfolio risk.
    """

    return (
        current_capital
        * max_portfolio_risk_pct
        / 100.0
    )


def is_portfolio_risk_allowed(
    current_capital: float,
    max_portfolio_risk_pct: float,
    current_open_risk: float,
    proposed_trade_risk: float,
) -> bool:
    """
    Check whether adding a proposed trade
    would remain within the maximum
    portfolio-risk limit.
    """

    max_portfolio_risk = (
        calculate_max_portfolio_risk(
            current_capital=current_capital,
            max_portfolio_risk_pct=(
                max_portfolio_risk_pct
            ),
        )
    )

    total_portfolio_risk = (
        current_open_risk
        + proposed_trade_risk
    )

    return (
        total_portfolio_risk
        <= max_portfolio_risk
    )