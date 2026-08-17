from pathlib import Path

import pandas as pd


# ============================================================
# GARUDA
# RETEST ENTRY — MFE / MAE EXCURSION ANALYSIS
# ============================================================

ROOT = Path(__file__).resolve().parent

INPUT_FILE = (
    ROOT
    / "data"
    / "retest_entry_2r_infy_corrected.csv"
)

PRICE_DATA_FILE = (
    ROOT
    / "data"
    / "raw"
    / "INFY_5MIN_REAL.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "retest_excursion_analysis_infy.csv"
)

SUMMARY_FILE = (
    ROOT
    / "data"
    / "retest_excursion_summary_infy.csv"
)


# ============================================================
# MFE THRESHOLDS
# ============================================================

THRESHOLDS_R = [
    0.25,
    0.50,
    0.75,
    1.00,
    1.25,
    1.50,
    1.75,
    2.00,
    2.50,
    3.00,
]


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 110)
print("GARUDA — RETEST ENTRY MFE / MAE EXCURSION ANALYSIS")
print("=" * 110)


# ============================================================
# LOAD PRICE DATA
# ============================================================

if not PRICE_DATA_FILE.exists():
    raise FileNotFoundError(
        f"Price data file not found:\n{PRICE_DATA_FILE}"
    )

price_df = pd.read_csv(
    PRICE_DATA_FILE
)

price_df["datetime"] = pd.to_datetime(
    price_df["datetime"]
)

price_df = (
    price_df
    .sort_values("datetime")
    .reset_index(drop=True)
)

print()
print(
    f"PRICE CANDLES LOADED : {len(price_df)}"
)


# ============================================================
# LOAD RETEST TRADES
# ============================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_FILE}"
    )

trades = pd.read_csv(
    INPUT_FILE
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "status",
    "trade_date",
    "direction",
    "entry_time",
    "entry_price",
    "stop_loss",
    "risk",
    "target",
    "exit_time",
    "exit_reason",
]

missing = [
    column
    for column in required_columns
    if column not in trades.columns
]

if missing:
    raise ValueError(
        "Missing required columns:\n"
        + "\n".join(missing)
    )


# ============================================================
# DATETIME CONVERSION
# ============================================================

trades["entry_time"] = pd.to_datetime(
    trades["entry_time"]
)

trades["exit_time"] = pd.to_datetime(
    trades["exit_time"]
)


# ============================================================
# KEEP ACTUAL TRADES
# ============================================================

trades = trades[
    trades["status"] == "TRADE"
].copy()

print()
print("=" * 110)
print("RAW TRADE VALIDATION")
print("=" * 110)

print(
    f"RAW TRADE ROWS : {len(trades)}"
)


# ============================================================
# ACTUAL TRADE IDENTITY
#
# One actual trade is defined by:
#
#   trade_date
#   direction
#   entry_time
#   entry_price
#
# We deliberately DO NOT use:
#
#   mode
#   retest_time
#   rejection_time
#   retest_high
#   retest_low
#   retest_vwap
#
# because ORB_LEVEL and ORB_VWAP_ZONE can describe the
# same actual execution differently.
# ============================================================

trades["trade_date_id"] = (
    trades["trade_date"]
    .astype(str)
    .str.strip()
)

trades["direction_id"] = (
    trades["direction"]
    .astype(str)
    .str.strip()
    .str.upper()
)

trades["entry_time_id"] = (
    trades["entry_time"]
    .astype(str)
    .str.strip()
)

trades["entry_price_id"] = (
    pd.to_numeric(
        trades["entry_price"],
        errors="coerce",
    )
    .round(6)
    .astype(str)
)

trades["trade_id"] = (
    trades["trade_date_id"]
    + "|"
    + trades["direction_id"]
    + "|"
    + trades["entry_time_id"]
    + "|"
    + trades["entry_price_id"]
)


# ============================================================
# COUNT UNIQUE TRADES
# ============================================================

