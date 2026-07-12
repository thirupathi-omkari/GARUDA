import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


import backtesting.multi_session_risk_backtester as module


def run_test_backtest(
    monkeypatch,
    session_results,
    initial_capital=100000.00,
):

    sessions = [
        {"data": "session_1"},
        {"data": "session_2"},
        {"data": "session_3"},
    ]

    historical_data = pd.DataFrame(
        {
            "close": [
                100.00,
                101.00,
                102.00,
            ],
        }
    )

    monkeypatch.setattr(
        module,
        "prepare_historical_sessions",
        lambda historical_data: sessions,
    )

    result_iterator = iter(
        session_results
    )

    monkeypatch.setattr(
        module,
        "run_pre_execution_risk_backtest",
        lambda **kwargs: next(result_iterator),
    )

    risk_manager = SimpleNamespace(
        account=SimpleNamespace(
            current_capital=initial_capital
        )
    )

    result = module.run_multi_session_risk_backtest(
        symbol="TEST",
        strategy=object(),
        historical_data=historical_data,
        risk_manager=risk_manager,
        stop_loss_pct=1.00,
        target_pct=2.00,
        cost_rate_pct=0.00,
        slippage_pct=0.00,
        lot_size=1,
    )

    return result, risk_manager


def test_only_executed_trades_update_capital(
    monkeypatch,
):

    session_results = [
        SimpleNamespace(
            status="EXECUTED",
            trade=SimpleNamespace(
                net_pnl=2000.00
            ),
        ),
        SimpleNamespace(
            status="REJECTED",
            trade=None,
        ),
        SimpleNamespace(
            status="NO_TRADE",
            trade=None,
        ),
    ]

    result, risk_manager = run_test_backtest(
        monkeypatch=monkeypatch,
        session_results=session_results,
    )

    assert result.initial_capital == 100000.00

    assert result.final_capital == 102000.00

    assert (
        risk_manager.account.current_capital
        == 102000.00
    )

    assert result.total_net_pnl == 2000.00


def test_multi_session_status_counts(
    monkeypatch,
):

    session_results = [
        SimpleNamespace(
            status="EXECUTED",
            trade=SimpleNamespace(
                net_pnl=2000.00
            ),
        ),
        SimpleNamespace(
            status="REJECTED",
            trade=None,
        ),
        SimpleNamespace(
            status="NO_TRADE",
            trade=None,
        ),
    ]

    result, _ = run_test_backtest(
        monkeypatch=monkeypatch,
        session_results=session_results,
    )

    assert result.total_sessions == 3

    assert result.executed_trades == 1

    assert result.rejected_trades == 1

    assert result.no_trade_sessions == 1

    assert (
        result.executed_trades
        + result.rejected_trades
        + result.no_trade_sessions
        == result.total_sessions
    )


def test_only_executed_trades_enter_performance_summary(
    monkeypatch,
):

    session_results = [
        SimpleNamespace(
            status="EXECUTED",
            trade=SimpleNamespace(
                net_pnl=2000.00
            ),
        ),
        SimpleNamespace(
            status="REJECTED",
            trade=None,
        ),
        SimpleNamespace(
            status="NO_TRADE",
            trade=None,
        ),
    ]

    result, _ = run_test_backtest(
        monkeypatch=monkeypatch,
        session_results=session_results,
    )

    summary = result.performance_summary

    assert summary["total_trades"] == 1

    assert summary["winning_trades"] == 1

    assert summary["losing_trades"] == 0

    assert summary["breakeven_trades"] == 0

    assert summary["total_net_pnl"] == 2000.00


def test_multiple_executed_trades_update_capital_sequentially(
    monkeypatch,
):

    session_results = [
        SimpleNamespace(
            status="EXECUTED",
            trade=SimpleNamespace(
                net_pnl=3000.00
            ),
        ),
        SimpleNamespace(
            status="EXECUTED",
            trade=SimpleNamespace(
                net_pnl=-1000.00
            ),
        ),
        SimpleNamespace(
            status="EXECUTED",
            trade=SimpleNamespace(
                net_pnl=2000.00
            ),
        ),
    ]

    result, risk_manager = run_test_backtest(
        monkeypatch=monkeypatch,
        session_results=session_results,
    )

    assert result.executed_trades == 3

    assert result.rejected_trades == 0

    assert result.no_trade_sessions == 0

    assert result.initial_capital == 100000.00

    assert result.final_capital == 104000.00

    assert result.total_net_pnl == 4000.00

    assert result.return_percentage == 4.00

    assert (
        risk_manager.account.current_capital
        == 104000.00
    )


def test_multi_session_pnl_matches_performance_summary(
    monkeypatch,
):

    session_results = [
        SimpleNamespace(
            status="EXECUTED",
            trade=SimpleNamespace(
                net_pnl=3000.00
            ),
        ),
        SimpleNamespace(
            status="EXECUTED",
            trade=SimpleNamespace(
                net_pnl=-1000.00
            ),
        ),
        SimpleNamespace(
            status="EXECUTED",
            trade=SimpleNamespace(
                net_pnl=2000.00
            ),
        ),
    ]

    result, _ = run_test_backtest(
        monkeypatch=monkeypatch,
        session_results=session_results,
    )

    assert (
        result.total_net_pnl
        == result.performance_summary[
            "total_net_pnl"
        ]
    )

    assert (
        result.executed_trades
        == result.performance_summary[
            "total_trades"
        ]
    )


def test_no_executed_trades_preserve_capital(
    monkeypatch,
):

    session_results = [
        SimpleNamespace(
            status="REJECTED",
            trade=None,
        ),
        SimpleNamespace(
            status="NO_TRADE",
            trade=None,
        ),
        SimpleNamespace(
            status="REJECTED",
            trade=None,
        ),
    ]

    result, risk_manager = run_test_backtest(
        monkeypatch=monkeypatch,
        session_results=session_results,
    )

    assert result.executed_trades == 0

    assert result.rejected_trades == 2

    assert result.no_trade_sessions == 1

    assert result.initial_capital == 100000.00

    assert result.final_capital == 100000.00

    assert result.total_net_pnl == 0.00

    assert result.return_percentage == 0.00

    assert (
        risk_manager.account.current_capital
        == 100000.00
    )

    assert (
        result.performance_summary[
            "total_trades"
        ]
        == 0
    )

    assert (
        result.performance_summary[
            "total_net_pnl"
        ]
        == 0.00
    )