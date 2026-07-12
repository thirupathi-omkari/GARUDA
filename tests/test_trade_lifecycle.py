import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.trade_lifecycle import evaluate_trade_candle


def test_buy_target_hit():

    candle = pd.Series(
        {
            "high": 102.50,
            "low": 100.00,
        }
    )

    result = evaluate_trade_candle(
        direction="BUY",
        candle=candle,
        stop_loss=99.00,
        target=102.00,
    )

    assert result is not None
    assert result["exit_reason"] == "TARGET"
    assert result["exit_price"] == 102.00


def test_buy_stop_loss_hit():

    candle = pd.Series(
        {
            "high": 100.50,
            "low": 98.50,
        }
    )

    result = evaluate_trade_candle(
        direction="BUY",
        candle=candle,
        stop_loss=99.00,
        target=102.00,
    )

    assert result is not None
    assert result["exit_reason"] == "STOP_LOSS"
    assert result["exit_price"] == 99.00


def test_sell_target_hit():

    candle = pd.Series(
        {
            "high": 100.00,
            "low": 97.50,
        }
    )

    result = evaluate_trade_candle(
        direction="SELL",
        candle=candle,
        stop_loss=101.00,
        target=98.00,
    )

    assert result is not None
    assert result["exit_reason"] == "TARGET"
    assert result["exit_price"] == 98.00


def test_sell_stop_loss_hit():

    candle = pd.Series(
        {
            "high": 101.50,
            "low": 99.50,
        }
    )

    result = evaluate_trade_candle(
        direction="SELL",
        candle=candle,
        stop_loss=101.00,
        target=98.00,
    )

    assert result is not None
    assert result["exit_reason"] == "STOP_LOSS"
    assert result["exit_price"] == 101.00


def test_no_exit():

    candle = pd.Series(
        {
            "high": 101.00,
            "low": 99.50,
        }
    )

    result = evaluate_trade_candle(
        direction="BUY",
        candle=candle,
        stop_loss=99.00,
        target=102.00,
    )

    assert result is None