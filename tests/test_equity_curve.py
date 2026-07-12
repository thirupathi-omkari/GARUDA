import pytest
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from risk.equity_curve import EquityCurve


def test_equity_curve_initialization():

    equity_curve = EquityCurve(initial_equity=100000.00)

    assert equity_curve.initial_equity == 100000.00
    assert equity_curve.current_equity == 100000.00
    assert equity_curve.equity_history == [100000.00]

def test_record_profitable_trade():

    equity_curve = EquityCurve(initial_equity=100000.00)

    equity_curve.record_trade(pnl=2000.00)

    assert equity_curve.current_equity == 102000.00
    assert equity_curve.equity_history == [
        100000.00,
        102000.00,
    ]

def test_record_losing_trade():

    equity_curve = EquityCurve(initial_equity=100000.00)

    equity_curve.record_trade(pnl=-3000.00)

    assert equity_curve.current_equity == 97000.00
    assert equity_curve.equity_history == [
        100000.00,
        97000.00,
    ]

def test_record_multiple_trades():

    equity_curve = EquityCurve(initial_equity=100000.00)

    equity_curve.record_trade(pnl=2000.00)
    equity_curve.record_trade(pnl=-1000.00)
    equity_curve.record_trade(pnl=3000.00)

    assert equity_curve.current_equity == 104000.00
    assert equity_curve.equity_history == [
        100000.00,
        102000.00,
        101000.00,
        104000.00,
    ]

def test_record_breakeven_trade():

    equity_curve = EquityCurve(initial_equity=100000.00)

    equity_curve.record_trade(pnl=0.00)

    assert equity_curve.current_equity == 100000.00
    assert equity_curve.equity_history == [
        100000.00,
        100000.00,
    ]

def test_initial_equity_must_be_positive():

    with pytest.raises(ValueError):

        EquityCurve(initial_equity=0.00)

    with pytest.raises(ValueError):

        EquityCurve(initial_equity=-100000.00)

def test_trade_count():

    equity_curve = EquityCurve(initial_equity=100000.00)

    equity_curve.record_trade(pnl=2000.00)
    equity_curve.record_trade(pnl=-1000.00)
    equity_curve.record_trade(pnl=3000.00)

    assert equity_curve.trade_count == 3

def test_net_pnl():

    equity_curve = EquityCurve(initial_equity=100000.00)

    equity_curve.record_trade(pnl=2000.00)
    equity_curve.record_trade(pnl=-1000.00)
    equity_curve.record_trade(pnl=3000.00)

    assert equity_curve.net_pnl == 4000.00

def test_return_percentage():

    equity_curve = EquityCurve(initial_equity=100000.00)

    equity_curve.record_trade(pnl=2000.00)
    equity_curve.record_trade(pnl=-1000.00)
    equity_curve.record_trade(pnl=3000.00)

    assert equity_curve.return_percentage == 4.00

def test_peak_equity():

    equity_curve = EquityCurve(initial_equity=100000.00)

    equity_curve.record_trade(pnl=5000.00)
    equity_curve.record_trade(pnl=-3000.00)
    equity_curve.record_trade(pnl=7000.00)

    assert equity_curve.peak_equity == 109000.00


def test_lowest_equity():

    equity_curve = EquityCurve(initial_equity=100000.00)

    equity_curve.record_trade(pnl=-5000.00)
    equity_curve.record_trade(pnl=2000.00)
    equity_curve.record_trade(pnl=-4000.00)

    assert equity_curve.lowest_equity == 93000.00