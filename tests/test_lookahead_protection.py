import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.candle_replay import (
    replay_session_candles,
)


def test_lookahead_bias_protection():

    future_value = 999999

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
                future_value,
            ],

            "high": [
                101,
                102,
                103,
                104,
                future_value,
            ],

            "low": [
                99,
                100,
                101,
                102,
                future_value,
            ],

            "close": [
                100,
                101,
                102,
                103,
                future_value,
            ],

            "volume": [
                1000,
                1200,
                1500,
                1800,
                future_value,
            ],
        }
    )

    replay_steps = list(
        replay_session_candles(
            session_data
        )
    )

    actual_visibility = [
        future_value in visible_data.values
        for visible_data in replay_steps
    ]

    expected_visibility = [
        False,
        False,
        False,
        False,
        True,
    ]

    assert len(replay_steps) == 5

    assert actual_visibility == expected_visibility

    for visible_data in replay_steps[:-1]:

        assert future_value not in visible_data.values

    assert future_value in replay_steps[-1].values