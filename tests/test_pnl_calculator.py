import sys
from pathlib import Path
from datetime import date, datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.backtest_trade import BacktestTrade

from backtesting.pnl_calculator import (
    calculate_trade_pnl,
)


def test_profitable_buy_trade_pnl():

    trade = BacktestTrade(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        trade_date=date(2026, 7, 1),
        direction="BUY",
        entry_time=datetime(
            2026,
            7,
            1,
            9,
            40,
        ),
        entry_price=100.00,
        exit_time=datetime(
            2026,
            7,
            1,
            10,
            30,
        ),
        exit_price=102.00,
        exit_reason="TARGET",
        quantity=10,
    )

    completed_trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=0.10,
    )

    assert completed_trade is not None

    assert completed_trade.direction == "BUY"

    assert round(
        completed_trade.gross_pnl,
        2,
    ) == 20.00

    assert round(
        completed_trade.costs,
        2,
    ) == 2.02

    assert round(
        completed_trade.net_pnl,
        2,
    ) == 17.98


def test_profitable_sell_trade_pnl():

    trade = BacktestTrade(
        symbol="TCS",
        strategy_name="ORB_VWAP",
        trade_date=date(2026, 7, 2),
        direction="SELL",
        entry_time=datetime(
            2026,
            7,
            2,
            10,
            0,
        ),
        entry_price=100.00,
        exit_time=datetime(
            2026,
            7,
            2,
            11,
            0,
        ),
        exit_price=98.00,
        exit_reason="TARGET",
        quantity=10,
    )

    completed_trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=0.10,
    )

    assert completed_trade is not None

    assert completed_trade.direction == "SELL"

    assert round(
        completed_trade.gross_pnl,
        2,
    ) == 20.00

    assert round(
        completed_trade.costs,
        2,
    ) == 1.98

    assert round(
        completed_trade.net_pnl,
        2,
    ) == 18.02