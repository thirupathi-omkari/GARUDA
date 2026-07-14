from dataclasses import dataclass
from datetime import datetime

import pytest

from execution.controlled_live_paper_trading_session import (
    ControlledLivePaperTradingSession,
)


# ============================================================
# TEST SUPPORT MODELS
# ============================================================


@dataclass
class FakePollingRunResult:

    status: str = "COMPLETED"

    requested_cycles: int = 1

    completed_cycles: int = 1

    total_symbol_polls: int = 1

    successful_symbol_polls: int = 1

    failed_symbol_polls: int = 0


class FakeAccount:

    def __init__(
        self,
        initial_capital=100000.0,
        current_capital=102000.0,
    ):

        self.initial_capital = initial_capital

        self.current_capital = current_capital


class FakeRiskManager:

    def __init__(
        self,
        account,
    ):

        self.account = account


class FakeExecutor:

    def __init__(
        self,
        risk_manager,
    ):

        self.risk_manager = risk_manager


class FakeSessionEngine:

    def __init__(
        self,
        executor,
    ):

        self.executor = executor


class FakeRunnerState:

    def __init__(self):

        self.started_at = None

        self.stopped_at = None

        self.running = False


class FakeRunner:

    def __init__(self):

        self.state = FakeRunnerState()

        self.start_call_count = 0

        self.stop_call_count = 0

        self.summary = {
            "registered_symbols": 5,
            "processed_candles": 15,
            "generated_signals": 2,
            "executed_trades": 1,
            "rejected_trades": 1,
            "open_positions": 0,
            "closed_trades": 1,
            "running": False,
        }


    def start(
        self,
        started_at=None,
    ):

        self.start_call_count += 1

        self.state.started_at = started_at

        self.state.stopped_at = None

        self.state.running = True

        return self.state


    def stop(
        self,
        stopped_at=None,
    ):

        self.stop_call_count += 1

        self.state.stopped_at = stopped_at

        self.state.running = False

        return self.state


    def get_summary(self):

        summary = dict(self.summary)

        summary["running"] = (
            self.state.running
        )

        return summary


class FakePollingEngine:

    def __init__(
        self,
        runner,
        session_engine,
    ):

        self.runner = runner

        self.session_engine = session_engine

        self.run_call_count = 0

        self.requested_cycles = None

        self.raise_on_run = False

        self.portfolio_state = {
            "current_exposure": 0.0,
            "current_open_risk": 0.0,
            "current_open_positions": 0,
            "daily_realized_pnl": 2000.0,
        }


    def run(
        self,
        cycles,
    ):

        self.run_call_count += 1

        self.requested_cycles = cycles

        if self.raise_on_run:

            raise RuntimeError(
                "Polling failure."
            )

        return FakePollingRunResult(
            requested_cycles=cycles,
            completed_cycles=cycles,
            total_symbol_polls=(
                cycles * 5
            ),
            successful_symbol_polls=(
                cycles * 5
            ),
            failed_symbol_polls=0,
        )


    def get_portfolio_state(self):

        return dict(
            self.portfolio_state
        )


# ============================================================
# TEST FIXTURE
# ============================================================


@pytest.fixture
def controlled_session_components():

    account = FakeAccount()

    risk_manager = FakeRiskManager(
        account=account
    )

    executor = FakeExecutor(
        risk_manager=risk_manager
    )

    session_engine = FakeSessionEngine(
        executor=executor
    )

    runner = FakeRunner()

    polling_engine = FakePollingEngine(
        runner=runner,
        session_engine=session_engine,
    )

    controller = (
        ControlledLivePaperTradingSession(
            polling_engine=polling_engine
        )
    )

    return {
        "account": account,
        "runner": runner,
        "polling_engine": polling_engine,
        "controller": controller,
    }


# ============================================================
# CONSTRUCTION TESTS
# ============================================================


def test_controlled_session_requires_polling_engine():

    with pytest.raises(
        ValueError,
        match="Polling engine is required.",
    ):

        ControlledLivePaperTradingSession(
            polling_engine=None
        )


# ============================================================
# CYCLE VALIDATION TESTS
# ============================================================


def test_controlled_session_rejects_non_integer_cycles(
    controlled_session_components,
):

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    with pytest.raises(
        TypeError,
        match="cycles must be an integer.",
    ):

        controller.run(
            cycles=1.5
        )


def test_controlled_session_rejects_zero_cycles(
    controlled_session_components,
):

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    with pytest.raises(
        ValueError,
        match=(
            "cycles must be greater than zero."
        ),
    ):

        controller.run(
            cycles=0
        )


def test_controlled_session_rejects_negative_cycles(
    controlled_session_components,
):

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    with pytest.raises(
        ValueError,
        match=(
            "cycles must be greater than zero."
        ),
    ):

        controller.run(
            cycles=-1
        )


