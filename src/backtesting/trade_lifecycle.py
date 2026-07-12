def evaluate_trade_candle(
    direction,
    candle,
    stop_loss,
    target,
):
    """Evaluate whether a candle hits stop-loss or target."""

    candle_high = candle["high"]
    candle_low = candle["low"]

    if direction == "BUY":

        if candle_low <= stop_loss:
            return {
                "exit_reason": "STOP_LOSS",
                "exit_price": stop_loss,
            }

        if candle_high >= target:
            return {
                "exit_reason": "TARGET",
                "exit_price": target,
            }

    elif direction == "SELL":

        if candle_high >= stop_loss:
            return {
                "exit_reason": "STOP_LOSS",
                "exit_price": stop_loss,
            }

        if candle_low <= target:
            return {
                "exit_reason": "TARGET",
                "exit_price": target,
            }

    return None