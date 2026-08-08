from datetime import datetime

import pytest

import pandas as pd

from execution.paper_order_manager import (
    PaperOrderManager,
)

from execution.paper_position_manager import (
    PaperPositionManager,
)

from execution.paper_state_store import (
    PaperStateStore,
)

from execution.paper_trading_session import (
    PaperTradingSessionEngine,
)

from execution.risk_managed_paper_executor import (
    RiskManagedPaperExecutor,
)

from execution.simulated_broker import (
    SimulatedBroker,
)

from risk.account import (
    TradingAccount,
)

from risk.equity_curve import (
    EquityCurve,
)

from risk.risk_config import (
    RiskConfig,
)

from risk.risk_manager import (
    RiskManager,
)

from strategy.strategy_result import (
    StrategyResult,
)


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

def create_paper_session():

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    risk_manager = RiskManager(
        account=account,
        config=RiskConfig(
            max_portfolio_exposure_pct=100.0,
        ),
    )

    order_manager = PaperOrderManager()

    position_manager = (
        PaperPositionManager()
    )

    equity_curve = EquityCurve(
        initial_equity=100000.00
    )

    executor = RiskManagedPaperExecutor(
        risk_manager=risk_manager,
        order_manager=order_manager,
        broker=SimulatedBroker(),
        position_manager=position_manager,
        equity_curve=equity_curve,
    )

    engine = PaperTradingSessionEngine(
        executor=executor
    )

    return (
        engine,
        account,
        position_manager,
    )

def create_restart_strategy_result():

    return StrategyResult(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        signal="BUY",
        entry_price=100.00,
        reason="restart recovery test",
    )


def test_restart_replay_closes_target_after_garuda_was_offline(
    tmp_path,
):

    state_file = (
        tmp_path
        / "paper_state.json"
    )

    state_store = PaperStateStore(
        file_path=state_file
    )

    (
        engine,
        account,
        position_manager,
    ) = create_paper_session()

    runner = LivePaperTradingRunner()

    runner.register_symbol(
        symbol="INFY",
        instrument_token=408065,
    )

    # --------------------------------------------------
    # ORIGINAL SESSION
    # --------------------------------------------------

    entry_result = engine.process_entry(
        strategy_result=(
            create_restart_strategy_result()
        ),
        stop_loss_price=95.00,
        market_price=100.00,
        lot_size=20,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert (
        entry_result.status
        == "POSITION_OPEN"
    )

    runner.record_execution(
        symbol="INFY",
        candle_time=datetime(
            2026,
            8,
            8,
            11,
            30,
        ),
    )

    # --------------------------------------------------
    # FORCE TARGET TO 110
    # --------------------------------------------------

    engine.restore_exit_levels(
        symbol="INFY",
        exit_levels={
            "direction": "BUY",
            "entry_price": 100.00,
            "stop_loss_price": 95.00,
            "target_price": 110.00,
            "initial_stop_loss": 95.00,
            "initial_risk": 5.00,
            "trade_state": "INITIAL",
            "break_even_done": False,
            "trailing_active": False,
        },
    )

    # --------------------------------------------------
    # SAVE BEFORE GARUDA STOPS
    # --------------------------------------------------

    runner.save_state(
        state_store=state_store,
        session_engine=engine,
    )

    # --------------------------------------------------
    # SIMULATED MISSED MARKET DATA
    #
    # 11:35 -> 105
    # 11:40 -> 108
    # 11:45 -> 113  <-- TARGET HIT
    # 11:50 -> 108
    # --------------------------------------------------

    missed_candles = pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp(
                    "2026-08-08 11:35:00"
                ),
                pd.Timestamp(
                    "2026-08-08 11:40:00"
                ),
                pd.Timestamp(
                    "2026-08-08 11:45:00"
                ),
                pd.Timestamp(
                    "2026-08-08 11:50:00"
                ),
            ],
            "open": [
                100.00,
                105.00,
                108.00,
                113.00,
            ],
            "high": [
                105.00,
                108.00,
                113.00,
                108.00,
            ],
            "low": [
                100.00,
                104.00,
                107.00,
                107.00,
            ],
            "close": [
                105.00,
                108.00,
                113.00,
                108.00,
            ],
        }
    )

    # --------------------------------------------------
    # NEW GARUDA PROCESS
    # --------------------------------------------------

    (
        restored_engine,
        restored_account,
        restored_position_manager,
    ) = create_paper_session()

    restored_runner = LivePaperTradingRunner()

    state_store.restore_account(
        restored_account
    )

    state_store.restore_positions(
        restored_position_manager
    )

    state_store.restore_runner(
        restored_runner
    )

    state_store.restore_exit_levels(
        restored_engine
    )

    # --------------------------------------------------
    # REPLAY MISSED CANDLES
    # --------------------------------------------------

    result = (
        restored_runner
        .replay_missed_candles(
            symbol="INFY",
            dataframe=missed_candles,
            session_engine=restored_engine,
        )
    )

    # --------------------------------------------------
    # VERIFY TARGET EXIT
    # --------------------------------------------------

    assert result is not None

    assert (
        result.status
        == "POSITION_CLOSED"
    )

    assert (
        result.exit_reason
        == "TARGET"
    )

    assert (
        result.exit_result.exit_price
        == 110.00
    )

    assert (
        restored_position_manager
        .position_count
        == 0
    )

    assert (
        result.exit_result.realized_pnl
        == 2000.00
    )

    assert (
        restored_account.current_capital
        == 102000.00
    )


