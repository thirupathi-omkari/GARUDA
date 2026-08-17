from pathlib import Path

import pandas as pd


# ============================================================
# GARUDA
# CORRECTED POST-ENTRY EXCURSION ANALYSIS
# ============================================================
#
# IMPORTANT RESEARCH RULE
# -----------------------
# Entry occurs at the OPEN of entry_time candle.
#
# Therefore:
#
#   entry candle = execution candle
#   next candle onward = valid post-entry excursion
#
# We DO NOT use the entry candle's full HIGH/LOW for MFE/MAE.
#
# This prevents same-candle look-ahead contamination.
#
# ============================================================


ROOT = Path(__file__).resolve().parent


PRICE_FILE = (
    ROOT
    / "data"
    / "raw"
    / "INFY_5MIN_REAL.csv"
)


TRADE_FILE = (
    ROOT
    / "data"
    / "retest_entry_2r_infy_corrected.csv"
)


OUTPUT_FILE = (
    ROOT
    / "corrected_post_entry_excursion_output.txt"
)


CSV_OUTPUT_FILE = (
    ROOT
    / "data"
    / "corrected_post_entry_excursion_analysis_infy.csv"
)


# ============================================================
# LOAD PRICE DATA
# ============================================================

prices = pd.read_csv(
    PRICE_FILE
)


prices["datetime"] = pd.to_datetime(
    prices["datetime"]
)


prices = (
    prices
    .sort_values("datetime")
    .reset_index(drop=True)
)


# ============================================================
# LOAD RETEST TRADES
# ============================================================

trades = pd.read_csv(
    TRADE_FILE
)


# ------------------------------------------------------------
# Normalize columns
# ------------------------------------------------------------

required_trade_columns = [
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
    for column in required_trade_columns
    if column not in trades.columns
]


if missing:

    raise ValueError(
        "Missing required trade columns: "
        + ", ".join(missing)
    )


# ------------------------------------------------------------
# Keep actual trade rows only when status exists
# ------------------------------------------------------------

if "status" in trades.columns:

    trades = trades[
        trades["status"]
        .astype(str)
        .str.upper()
        == "TRADE"
    ].copy()


# ============================================================
# PARSE DATETIME
# ============================================================

trades["entry_time"] = pd.to_datetime(
    trades["entry_time"]
)


trades["exit_time"] = pd.to_datetime(
    trades["exit_time"]
)


trades["trade_date"] = (
    trades["trade_date"]
    .astype(str)
)


trades["direction"] = (
    trades["direction"]
    .astype(str)
    .str.upper()
)


# ============================================================
# NUMERIC NORMALIZATION
# ============================================================

numeric_columns = [
    "entry_price",
    "stop_loss",
    "risk",
    "target",
]


for column in numeric_columns:

    trades[column] = pd.to_numeric(
        trades[column],
        errors="coerce",
    )


# ============================================================
# REMOVE INVALID ROWS
# ============================================================

trades = trades[
    trades["entry_price"].notna()
    &
    trades["risk"].notna()
    &
    trades["stop_loss"].notna()
    &
    trades["target"].notna()
].copy()


# ============================================================
# UNIQUE TRADE DEDUPLICATION
# ============================================================
#
# ORB_LEVEL and ORB_VWAP_ZONE represent the same underlying
# retest entry in the current experiment.
#
# Therefore one actual trade must be counted once.
#
# ============================================================

RAW_ROWS = len(trades)


dedupe_columns = [
    "trade_date",
    "direction",
    "entry_time",
    "entry_price",
]


trades = (
    trades
    .sort_values(
        [
            "trade_date",
            "entry_time",
            "direction",
            "entry_price",
        ]
    )
    .drop_duplicates(
        subset=dedupe_columns,
        keep="first",
    )
    .reset_index(drop=True)
)


UNIQUE_ROWS = len(trades)


DUPLICATE_ROWS = (
    RAW_ROWS
    - UNIQUE_ROWS
)


# ============================================================
# OUTPUT BUFFER
# ============================================================

output = []


def emit(text=""):

    print(text)

    output.append(
        str(text)
    )


# ============================================================
# HEADER
# ============================================================

