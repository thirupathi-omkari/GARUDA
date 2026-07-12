from datetime import datetime

import pytest


from execution.live_paper_trading_runner import (
    LivePaperTradingRunner,
)


def create_runner():

    runner = LivePaperTradingRunner()

    runner.register_symbol(
        symbol="INFY",
        instrument_token=408065,
    )

    runner.register_symbol(
        symbol="TCS",
        instrument_token=2953217,
    )

    return runner


def test_runner_starts_empty():

    runner = LivePaperTradingRunner()

    summary = runner.get_summary()

    assert summary[
        "registered_symbols"
    ] == 0

    assert summary[
        "processed_candles"
    ] == 0

    assert summary[
        "generated_signals"
    ] == 0

    assert summary[
        "executed_trades"
    ] == 0

    assert summary[
        "rejected_trades"
    ] == 0

    assert summary[
        "open_positions"
    ] == 0

    assert summary[
        "closed_trades"
    ] == 0

    assert summary[
        "running"
    ] is False


def test_register_symbol():

    runner = LivePaperTradingRunner()

    state = runner.register_symbol(
        symbol="infy",
        instrument_token=408065,
    )

    assert state.symbol == "INFY"

    assert state.instrument_token == 408065

    assert (
        runner.get_summary()[
            "registered_symbols"
        ]
        == 1
    )


def test_duplicate_symbol_is_rejected():

    runner = LivePaperTradingRunner()

    runner.register_symbol(
        symbol="INFY",
        instrument_token=408065,
    )

    with pytest.raises(
        ValueError,
        match="already registered",
    ):

        runner.register_symbol(
            symbol="infy",
            instrument_token=408065,
        )


def test_runner_start_and_stop():

    runner = create_runner()

    started_at = datetime(
        2026,
        7,
        13,
        9,
        10,
    )

    stopped_at = datetime(
        2026,
        7,
        13,
        15,
        30,
    )

    runner.start(
        started_at=started_at
    )

    assert runner.state.running is True

    assert (
        runner.state.started_at
        == started_at
    )

    runner.stop(
        stopped_at=stopped_at
    )

    assert runner.state.running is False

    assert (
        runner.state.stopped_at
        == stopped_at
    )


def test_market_session_timing():

    runner = create_runner()

    assert (
        runner.is_market_session_active(
            datetime(
                2026,
                7,
                13,
                9,
                14,
            )
        )
        is False
    )

    assert (
        runner.is_market_session_active(
            datetime(
                2026,
                7,
                13,
                9,
                15,
            )
        )
        is True
    )

    assert (
        runner.is_market_session_active(
            datetime(
                2026,
                7,
                13,
                15,
                30,
            )
        )
        is True
    )

    assert (
        runner.is_market_session_active(
            datetime(
                2026,
                7,
                13,
                15,
                31,
            )
        )
        is False
    )


def test_new_entry_cutoff_time():

    runner = create_runner()

    assert (
        runner.is_new_entry_allowed_by_time(
            datetime(
                2026,
                7,
                13,
                14,
                59,
            )
        )
        is True
    )

    assert (
        runner.is_new_entry_allowed_by_time(
            datetime(
                2026,
                7,
                13,
                15,
                0,
            )
        )
        is True
    )

    assert (
        runner.is_new_entry_allowed_by_time(
            datetime(
                2026,
                7,
                13,
                15,
                1,
            )
        )
        is False
    )


def test_first_candle_is_new():

    runner = create_runner()

    candle_time = datetime(
        2026,
        7,
        13,
        9,
        20,
    )

    assert (
        runner.is_new_candle(
            symbol="INFY",
            candle_time=candle_time,
        )
        is True
    )


def test_processed_candle_is_not_new():

    runner = create_runner()

    candle_time = datetime(
        2026,
        7,
        13,
        9,
        20,
    )

    runner.mark_candle_processed(
        symbol="INFY",
        candle_time=candle_time,
    )

    assert (
        runner.is_new_candle(
            symbol="INFY",
            candle_time=candle_time,
        )
        is False
    )


def test_older_candle_is_not_new():

    runner = create_runner()

    runner.mark_candle_processed(
        symbol="INFY",
        candle_time=datetime(
            2026,
            7,
            13,
            9,
            25,
        ),
    )

    assert (
        runner.is_new_candle(
            symbol="INFY",
            candle_time=datetime(
                2026,
                7,
                13,
                9,
                20,
            ),
        )
        is False
    )


