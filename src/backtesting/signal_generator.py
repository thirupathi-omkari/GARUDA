def generate_historical_signals(
    strategy,
    session_data,
    replay_function,
):
    """Generate strategy results from expanding historical data."""

    if session_data is None or session_data.empty:
        return []

    signal_results = []

    for visible_data in replay_function(session_data):

        result = strategy.evaluate(
            symbol="BACKTEST",
            dataframe=visible_data,
        )

        signal_results.append(
            {
                "evaluation_time": (
                    visible_data["datetime"].iloc[-1]
                ),
                "visible_candles": len(visible_data),
                "result": result,
            }
        )

    return signal_results