def test_restart_replay_closes_stop_loss_after_garuda_was_offline(
    tmp_path,
):

    state_file = (
        tmp_path
        / "paper_state.json"
    )

    state_store = PaperStateStore(
        file_path=state_file
    )

    (
        engine,
        account,
        position_manager,
    ) = create_paper_session()

    runner = LivePaperTradingRunner()

    runner.register_symbol(
        symbol="INFY",
        instrument_token=408065,
    )

    # --------------------------------------------------
    # ORIGINAL SESSION
    # --------------------------------------------------

    entry_result = engine.process_entry(
        strategy_result=(
            create_restart_strategy_result()
        ),
        stop_loss_price=95.00,
        market_price=100.00,
        lot_size=20,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert (
        entry_result.status
        == "POSITION_OPEN"
    )

    runner.record_execution(
        symbol="INFY",
        candle_time=datetime(
            2026,
            8,
            8,
            11,
            30,
        ),
    )

    # --------------------------------------------------
    # RESTORE EXACT EXIT STATE
    # --------------------------------------------------

    engine.restore_exit_levels(
        symbol="INFY",
        exit_levels={
            "direction": "BUY",
            "entry_price": 100.00,
            "stop_loss_price": 95.00,
            "target_price": 110.00,
            "initial_stop_loss": 95.00,
            "initial_risk": 5.00,
            "trade_state": "INITIAL",
            "break_even_done": False,
            "trailing_active": False,
        },
    )

    # --------------------------------------------------
    # SAVE BEFORE GARUDA STOPS
    # --------------------------------------------------

    runner.save_state(
        state_store=state_store,
        session_engine=engine,
    )

    # --------------------------------------------------
    # MISSED CANDLES
    #
    # 11:35 -> 98
    # 11:40 -> 96
    # 11:45 -> 93  <-- STOP LOSS HIT
    # 11:50 -> 97
    # --------------------------------------------------

    missed_candles = pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp(
                    "2026-08-08 11:35:00"
                ),
                pd.Timestamp(
                    "2026-08-08 11:40:00"
                ),
                pd.Timestamp(
                    "2026-08-08 11:45:00"
                ),
                pd.Timestamp(
                    "2026-08-08 11:50:00"
                ),
            ],
            "open": [
                100.00,
                98.00,
                96.00,
                93.00,
            ],
            "high": [
                99.00,
                97.00,
                97.00,
                98.00,
            ],
            "low": [
                97.00,
                95.50,
                93.00,
                92.50,
            ],
            "close": [
                98.00,
                96.00,
                93.00,
                97.00,
            ],
        }
    )

    # --------------------------------------------------
    # NEW GARUDA PROCESS
    # --------------------------------------------------

    (
        restored_engine,
        restored_account,
        restored_position_manager,
    ) = create_paper_session()

    restored_runner = (
        LivePaperTradingRunner()
    )

    state_store.restore_account(
        restored_account
    )

    state_store.restore_positions(
        restored_position_manager
    )

    state_store.restore_runner(
        restored_runner
    )

    state_store.restore_exit_levels(
        restored_engine
    )

    # --------------------------------------------------
    # REPLAY MISSED CANDLES
    # --------------------------------------------------

    result = (
        restored_runner
        .replay_missed_candles(
            symbol="INFY",
            dataframe=missed_candles,
            session_engine=restored_engine,
        )
    )

    # --------------------------------------------------
    # VERIFY STOP LOSS EXIT
    # --------------------------------------------------

    assert result is not None

    assert (
        result.status
        == "POSITION_CLOSED"
    )

    assert (
        result.exit_reason
        == "STOP_LOSS"
    )

    assert (
        result.exit_result.exit_price
        == 95.00
    )

    assert (
        result.exit_result.realized_pnl
        == -1000.00
    )

    assert (
        restored_position_manager
        .position_count
        == 0
    )

    assert (
        restored_account.current_capital
        == 99000.00
    )