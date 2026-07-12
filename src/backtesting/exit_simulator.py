from backtesting.trade_lifecycle import (
    evaluate_trade_candle,
)


def simulate_trade_exit(
    trade,
    future_candles,
    stop_loss,
    target,
):
    """Simulate trade exit across future candles."""

    if trade is None:
        return None

    if future_candles is None or future_candles.empty:
        return None

    for _, candle in future_candles.iterrows():

        exit_result = evaluate_trade_candle(
            direction=trade.direction,
            candle=candle,
            stop_loss=stop_loss,
            target=target,
        )

        if exit_result is not None:

            trade.exit_time = candle["datetime"]

            trade.exit_price = exit_result[
                "exit_price"
            ]

            trade.exit_reason = exit_result[
                "exit_reason"
            ]

            return trade

    # Neither stop-loss nor target was hit.
    # Close the intraday trade at the final candle close.

    final_candle = future_candles.iloc[-1]

    trade.exit_time = final_candle["datetime"]
    trade.exit_price = final_candle["close"]
    trade.exit_reason = "END_OF_DAY"

    return trade