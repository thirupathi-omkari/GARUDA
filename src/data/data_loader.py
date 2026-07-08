import pandas as pd


def create_sample_market_data():
    """Create sample OHLCV market data for testing."""

    data = {
        "datetime": [
            "2026-07-06 09:15:00",
            "2026-07-06 09:20:00",
            "2026-07-06 09:25:00",
            "2026-07-06 09:30:00",
            "2026-07-06 09:35:00",
        ],
        "open": [25000, 25020, 25035, 25025, 25050],
        "high": [25030, 25050, 25060, 25055, 25080],
        "low": [24990, 25010, 25020, 25015, 25040],
        "close": [25020, 25035, 25025, 25050, 25070],
        "volume": [1000, 1200, 900, 1500, 1800],
    }

    dataframe = pd.DataFrame(data)

    return dataframe