emit("=" * 110)
emit(
    "GARUDA — CORRECTED POST-ENTRY EXCURSION ANALYSIS"
)
emit("=" * 110)

emit()

emit(
    f"RAW TRADE ROWS       : {RAW_ROWS}"
)

emit(
    f"UNIQUE TRADE COUNT   : {UNIQUE_ROWS}"
)

emit(
    f"DUPLICATE ROWS       : {DUPLICATE_ROWS}"
)

emit()

emit(
    "RESEARCH RULE:"
)

emit(
    "MFE / MAE begins from the candle AFTER entry_time."
)

emit(
    "The entry candle itself is NOT used for post-entry excursion."
)

emit(
    "This eliminates same-candle look-ahead contamination."
)

emit()


# ============================================================
# ANALYSIS RESULTS
# ============================================================

results = []


# ============================================================
# PROCESS EACH UNIQUE TRADE
# ============================================================

for trade_index, trade in trades.iterrows():

    trade_date = trade["trade_date"]

    direction = trade["direction"]

    entry_time = pd.Timestamp(
        trade["entry_time"]
    )

    exit_time = pd.Timestamp(
        trade["exit_time"]
    )

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

    original_exit_reason = str(
        trade["exit_reason"]
    )

    # --------------------------------------------------------
    # Safety
    # --------------------------------------------------------

    if risk <= 0:

        continue


    # --------------------------------------------------------
    # FIND ENTRY CANDLE
    # --------------------------------------------------------

    entry_positions = prices.index[
        prices["datetime"] == entry_time
    ].tolist()


    if not entry_positions:

        results.append(
            {
                "trade_index":
                    trade_index + 1,

                "trade_date":
                    trade_date,

                "direction":
                    direction,

                "entry_time":
                    entry_time,

                "exit_time":
                    exit_time,

                "entry_price":
                    entry_price,

                "risk":
                    risk,

                "stop_loss":
                    stop_loss,

                "target":
                    target,

                "original_exit_reason":
                    original_exit_reason,

                "entry_candle_found":
                    False,

                "post_entry_candles":
                    0,

                "mfe_r":
                    0.0,

                "mae_r":
                    0.0,

                "max_mfe_time":
                    None,

                "max_mae_time":
                    None,

                "r05_reached":
                    False,

                "r10_reached":
                    False,

                "r15_reached":
                    False,

                "r20_reached":
                    False,

                "exit_candle_is_entry_candle":
                    False,

                "valid_post_entry_path":
                    False,
            }
        )

        continue


    entry_index = entry_positions[0]


    # --------------------------------------------------------
    # CRITICAL CORRECTION
    #
    # Start from NEXT candle.
    # --------------------------------------------------------

    post_entry = prices.iloc[
        entry_index + 1:
    ].copy()


    # Only candles through original exit
    post_entry = post_entry[
        post_entry["datetime"]
        <= exit_time
    ].copy()


    post_entry = (
        post_entry
        .sort_values("datetime")
        .reset_index(drop=True)
    )


    # --------------------------------------------------------
    # Was exit on entry candle?
    # --------------------------------------------------------

    exit_on_entry_candle = (
        exit_time == entry_time
    )


    # --------------------------------------------------------
    # R LEVELS
    # --------------------------------------------------------

    if direction == "BUY":

        r05 = (
            entry_price
            + 0.5 * risk
        )

        r10 = (
            entry_price
            + 1.0 * risk
        )

        r15 = (
            entry_price
            + 1.5 * risk
        )

        r20 = (
            entry_price
            + 2.0 * risk
        )

    else:

        r05 = (
            entry_price
            - 0.5 * risk
        )

        r10 = (
            entry_price
            - 1.0 * risk
        )

        r15 = (
            entry_price
            - 1.5 * risk
        )

        r20 = (
            entry_price
            - 2.0 * risk
        )


    # --------------------------------------------------------
    # INITIAL VALUES
    # --------------------------------------------------------

    mfe_r = 0.0

    mae_r = 0.0

    max_mfe_time = None

    max_mae_time = None


    r05_reached = False
    r10_reached = False
    r15_reached = False
    r20_reached = False


    r05_time = None
    r10_time = None
    r15_time = None
    r20_time = None


    # --------------------------------------------------------
    # CANDLE-BY-CANDLE POST-ENTRY PATH
    # --------------------------------------------------------

    for _, candle in post_entry.iterrows():

        candle_time = candle["datetime"]

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        close = float(
            candle["close"]
        )


        # ----------------------------------------------------
        # BUY
        # ----------------------------------------------------

        if direction == "BUY":

            favorable_price = high

            adverse_price = low

            current_mfe_r = (
                favorable_price
                - entry_price
            ) / risk

            current_mae_r = (
                entry_price
                - adverse_price
            ) / risk


            # R thresholds

            if (
                not r05_reached
                and high >= r05
            ):

                r05_reached = True
                r05_time = candle_time


            if (
                not r10_reached
                and high >= r10
            ):

                r10_reached = True
                r10_time = candle_time


            if (
                not r15_reached
                and high >= r15
            ):

                r15_reached = True
                r15_time = candle_time


            if (
                not r20_reached
                and high >= r20
            ):

                r20_reached = True
                r20_time = candle_time


        # ----------------------------------------------------
        # SELL
        # ----------------------------------------------------

        else:

            favorable_price = low

            adverse_price = high

            current_mfe_r = (
                entry_price
                - favorable_price
            ) / risk

            current_mae_r = (
                adverse_price
                - entry_price
            ) / risk


            # R thresholds

            if (
                not r05_reached
                and low <= r05
            ):

                r05_reached = True
                r05_time = candle_time


            if (
                not r10_reached
                and low <= r10
            ):

                r10_reached = True
                r10_time = candle_time


            if (
                not r15_reached
                and low <= r15
            ):

                r15_reached = True
                r15_time = candle_time


            if (
                not r20_reached
                and low <= r20
            ):

                r20_reached = True
                r20_time = candle_time


        # ----------------------------------------------------
        # MFE / MAE
        # ----------------------------------------------------

        if current_mfe_r > mfe_r:

            mfe_r = current_mfe_r

            max_mfe_time = candle_time


        if current_mae_r > mae_r:

            mae_r = current_mae_r

            max_mae_time = candle_time


    # ========================================================
    # STORE RESULT
    # ========================================================

    results.append(
        {
            "trade_index":
                trade_index + 1,

            "trade_date":
                trade_date,

            "direction":
                direction,

            "entry_time":
                entry_time,

            "exit_time":
                exit_time,

            "entry_price":
                entry_price,

            "risk":
                risk,

            "stop_loss":
                stop_loss,

            "target":
                target,

            "original_exit_reason":
                original_exit_reason,

            "entry_candle_found":
                True,

            "post_entry_candles":
                len(post_entry),

            "exit_candle_is_entry_candle":
                exit_on_entry_candle,

            "valid_post_entry_path":
                len(post_entry) > 0,

            "mfe_r":
                mfe_r,

            "mae_r":
                mae_r,

            "max_mfe_time":
                max_mfe_time,

            "max_mae_time":
                max_mae_time,

            "r05_reached":
                r05_reached,

            "r05_time":
                r05_time,

            "r10_reached":
                r10_reached,

            "r10_time":
                r10_time,

            "r15_reached":
                r15_reached,

            "r15_time":
                r15_time,

            "r20_reached":
                r20_reached,

            "r20_time":
                r20_time,
        }
    )


