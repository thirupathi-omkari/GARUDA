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


def test_no_signal_integration():

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
                ]
            ),

            "open": [
                100.00,
                100.20,
                100.10,
                100.30,
                100.20,
                100.40,
            ],

            "high": [
                101.00,
                100.80,
                100.90,
                100.70,
                100.80,
                100.90,
            ],

            "low": [
                99.00,
                99.50,
                99.40,
                99.60,
                99.50,
                99.70,
            ],

            "close": [
                100.20,
                100.10,
                100.30,
                100.20,
                100.40,
                100.30,
            ],

            "volume": [
                1000,
                1100,
                1200,
                1300,
                1400,
                1500,
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

    assert trade is None