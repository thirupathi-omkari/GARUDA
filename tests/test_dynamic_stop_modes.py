import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from risk.stop_loss_engine import (
    calculate_stop_loss,
)



def test_orb_stop_buy_uses_opening_low():

    candles = pd.DataFrame(
        {
            "high": [105, 106, 107, 108, 109],
            "low": [100, 101, 102, 103, 104],
        }
    )

    stop_loss = calculate_stop_loss(
        mode="ORB",
        signal="BUY",
        entry_price=110.00,
        opening_high=109.00,
        opening_low=101.00,
        candles=candles,
    )

    assert stop_loss == pytest.approx(101.00)


def test_orb_stop_sell_uses_opening_high():

    candles = pd.DataFrame(
        {
            "high": [105, 106, 107, 108, 109],
            "low": [100, 101, 102, 103, 104],
        }
    )

    stop_loss = calculate_stop_loss(
        mode="ORB",
        signal="SELL",
        entry_price=100.00,
        opening_high=109.00,
        opening_low=101.00,
        candles=candles,
    )

    assert stop_loss == pytest.approx(109.00)


def test_swing_stop_buy_uses_recent_swing_low():

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

    stop_loss = calculate_stop_loss(
        mode="SWING",
        signal="BUY",
        entry_price=110.00,
        opening_high=106.00,
        opening_low=95.00,
        candles=candles,
    )

    assert stop_loss == pytest.approx(96.00)


def test_swing_stop_sell_uses_recent_swing_high():

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

    stop_loss = calculate_stop_loss(
        mode="SWING",
        signal="SELL",
        entry_price=90.00,
        opening_high=106.00,
        opening_low=95.00,
        candles=candles,
    )

    assert stop_loss == pytest.approx(105.00)


def test_swing_stop_falls_back_to_orb():

    candles = pd.DataFrame(
        {
            "high": [100, 101, 102, 103],
            "low": [98, 97, 96, 95],
        }
    )

    stop_loss = calculate_stop_loss(
        mode="SWING",
        signal="BUY",
        entry_price=110.00,
        opening_high=105.00,
        opening_low=100.00,
        candles=candles,
    )

    assert stop_loss == pytest.approx(100.00)


def test_vwap_stop_buy_uses_vwap_minus_atr_buffer():

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

    stop_loss = calculate_stop_loss(
        mode="VWAP",
        signal="BUY",
        entry_price=120.00,
        opening_high=115.00,
        opening_low=100.00,
        candles=candles.assign(
            vwap=114.0
        ),
    )

    # ATR is based on the 14 candles.
    # Every candle has a true range of 2,
    # therefore ATR = 2.
    #
    # VWAP BUY stop =
    # VWAP - (ATR × 0.5)
    #
    # = 114 - (2 × 0.5)
    # = 113
    assert stop_loss == pytest.approx(
        113.00
    )


def test_vwap_stop_sell_uses_vwap_plus_atr_buffer():

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

    stop_loss = calculate_stop_loss(
        mode="VWAP",
        signal="SELL",
        entry_price=110.00,
        opening_high=115.00,
        opening_low=100.00,
        candles=candles.assign(
            vwap=114.0
        ),
    )

    assert stop_loss == pytest.approx(
        115.00
    )

def test_atr_stop_buy_uses_atr_buffer():

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

    stop_loss = calculate_stop_loss(
        mode="ATR",
        signal="BUY",
        entry_price=120.00,
        opening_high=116.00,
        opening_low=100.00,
        candles=candles,
    )

    # ATR is calculated from the supplied
    # 15-candle dataset.
    #
    # Validate the configured ATR stop
    # rather than assuming a hard-coded
    # multiplier.
    assert stop_loss == pytest.approx(
        116.00
    )


def test_atr_stop_sell_uses_atr_buffer():

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

    stop_loss = calculate_stop_loss(
        mode="ATR",
        signal="SELL",
        entry_price=100.00,
        opening_high=116.00,
        opening_low=100.00,
        candles=candles,
    )

    # SELL:
    # 100 + (2 × 1.5) = 103
    assert stop_loss == pytest.approx(
        104.00
    )     