# ============================================================
# DATAFRAME
# ============================================================

analysis = pd.DataFrame(
    results
)


# ============================================================
# SAVE CSV
# ============================================================

CSV_OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)


analysis.to_csv(
    CSV_OUTPUT_FILE,
    index=False,
)


# ============================================================
# SUMMARY
# ============================================================

total = len(analysis)


valid_path = analysis[
    analysis["valid_post_entry_path"]
].copy()


entry_candle_exits = analysis[
    analysis[
        "exit_candle_is_entry_candle"
    ]
].copy()


def count_true(column):

    if column not in valid_path.columns:
        return 0

    return int(
        valid_path[column]
        .fillna(False)
        .sum()
    )


reached_05 = count_true(
    "r05_reached"
)

reached_10 = count_true(
    "r10_reached"
)

reached_15 = count_true(
    "r15_reached"
)

reached_20 = count_true(
    "r20_reached"
)


# ============================================================
# STOP AFTER EXCURSION
# ============================================================

def reached_then_stopped(
    threshold_column,
):

    if valid_path.empty:
        return 0

    subset = valid_path[
        valid_path[threshold_column]
        &
        (
            valid_path[
                "original_exit_reason"
            ]
            .astype(str)
            .str.upper()
            == "STOP_LOSS"
        )
    ]

    return len(subset)