# ============================================================
# RUNNER LIFECYCLE TESTS
# ============================================================


def test_controlled_session_starts_runner(
    controlled_session_components,
):

    runner = (
        controlled_session_components[
            "runner"
        ]
    )

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    controller.run(
        cycles=1
    )

    assert runner.start_call_count == 1


def test_controlled_session_stops_runner_after_completion(
    controlled_session_components,
):

    runner = (
        controlled_session_components[
            "runner"
        ]
    )

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    controller.run(
        cycles=1
    )

    assert runner.stop_call_count == 1

    assert runner.state.running is False


# ============================================================
# POLLING COORDINATION TESTS
# ============================================================


def test_controlled_session_runs_requested_cycles(
    controlled_session_components,
):

    polling_engine = (
        controlled_session_components[
            "polling_engine"
        ]
    )

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    result = controller.run(
        cycles=3
    )

    assert polling_engine.run_call_count == 1

    assert polling_engine.requested_cycles == 3

    assert result.requested_cycles == 3

    assert result.completed_cycles == 3


def test_controlled_session_preserves_polling_result(
    controlled_session_components,
):

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    result = controller.run(
        cycles=2
    )

    assert result.polling_result is not None

    assert (
        result.polling_result.requested_cycles
        == 2
    )

    assert (
        result.polling_result.completed_cycles
        == 2
    )


# ============================================================
# FINAL STATE TESTS
# ============================================================


def test_controlled_session_returns_runner_summary(
    controlled_session_components,
):

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    result = controller.run(
        cycles=1
    )

    assert (
        result.runner_summary[
            "registered_symbols"
        ]
        == 5
    )

    assert (
        result.runner_summary[
            "processed_candles"
        ]
        == 15
    )

    assert (
        result.runner_summary[
            "running"
        ]
        is False
    )


def test_controlled_session_returns_portfolio_state(
    controlled_session_components,
):

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    result = controller.run(
        cycles=1
    )

    assert result.portfolio_state == {
        "current_exposure": 0.0,
        "current_open_risk": 0.0,
        "current_open_positions": 0,
        "daily_realized_pnl": 2000.0,
    }


def test_controlled_session_returns_account_state(
    controlled_session_components,
):

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    result = controller.run(
        cycles=1
    )

    assert result.initial_capital == 100000.0

    assert result.current_capital == 102000.0

    assert result.net_realized_pnl == 2000.0


# ============================================================
# INJECTABLE TIME TEST
# ============================================================


def test_controlled_session_uses_injected_session_times(
    controlled_session_components,
):

    polling_engine = (
        controlled_session_components[
            "polling_engine"
        ]
    )

    session_times = iter(
        [
            datetime(
                2026,
                7,
                14,
                9,
                15,
            ),
            datetime(
                2026,
                7,
                14,
                15,
                30,
            ),
        ]
    )

    controller = (
        ControlledLivePaperTradingSession(
            polling_engine=polling_engine,
            current_time_provider=(
                lambda: next(session_times)
            ),
        )
    )

    result = controller.run(
        cycles=1
    )

    assert result.started_at == datetime(
        2026,
        7,
        14,
        9,
        15,
    )

    assert result.stopped_at == datetime(
        2026,
        7,
        14,
        15,
        30,
    )


# ============================================================
# GUARANTEED CLEANUP TEST
# ============================================================


def test_controlled_session_stops_runner_when_polling_fails(
    controlled_session_components,
):

    runner = (
        controlled_session_components[
            "runner"
        ]
    )

    polling_engine = (
        controlled_session_components[
            "polling_engine"
        ]
    )

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    polling_engine.raise_on_run = True

    with pytest.raises(
        RuntimeError,
        match="Polling failure.",
    ):

        controller.run(
            cycles=2
        )

    assert runner.start_call_count == 1

    assert runner.stop_call_count == 1

    assert runner.state.running is False


# ============================================================
# EXISTING STATE PRESERVATION TEST
# ============================================================


def test_controlled_session_uses_existing_component_instances(
    controlled_session_components,
):

    runner = (
        controlled_session_components[
            "runner"
        ]
    )

    polling_engine = (
        controlled_session_components[
            "polling_engine"
        ]
    )

    account = (
        controlled_session_components[
            "account"
        ]
    )

    controller = (
        controlled_session_components[
            "controller"
        ]
    )

    original_runner = runner

    original_session_engine = (
        polling_engine.session_engine
    )

    original_account = account

    controller.run(
        cycles=3
    )

    assert controller.runner is original_runner

    assert (
        controller.session_engine
        is original_session_engine
    )

    assert (
        controller._get_account()
        is original_account
    )