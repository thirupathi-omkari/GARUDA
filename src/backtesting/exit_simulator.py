from backtesting.trade_lifecycle import (
    evaluate_trade_candle,
)

from risk.break_even_engine import (
    calculate_break_even,
)

from risk.risk_config import RiskConfig


risk_config = RiskConfig()


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

    # --------------------------------------------------
    # INITIAL STOP
    # --------------------------------------------------

    current_stop = stop_loss

    # Keep BacktestTrade synchronized with
    # the active stop used by the simulator.

    trade.current_stop_loss = current_stop

    # --------------------------------------------------
    # INITIAL RISK
    # --------------------------------------------------

    initial_risk = trade.initial_risk

    # --------------------------------------------------
    # CANDLE-BY-CANDLE EXIT SIMULATION
    # --------------------------------------------------

    for _, candle in future_candles.iterrows():

        # --------------------------------------------------
        # STEP 1
        # Evaluate the candle against the CURRENT
        # stop-loss and target.
        #
        # These levels existed BEFORE this candle.
        # --------------------------------------------------

        exit_result = evaluate_trade_candle(
            direction=trade.direction,
            candle=candle,
            stop_loss=current_stop,
            target=target,
        )

        # --------------------------------------------------
        # STEP 2
        # EXIT IF STOP OR TARGET WAS HIT
        # --------------------------------------------------

        if exit_result is not None:

            trade.exit_time = candle[
                "datetime"
            ]

            trade.exit_price = (
                exit_result["exit_price"]
            )

            trade.exit_reason = (
                exit_result["exit_reason"]
            )

            return trade

        # --------------------------------------------------
        # STEP 3
        # BREAK-EVEN MANAGEMENT
        #
        # Only execute after the candle survives.
        #
        # The new stop applies to the NEXT candle.
        # --------------------------------------------------

        if (
            risk_config.break_even_enabled
            and initial_risk is not None
            and initial_risk > 0
        ):

            latest_price = candle["close"]

            current_stop = calculate_break_even(
                mode=risk_config.active_break_even_mode,
                signal=trade.direction,
                entry_price=trade.entry_price,
                current_stop=current_stop,
                latest_price=latest_price,
                initial_risk=initial_risk,
                trigger_multiple=(
                    risk_config.break_even_trigger_multiple
                ),
            )

            trade.current_stop_loss = (
                current_stop
            )

    # --------------------------------------------------
    # END OF DAY
    # --------------------------------------------------

    final_candle = future_candles.iloc[-1]

    trade.exit_time = final_candle[
        "datetime"
    ]

    trade.exit_price = final_candle[
        "close"
    ]

    trade.exit_reason = "END_OF_DAY"

    return trade