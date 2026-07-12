import sys
from pathlib import Path
from datetime import date, datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.backtest_trade import BacktestTrade


def test_backtest_trade_model():

    trade = BacktestTrade(
        symbol="INFY",
        strategy_name="ORB_VWAP",
        trade_date=date(2026, 7, 10),
        direction="SELL",
        entry_time=datetime(
            2026,
            7,
            10,
            10,
            30,
        ),
        entry_price=1068.70,
        exit_time=datetime(
            2026,
            7,
            10,
            14,
            45,
        ),
        exit_price=1060.00,
        exit_reason="TARGET",
        quantity=1,
        gross_pnl=8.70,
        costs=1.00,
        net_pnl=7.70,
    )

    assert trade.symbol == "INFY"

    assert trade.strategy_name == "ORB_VWAP"

    assert trade.trade_date == date(
        2026,
        7,
        10,
    )

    assert trade.direction == "SELL"

    assert trade.entry_time == datetime(
        2026,
        7,
        10,
        10,
        30,
    )

    assert trade.entry_price == 1068.70

    assert trade.exit_time == datetime(
        2026,
        7,
        10,
        14,
        45,
    )

    assert trade.exit_price == 1060.00

    assert trade.exit_reason == "TARGET"

    assert trade.quantity == 1

    assert trade.gross_pnl == 8.70

    assert trade.costs == 1.00

    assert trade.net_pnl == 7.70