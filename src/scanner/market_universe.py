NIFTY_TEST_UNIVERSE = [
    {
        "tradingsymbol": "RELIANCE",
        "exchange": "NSE",
    },
    {
        "tradingsymbol": "TCS",
        "exchange": "NSE",
    },
    {
        "tradingsymbol": "INFY",
        "exchange": "NSE",
    },
    {
        "tradingsymbol": "HDFCBANK",
        "exchange": "NSE",
    },
    {
        "tradingsymbol": "ICICIBANK",
        "exchange": "NSE",
    },
]


def get_test_universe():
    """Return the initial GARUDA scanner universe."""

    return NIFTY_TEST_UNIVERSE.copy()