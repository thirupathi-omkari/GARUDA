import pandas as pd

from backtesting.candle_replay import (
    replay_session_candles,
)

from backtesting.entry_simulator import (
    simulate_entry,
)


from backtesting.exit_simulator import (
    simulate_trade_exit,
)

from backtesting.pnl_calculator import (
    calculate_trade_pnl,
)

from backtesting.slippage import (
    apply_slippage,
)


def run_session_backtest(
    symbol,
    strategy,
    session_data,
    stop_loss_pct=1.0,
    target_pct=2.0,
    cost_rate_pct=0.10,
    slippage_pct=0.05,
    historical_context=None,
):
    """Run one strategy backtest over one trading session."""

    if session_data is None or session_data.empty:
        return None

    replay_steps = list(
        replay_session_candles(
            session_data
        )
    )

    for step_index, visible_data in enumerate(
        replay_steps
    ):

        # --------------------------------------------------
        # STRATEGY CONTEXT
        #
        # visible_data contains ONLY the current
        # trading session.
        #
        # historical_context contains candles from
        # previous sessions and is used only for
        # indicator warm-up such as ATR.
        #
        # This prevents previous-day candles from
        # becoming part of the current session replay.
        # --------------------------------------------------

        if (
            historical_context is not None
            and not historical_context.empty
        ):

            strategy_data = pd.concat(
                [
                    historical_context,
                    visible_data,
                ],
                ignore_index=True,
            )

        else:

            strategy_data = visible_data

        result = strategy.evaluate(
            symbol=symbol,
            dataframe=strategy_data,
        )

        if result.signal not in (
            "BUY",
            "SELL",
        ):
            continue

        next_candle_index = (
            step_index + 1
        )

        if next_candle_index >= len(
            session_data
        ):
            return None

        signal_record = {
            "evaluation_time": (
                visible_data[
                    "datetime"
                ].iloc[-1]
            ),
            "visible_candles": len(
                visible_data
            ),
            "result": result,
        }

        next_candle = session_data.iloc[
            next_candle_index
        ]

        trade = simulate_entry(
            symbol=symbol,
            strategy_name=(
                result.strategy_name
            ),
            signal_record=signal_record,
            next_candle=next_candle,
        )

        if trade is None:
            continue

        # Apply adverse entry slippage.

        trade.entry_price = apply_slippage(
            price=trade.entry_price,
            direction=trade.direction,
            slippage_pct=slippage_pct,
            is_entry=True,
        )

        # Calculate stop-loss and target
        # from the actual simulated entry price.

        # Use the dynamic stop-loss and target
        # already calculated by the strategy
        # and carried by BacktestTrade.

        stop_loss = trade.current_stop_loss
        target = trade.target_price

        if (
            stop_loss is None
            or target is None
        ):
            return None

        # The entry candle is included because entry
        # occurs at its open.

        future_candles = session_data.iloc[
            next_candle_index:
        ].copy()

        trade = simulate_trade_exit(
            trade=trade,
            future_candles=future_candles,
            stop_loss=stop_loss,
            target=target,
        )

        if trade.exit_price is None:
            return trade

        # Apply adverse exit slippage.

        trade.exit_price = apply_slippage(
            price=trade.exit_price,
            direction=trade.direction,
            slippage_pct=slippage_pct,
            is_entry=False,
        )

        # Calculate final P&L and costs.

        trade = calculate_trade_pnl(
            trade=trade,
            cost_rate_pct=cost_rate_pct,
        )

        return trade

    return None