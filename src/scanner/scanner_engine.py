from data.instrument_resolver import resolve_instrument_token
from data.historical_data import (
    fetch_historical_data,
    standardize_historical_data,
)
from data.data_validator import validate_market_data


def fetch_universe_data(
    kite,
    universe,
    from_date,
    to_date,
    interval="5minute",
):
    """Fetch and validate market data for a universe of instruments."""

    print("\n" + "=" * 60)
    print("GARUDA MULTI-STOCK DATA FETCHER")
    print("=" * 60)

    universe_data = {}

    for instrument in universe:

        tradingsymbol = instrument["tradingsymbol"]
        exchange = instrument["exchange"]

        print(f"\nProcessing {exchange}:{tradingsymbol}")
        print("-" * 60)

        instrument_token = resolve_instrument_token(
            kite=kite,
            tradingsymbol=tradingsymbol,
            exchange=exchange,
        )

        if instrument_token is None:
            print(f"Skipping {tradingsymbol}: Token unavailable.")
            continue

        market_data = fetch_historical_data(
            kite=kite,
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
        )

        if market_data.empty:
            print(f"Skipping {tradingsymbol}: No market data.")
            continue

        standardized_data = standardize_historical_data(
            market_data
        )

        is_valid = validate_market_data(
            standardized_data
        )

        if not is_valid:
            print(f"Skipping {tradingsymbol}: Validation failed.")
            continue

        universe_data[tradingsymbol] = standardized_data

        print(
            f"✅ {tradingsymbol}: "
            f"{len(standardized_data)} candles ready"
        )

    print("\n" + "=" * 60)
    print("MULTI-STOCK FETCH SUMMARY")
    print("=" * 60)

    print(f"Requested Instruments : {len(universe)}")
    print(f"Successful Instruments: {len(universe_data)}")
    print(f"Failed Instruments    : {len(universe) - len(universe_data)}")

    print("=" * 60)

    return universe_data