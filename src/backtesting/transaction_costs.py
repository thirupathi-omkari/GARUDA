def calculate_transaction_costs(
    entry_price,
    exit_price,
    quantity,
    cost_rate_pct=0.10,
):
    """Calculate simplified round-trip transaction costs."""

    entry_turnover = entry_price * quantity
    exit_turnover = exit_price * quantity

    total_turnover = (
        entry_turnover
        + exit_turnover
    )

    costs = total_turnover * (
        cost_rate_pct / 100
    )

    return costs