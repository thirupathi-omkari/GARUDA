import sys
from pathlib import Path
from datetime import date, datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.backtest_trade import BacktestTrade

from backtesting.performance_metrics import (
    calculate_profit_factor,
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


def test_profit_factor():

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
            -30.00,
        ),
        create_test_trade(
            "ICICIBANK",
            date(2026, 7, 5),
            25.00,
        ),
    ]

    profit_factor = calculate_profit_factor(
        trades
    )

    gross_profit = sum(
        trade.net_pnl
        for trade in trades
        if trade.net_pnl > 0
    )

    gross_loss = abs(
        sum(
            trade.net_pnl
            for trade in trades
            if trade.net_pnl < 0
        )
    )

    assert gross_profit == 200.00
    assert gross_loss == 80.00

    assert round(
        profit_factor,
        2,
    ) == 2.50