raw_trade_rows = len(trades)

unique_trade_count = (
    trades["trade_id"].nunique()
)

duplicate_trade_rows = (
    raw_trade_rows
    - unique_trade_count
)


print(
    f"UNIQUE TRADE COUNT : {unique_trade_count}"
)

print(
    f"DUPLICATE ROWS     : {duplicate_trade_rows}"
)


# ============================================================
# SHOW DUPLICATE GROUPS
# ============================================================

duplicate_groups = (
    trades[
        trades["trade_id"].duplicated(
            keep=False
        )
    ]
    .sort_values(
        [
            "trade_date",
            "entry_time",
            "entry_price",
        ]
    )
)

if not duplicate_groups.empty:

    print()
    print("=" * 110)
    print("DUPLICATE TRADE GROUPS")
    print("=" * 110)

    print(
        duplicate_groups[
            [
                "trade_date",
                "direction",
                "entry_time",
                "entry_price",
                "mode",
            ]
        ].to_string(
            index=False
        )
    )


# ============================================================
# KEEP ONE ROW PER ACTUAL TRADE
# ============================================================

trades = (
    trades
    .sort_values(
        [
            "trade_date",
            "entry_time",
            "entry_price",
        ]
    )
    .drop_duplicates(
        subset=["trade_id"],
        keep="first",
    )
    .reset_index(drop=True)
)


# ============================================================
# FINAL UNIQUE TRADE CHECK
# ============================================================

print()
print("=" * 110)
print("FINAL UNIQUE TRADE CHECK")
print("=" * 110)

print(
    trades[
        [
            "trade_date",
            "direction",
            "entry_time",
            "entry_price",
        ]
    ].to_string(
        index=False
    )
)

print()
print(
    f"FINAL UNIQUE TRADES : {len(trades)}"
)

print("=" * 110)


# ============================================================
# BUILD TRADE PRICE PATHS
# ============================================================

results = []


for trade_index, trade in trades.iterrows():

    direction = str(
        trade["direction"]
    ).upper()

    entry_time = trade["entry_time"]

    exit_time = trade["exit_time"]

    entry_price = float(
        trade["entry_price"]
    )

    stop_loss = float(
        trade["stop_loss"]
    )

    risk = float(
        trade["risk"]
    )

    target = float(
        trade["target"]
    )

    exit_reason = str(
        trade["exit_reason"]
    )

    # --------------------------------------------------------
    # Validate risk
    # --------------------------------------------------------

    if risk <= 0:

        print(
            f"WARNING: invalid risk, "
            f"skipping trade {trade_index + 1}"
        )

        continue

    # --------------------------------------------------------
    # Price candles from entry through exit
    # --------------------------------------------------------

    future = price_df[
        (price_df["datetime"] >= entry_time)
        &
        (price_df["datetime"] <= exit_time)
    ].copy()

    if future.empty:

        print(
            f"WARNING: no candles found for "
            f"trade {trade_index + 1}"
        )

        continue

    # --------------------------------------------------------
    # Running excursion
    # --------------------------------------------------------

    running_mfe = 0.0

    running_mae = 0.0

    reached = {
        threshold: False
        for threshold in THRESHOLDS_R
    }

    reached_time = {
        threshold: None
        for threshold in THRESHOLDS_R
    }

    # --------------------------------------------------------
    # Replay candles
    # --------------------------------------------------------

    for _, candle in future.iterrows():

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        candle_time = candle[
            "datetime"
        ]

        if direction == "BUY":

            favorable_distance = max(
                0.0,
                high - entry_price,
            )

            adverse_distance = max(
                0.0,
                entry_price - low,
            )

        elif direction == "SELL":

            favorable_distance = max(
                0.0,
                entry_price - low,
            )

            adverse_distance = max(
                0.0,
                high - entry_price,
            )

        else:

            raise ValueError(
                f"Unknown direction: {direction}"
            )

        running_mfe = max(
            running_mfe,
            favorable_distance,
        )

        running_mae = max(
            running_mae,
            adverse_distance,
        )

        current_mfe_r = (
            running_mfe / risk
        )

        for threshold in THRESHOLDS_R:

            if (
                not reached[threshold]
                and current_mfe_r >= threshold
            ):

                reached[threshold] = True

                reached_time[
                    threshold
                ] = candle_time

    # --------------------------------------------------------
    # Final MFE / MAE
    # --------------------------------------------------------

    final_mfe_r = (
        running_mfe / risk
    )

    final_mae_r = (
        running_mae / risk
    )

    # --------------------------------------------------------
    # Store trade
    # --------------------------------------------------------

    row = {
        "trade_index":
            trade_index + 1,

        "trade_id":
            trade["trade_id"],

        "trade_date":
            trade["trade_date"],

        "direction":
            direction,

        "entry_time":
            entry_time,

        "entry_price":
            entry_price,

        "stop_loss":
            stop_loss,

        "risk":
            risk,

        "target":
            target,

        "exit_time":
            exit_time,

        "exit_reason":
            exit_reason,

        "mfe_r":
            final_mfe_r,

        "mae_r":
            final_mae_r,
    }

    for threshold in THRESHOLDS_R:

        name = f"{threshold:.2f}r"

        row[
            f"reached_{name}"
        ] = reached[threshold]

        row[
            f"reached_{name}_time"
        ] = reached_time[threshold]

    results.append(row)


