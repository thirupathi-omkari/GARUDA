import pandas as pd

from backtesting.trade_lifecycle import (
    evaluate_trade_candle,
)

from risk.break_even_engine import (
    calculate_break_even,
)

from risk.risk_config import RiskConfig

from risk.trailing_stop_engine import (
    calculate_trailing_stop,
)


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

    trade.current_stop_loss = current_stop

    # --------------------------------------------------
    # INITIAL RISK
    # --------------------------------------------------

    initial_risk = trade.initial_risk

    if initial_risk is None:
        initial_risk = abs(
            trade.entry_price - stop_loss
        )

        trade.initial_risk = initial_risk

    if initial_risk <= 0:
        raise ValueError(
            "Initial risk must be greater than zero."
        )

    # --------------------------------------------------
    # MFE / MAE INITIALIZATION
    # --------------------------------------------------

    trade.mfe = 0.0
    trade.mae = 0.0
    trade.mfe_r = 0.0
    trade.mae_r = 0.0

    # --------------------------------------------------
    # CANDLE-BY-CANDLE EXIT SIMULATION
    # --------------------------------------------------

    for candle_index, (_, candle) in enumerate(
        future_candles.iterrows()
    ):

        # --------------------------------------------------
        # MFE / MAE
        #
        # Measure excursion from the entry price using
        # the current candle BEFORE evaluating its exit.
        # --------------------------------------------------

        if trade.direction == "BUY":

            favorable_excursion = (
                candle["high"]
                - trade.entry_price
            )

            adverse_excursion = (
                trade.entry_price
                - candle["low"]
            )

        elif trade.direction == "SELL":

            favorable_excursion = (
                trade.entry_price
                - candle["low"]
            )

            adverse_excursion = (
                candle["high"]
                - trade.entry_price
            )

        else:
            raise ValueError(
                "Trade direction must be BUY or SELL."
            )

        trade.mfe = max(
            trade.mfe,
            max(0.0, favorable_excursion),
        )

        trade.mae = max(
            trade.mae,
            max(0.0, adverse_excursion),
        )

        trade.mfe_r = (
            trade.mfe / initial_risk
        )

        trade.mae_r = (
            trade.mae / initial_risk
        )

        # --------------------------------------------------
        # STEP 1
        # Check the candle against the CURRENT
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

        if exit_result is not None:

            trade.exit_time = (
                candle["datetime"]
            )

            trade.exit_price = (
                exit_result["exit_price"]
            )

            trade.exit_reason = (
                exit_result["exit_reason"]
            )

            return trade

        # --------------------------------------------------
        # STEP 2
        # BREAK-EVEN
        #
        # Update only after the current candle
        # has survived the exit check.
        # --------------------------------------------------

        if (
            risk_config.break_even_enabled
            and initial_risk is not None
            and initial_risk > 0
        ):

            current_stop = calculate_break_even(
                mode=(
                    risk_config
                    .active_break_even_mode
                ),
                signal=trade.direction,
                entry_price=trade.entry_price,
                current_stop=current_stop,
                latest_price=candle["close"],
                initial_risk=initial_risk,
                trigger_multiple=(
                    risk_config
                    .break_even_trigger_multiple
                ),
            )

            trade.current_stop_loss = (
                current_stop
            )

        # --------------------------------------------------
        # STEP 3
        # ATR TRAILING STOP
        #
        # Build historical candles visible up
        # to and including the current candle.
        #
        # The updated trailing stop applies only
        # to the NEXT candle.
        # --------------------------------------------------

        if (
            risk_config.trailing_stop_enabled
        ):

            visible_candles = (
                future_candles
                .iloc[
                    : candle_index + 1
                ]
                .copy()
            )

            new_stop = calculate_trailing_stop(
                mode=(
                    risk_config
                    .active_trailing_stop_mode
                ),
                signal=trade.direction,
                current_stop=current_stop,
                candles=visible_candles,
            )

            # --------------------------------------------------
            # Protect against insufficient ATR history.
            # --------------------------------------------------

            if (
                new_stop is not None
                and pd.notna(new_stop)
            ):

                current_stop = new_stop

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