import math


def calculate_position_size(
    risk_amount: float,
    entry_price: float,
    stop_loss_price: float,
) -> int:
    """
    Calculate position size based on the maximum
    permitted risk amount and price risk per unit.
    """

    risk_per_unit = abs(
        entry_price - stop_loss_price
    )

    if risk_per_unit <= 0:
        raise ValueError(
            "Risk per unit must be greater than zero."
        )

    position_size = (
        risk_amount / risk_per_unit
    )

    return math.floor(position_size)