def is_new_position_allowed(
    current_open_positions: int,
    max_open_positions: int,
) -> bool:
    """
    Check whether GARUDA may open
    one additional position.
    """

    if current_open_positions < 0:
        raise ValueError(
            "Current open positions cannot be negative."
        )

    if max_open_positions <= 0:
        raise ValueError(
            "Maximum open positions must be greater than zero."
        )

    return current_open_positions < max_open_positions