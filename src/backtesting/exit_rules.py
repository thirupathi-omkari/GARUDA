def calculate_exit_levels(
    direction,
    entry_price,
    stop_loss_pct=1.0,
    target_pct=2.0,
):
    """Calculate stop-loss and target levels."""

    if direction == "BUY":

        stop_loss = entry_price * (
            1 - stop_loss_pct / 100
        )

        target = entry_price * (
            1 + target_pct / 100
        )

    elif direction == "SELL":

        stop_loss = entry_price * (
            1 + stop_loss_pct / 100
        )

        target = entry_price * (
            1 - target_pct / 100
        )

    else:
        return None

    return {
        "stop_loss": stop_loss,
        "target": target,
    }