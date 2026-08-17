import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd


# ============================================================
# GARUDA — KITE 5-MINUTE HISTORICAL DATA DOWNLOADER
#
# Purpose:
#   Build a reproducible 6–12 month (default: 365-day)
#   local 5-minute OHLCV research dataset for GARUDA's
#   seven-symbol equity universe.
#
# Design:
#   - Reuses GARUDA's existing Kite authentication.
#   - Reuses GARUDA's existing instrument resolver interface.
#   - Requests historical data in safe sub-100-day chunks.
#   - Resumes from existing CSVs where possible.
#   - Does not touch the live/paper trading engine.
#   - Does not place broker orders.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))

from broker.session_manager import create_authenticated_session
from data.instrument_resolver import resolve_instrument_token


# ============================================================
# CONFIGURATION
# ============================================================

SYMBOLS = [
    "INFY",
    "RELIANCE",
    "ICICIBANK",
    "TMPV",
    "ASHOKLEY",
    "OLAELEC",
    "SUZLON",
]

EXCHANGE = "NSE"
INTERVAL = "5minute"

# Default research window.
LOOKBACK_DAYS = 365

# Kite's documented 5-minute per-request range is 100 days.
# We deliberately use 90 days for a safety margin.
CHUNK_DAYS = 90

# Keep requests comfortably below the documented 3 req/sec
# historical API rate.
REQUEST_DELAY_SECONDS = 0.40

RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Existing GARUDA naming convention.
def output_path(symbol):
    return RAW_DIR / f"{symbol}_5MIN_REAL.csv"


# ============================================================
# HELPERS
# ============================================================

