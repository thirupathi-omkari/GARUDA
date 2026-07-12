import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.candle_replay import (
    replay_session_candles,
)


def test_candle_by_candle_replay():

    session_data = pd.DataFrame(
        {
            "datetime": [
                "2026-07-01 09:15:00",
                "2026-07-01 09:20:00",
                "2026-07-01 09:25:00",
                "2026-07-01 09:30:00",
                "2026-07-01 09:35:00",
            ],

            "open": [
                100,
                101,
                102,
                103,
                104,
            ],

            "high": [
                102,
                103,
                104,
                105,
                106,
            ],

            "low": [
                99,
                100,
                101,
                102,
                103,
            ],

            "close": [
                101,
                102,
                103,
                104,
                105,
            ],

            "volume": [
                1000,
                1200,
                1500,
                1800,
                2000,
            ],
        }
    )

    visible_lengths = []

    latest_times = []

    for visible_data in replay_session_candles(
        session_data
    ):

        visible_length = len(
            visible_data
        )

        latest_time = (
            pd.to_datetime(
                visible_data["datetime"].iloc[-1]
            )
            .strftime("%H:%M")
        )

        visible_lengths.append(
            visible_length
        )

        latest_times.append(
            latest_time
        )

    expected_lengths = [
        1,
        2,
        3,
        4,
        5,
    ]

    expected_times = [
        "09:15",
        "09:20",
        "09:25",
        "09:30",
        "09:35",
    ]

    assert visible_lengths == expected_lengths

    assert latest_times == expected_times