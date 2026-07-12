import sys
from pathlib import Path
from datetime import date, datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.backtest_trade import BacktestTrade

from backtesting.performance_metrics import (
    generate_backtest_summary,
)


def create_test_trade(
    symbol,
    trade_date,
    net_pnl,
):
    """Create a completed trade for summary testing."""

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


def test_backtest_summary():

    trades = [
        create_test_trade(
            "INFY",
            date(2026, 7, 1),
            100.00,
        ),
        create_test_trade(
            "TCS",
            date(2026, 7, 2),
            50.00,
        ),
        create_test_trade(
            "RELIANCE",
            date(2026, 7, 3),
            -80.00,
        ),
        create_test_trade(
            "HDFCBANK",
            date(2026, 7, 4),
            -40.00,
        ),
        create_test_trade(
            "ICICIBANK",
            date(2026, 7, 5),
            30.00,
        ),
    ]

    summary = generate_backtest_summary(
        trades
    )

    assert summary is not None

    assert summary["total_trades"] == 5

    assert summary["winning_trades"] == 3

    assert summary["losing_trades"] == 2

    assert summary["breakeven_trades"] == 0

    assert round(
        summary["total_net_pnl"],
        2,
    ) == 60.00

    assert round(
        summary["win_rate"],
        2,
    ) == 60.00

    assert round(
        summary["profit_factor"],
        2,
    ) == 1.50

    assert round(
        summary["expectancy"],
        2,
    ) == 12.00

    assert round(
        summary["max_drawdown"],
        2,
    ) == 120.00