def normalize_candles(candles):
    """Convert Kite candle records into GARUDA OHLCV format."""

    if not candles:
        return pd.DataFrame(
            columns=[
                "datetime",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]
        )

    dataframe = pd.DataFrame(candles)

    # Kite normally returns:
    # date, open, high, low, close, volume
    if "date" in dataframe.columns:
        dataframe = dataframe.rename(
            columns={"date": "datetime"}
        )

    required = [
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    missing = [
        column
        for column in required
        if column not in dataframe.columns
    ]

    if missing:
        raise RuntimeError(
            "Kite response missing required columns: "
            f"{missing}"
        )

    dataframe = dataframe[required].copy()

    dataframe["datetime"] = pd.to_datetime(
        dataframe["datetime"],
        errors="coerce",
    )

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    return dataframe


def validate_ohlcv(dataframe, symbol):
    """Strict local validation for the research dataset."""

    if dataframe.empty:
        raise RuntimeError(
            f"{symbol}: no candles available."
        )

    required = {
        "datetime",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    missing = required - set(dataframe.columns)

    if missing:
        raise RuntimeError(
            f"{symbol}: missing columns {sorted(missing)}"
        )

    if dataframe["datetime"].isna().any():
        raise RuntimeError(
            f"{symbol}: invalid datetime values."
        )

    if dataframe[
        [
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ].isna().any().any():
        raise RuntimeError(
            f"{symbol}: missing OHLCV values."
        )

    if dataframe["datetime"].duplicated().any():
        duplicates = int(
            dataframe["datetime"].duplicated().sum()
        )
        raise RuntimeError(
            f"{symbol}: {duplicates} duplicate candles."
        )

    invalid_high = (
        (dataframe["high"] < dataframe["open"])
        | (dataframe["high"] < dataframe["close"])
        | (dataframe["high"] < dataframe["low"])
    )

    if invalid_high.any():
        raise RuntimeError(
            f"{symbol}: invalid HIGH candle(s)."
        )

    invalid_low = (
        (dataframe["low"] > dataframe["open"])
        | (dataframe["low"] > dataframe["close"])
        | (dataframe["low"] > dataframe["high"])
    )

    if invalid_low.any():
        raise RuntimeError(
            f"{symbol}: invalid LOW candle(s)."
        )

    if (dataframe["volume"] < 0).any():
        raise RuntimeError(
            f"{symbol}: negative volume detected."
        )

    return True


def load_existing(path):
    """Load an existing local dataset if present."""

    if not path.exists():
        return pd.DataFrame()

    print(
        f"Existing local file found: {path}"
    )

    dataframe = pd.read_csv(path)

    if "datetime" not in dataframe.columns:
        raise RuntimeError(
            f"Existing file has no datetime column: {path}"
        )

    dataframe["datetime"] = pd.to_datetime(
        dataframe["datetime"],
        errors="coerce",
    )

    return dataframe


def request_chunk(
    kite,
    instrument_token,
    start_date,
    end_date,
    symbol,
):
    """Fetch one safe historical chunk."""

    print(
        f"  Request: {start_date} -> {end_date}"
    )

    try:
        candles = kite.historical_data(
            instrument_token=instrument_token,
            from_date=start_date,
            to_date=end_date,
            interval=INTERVAL,
        )
    except Exception as error:
        raise RuntimeError(
            f"{symbol}: Kite historical request failed "
            f"for {start_date} -> {end_date}: {error}"
        ) from error

    dataframe = normalize_candles(candles)

    print(
        f"  Candles received: {len(dataframe)}"
    )

    return dataframe


def merge_and_save(
    existing,
    new_data,
    path,
    symbol,
):
    """Merge, de-duplicate, sort, validate, and save."""

    frames = []

    if existing is not None and not existing.empty:
        frames.append(existing)

    if new_data is not None and not new_data.empty:
        frames.append(new_data)

    if not frames:
        raise RuntimeError(
            f"{symbol}: no data to save."
        )

    dataframe = pd.concat(
        frames,
        ignore_index=True,
    )

    dataframe["datetime"] = pd.to_datetime(
        dataframe["datetime"],
        errors="coerce",
    )

    dataframe = (
        dataframe
        .dropna(subset=["datetime"])
        .sort_values("datetime")
        .drop_duplicates(
            subset=["datetime"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    dataframe = dataframe[
        [
            "datetime",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ]
    ]

    validate_ohlcv(
        dataframe,
        symbol,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_csv(
        path,
        index=False,
    )

    return dataframe


def coverage_summary(dataframe):
    """Return coverage information."""

    if dataframe.empty:
        return None

    start = pd.Timestamp(
        dataframe["datetime"].min()
    )

    end = pd.Timestamp(
        dataframe["datetime"].max()
    )

    calendar_days = (
        end - start
    ).total_seconds() / 86400.0

    trading_dates = (
        dataframe["datetime"]
        .dt.date
        .nunique()
    )

    return {
        "start": start,
        "end": end,
        "calendar_days": calendar_days,
        "trading_days": trading_dates,
        "rows": len(dataframe),
    }


# ============================================================
# MAIN SYMBOL DOWNLOAD
# ============================================================

def download_symbol(
    kite,
    symbol,
    from_date,
    to_date,
):
    print()
    print("=" * 80)
    print(f"DOWNLOAD : {symbol}")
    print("=" * 80)

    path = output_path(symbol)

    # Resolve current NSE instrument token using GARUDA's
    # existing resolver interface.
    token = resolve_instrument_token(
        kite=kite,
        tradingsymbol=symbol,
        exchange=EXCHANGE,
    )

    if token is None:
        raise RuntimeError(
            f"{symbol}: instrument token could not be resolved."
        )

    print(
        f"Instrument token : {token}"
    )

    existing = load_existing(path)

    # Only fetch the requested research window.
    existing_window = pd.DataFrame()

    if not existing.empty:
        existing_window = existing[
            (
                existing["datetime"]
                >= pd.Timestamp(from_date)
            )
            & (
                existing["datetime"]
                <= pd.Timestamp(to_date)
            )
        ].copy()

        if not existing_window.empty:
            print(
                "Existing candles inside requested window: "
                f"{len(existing_window)}"
            )

    # Fetch all chunks. This is intentionally deterministic and
    # easy to audit; existing data is merged afterwards.
    chunks = []

    cursor = from_date

    while cursor <= to_date:

        chunk_end = min(
            cursor
            + timedelta(
                days=CHUNK_DAYS
            ),
            to_date,
        )

        # Small overlap between chunks avoids boundary gaps.
        request_end = chunk_end

        chunk = request_chunk(
            kite=kite,
            instrument_token=token,
            start_date=cursor,
            end_date=request_end,
            symbol=symbol,
        )

        if not chunk.empty:
            chunks.append(chunk)

        cursor = (
            chunk_end
            + timedelta(days=1)
        )

        if cursor <= to_date:
            time.sleep(
                REQUEST_DELAY_SECONDS
            )

    fetched = (
        pd.concat(
            chunks,
            ignore_index=True,
        )
        if chunks
        else pd.DataFrame()
    )

    dataframe = merge_and_save(
        existing=existing,
        new_data=fetched,
        path=path,
        symbol=symbol,
    )

    summary = coverage_summary(
        dataframe
    )

    print()
    print(
        f"{symbol} SAVED"
    )
    print(
        f"Rows          : {summary['rows']}"
    )
    print(
        f"Coverage      : "
        f"{summary['start']} -> {summary['end']}"
    )
    print(
        f"Calendar days : "
        f"{summary['calendar_days']:.1f}"
    )
    print(
        f"Trading days  : "
        f"{summary['trading_days']}"
    )
    print(
        f"File          : {path}"
    )

    return {
        "symbol": symbol,
        "token": token,
        "path": path,
        **summary,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print(
        "GARUDA — KITE 5-MINUTE HISTORICAL DATA BUILD"
    )
    print("=" * 100)
    print(
        f"Symbols       : {len(SYMBOLS)}"
    )
    print(
        f"Interval      : {INTERVAL}"
    )
    print(
        f"Lookback      : {LOOKBACK_DAYS} calendar days"
    )
    print(
        f"Chunk size    : {CHUNK_DAYS} days"
    )
    print(
        f"Request delay : {REQUEST_DELAY_SECONDS:.2f}s"
    )
    print("=" * 100)

    # --------------------------------------------------------
    # Date window
    # --------------------------------------------------------
    to_date = (
        date.today()
        - timedelta(days=1)
    )

    from_date = (
        to_date
        - timedelta(days=LOOKBACK_DAYS)
    )

    print()
    print(
        f"Research window: "
        f"{from_date} -> {to_date}"
    )

    # --------------------------------------------------------
    # Authenticate using existing GARUDA session manager.
    # No credentials are embedded in this script.
    # --------------------------------------------------------
    print()
    print(
        "Authenticating GARUDA Kite session..."
    )

    kite = create_authenticated_session()

    if kite is None:
        raise RuntimeError(
            "Authenticated Kite session unavailable. "
            "Refresh the normal GARUDA Kite session first."
        )

    print(
        "Kite session : READY"
    )

    # --------------------------------------------------------
    # Download all seven symbols.
    # One symbol failure does not destroy completed symbols.
    # --------------------------------------------------------
    results = []
    failures = []

    for symbol in SYMBOLS:

        try:

            result = download_symbol(
                kite=kite,
                symbol=symbol,
                from_date=from_date,
                to_date=to_date,
            )

            results.append(result)

        except Exception as error:

            failures.append(
                {
                    "symbol": symbol,
                    "error": str(error),
                }
            )

            print()
            print(
                f"❌ {symbol} FAILED"
            )
            print(
                f"Reason: {error}"
            )

    # --------------------------------------------------------
    # Final coverage report
    # --------------------------------------------------------
    print()
    print("=" * 110)
    print(
        "GARUDA — HISTORICAL DATA COVERAGE REPORT"
    )
    print("=" * 110)

    print(
        f"{'SYMBOL':<14}"
        f"{'ROWS':>10}"
        f"{'TRADING DAYS':>15}"
        f"{'CALENDAR DAYS':>15}"
        f"{'START':<24}"
        f"{'END':<24}"
        f"{'STATUS':<12}"
    )

    print("-" * 110)

    for result in results:

        status = (
            "PASS"
            if result["calendar_days"]
            >= 180
            else "SHORT"
        )

        print(
            f"{result['symbol']:<14}"
            f"{result['rows']:>10}"
            f"{result['trading_days']:>15}"
            f"{result['calendar_days']:>15.1f}"
            f"{str(result['start']):<24}"
            f"{str(result['end']):<24}"
            f"{status:<12}"
        )

    for failure in failures:

        print(
            f"{failure['symbol']:<14}"
            f"{'-':>10}"
            f"{'-':>15}"
            f"{'-':>15}"
            f"{'-':<24}"
            f"{'-':<24}"
            f"{'FAILED':<12}"
        )

    print("-" * 110)

    print(
        f"Successful symbols : {len(results)} / {len(SYMBOLS)}"
    )

    print(
        f"Failed symbols     : {len(failures)}"
    )

    print()

    if failures:

        print(
            "FAILED SYMBOLS"
        )

        for failure in failures:
            print(
                f"  - {failure['symbol']}: "
                f"{failure['error']}"
            )

    # --------------------------------------------------------
    # Research readiness
    # --------------------------------------------------------
    inadequate = [
        result
        for result in results
        if result["calendar_days"] < 180
    ]

    print()
    print("=" * 110)

    if not failures and not inadequate:

        print(
            "HISTORICAL DATA BUILD : READY FOR 7-STOCK RESEARCH"
        )

    else:

        print(
            "HISTORICAL DATA BUILD : NOT YET READY"
        )

        if inadequate:
            print(
                "Reason: one or more symbols have less than "
                "180 calendar days of local data."
            )

        if failures:
            print(
                "Reason: one or more symbols failed download."
            )

    print("=" * 110)

    print()
    print(
        "IMPORTANT:"
    )
    print(
        "This program ONLY downloads and validates historical market data."
    )
    print(
        "It does not place, modify, or simulate broker orders."
    )
    print(
        "The next research program should consume these local CSV files."
    )


if __name__ == "__main__":
    main()
