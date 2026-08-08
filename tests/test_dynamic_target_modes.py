import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from risk.target_engine import calculate_target


def test_risk_reward_target_buy():

    candles = pd.DataFrame(
        {
            "high": [100, 101, 102, 103, 104],
            "low": [95, 96, 97, 98, 99],
            "close": [98, 99, 100, 101, 102],
        }
    )

    target = calculate_target(
        mode="RISK_REWARD",
        signal="BUY",
        entry_price=100.00,
        stop_loss=95.00,
        candles=candles,
        risk_reward_ratio=2.0,
    )

    assert target == pytest.approx(110.00)


def test_risk_reward_target_sell():

    candles = pd.DataFrame(
        {
            "high": [105, 104, 103, 102, 101],
            "low": [100, 99, 98, 97, 96],
            "close": [103, 102, 101, 100, 99],
        }
    )

    target = calculate_target(
        mode="RISK_REWARD",
        signal="SELL",
        entry_price=100.00,
        stop_loss=105.00,
        candles=candles,
        risk_reward_ratio=2.0,
    )

    assert target == pytest.approx(90.00)


def test_atr_target_buy():

    candles = pd.DataFrame(
        {
            "high": [
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
                111.0,
                112.0,
                113.0,
                114.0,
                115.0,
                116.0,
            ],
            "low": [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
                111.0,
                112.0,
                113.0,
                114.0,
            ],
            "close": [
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
                111.0,
                112.0,
                113.0,
                114.0,
                115.0,
            ],
        }
    )

    target = calculate_target(
        mode="ATR",
        signal="BUY",
        entry_price=100.00,
        stop_loss=95.00,
        candles=candles,
        risk_reward_ratio=2.0,
    )

    assert target == pytest.approx(106.00)


def test_atr_target_sell():

    candles = pd.DataFrame(
        {
            "high": [
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
                111.0,
                112.0,
                113.0,
                114.0,
                115.0,
                116.0,
            ],
            "low": [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
                111.0,
                112.0,
                113.0,
                114.0,
            ],
            "close": [
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
                111.0,
                112.0,
                113.0,
                114.0,
                115.0,
            ],
        }
    )

    target = calculate_target(
        mode="ATR",
        signal="SELL",
        entry_price=100.00,
        stop_loss=105.00,
        candles=candles,
        risk_reward_ratio=2.0,
    )

    assert target == pytest.approx(94.00)


def test_support_resistance_target_buy():

    candles = pd.DataFrame(
        {
            "high": [
                100,
                101,
                105,
                102,
                103,
                104,
                106,
            ],
            "low": [
                98,
                97,
                99,
                95,
                97,
                96,
                98,
            ],
        }
    )

    target = calculate_target(
        mode="SUPPORT_RESISTANCE",
        signal="BUY",
        entry_price=100.00,
        stop_loss=95.00,
        candles=candles,
        risk_reward_ratio=2.0,
    )

    assert target == pytest.approx(105.00)


def test_support_resistance_target_sell():

    candles = pd.DataFrame(
        {
            "high": [
                100,
                101,
                105,
                102,
                103,
                104,
                106,
            ],
            "low": [
                98,
                97,
                99,
                95,
                97,
                96,
                98,
            ],
        }
    )

    target = calculate_target(
        mode="SUPPORT_RESISTANCE",
        signal="SELL",
        entry_price=110.00,
        stop_loss=115.00,
        candles=candles,
        risk_reward_ratio=2.0,
    )

    assert target == pytest.approx(96.00)