import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.session_preparer import (
    prepare_historical_sessions,
)


def test_historical_session_preparation():

    sample_data = pd.DataFrame(
        {
            "datetime": [
                "2026-07-03 09:20:00",
                "2026-07-01 09:15:00",
                "2026-07-02 09:20:00",
                "2026-07-01 09:20:00",
                "2026-07-03 09:15:00",
                "2026-07-02 09:15:00",
            ],

            "open": [
                302,
                100,
                202,
                102,
                300,
                200,
            ],

            "high": [
                303,
                101,
                203,
                103,
                301,
                201,
            ],

            "low": [
                301,
                99,
                201,
                101,
                299,
                199,
            ],

            "close": [
                302,
                100,
                202,
                102,
                300,
                200,
            ],

            "volume": [
                3000,
                1000,
                2000,
                1200,
                2800,
                1800,
            ],
        }
    )

    sessions = prepare_historical_sessions(
        sample_data
    )

    actual_dates = [
        str(session["session_date"])
        for session in sessions
    ]

    expected_dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
    ]

    assert len(sessions) == 3

    assert actual_dates == expected_dates

    assert all(
        len(session["data"]) == 2
        for session in sessions
    )

    assert all(
        session["data"]["datetime"]
        .is_monotonic_increasing
        for session in sessions
    )