stopped_after_05 = reached_then_stopped(
    "r05_reached"
)

stopped_after_10 = reached_then_stopped(
    "r10_reached"
)

stopped_after_15 = reached_then_stopped(
    "r15_reached"
)

stopped_after_20 = reached_then_stopped(
    "r20_reached"
)


# ============================================================
# TARGET AFTER EXCURSION
# ============================================================

def reached_then_target(
    threshold_column,
):

    if valid_path.empty:
        return 0

    subset = valid_path[
        valid_path[threshold_column]
        &
        (
            valid_path[
                "original_exit_reason"
            ]
            .astype(str)
            .str.upper()
            == "TARGET"
        )
    ]

    return len(subset)


target_after_05 = reached_then_target(
    "r05_reached"
)

target_after_10 = reached_then_target(
    "r10_reached"
)

target_after_15 = reached_then_target(
    "r15_reached"
)

target_after_20 = reached_then_target(
    "r20_reached"
)


# ============================================================
# PRINT SUMMARY
# ============================================================

emit()
emit("=" * 110)
emit("CORRECTED EXCURSION LADDER")
emit("=" * 110)

emit()

emit(
    f"RAW TRADE ROWS             : {RAW_ROWS}"
)

emit(
    f"UNIQUE TRADE COUNT         : {UNIQUE_ROWS}"
)

emit(
    f"DUPLICATE ROWS             : {DUPLICATE_ROWS}"
)

emit(
    f"VALID POST-ENTRY TRADES    : {len(valid_path)}"
)

emit(
    f"ENTRY-CANDLE EXIT TRADES   : "
    f"{len(entry_candle_exits)}"
)

emit()

emit(
    "IMPORTANT:"
)

emit(
    "Entry-candle OHLC is excluded from MFE/MAE."
)

emit(
    "Only candles AFTER entry_time are used."
)

emit()

emit(
    "threshold    reached    reached_%    "
    "stopped_after    target_after"
)

emit("-" * 80)


ladder = [
    (
        0.50,
        "r05_reached",
        stopped_after_05,
        target_after_05,
    ),
    (
        1.00,
        "r10_reached",
        stopped_after_10,
        target_after_10,
    ),
    (
        1.50,
        "r15_reached",
        stopped_after_15,
        target_after_15,
    ),
    (
        2.00,
        "r20_reached",
        stopped_after_20,
        target_after_20,
    ),
]


for threshold, column, stopped, target_count in ladder:

    reached = count_true(column)

    if len(valid_path) > 0:

        pct = (
            reached
            / len(valid_path)
            * 100
        )

    else:

        pct = 0.0


    emit(
        f"{threshold:>5.2f}R"
        f"{reached:>12}"
        f"{pct:>13.2f}%"
        f"{stopped:>16}"
        f"{target_count:>15}"
    )


# ============================================================
# MFE SUMMARY
# ============================================================

emit()
emit("=" * 110)
emit("CORRECTED MFE / MAE SUMMARY")
emit("=" * 110)

