from config.settings import *
from data.data_loader import create_sample_market_data
from data.data_validator import validate_market_data
from data.data_storage import (
    save_market_data,
    load_saved_market_data,
)

def main():

    print("=" * 60)
    print(PROJECT_NAME)
    print(f"Version : {VERSION}")
    print(f"Mode    : {MODE}")
    print("=" * 60)

    print("\nLoading market data...\n")

    market_data = create_sample_market_data()

    is_valid = validate_market_data(market_data)

    if not is_valid:
        print("\nGARUDA stopped: Invalid market data.")
        return
    
    file_path = save_market_data(
    market_data,
    "NIFTY_5MIN.csv"
    )

    reloaded_data = load_saved_market_data(file_path)

    reloaded_is_valid = validate_market_data(reloaded_data)

    if not reloaded_is_valid:
        print("\nGARUDA stopped: Reloaded data failed validation.")
        return

    print(market_data)

    print("\nMarket Data Summary")
    print("-" * 60)

    print(f"Number of Candles : {len(market_data)}")
    print(f"Latest Close      : {market_data['close'].iloc[-1]}")
    print(f"Total Volume      : {market_data['volume'].sum()}")

    print("-" * 60)
    print("GARUDA Market Data Engine: RUNNING")

    print("\n" + "=" * 60)
    print("GARUDA MARKET DATA ENGINE")
    print("=" * 60)
    print(f"Original Candles : {len(market_data)}")
    print(f"Reloaded Candles : {len(reloaded_data)}")
    print("Pipeline Status  : SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()