def replay_session_candles(session_data):
    """Yield expanding market data windows candle by candle."""

    if session_data is None or session_data.empty:
        return

    for candle_index in range(len(session_data)):

        visible_data = (
            session_data
            .iloc[:candle_index + 1]
            .copy()
            .reset_index(drop=True)
        )

        yield visible_data