import sys
from pathlib import Path
from datetime import date, timedelta



PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from broker.session_manager import create_authenticated_session
from data.historical_data import (
    fetch_historical_data,
    standardize_historical_data,
)
from data.data_validator import validate_market_data
from data.data_storage import (
    save_market_data,
    load_saved_market_data,
)
from data.instrument_resolver import resolve_instrument_token

def main():

    print("=" * 60)
    print("GARUDA REAL HISTORICAL DATA TEST")
    print("=" * 60)

    kite = create_authenticated_session()

    if kite is None:
        print("Test Failed: Authenticated session unavailable.")
        return

    # Temporary test token.
    # We will build proper instrument resolution next.
    instrument_token = resolve_instrument_token(
        kite=kite,
        tradingsymbol="NIFTY 50",
        exchange="NSE",
    )

    if instrument_token is None:
        print("\n❌ Test Failed: Instrument resolution failed.")
        return

    to_date = date.today() - timedelta(days=1)
    from_date = to_date - timedelta(days=5)

    market_data = fetch_historical_data(
        kite=kite,
        instrument_token=instrument_token,
        from_date=from_date,
        to_date=to_date,
        interval="5minute",
    )

    standardized_data = standardize_historical_data(market_data)

    is_valid = validate_market_data(standardized_data)

    if not is_valid:
        print("\n❌ Real market data validation failed.")
        return

    file_path = save_market_data(
    standardized_data,
    "NIFTY_5MIN_REAL.csv",
    )

    reloaded_data = load_saved_market_data(file_path)

    reloaded_is_valid = validate_market_data(reloaded_data)

    if not reloaded_is_valid:
        print("\n❌ Reloaded real market data validation failed.")
        return
    original_for_comparison = standardized_data.copy()
    reloaded_for_comparison = reloaded_data.copy()

    original_for_comparison["datetime"] = (
        original_for_comparison["datetime"].astype(str)
    )

    reloaded_for_comparison["datetime"] = (
        reloaded_for_comparison["datetime"].astype(str)
    )

    data_matches = original_for_comparison.equals(
        reloaded_for_comparison
    )

    if not data_matches:
        print("\n❌ Data Integrity Check: FAILED")
        return

    print("\n✅ Data Integrity Check: PASSED")
    # print("\nFirst 5 Candles")
    # print("-" * 60)
    # print(standardized_data.head())

    # print("\nTest Summary")
    # print("-" * 60)
    # print(f"Rows Received : {len(standardized_data)}")

    # print("\n" + "=" * 60)
    # print("GARUDA REAL MARKET DATA PIPELINE")
    # print("=" * 60)

    # print(f"Candles Received : {len(market_data)}")
    # print(f"Candles Validated: {len(standardized_data)}")
    # print("Data Source      : KITE")
    # print("Data Validation  : PASSED")
    # print("Pipeline Status  : SUCCESS")

    # print("=" * 60)
    # ###
    # if not standardized_data.empty:
    #     print("Historical Data Test : SUCCESS")
    # else:
    #     print("Historical Data Test : FAILED")

    print("\n" + "=" * 60)
    print("GARUDA REAL MARKET DATA PIPELINE")
    print("=" * 60)

    print(f"Raw Candles       : {len(market_data)}")
    print(f"Validated Candles : {len(standardized_data)}")
    print(f"Reloaded Candles  : {len(reloaded_data)}")
    print(f"Saved File        : {file_path.name}")
    print("Data Source       : KITE")
    print("Validation        : PASSED")
    print("Storage           : PASSED")
    print("Reload            : PASSED")
    print("Pipeline Status   : SUCCESS")
    print("Data Integrity     : PASSED")

    print("=" * 60)
if __name__ == "__main__":
    main()