def test_marking_duplicate_candle_raises_error():

    runner = create_runner()

    candle_time = datetime(
        2026,
        7,
        13,
        9,
        20,
    )

    runner.mark_candle_processed(
        symbol="INFY",
        candle_time=candle_time,
    )

    with pytest.raises(
        ValueError,
        match="already been processed",
    ):

        runner.mark_candle_processed(
            symbol="INFY",
            candle_time=candle_time,
        )


def test_entry_is_allowed_without_open_position():

    runner = create_runner()

    candle_time = datetime(
        2026,
        7,
        13,
        9,
        30,
    )

    assert (
        runner.can_create_entry(
            symbol="INFY",
            candle_time=candle_time,
        )
        is True
    )


def test_execution_opens_position():

    runner = create_runner()

    candle_time = datetime(
        2026,
        7,
        13,
        9,
        30,
    )

    runner.record_signal(
        symbol="INFY"
    )

    runner.record_execution(
        symbol="INFY",
        candle_time=candle_time,
    )

    state = runner.get_symbol_state(
        "INFY"
    )

    assert state.position_open is True

    assert state.generated_signal_count == 1

    assert state.executed_trade_count == 1

    assert (
        state.last_entry_candle_time
        == candle_time
    )


def test_open_position_blocks_duplicate_entry():

    runner = create_runner()

    candle_time = datetime(
        2026,
        7,
        13,
        9,
        30,
    )

    runner.record_execution(
        symbol="INFY",
        candle_time=candle_time,
    )

    assert (
        runner.can_create_entry(
            symbol="INFY",
            candle_time=datetime(
                2026,
                7,
                13,
                9,
                35,
            ),
        )
        is False
    )


def test_same_entry_candle_cannot_reenter():

    runner = create_runner()

    candle_time = datetime(
        2026,
        7,
        13,
        9,
        30,
    )

    runner.record_execution(
        symbol="INFY",
        candle_time=candle_time,
    )

    runner.record_position_closed(
        symbol="INFY"
    )

    assert (
        runner.can_create_entry(
            symbol="INFY",
            candle_time=candle_time,
        )
        is False
    )


def test_new_candle_can_enter_after_position_closed():

    runner = create_runner()

    first_candle_time = datetime(
        2026,
        7,
        13,
        9,
        30,
    )

    second_candle_time = datetime(
        2026,
        7,
        13,
        9,
        35,
    )

    runner.record_execution(
        symbol="INFY",
        candle_time=first_candle_time,
    )

    runner.record_position_closed(
        symbol="INFY"
    )

    assert (
        runner.can_create_entry(
            symbol="INFY",
            candle_time=second_candle_time,
        )
        is True
    )


def test_rejection_is_recorded():

    runner = create_runner()

    runner.record_signal(
        symbol="INFY"
    )

    runner.record_rejection(
        symbol="INFY"
    )

    state = runner.get_symbol_state(
        "INFY"
    )

    assert state.generated_signal_count == 1

    assert state.rejected_trade_count == 1

    assert state.position_open is False


def test_position_close_is_recorded():

    runner = create_runner()

    runner.record_execution(
        symbol="INFY",
        candle_time=datetime(
            2026,
            7,
            13,
            9,
            30,
        ),
    )

    runner.record_position_closed(
        symbol="INFY"
    )

    state = runner.get_symbol_state(
        "INFY"
    )

    assert state.position_open is False

    assert state.closed_trade_count == 1


def test_multi_symbol_summary():

    runner = create_runner()

    runner.start(
        started_at=datetime(
            2026,
            7,
            13,
            9,
            15,
        )
    )

    runner.mark_candle_processed(
        symbol="INFY",
        candle_time=datetime(
            2026,
            7,
            13,
            9,
            20,
        ),
    )

    runner.mark_candle_processed(
        symbol="TCS",
        candle_time=datetime(
            2026,
            7,
            13,
            9,
            20,
        ),
    )

    runner.record_signal(
        symbol="INFY"
    )

    runner.record_execution(
        symbol="INFY",
        candle_time=datetime(
            2026,
            7,
            13,
            9,
            20,
        ),
    )

    runner.record_signal(
        symbol="TCS"
    )

    runner.record_rejection(
        symbol="TCS"
    )

    summary = runner.get_summary()

    assert summary[
        "registered_symbols"
    ] == 2

    assert summary[
        "processed_candles"
    ] == 2

    assert summary[
        "generated_signals"
    ] == 2

    assert summary[
        "executed_trades"
    ] == 1

    assert summary[
        "rejected_trades"
    ] == 1

    assert summary[
        "open_positions"
    ] == 1

    assert summary[
        "closed_trades"
    ] == 0

    assert summary[
        "running"
    ] is True