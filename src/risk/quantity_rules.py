def adjust_quantity_to_lot_size(
    position_size: int,
    lot_size: int,
) -> int:
    """
    Adjust a raw position size downward
    to the nearest valid lot-size multiple.
    """

    if position_size < 0:
        raise ValueError(
            "Position size cannot be negative."
        )

    if lot_size <= 0:
        raise ValueError(
            "Lot size must be greater than zero."
        )

    adjusted_quantity = (
        position_size // lot_size
    ) * lot_size

    return adjusted_quantity