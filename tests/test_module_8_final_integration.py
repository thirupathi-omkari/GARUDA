import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


import backtesting.multi_session_risk_backtester as module

from risk.account import TradingAccount
from risk.equity_curve import EquityCurve
from risk.risk_config import RiskConfig
from risk.risk_manager import RiskManager


def test_module_8_final_integration(monkeypatch):

    # --------------------------------------------------
    # CREATE HISTORICAL DATA
    # --------------------------------------------------

    historical_data = pd.DataFrame(
        {
            "close": [
                100.00,
                101.00,
                102.00,
                103.00,
            ],
        }
    )

    # --------------------------------------------------
    # CREATE MULTIPLE SESSIONS
    # --------------------------------------------------

    sessions = [
        {"data": "session_1"},
        {"data": "session_2"},
        {"data": "session_3"},
        {"data": "session_4"},
    ]

    monkeypatch.setattr(
        module,
        "prepare_historical_sessions",
        lambda historical_data: sessions,
    )

    # --------------------------------------------------
    # CREATE SESSION RESULTS
    #
    # SESSION 1 = PROFIT
    # SESSION 2 = LOSS
    # SESSION 3 = REJECTED
    # SESSION 4 = NO TRADE
    # --------------------------------------------------

    session_results = iter(
        [
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
                status="REJECTED",
                trade=None,
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

    # --------------------------------------------------
    # CREATE TRADING ACCOUNT
    # --------------------------------------------------

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    # --------------------------------------------------
    # CREATE RISK CONFIGURATION
    # --------------------------------------------------

    config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=100.0,
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    # --------------------------------------------------
    # CREATE RISK MANAGER
    # --------------------------------------------------

    risk_manager = RiskManager(
        account=account,
        config=config,
    )

    # --------------------------------------------------
    # RUN MULTI-SESSION BACKTEST
    # --------------------------------------------------

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

    # --------------------------------------------------
    # VERIFY SESSION CLASSIFICATION
    # --------------------------------------------------

    assert result.total_sessions == 4

    assert result.executed_trades == 2

    assert result.rejected_trades == 1

    assert result.no_trade_sessions == 1

    assert (
        result.executed_trades
        + result.rejected_trades
        + result.no_trade_sessions
        == result.total_sessions
    )

    # --------------------------------------------------
    # VERIFY CAPITAL PROGRESSION
    # --------------------------------------------------

    assert result.initial_capital == 100000.00

    assert result.final_capital == 102000.00

    assert account.current_capital == 102000.00

    assert result.total_net_pnl == 2000.00

    assert result.return_percentage == 2.00

    # --------------------------------------------------
    # VERIFY PERFORMANCE SUMMARY
    # --------------------------------------------------

    summary = result.performance_summary

    assert summary["total_trades"] == 2

    assert summary["winning_trades"] == 1

    assert summary["losing_trades"] == 1

    assert summary["breakeven_trades"] == 0

    assert summary["total_net_pnl"] == 2000.00

    assert summary["win_rate"] == 50.00

    assert summary["expectancy"] == 1000.00

    # --------------------------------------------------
    # CREATE EQUITY CURVE
    # --------------------------------------------------

    equity_curve = EquityCurve(
        initial_equity=result.initial_capital
    )

    for session_result in result.session_results:

        if session_result.status == "EXECUTED":

            equity_curve.record_trade(
                pnl=session_result.trade.net_pnl
            )

    # --------------------------------------------------
    # VERIFY EQUITY CURVE
    # --------------------------------------------------

    assert equity_curve.trade_count == 2

    assert equity_curve.current_equity == 102000.00

    assert equity_curve.net_pnl == 2000.00

    assert equity_curve.return_percentage == 2.00

    assert equity_curve.equity_history == [
        100000.00,
        103000.00,
        102000.00,
    ]

    assert equity_curve.peak_equity == 103000.00

    assert equity_curve.lowest_equity == 100000.00

    # --------------------------------------------------
    # VERIFY CROSS-COMPONENT CONSISTENCY
    # --------------------------------------------------

    assert (
        equity_curve.current_equity
        == result.final_capital
    )

    assert (
        equity_curve.net_pnl
        == result.total_net_pnl
    )

    assert (
        equity_curve.net_pnl
        == summary["total_net_pnl"]
    )

    assert (
        equity_curve.trade_count
        == result.executed_trades
    )

    assert (
        equity_curve.trade_count
        == summary["total_trades"]
    )