# ============================================================
# RESULT DATAFRAME
# ============================================================

result_df = pd.DataFrame(
    results
)

total_trades = len(
    result_df
)


# ============================================================
# FINAL RESULT COUNT
# ============================================================

print()
print("=" * 110)
print(
    f"FINAL UNIQUE TRADES ANALYSED : {total_trades}"
)
print("=" * 110)


# ============================================================
# EXCURSION SUMMARY
# ============================================================

summary_rows = []


for threshold in THRESHOLDS_R:

    name = f"{threshold:.2f}r"

    reached_column = (
        f"reached_{name}"
    )

    reached_trades = result_df[
        result_df[reached_column]
    ]

    reached_count = len(
        reached_trades
    )

    reached_pct = (
        reached_count
        / total_trades
        * 100
        if total_trades
        else 0.0
    )

    stopped_after_reaching = len(
        reached_trades[
            reached_trades[
                "exit_reason"
            ].str.startswith(
                "STOP_LOSS"
            )
        ]
    )

    target_after_reaching = len(
        reached_trades[
            reached_trades[
                "exit_reason"
            ] == "TARGET"
        ]
    )

    eod_after_reaching = len(
        reached_trades[
            reached_trades[
                "exit_reason"
            ] == "END_OF_DAY"
        ]
    )

    avg_mfe = (
        reached_trades["mfe_r"].mean()
        if not reached_trades.empty
        else 0.0
    )

    avg_mae = (
        reached_trades["mae_r"].mean()
        if not reached_trades.empty
        else 0.0
    )

    summary_rows.append(
        {
            "threshold_r":
                threshold,

            "reached":
                reached_count,

            "reached_pct":
                reached_pct,

            "stopped_after_reaching":
                stopped_after_reaching,

            "target_after_reaching":
                target_after_reaching,

            "eod_after_reaching":
                eod_after_reaching,

            "avg_mfe_r":
                avg_mfe,

            "avg_mae_r":
                avg_mae,
        }
    )


summary_df = pd.DataFrame(
    summary_rows
)


# ============================================================
# PRINT EXCURSION LADDER
# ============================================================

print()
print("=" * 110)
print("EXCURSION LADDER")
print("=" * 110)

print()

