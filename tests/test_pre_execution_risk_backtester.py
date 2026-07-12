import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.pre_execution_risk_backtester import (
    run_pre_execution_risk_backtest,
)

from risk.account import TradingAccount
from risk.risk_config import RiskConfig
from risk.risk_manager import RiskManager

from strategy.orb_vwap_strategy import (
    ORBVWAPStrategy,
)


def test_pre_execution_risk_rejection():

    session_data = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    "2026-07-01 09:15:00",
                    "2026-07-01 09:20:00",
                    "2026-07-01 09:25:00",
                    "2026-07-01 09:30:00",
                    "2026-07-01 09:35:00",
                    "2026-07-01 09:40:00",
                    "2026-07-01 09:45:00",
                    "2026-07-01 09:50:00",
                ]
            ),

            "open": [
                100.00,
                101.00,
                102.00,
                103.00,
                104.00,
                107.00,
                108.00,
                109.00,
            ],

            "high": [
                102.00,
                103.00,
                104.00,
                105.00,
                107.00,
                108.00,
                110.00,
                111.00,
            ],

            "low": [
                99.00,
                100.00,
                101.00,
                102.00,
                103.00,
                106.50,
                107.50,
                108.50,
            ],

            "close": [
                101.00,
                102.00,
                103.00,
                104.00,
                106.00,
                107.50,
                109.50,
                110.50,
            ],

            "volume": [
                1000,
                1200,
                1500,
                1800,
                2500,
                3500,
                4000,
                4500,
            ],
        }
    )

    strategy = ORBVWAPStrategy(
        opening_start_time="09:15",
        opening_end_time="09:30",
    )

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=100.0,
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    risk_manager = RiskManager(
        account=account,
        config=config,
    )

    result = run_pre_execution_risk_backtest(
        symbol="INFY",
        strategy=strategy,
        session_data=session_data,
        risk_manager=risk_manager,
        stop_loss_pct=1.0,
        target_pct=2.0,
        cost_rate_pct=0.10,
        slippage_pct=0.05,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,

        # Deliberately trigger daily loss rejection.
        daily_realized_pnl=-3000.00,
    )

    assert result.status == "REJECTED"

    assert result.trade is None

    assert result.risk_decision is not None

    assert result.risk_decision.approved is False

    assert (
        result.risk_decision.reason
        == "DAILY_LOSS_LIMIT"
    )

def test_pre_execution_risk_approved_trade_executes():

    session_data = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    "2026-07-01 09:15:00",
                    "2026-07-01 09:20:00",
                    "2026-07-01 09:25:00",
                    "2026-07-01 09:30:00",
                    "2026-07-01 09:35:00",
                    "2026-07-01 09:40:00",
                    "2026-07-01 09:45:00",
                    "2026-07-01 09:50:00",
                ]
            ),

            "open": [
                100.00,
                101.00,
                102.00,
                103.00,
                104.00,
                107.00,
                108.00,
                109.00,
            ],

            "high": [
                102.00,
                103.00,
                104.00,
                105.00,
                107.00,
                108.00,
                111.00,
                112.00,
            ],

            "low": [
                99.00,
                100.00,
                101.00,
                102.00,
                103.00,
                106.50,
                107.50,
                108.50,
            ],

            "close": [
                101.00,
                102.00,
                103.00,
                104.00,
                106.00,
                107.50,
                110.50,
                111.00,
            ],

            "volume": [
                1000,
                1200,
                1500,
                1800,
                2500,
                3500,
                4000,
                4500,
            ],
        }
    )

    strategy = ORBVWAPStrategy(
        opening_start_time="09:15",
        opening_end_time="09:30",
    )

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=100.0,
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    risk_manager = RiskManager(
        account=account,
        config=config,
    )

    result = run_pre_execution_risk_backtest(
        symbol="INFY",
        strategy=strategy,
        session_data=session_data,
        risk_manager=risk_manager,
        stop_loss_pct=1.0,
        target_pct=2.0,
        cost_rate_pct=0.10,
        slippage_pct=0.05,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.status == "EXECUTED"

    assert result.risk_decision is not None

    assert result.risk_decision.approved is True

    assert result.risk_decision.reason == "APPROVED"

    assert result.trade is not None

    assert (
        result.trade.quantity
        == result.risk_decision.approved_quantity
    )

    assert result.trade.quantity > 0

    assert result.trade.exit_time is not None

    assert result.trade.exit_price is not None

    assert result.trade.exit_reason is not None

    assert result.trade.gross_pnl is not None

    assert result.trade.costs is not None

    assert result.trade.net_pnl is not None

def test_pre_execution_risk_no_trade():

    session_data = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    "2026-07-01 09:15:00",
                    "2026-07-01 09:20:00",
                    "2026-07-01 09:25:00",
                    "2026-07-01 09:30:00",
                    "2026-07-01 09:35:00",
                    "2026-07-01 09:40:00",
                ]
            ),

            "open": [
                100.00,
                100.20,
                100.10,
                100.30,
                100.20,
                100.40,
            ],

            "high": [
                101.00,
                100.80,
                100.90,
                100.70,
                100.80,
                100.90,
            ],

            "low": [
                99.00,
                99.50,
                99.40,
                99.60,
                99.50,
                99.70,
            ],

            "close": [
                100.20,
                100.10,
                100.30,
                100.20,
                100.40,
                100.30,
            ],

            "volume": [
                1000,
                1100,
                1200,
                1300,
                1400,
                1500,
            ],
        }
    )

    strategy = ORBVWAPStrategy(
        opening_start_time="09:15",
        opening_end_time="09:30",
    )

    account = TradingAccount.create(
        initial_capital=100000.00
    )

    config = RiskConfig(
        risk_per_trade_pct=1.0,
        max_daily_loss_pct=3.0,
        max_portfolio_exposure_pct=100.0,
        max_portfolio_risk_pct=5.0,
        max_open_positions=5,
    )

    risk_manager = RiskManager(
        account=account,
        config=config,
    )

    result = run_pre_execution_risk_backtest(
        symbol="INFY",
        strategy=strategy,
        session_data=session_data,
        risk_manager=risk_manager,
        stop_loss_pct=1.0,
        target_pct=2.0,
        cost_rate_pct=0.10,
        slippage_pct=0.05,
        lot_size=1,
        current_exposure=0.00,
        current_open_risk=0.00,
        current_open_positions=0,
        daily_realized_pnl=0.00,
    )

    assert result.status == "NO_TRADE"

    assert result.trade is None

    assert result.risk_decision is None