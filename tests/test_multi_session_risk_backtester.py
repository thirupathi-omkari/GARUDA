import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.multi_session_risk_backtester import (
    run_multi_session_risk_backtest,
)

from risk.account import TradingAccount
from risk.risk_config import RiskConfig
from risk.risk_manager import RiskManager

from strategy.orb_vwap_strategy import (
    ORBVWAPStrategy,
)


def test_multi_session_risk_backtester_foundation():

    historical_data = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    # ----------------------------------
                    # SESSION 1
                    # ----------------------------------

                    "2026-07-01 09:15:00",
                    "2026-07-01 09:20:00",
                    "2026-07-01 09:25:00",
                    "2026-07-01 09:30:00",
                    "2026-07-01 09:35:00",
                    "2026-07-01 09:40:00",
                    "2026-07-01 09:45:00",
                    "2026-07-01 09:50:00",

                    # ----------------------------------
                    # SESSION 2
                    # ----------------------------------

                    "2026-07-02 09:15:00",
                    "2026-07-02 09:20:00",
                    "2026-07-02 09:25:00",
                    "2026-07-02 09:30:00",
                    "2026-07-02 09:35:00",
                    "2026-07-02 09:40:00",
                ]
            ),

            "open": [
                # SESSION 1

                100.00,
                101.00,
                102.00,
                103.00,
                104.00,
                107.00,
                108.00,
                109.00,

                # SESSION 2

                100.00,
                100.20,
                100.10,
                100.30,
                100.20,
                100.40,
            ],

            "high": [
                # SESSION 1

                102.00,
                103.00,
                104.00,
                105.00,
                107.00,
                108.00,
                111.00,
                112.00,

                # SESSION 2

                101.00,
                100.80,
                100.90,
                100.70,
                100.80,
                100.90,
            ],

            "low": [
                # SESSION 1

                99.00,
                100.00,
                101.00,
                102.00,
                103.00,
                106.50,
                107.50,
                108.50,

                # SESSION 2

                99.00,
                99.50,
                99.40,
                99.60,
                99.50,
                99.70,
            ],

            "close": [
                # SESSION 1

                101.00,
                102.00,
                103.00,
                104.00,
                106.00,
                107.50,
                110.50,
                111.00,

                # SESSION 2

                100.20,
                100.10,
                100.30,
                100.20,
                100.40,
                100.30,
            ],

            "volume": [
                # SESSION 1

                1000,
                1200,
                1500,
                1800,
                2500,
                3500,
                4000,
                4500,

                # SESSION 2

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

    result = run_multi_session_risk_backtest(
        symbol="INFY",
        strategy=strategy,
        historical_data=historical_data,
        risk_manager=risk_manager,
        stop_loss_pct=1.0,
        target_pct=2.0,
        cost_rate_pct=0.10,
        slippage_pct=0.05,
        lot_size=1,
    )

    assert result.total_sessions == 2

    assert len(result.session_results) == 2

    assert result.executed_trades == 1

    assert result.rejected_trades == 0

    assert result.no_trade_sessions == 1

    assert (
        result.session_results[0].status
        == "EXECUTED"
    )

    assert (
        result.session_results[1].status
        == "NO_TRADE"
    )

    assert (
        result.executed_trades
        + result.rejected_trades
        + result.no_trade_sessions
        == result.total_sessions
    )

def test_multi_session_account_equity_progression():

    historical_data = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    # SESSION 1

                    "2026-07-01 09:15:00",
                    "2026-07-01 09:20:00",
                    "2026-07-01 09:25:00",
                    "2026-07-01 09:30:00",
                    "2026-07-01 09:35:00",
                    "2026-07-01 09:40:00",
                    "2026-07-01 09:45:00",
                    "2026-07-01 09:50:00",

                    # SESSION 2

                    "2026-07-02 09:15:00",
                    "2026-07-02 09:20:00",
                    "2026-07-02 09:25:00",
                    "2026-07-02 09:30:00",
                    "2026-07-02 09:35:00",
                    "2026-07-02 09:40:00",
                ]
            ),

            "open": [
                # SESSION 1

                100.00,
                101.00,
                102.00,
                103.00,
                104.00,
                107.00,
                108.00,
                109.00,

                # SESSION 2

                100.00,
                100.20,
                100.10,
                100.30,
                100.20,
                100.40,
            ],

            "high": [
                # SESSION 1

                102.00,
                103.00,
                104.00,
                105.00,
                107.00,
                108.00,
                111.00,
                112.00,

                # SESSION 2

                101.00,
                100.80,
                100.90,
                100.70,
                100.80,
                100.90,
            ],

            "low": [
                # SESSION 1

                99.00,
                100.00,
                101.00,
                102.00,
                103.00,
                106.50,
                107.50,
                108.50,

                # SESSION 2

                99.00,
                99.50,
                99.40,
                99.60,
                99.50,
                99.70,
            ],

            "close": [
                # SESSION 1

                101.00,
                102.00,
                103.00,
                104.00,
                106.00,
                107.50,
                110.50,
                111.00,

                # SESSION 2

                100.20,
                100.10,
                100.30,
                100.20,
                100.40,
                100.30,
            ],

            "volume": [
                # SESSION 1

                1000,
                1200,
                1500,
                1800,
                2500,
                3500,
                4000,
                4500,

                # SESSION 2

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

    result = run_multi_session_risk_backtest(
        symbol="INFY",
        strategy=strategy,
        historical_data=historical_data,
        risk_manager=risk_manager,
        stop_loss_pct=1.0,
        target_pct=2.0,
        cost_rate_pct=0.10,
        slippage_pct=0.05,
        lot_size=1,
    )

    assert result.initial_capital == 100000.00

    assert result.executed_trades == 1

    executed_trade = (
        result.session_results[0].trade
    )

    assert executed_trade is not None

    expected_final_capital = (
        result.initial_capital
        + executed_trade.net_pnl
    )

    assert (
        round(result.final_capital, 2)
        == round(expected_final_capital, 2)
    )

    assert (
        round(
            risk_manager.account.current_capital,
            2,
        )
        == round(result.final_capital, 2)
    )

    assert result.final_capital > result.initial_capital