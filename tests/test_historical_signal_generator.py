import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.candle_replay import (
    replay_session_candles,
)

from backtesting.signal_generator import (
    generate_historical_signals,
)

from strategy.orb_vwap_strategy import (
    ORBVWAPStrategy,
)


def test_historical_signal_generator():

    session_data = pd.DataFrame(
        {
            "datetime": [
                "2026-07-01 09:15:00",
                "2026-07-01 09:20:00",
                "2026-07-01 09:25:00",
                "2026-07-01 09:30:00",
                "2026-07-01 09:35:00",
                "2026-07-01 09:40:00",
            ],

            "open": [
                100,
                101,
                102,
                103,
                104,
                106,
            ],

            "high": [
                102,
                103,
                104,
                105,
                107,
                110,
            ],

            "low": [
                99,
                100,
                101,
                102,
                103,
                105,
            ],

            "close": [
                101,
                102,
                103,
                104,
                106,
                109,
            ],

            "volume": [
                1000,
                1200,
                1500,
                1800,
                2500,
                3500,
            ],
        }
    )

    strategy = ORBVWAPStrategy(
        opening_start_time="09:15",
        opening_end_time="09:30",
    )

    signal_results = generate_historical_signals(
        strategy=strategy,
        session_data=session_data,
        replay_function=replay_session_candles,
    )

    signals = [
        signal_record["result"].signal
        for signal_record in signal_results
    ]

    expected_signals = [
        "NO_SIGNAL",
        "NO_SIGNAL",
        "NO_SIGNAL",
        "NO_SIGNAL",
        "BUY",
        "BUY",
    ]

    assert len(signal_results) == 6

    assert signals == expected_signals