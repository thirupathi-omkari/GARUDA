import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from indicators.vwap import calculate_vwap

SYMBOLS = [
    "INFY",
    "RELIANCE",
    "ICICIBANK",
    "TMPV",
    "ASHOKLEY",
    "OLAELEC",
    "SUZLON",
]

RESEARCH_DIR = ROOT / "data" / "research"
RAW_DIR = ROOT / "data" / "raw"

# Locked provisional baseline for this diagnostic only.
# Do not change the frozen entries or generate a new strategy.
TARGET_R = 2.0


def load_entries(symbol):
    path = RESEARCH_DIR / f"{symbol}_frozen_entries_1y.csv"
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    for col in [
        "signal_candle_time",
        "entry_candle_time",
        "trade_date",
    ]:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
            )

    return df


def load_data(symbol):
    path = RAW_DIR / f"{symbol}_5MIN_REAL.csv"
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(
        df["datetime"],
        errors="coerce",
    )

    df = (
        df.dropna(subset=["datetime"])
        .sort_values("datetime")
        .drop_duplicates("datetime")
        .reset_index(drop=True)
    )

    return df


def session_map(df):
    result = {}

    for trade_date, group in df.groupby(
        df["datetime"].dt.date
    ):
        session = (
            group
            .sort_values("datetime")
            .reset_index(drop=True)
        )

        session = session[
            (
                session["datetime"].dt.time
                >= pd.Timestamp("09:15").time()
            )
            & (
                session["datetime"].dt.time
                <= pd.Timestamp("15:30").time()
            )
        ].reset_index(drop=True)

        if not session.empty:
            result[trade_date] = calculate_vwap(
                session
            )

    return result


def opening_range(session):
    orb = session[
        (
            session["datetime"].dt.time
            >= pd.Timestamp("09:15").time()
        )
        & (
            session["datetime"].dt.time
            < pd.Timestamp("09:30").time()
        )
    ]

    if orb.empty:
        return np.nan, np.nan, np.nan

    high = float(orb["high"].max())
    low = float(orb["low"].min())

    return high, low, high - low


def safe_slope(series):
    if len(series) < 2:
        return np.nan

    x = np.arange(len(series), dtype=float)
    y = np.asarray(series, dtype=float)

    if not np.isfinite(y).all():
        return np.nan

    return float(
        np.polyfit(x, y, 1)[0]
    )


