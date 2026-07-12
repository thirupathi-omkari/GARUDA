import sys
from pathlib import Path
from datetime import date, datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.backtest_trade import BacktestTrade

from backtesting.performance_metrics import (
    calculate_win_rate,
)


def create_test_trade(
    symbol,
    trade_date,
    net_pnl,
):
    """Create a completed trade for metric testing."""

    return BacktestTrade(
        symbol=symbol,
        strategy_name="ORB_VWAP",
        trade_date=trade_date,
        direction="BUY",
        entry_time=datetime.combine(
            trade_date,
            datetime.min.time(),
        ),
        entry_price=100.00,
        exit_time=datetime.combine(
            trade_date,
            datetime.min.time(),
        ),
        exit_price=100.00,
        exit_reason="TEST",
        quantity=1,
        gross_pnl=net_pnl,
        costs=0.0,
        net_pnl=net_pnl,
    )


def test_win_rate():

    trades = [
        create_test_trade(
            "INFY",
            date(2026, 7, 1),
            100.00,
        ),
        create_test_trade(
            "TCS",
            date(2026, 7, 2),
            -50.00,
        ),
        create_test_trade(
            "RELIANCE",
            date(2026, 7, 3),
            75.00,
        ),
        create_test_trade(
            "HDFCBANK",
            date(2026, 7, 4),
            -25.00,
        ),
        create_test_trade(
            "ICICIBANK",
            date(2026, 7, 5),
            40.00,
        ),
    ]

    win_rate = calculate_win_rate(
        trades
    )

    assert len(trades) == 5

    winning_trades = sum(
        1
        for trade in trades
        if trade.net_pnl > 0
    )

    losing_trades = sum(
        1
        for trade in trades
        if trade.net_pnl < 0
    )

    assert winning_trades == 3
    assert losing_trades == 2

    assert round(win_rate, 2) == 60.00