if not valid_path.empty:

    emit(
        f"AVG MFE_R       : "
        f"{valid_path['mfe_r'].mean():.3f}"
    )

    emit(
        f"MEDIAN MFE_R    : "
        f"{valid_path['mfe_r'].median():.3f}"
    )

    emit(
        f"P75 MFE_R       : "
        f"{valid_path['mfe_r'].quantile(0.75):.3f}"
    )

    emit(
        f"P90 MFE_R       : "
        f"{valid_path['mfe_r'].quantile(0.90):.3f}"
    )

    emit()

    emit(
        f"AVG MAE_R       : "
        f"{valid_path['mae_r'].mean():.3f}"
    )

    emit(
        f"MEDIAN MAE_R    : "
        f"{valid_path['mae_r'].median():.3f}"
    )

    emit(
        f"P75 MAE_R       : "
        f"{valid_path['mae_r'].quantile(0.75):.3f}"
    )

    emit(
        f"P90 MAE_R       : "
        f"{valid_path['mae_r'].quantile(0.90):.3f}"
    )

else:

    emit(
        "No valid post-entry candles."
    )


# ============================================================
# STRONG REVERSAL TRADES
# ============================================================

emit()
emit("=" * 110)
emit(
    "VALID >= 1.0R THEN STOP_LOSS"
)
emit("=" * 110)


strong_1r = valid_path[
    valid_path["r10_reached"]
    &
    (
        valid_path[
            "original_exit_reason"
        ]
        .astype(str)
        .str.upper()
        == "STOP_LOSS"
    )
].copy()


if strong_1r.empty:

    emit(
        "None."
    )

else:

    emit(
        "date        side       entry       "
        "MFE_R       MAE_R       MFE_TIME"
    )

    emit("-" * 100)

    for _, row in strong_1r.iterrows():

        emit(
            f"{row['trade_date']:<12}"
            f"{row['direction']:<10}"
            f"{row['entry_price']:>10.4f}"
            f"{row['mfe_r']:>12.3f}"
            f"{row['mae_r']:>12.3f}"
            f"  {row['max_mfe_time']}"
        )


# ============================================================
# >= 1.5R THEN STOP
# ============================================================

emit()
emit("=" * 110)
emit(
    "VALID >= 1.5R THEN STOP_LOSS"
)
emit("=" * 110)


strong_15r = valid_path[
    valid_path["r15_reached"]
    &
    (
        valid_path[
            "original_exit_reason"
        ]
        .astype(str)
        .str.upper()
        == "STOP_LOSS"
    )
].copy()


if strong_15r.empty:

    emit(
        "None."
    )

else:

    emit(
        "date        side       entry       "
        "MFE_R       MAE_R       MFE_TIME"
    )

    emit("-" * 100)

    for _, row in strong_15r.iterrows():

        emit(
            f"{row['trade_date']:<12}"
            f"{row['direction']:<10}"
            f"{row['entry_price']:>10.4f}"
            f"{row['mfe_r']:>12.3f}"
            f"{row['mae_r']:>12.3f}"
            f"  {row['max_mfe_time']}"
        )


# ============================================================
# TRADE-BY-TRADE AUDIT
# ============================================================

emit()
emit("=" * 110)
emit(
    "FULL CORRECTED TRADE AUDIT"
)
emit("=" * 110)

emit()

for _, row in analysis.iterrows():

    emit(
        f"{row['trade_date']} "
        f"{row['direction']} "
        f"ENTRY={row['entry_time']} "
        f"EXIT={row['exit_time']} "
        f"ENTRY_CANDLE_EXIT="
        f"{row['exit_candle_is_entry_candle']} "
        f"POST_CANDLES="
        f"{row['post_entry_candles']} "
        f"MFE_R="
        f"{row['mfe_r']:.3f} "
        f"MAE_R="
        f"{row['mae_r']:.3f} "
        f"0.5R="
        f"{row['r05_reached']} "
        f"1R="
        f"{row['r10_reached']} "
        f"1.5R="
        f"{row['r15_reached']} "
        f"2R="
        f"{row['r20_reached']} "
        f"EXIT="
        f"{row['original_exit_reason']}"
    )


# ============================================================
# SAVE TEXT
# ============================================================

Path(
    OUTPUT_FILE
).write_text(
    "\n".join(output),
    encoding="utf-8",
)


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 110)
print(
    "CORRECTED POST-ENTRY EXCURSION ANALYSIS COMPLETED"
)
print("=" * 110)

print(
    f"Text output : {OUTPUT_FILE}"
)

print(
    f"CSV output  : {CSV_OUTPUT_FILE}"
)

print("=" * 110)