print(
    summary_df.to_string(
        index=False,
        formatters={
            "threshold_r":
                lambda x: f"{x:.2f}",

            "reached_pct":
                lambda x: f"{x:.2f}",

            "avg_mfe_r":
                lambda x: f"{x:.3f}",

            "avg_mae_r":
                lambda x: f"{x:.3f}",
        },
    )
)


# ============================================================
# IMPORTANT MFE / STOP ANALYSIS
# ============================================================

print()
print("=" * 110)
print(
    "IMPORTANT MFE / STOP-LOSS ANALYSIS"
)
print("=" * 110)


for threshold in [
    0.50,
    1.00,
    1.25,
    1.50,
    1.75,
    2.00,
]:

    name = f"{threshold:.2f}r"

    reached_column = (
        f"reached_{name}"
    )

    reached_trades = result_df[
        result_df[reached_column]
    ]

    stopped = reached_trades[
        reached_trades[
            "exit_reason"
        ].str.startswith(
            "STOP_LOSS"
        )
    ]

    targets = reached_trades[
        reached_trades[
            "exit_reason"
        ] == "TARGET"
    ]

    eod = reached_trades[
        reached_trades[
            "exit_reason"
        ] == "END_OF_DAY"
    ]

    print()
    print(
        f"{threshold:.2f}R"
    )

    print(
        f"  Reached      : "
        f"{len(reached_trades)} / "
        f"{total_trades}"
    )

    print(
        f"  Then STOP   : "
        f"{len(stopped)}"
    )

    print(
        f"  Then TARGET : "
        f"{len(targets)}"
    )

    print(
        f"  Then EOD    : "
        f"{len(eod)}"
    )


# ============================================================
# >= 1R THEN STOP
# ============================================================

print()
print("=" * 110)
print(
    "TRADES THAT REACHED >= 1R BUT EVENTUALLY STOPPED"
)
print("=" * 110)

one_r_stops = result_df[
    result_df["reached_1.00r"]
    &
    result_df[
        "exit_reason"
    ].str.startswith(
        "STOP_LOSS"
    )
]

if one_r_stops.empty:

    print("NONE")

else:

    print(
        one_r_stops[
            [
                "trade_date",
                "direction",
                "entry_price",
                "risk",
                "mfe_r",
                "mae_r",
                "exit_reason",
            ]
        ].to_string(
            index=False
        )
    )


# ============================================================
# >= 1.5R THEN STOP
# ============================================================

print()
print("=" * 110)
print(
    "TRADES THAT REACHED >= 1.5R BUT EVENTUALLY STOPPED"
)
print("=" * 110)

one_half_r_stops = result_df[
    result_df["reached_1.50r"]
    &
    result_df[
        "exit_reason"
    ].str.startswith(
        "STOP_LOSS"
    )
]

if one_half_r_stops.empty:

    print("NONE")

else:

    print(
        one_half_r_stops[
            [
                "trade_date",
                "direction",
                "entry_price",
                "risk",
                "mfe_r",
                "mae_r",
                "exit_reason",
            ]
        ].to_string(
            index=False
        )
    )


# ============================================================
# FULL UNIQUE TRADE TABLE
# ============================================================

print()
print("=" * 110)
print("FULL UNIQUE TRADE MFE / MAE TABLE")
print("=" * 110)

print()

print(
    result_df[
        [
            "trade_date",
            "direction",
            "entry_price",
            "risk",
            "mfe_r",
            "mae_r",
            "exit_reason",
        ]
    ].to_string(
        index=False
    )
)


# ============================================================
# SAVE RESULTS
# ============================================================

result_df.to_csv(
    OUTPUT_FILE,
    index=False,
)

summary_df.to_csv(
    SUMMARY_FILE,
    index=False,
)


# ============================================================
# DONE
# ============================================================

print()
print("=" * 110)
print("SAVED")
print("=" * 110)

print(
    f"Trade-level file : {OUTPUT_FILE}"
)

print(
    f"Summary file     : {SUMMARY_FILE}"
)

print("=" * 110)