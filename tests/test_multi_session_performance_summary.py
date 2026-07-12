import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


import backtesting.multi_session_risk_backtester as module


def create_test_result():

    historical_data = pd.DataFrame(
        {
            "date": [
                "2026-01-01",
                "2026-01-02",
                "2026-01-03",
            ],
            "close": [
                100.00,
                101.00,
                102.00,
            ],
        }
    )

    sessions = [
        {"data": "session_1"},
        {"data": "session_2"},
        {"data": "session_3"},
    ]

    return historical_data, sessions


def test_multi_session_performance_summary(monkeypatch):

    historical_data, sessions = create_test_result()

    monkeypatch.setattr(
        module,
        "prepare_historical_sessions",
        lambda historical_data: sessions,
    )

    session_results = iter(
        [
            SimpleNamespace(
                status="EXECUTED",
                trade=SimpleNamespace(
                    net_pnl=2000.00
                ),
            ),
            SimpleNamespace(
                status="EXECUTED",
                trade=SimpleNamespace(
                    net_pnl=-1000.00
                ),
            ),
            SimpleNamespace(
                status="NO_TRADE",
                trade=None,
            ),
        ]
    )

    monkeypatch.setattr(
        module,
        "run_pre_execution_risk_backtest",
        lambda **kwargs: next(session_results),
    )

    risk_manager = SimpleNamespace(
        account=SimpleNamespace(
            current_capital=100000.00
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

    assert result.performance_summary[
        "total_trades"
    ] == 2

    assert result.performance_summary[
        "winning_trades"
    ] == 1

    assert result.performance_summary[
        "losing_trades"
    ] == 1

    assert result.performance_summary[
        "total_net_pnl"
    ] == 1000.00

    assert result.performance_summary[
        "win_rate"
    ] == 50.00

    assert result.performance_summary[
        "expectancy"
    ] == 500.00


def test_multi_session_total_net_pnl(monkeypatch):

    historical_data, sessions = create_test_result()

    monkeypatch.setattr(
        module,
        "prepare_historical_sessions",
        lambda historical_data: sessions,
    )

    session_results = iter(
        [
            SimpleNamespace(
                status="EXECUTED",
                trade=SimpleNamespace(
                    net_pnl=2000.00
                ),
            ),
            SimpleNamespace(
                status="EXECUTED",
                trade=SimpleNamespace(
                    net_pnl=-1000.00
                ),
            ),
            SimpleNamespace(
                status="NO_TRADE",
                trade=None,
            ),
        ]
    )

    monkeypatch.setattr(
        module,
        "run_pre_execution_risk_backtest",
        lambda **kwargs: next(session_results),
    )

    risk_manager = SimpleNamespace(
        account=SimpleNamespace(
            current_capital=100000.00
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

    assert result.initial_capital == 100000.00
    assert result.final_capital == 101000.00
    assert result.total_net_pnl == 1000.00


def test_multi_session_return_percentage(monkeypatch):

    historical_data, sessions = create_test_result()

    monkeypatch.setattr(
        module,
        "prepare_historical_sessions",
        lambda historical_data: sessions,
    )

    session_results = iter(
        [
            SimpleNamespace(
                status="EXECUTED",
                trade=SimpleNamespace(
                    net_pnl=2000.00
                ),
            ),
            SimpleNamespace(
                status="EXECUTED",
                trade=SimpleNamespace(
                    net_pnl=-1000.00
                ),
            ),
            SimpleNamespace(
                status="NO_TRADE",
                trade=None,
            ),
        ]
    )

    monkeypatch.setattr(
        module,
        "run_pre_execution_risk_backtest",
        lambda **kwargs: next(session_results),
    )

    risk_manager = SimpleNamespace(
        account=SimpleNamespace(
            current_capital=100000.00
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

    assert result.return_percentage == 1.00