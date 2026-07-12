import sys
from pathlib import Path
from datetime import date, datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.backtest_trade import BacktestTrade


def test_backtest_trade_validation():

    trade = BacktestTrade(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        trade_date=date(2026, 7, 10),
        direction="BUY",
        entry_time=datetime(
            2026,
            7,
            10,
            10,
            30,
        ),
        entry_price=1500.00,
        quantity=1,
    )

    assert trade.symbol == "INFY"

    assert trade.strategy_name == "ORB_VWAP"

    assert trade.trade_date == date(
        2026,
        7,
        10,
    )

    assert trade.direction == "BUY"

    assert trade.entry_time == datetime(
        2026,
        7,
        10,
        10,
        30,
    )

    assert trade.entry_price == 1500.00

    assert trade.exit_time is None

    assert trade.exit_price is None

    assert trade.exit_reason is None

    assert trade.quantity == 1

    assert trade.gross_pnl == 0.0

    assert trade.costs == 0.0

    assert trade.net_pnl == 0.0