def main():
    print()
    print("=" * 120)
    print("GARUDA — ORB+VWAP 1-YEAR ENTRY DIAGNOSTIC")
    print("=" * 120)
    print("Universe       : existing frozen 1-year entries")
    print("Symbols        : 7")
    print("Entries        : 1,880 total expected")
    print("Baseline       : 50% ORB SL + 2R target")
    print("BE             : OFF")
    print("Trailing       : OFF")
    print("Purpose        : diagnose entry quality, NOT create a new strategy")
    print("=" * 120)

    all_rows = []

    for symbol in SYMBOLS:

        entries = load_entries(symbol)
        data = load_data(symbol)
        sessions = session_map(data)

        print()
        print("-" * 110)
        print(
            f"{symbol}: frozen entries={len(entries)}"
        )
        print("-" * 110)

        for _, entry in entries.iterrows():

            trade_date = (
                pd.Timestamp(
                    entry["trade_date"]
                ).date()
            )

            session = sessions.get(
                trade_date
            )

            if session is None:
                raise RuntimeError(
                    f"{symbol}: missing session {trade_date}"
                )

            signal_time = pd.Timestamp(
                entry["signal_candle_time"]
            )

            entry_time = pd.Timestamp(
                entry["entry_candle_time"]
            )

            signal_match = session[
                session["datetime"] == signal_time
            ]

            entry_match = session[
                session["datetime"] == entry_time
            ]

            if signal_match.empty or entry_match.empty:
                raise RuntimeError(
                    f"{symbol}: frozen candle not found "
                    f"for {trade_date}"
                )

            signal_idx = int(
                signal_match.index[0]
            )
            entry_idx = int(
                entry_match.index[0]
            )

            signal = session.iloc[
                signal_idx
            ]

            entry_candle = session.iloc[
                entry_idx
            ]

            orb_high, orb_low, orb_range = (
                opening_range(session)
            )

            direction = str(
                entry["direction"]
            ).upper()

            entry_price = float(
                entry["entry_price"]
            )

            entry_vwap = float(
                entry_candle["vwap"]
            )

            signal_vwap = float(
                signal["vwap"]
            )

            # VWAP slope immediately before signal.
            lookback_start = max(
                0,
                signal_idx - 5,
            )

            vwap_window = session.iloc[
                lookback_start:
                signal_idx + 1
            ]["vwap"]

            vwap_slope = safe_slope(
                vwap_window
            )

            if direction == "BUY":

                vwap_distance = (
                    entry_price
                    - entry_vwap
                )

                signal_vwap_distance = (
                    float(signal["close"])
                    - signal_vwap
                )

                entry_bar_return = (
                    float(entry_candle["close"])
                    / float(entry_candle["open"])
                    - 1
                )

                close_vs_orb = (
                    float(signal["close"])
                    - orb_high
                )

            else:

                vwap_distance = (
                    entry_vwap
                    - entry_price
                )

                signal_vwap_distance = (
                    signal_vwap
                    - float(signal["close"])
                )

                entry_bar_return = (
                    float(entry_candle["close"])
                    / float(entry_candle["open"])
                    - 1
                )

                close_vs_orb = (
                    orb_low
                    - float(signal["close"])
                )

            # Forward excursion from the entry candle onward.
            future = session.iloc[
                entry_idx:
            ]

            if direction == "BUY":
                mfe = (
                    float(future["high"].max())
                    - entry_price
                )
                mae = (
                    entry_price
                    - float(future["low"].min())
                )

                risk = (
                    0.50 * orb_range
                )

            else:
                mfe = (
                    entry_price
                    - float(future["low"].min())
                )
                mae = (
                    float(future["high"].max())
                    - entry_price
                )

                risk = (
                    0.50 * orb_range
                )

            mfe = max(0.0, mfe)
            mae = max(0.0, mae)

            mfe_r = (
                mfe / risk
                if risk > 0
                else np.nan
            )

            mae_r = (
                mae / risk
                if risk > 0
                else np.nan
            )

            target_hit = (
                mfe_r >= TARGET_R
                if np.isfinite(mfe_r)
                else False
            )

            stop_hit = (
                mae_r >= 1.0
                if np.isfinite(mae_r)
                else False
            )

            # The diagnostic intentionally does not resolve
            # intrabar ambiguity. It only describes excursion.
            all_rows.append(
                {
                    "SYMBOL": symbol,
                    "trade_date": trade_date,
                    "direction": direction,
                    "signal_time": signal_time,
                    "entry_time": entry_time,
                    "entry_price": entry_price,
                    "signal_close": float(
                        signal["close"]
                    ),
                    "signal_vwap": signal_vwap,
                    "entry_open": float(
                        entry_candle["open"]
                    ),
                    "entry_high": float(
                        entry_candle["high"]
                    ),
                    "entry_low": float(
                        entry_candle["low"]
                    ),
                    "entry_close": float(
                        entry_candle["close"]
                    ),
                    "entry_vwap": entry_vwap,
                    "orb_high": orb_high,
                    "orb_low": orb_low,
                    "orb_range": orb_range,
                    "signal_vwap_distance": signal_vwap_distance,
                    "entry_vwap_distance": vwap_distance,
                    "vwap_slope_5bars": vwap_slope,
                    "signal_close_vs_orb": close_vs_orb,
                    "entry_bar_return_pct":
                        entry_bar_return * 100,
                    "risk": risk,
                    "mfe": mfe,
                    "mae": mae,
                    "mfe_r": mfe_r,
                    "mae_r": mae_r,
                    "target_2r_reached":
                        target_hit,
                    "stop_1r_reached":
                        stop_hit,
                    "entry_hour":
                        entry_time.hour,
                    "entry_minute":
                        entry_time.minute,
                    "minutes_from_open":
                        (
                            entry_time.hour * 60
                            + entry_time.minute
                            - 9 * 60
                            - 15
                        ),
                }
            )

    df = pd.DataFrame(all_rows)

    expected = 1880

    if len(df) != expected:
        raise RuntimeError(
            f"Expected {expected} diagnostic rows, got {len(df)}"
        )

    # --------------------------------------------------------
    # Save raw diagnostic dataset.
    # --------------------------------------------------------
    detail_path = (
        RESEARCH_DIR
        / "garuda_orbvwap_1year_entry_diagnostic_detail.csv"
    )

    df.to_csv(
        detail_path,
        index=False,
    )

    # --------------------------------------------------------
    # Helper: summary by grouping variable.
    # --------------------------------------------------------
    def group_summary(column):
        rows = []

        for value, group in df.groupby(
            column,
            dropna=False
        ):
            rows.append(
                {
                    "GROUP":
                        value,
                    "TRADES":
                        len(group),
                    "AVG_MFE_R":
                        group["mfe_r"].mean(),
                    "MEDIAN_MFE_R":
                        group["mfe_r"].median(),
                    "AVG_MAE_R":
                        group["mae_r"].mean(),
                    "MEDIAN_MAE_R":
                        group["mae_r"].median(),
                    "TARGET_2R_RATE_PCT":
                        group[
                            "target_2r_reached"
                        ].mean() * 100,
                    "STOP_1R_RATE_PCT":
                        group[
                            "stop_1r_reached"
                        ].mean() * 100,
                    "AVG_ENTRY_VWAP_DISTANCE":
                        group[
                            "entry_vwap_distance"
                        ].mean(),
                    "AVG_SIGNAL_VWAP_DISTANCE":
                        group[
                            "signal_vwap_distance"
                        ].mean(),
                    "AVG_ORB_RANGE":
                        group[
                            "orb_range"
                        ].mean(),
                }
            )

        return pd.DataFrame(rows)

    summaries = {}

    group_columns = [
        "SYMBOL",
        "direction",
        "entry_hour",
        "minutes_from_open",
    ]

    for column in group_columns:
        summary = group_summary(
            column
        )

        summaries[column] = summary

        path = (
            RESEARCH_DIR
            / f"garuda_orbvwap_entry_diagnostic_by_{column}.csv"
        )

        summary.to_csv(
            path,
            index=False,
        )

    # --------------------------------------------------------
    # Time buckets.
    # --------------------------------------------------------
    bins = [
        -1,
        30,
        60,
        90,
        120,
        180,
        240,
        9999,
    ]

    labels = [
        "0-30m",
        "31-60m",
        "61-90m",
        "91-120m",
        "121-180m",
        "181-240m",
        "241m+",
    ]

    df["entry_time_bucket"] = pd.cut(
        df["minutes_from_open"],
        bins=bins,
        labels=labels,
    )

    time_summary = group_summary(
        "entry_time_bucket"
    )

    time_summary.to_csv(
        RESEARCH_DIR
        / "garuda_orbvwap_entry_diagnostic_by_time_bucket.csv",
        index=False,
    )

    # --------------------------------------------------------
    # ORB range buckets by cross-sectional quartiles.
    # --------------------------------------------------------
    q1, q2, q3 = df[
        "orb_range"
    ].quantile(
        [0.25, 0.50, 0.75]
    )

    df["orb_range_bucket"] = pd.cut(
        df["orb_range"],
        bins=[
            -np.inf,
            q1,
            q2,
            q3,
            np.inf,
        ],
        labels=[
            "Q1_smallest",
            "Q2",
            "Q3",
            "Q4_largest",
        ],
        include_lowest=True,
    )

    orb_summary = group_summary(
        "orb_range_bucket"
    )

    orb_summary.to_csv(
        RESEARCH_DIR
        / "garuda_orbvwap_entry_diagnostic_by_orb_range.csv",
        index=False,
    )

    # --------------------------------------------------------
    # VWAP distance buckets.
    # --------------------------------------------------------
    v1, v2, v3 = df[
        "entry_vwap_distance"
    ].abs().quantile(
        [0.25, 0.50, 0.75]
    )

    df["entry_vwap_distance_bucket"] = pd.cut(
        df["entry_vwap_distance"].abs(),
        bins=[
            -np.inf,
            v1,
            v2,
            v3,
            np.inf,
        ],
        labels=[
            "Q1_closest",
            "Q2",
            "Q3",
            "Q4_farthest",
        ],
        include_lowest=True,
    )

    vwap_summary = group_summary(
        "entry_vwap_distance_bucket"
    )

    vwap_summary.to_csv(
        RESEARCH_DIR
        / "garuda_orbvwap_entry_diagnostic_by_vwap_distance.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Signal VWAP slope buckets.
    # --------------------------------------------------------
    df["vwap_slope_sign"] = np.select(
        [
            df["vwap_slope_5bars"] > 0,
            df["vwap_slope_5bars"] < 0,
        ],
        [
            "UP",
            "DOWN",
        ],
        default="FLAT",
    )

    slope_summary = group_summary(
        "vwap_slope_sign"
    )

    slope_summary.to_csv(
        RESEARCH_DIR
        / "garuda_orbvwap_entry_diagnostic_by_vwap_slope.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Print the core findings.
    # --------------------------------------------------------
    print()
    print("=" * 120)
    print("CORE DIAGNOSTIC — 7 STOCKS")
    print("=" * 120)

    print(
        f"Total frozen entries : {len(df)}"
    )

    print()
    print("BY SYMBOL")
    print(
        summaries["SYMBOL"].to_string(
            index=False
        )
    )

    print()
    print("BY DIRECTION")
    print(
        summaries["direction"].to_string(
            index=False
        )
    )

    print()
    print("BY ENTRY TIME")
    print(
        time_summary.to_string(
            index=False
        )
    )

    print()
    print("BY ORB RANGE")
    print(
        orb_summary.to_string(
            index=False
        )
    )

    print()
    print("BY ENTRY-VWAP DISTANCE")
    print(
        vwap_summary.to_string(
            index=False
        )
    )

    print()
    print("BY VWAP SLOPE")
    print(
        slope_summary.to_string(
            index=False
        )
    )

    print()
    print("=" * 120)
    print("TOP / BOTTOM SYMBOLS BY AVG MFE")
    print("=" * 120)

    symbol_sorted = summaries[
        "SYMBOL"
    ].sort_values(
        "AVG_MFE_R",
        ascending=False,
    )

    print(
        symbol_sorted.to_string(
            index=False
        )
    )

    print()
    print("=" * 120)
    print("DIAGNOSTIC FILE")
    print("=" * 120)

    print(detail_path)

    print()
    print(
        "This diagnostic does NOT alter the locked entry logic "
        "and does NOT propose a new strategy."
    )


if __name__ == "__main__":
    main()
