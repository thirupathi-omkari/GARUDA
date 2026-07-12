def apply_slippage(
    price,
    direction,
    slippage_pct=0.05,
    is_entry=True,
):
    """Apply adverse slippage to an execution price."""

    slippage_amount = price * (
        slippage_pct / 100
    )

    if direction == "BUY":

        if is_entry:
            adjusted_price = (
                price + slippage_amount
            )
        else:
            adjusted_price = (
                price - slippage_amount
            )

    elif direction == "SELL":

        if is_entry:
            adjusted_price = (
                price - slippage_amount
            )
        else:
            adjusted_price = (
                price + slippage_amount
            )

    else:
        return None

    return adjusted_price