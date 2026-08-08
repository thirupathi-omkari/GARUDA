import pytest
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.session_backtester import (
    run_session_backtest,
)

from strategy.orb_vwap_strategy import (
    ORBVWAPStrategy,
)


def test_stop_loss_integration():
    session_data = pd.DataFrame(
        {
            "datetime": pd.to_datetime(
                [
                    "2026-07-01 09:15:00",
                    "2026-07-01 09:20:00",
                    "2026-07-01 09:25:00",
                    "2026-07-01 09:30:00",
                    "2026-07-01 09:35:00",
                    "2026-07-01 09:40:00",
                    "2026-07-01 09:45:00",
                    "2026-07-01 09:50:00",
                ]
            ),
            "open": [
                100.00,
                101.00,
                102.00,
                103.00,
                104.00,
                107.00,
                95.00,
                95.00,
            ],
            "high": [
                102.00,
                103.00,
                104.00,
                105.00,
                107.00,
                107.50,
                96.00,
                96.00,
            ],
            "low": [
                99.00,
                100.00,
                101.00,
                102.00,
                103.00,
                106.50,
                94.00,
                94.00,
            ],
            "close": [
                101.00,
                102.00,
                103.00,
                104.00,
                106.00,
                106.80,
                95.00,
                95.00,
            ],
            "volume": [
                1000,
                1200,
                1500,
                1800,
                2500,
                3500,
                3000,
                2800,
            ],
        }
    )

    strategy = ORBVWAPStrategy(
        opening_start_time="09:15",
        opening_end_time="09:30",
    )

    trade = run_session_backtest(
        symbol="INFY",
        strategy=strategy,
        session_data=session_data,
        stop_loss_pct=1.0,
        target_pct=2.0,
        cost_rate_pct=0.10,
        slippage_pct=0.05,
    )

    assert trade is not None

    assert trade.symbol == "INFY"

    assert trade.direction == "BUY"

    assert trade.entry_time == pd.Timestamp(
        "2026-07-01 09:40:00"
    )

    # --------------------------------------------------
    # V2 DYNAMIC STOP VALIDATION
    # --------------------------------------------------

    assert trade.initial_stop_loss is not None

    assert trade.current_stop_loss == (
        trade.initial_stop_loss
    )

    assert trade.initial_risk > 0

    # The ORB stop is below the entry.
    assert trade.initial_stop_loss < (
        trade.entry_price
    )

    # The 09:45 candle reaches the dynamic
    # ORB stop, so the trade must exit there.

    assert trade.exit_reason == "STOP_LOSS"

    assert trade.exit_time == pd.Timestamp(
        "2026-07-01 09:45:00"
    )