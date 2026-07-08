from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def save_market_data(dataframe, filename):
    """Save validated market data to the raw data folder."""

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_path = RAW_DATA_DIR / filename

    dataframe.to_csv(file_path, index=False)

    print("\nSaving market data...")
    print("-" * 60)
    print(f"File saved successfully: {file_path}")
    print("-" * 60)

    return file_path


def load_saved_market_data(file_path):
    """Load previously saved market data from CSV."""

    print("\nReloading saved market data...")
    print("-" * 60)

    dataframe = pd.read_csv(file_path)

    print(f"File loaded successfully: {file_path}")
    print(f"Candles loaded: {len(dataframe)}")
    print("-" * 60)

    return dataframe