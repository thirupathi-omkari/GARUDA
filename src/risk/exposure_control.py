def calculate_max_exposure(
    current_capital: float,
    max_portfolio_exposure_pct: float,
) -> float:
    """
    Calculate the maximum permitted portfolio exposure.
    """

    return (
        current_capital
        * max_portfolio_exposure_pct
        / 100.0
    )


def is_exposure_allowed(
    current_capital: float,
    max_portfolio_exposure_pct: float,
    current_exposure: float,
    proposed_exposure: float,
) -> bool:
    """
    Check whether adding a proposed position
    would remain within the maximum exposure limit.
    """

    max_exposure = calculate_max_exposure(
        current_capital=current_capital,
        max_portfolio_exposure_pct=(
            max_portfolio_exposure_pct
        ),
    )

    total_exposure = (
        current_exposure
        + proposed_exposure
    )

    return total_exposure <= max_exposure