import sys
from pathlib import Path
from datetime import date, datetime


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.backtest_trade import BacktestTrade
from backtesting.trade_ledger import TradeLedger


def test_trade_ledger():

    ledger = TradeLedger()

    trade_1 = BacktestTrade(
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
        quantity=1,
        gross_pnl=2.00,
        costs=0.20,
        net_pnl=1.80,
    )

    trade_2 = BacktestTrade(
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
        entry_price=200.00,
        exit_time=datetime(
            2026,
            7,
            2,
            11,
            15,
        ),
        exit_price=198.00,
        exit_reason="TARGET",
        quantity=1,
        gross_pnl=2.00,
        costs=0.40,
        net_pnl=1.60,
    )

    ledger.add_trade(trade_1)
    ledger.add_trade(trade_2)

    recorded_trades = ledger.get_trades()

    assert ledger.trade_count() == 2
    assert len(recorded_trades) == 2

    assert recorded_trades[0].symbol == "INFY"
    assert recorded_trades[1].symbol == "TCS"

    assert recorded_trades[0].direction == "BUY"
    assert recorded_trades[1].direction == "SELL"

    assert recorded_trades[0].net_pnl == 1.80
    assert recorded_trades[1].net_pnl == 1.60