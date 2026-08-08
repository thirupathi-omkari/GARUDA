import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(
    0,
    str(SRC_DIR),
)

from risk.account import TradingAccount

from execution.paper_position_manager import (
    PaperPositionManager,
)

from execution.paper_state_store import (
    PaperStateStore,
)


def test_paper_state_store_saves_and_restores_account(
    tmp_path,
):

    state_file = (
        tmp_path
        / "paper_state.json"
    )

    store = PaperStateStore(
        file_path=state_file
    )

    account = TradingAccount.create(
        initial_capital=100000.0
    )

    account.current_capital = (
        102500.0
    )

    position_manager = (
        PaperPositionManager()
    )

    store.save(
        account=account,
        position_manager=position_manager,
    )

    restored_account = (
        TradingAccount.create(
            initial_capital=1.0
        )
    )

    store.restore_account(
        restored_account
    )

    assert (
        restored_account.initial_capital
        == 100000.0
    )

    assert (
        restored_account.current_capital
        == 102500.0
    )


def test_paper_state_store_restores_open_position(
    tmp_path,
):

    state_file = (
        tmp_path
        / "paper_state.json"
    )

    store = PaperStateStore(
        file_path=state_file
    )

    account = TradingAccount.create(
        initial_capital=100000.0
    )

    position_manager = (
        PaperPositionManager()
    )

    original_position = (
        position_manager.restore_position(
            symbol="INFY",
            side="LONG",
            quantity=10,
            entry_price=1500.0,
            current_price=1510.0,
            entry_time=datetime(
                2026,
                8,
                8,
                9,
                40,
            ),
        )
    )

    store.save(
        account=account,
        position_manager=position_manager,
    )

    restored_manager = (
        PaperPositionManager()
    )

    store.restore_positions(
        restored_manager
    )

    assert (
        restored_manager.position_count
        == 1
    )

    restored_position = (
        restored_manager.get_position(
            "INFY"
        )
    )

    assert (
        restored_position.symbol
        == "INFY"
    )

    assert (
        restored_position.side
        == "LONG"
    )

    assert (
        restored_position.quantity
        == 10
    )

    assert (
        restored_position.entry_price
        == 1500.0
    )

    assert (
        restored_position.current_price
        == 1510.0
    )

    assert (
        restored_position.entry_time
        == datetime(
            2026,
            8,
            8,
            9,
            40,
        )
    )


def test_paper_state_store_missing_file_does_not_reset_account(
    tmp_path,
):

    state_file = (
        tmp_path
        / "missing_state.json"
    )

    store = PaperStateStore(
        file_path=state_file
    )

    account = TradingAccount.create(
        initial_capital=100000.0
    )

    account.current_capital = (
        100500.0
    )

    store.restore_account(
        account
    )

    assert (
        account.initial_capital
        == 100000.0
    )

    assert (
        account.current_capital
        == 100500.0
    )


def test_paper_state_store_restores_exit_levels(
    tmp_path,
):

    state_file = (
        tmp_path
        / "paper_state.json"
    )

    store = PaperStateStore(
        file_path=state_file
    )

    account = TradingAccount.create(
        initial_capital=100000.0
    )

    position_manager = (
        PaperPositionManager()
    )

    # Minimal fake session engine.
    # We only need its active exit state
    # for this persistence test.
    class FakeSessionEngine:

        def __init__(self):

            self._active_exit_levels = {}

        def restore_exit_levels(
            self,
            symbol,
            exit_levels,
        ):

            self._active_exit_levels[
                symbol.upper()
            ] = dict(exit_levels)

    session_engine = (
        FakeSessionEngine()
    )

    session_engine._active_exit_levels[
        "INFY"
    ] = {
        "direction": "BUY",
        "entry_price": 100.0,
        "stop_loss_price": 95.0,
        "target_price": 110.0,
        "initial_stop_loss": 95.0,
        "initial_risk": 5.0,
        "trade_state": "INITIAL",
        "break_even_done": False,
        "trailing_active": False,
    }

    store.save(
        account=account,
        position_manager=position_manager,
        session_engine=session_engine,
    )

    restored_session_engine = (
        FakeSessionEngine()
    )

    store.restore_exit_levels(
        restored_session_engine
    )

    assert (
        "INFY"
        in restored_session_engine
        ._active_exit_levels
    )

    restored_levels = (
        restored_session_engine
        ._active_exit_levels["INFY"]
    )

    assert (
        restored_levels["direction"]
        == "BUY"
    )

    assert (
        restored_levels["entry_price"]
        == 100.0
    )

    assert (
        restored_levels["stop_loss_price"]
        == 95.0
    )

    assert (
        restored_levels["target_price"]
        == 110.0
    )

    assert (
        restored_levels["initial_risk"]
        == 5.0
    )

    assert (
        restored_levels["trade_state"]
        == "INITIAL"
    )

    assert (
        restored_levels["break_even_done"]
        is False
    )

    assert (
        restored_levels["trailing_active"]
        is False
    )