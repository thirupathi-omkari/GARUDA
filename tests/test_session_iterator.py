import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from backtesting.session_preparer import (
    prepare_historical_sessions,
)

from backtesting.session_iterator import (
    iterate_sessions,
)


def test_multi_day_session_iterator():

    sample_data = pd.DataFrame(
        {
            "datetime": [
                "2026-07-03 09:15:00",
                "2026-07-01 09:15:00",
                "2026-07-02 09:15:00",
            ],

            "open": [
                300,
                100,
                200,
            ],

            "high": [
                301,
                101,
                201,
            ],

            "low": [
                299,
                99,
                199,
            ],

            "close": [
                300,
                100,
                200,
            ],

            "volume": [
                3000,
                1000,
                2000,
            ],
        }
    )

    sessions = prepare_historical_sessions(
        sample_data
    )

    iterated_dates = []

    for session in iterate_sessions(sessions):

        session_date = session["session_date"]

        iterated_dates.append(
            str(session_date)
        )

    expected_dates = [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
    ]

    assert len(iterated_dates) == 3

    assert iterated_dates == expected_dates