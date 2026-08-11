import sys
from pathlib import Path
from datetime import date, datetime

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from backtesting.backtest_trade import BacktestTrade
from backtesting.exit_simulator import simulate_trade_exit


def test_buy_mfe_mae():

    trade = BacktestTrade(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        trade_date=date(2026, 7, 1),
        direction="BUY",
        entry_time=datetime(2026, 7, 1, 9, 40),
        entry_price=100.00,
        quantity=1,
        initial_risk=5.00,
    )

    candles = pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp("2026-07-01 09:45"),
                pd.Timestamp("2026-07-01 09:50"),
            ],
            "open": [100.00, 102.00],
            "high": [103.00, 104.00],
            "low": [99.00, 101.00],
            "close": [102.00, 103.00],
        }
    )

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=95.00,
        target=110.00,
    )

    assert result.mfe == 4.00
    assert result.mae == 1.00
    assert result.mfe_r == 0.8
    assert result.mae_r == 0.2


def test_sell_mfe_mae():

    trade = BacktestTrade(
        symbol="ICICIBANK",
        strategy_name="ORB_VWAP",
        trade_date=date(2026, 7, 1),
        direction="SELL",
        entry_time=datetime(2026, 7, 1, 9, 40),
        entry_price=100.00,
        quantity=1,
        initial_risk=10.00,
    )

    candles = pd.DataFrame(
        {
            "datetime": [
                pd.Timestamp("2026-07-01 09:45"),
                pd.Timestamp("2026-07-01 09:50"),
            ],
            "open": [100.00, 97.00],
            "high": [102.00, 101.00],
            "low": [96.00, 95.00],
            "close": [97.00, 96.00],
        }
    )

    result = simulate_trade_exit(
        trade=trade,
        future_candles=candles,
        stop_loss=110.00,
        target=90.00,
    )

    assert result.mfe == 5.00
    assert result.mae == 2.00
    assert result.mfe_r == 0.5
    assert result.mae_r == 0.2