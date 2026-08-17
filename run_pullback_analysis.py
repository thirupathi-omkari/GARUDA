import pandas as pd
from pathlib import Path


# ==========================================================
# CONFIGURATION
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

TRADE_FILE = (
    PROJECT_ROOT
    / "data"
    / "signal_candle_sl_2r_infy.csv"
)

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "INFY_5MIN_REAL.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "pullback_analysis_infy_61trades_corrected.csv"
)

TARGET_R = 2.0

INITIAL_MOVE_R_LEVELS = [
    0.50,
    0.75,
    1.00,
    1.25,
    1.50,
]

PULLBACK_R_LEVELS = [
    0.25,
    0.50,
    0.75,
    1.00,
]


# ==========================================================
# LOAD
# ==========================================================

if not TRADE_FILE.exists():
    raise FileNotFoundError(
        f"Trade file not found:\n{TRADE_FILE}"
    )

if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Market data file not found:\n{DATA_FILE}"
    )


trades = pd.read_csv(TRADE_FILE)
candles = pd.read_csv(DATA_FILE)


# ==========================================================
# DATETIME
# ==========================================================

trades["signal_candle_time"] = pd.to_datetime(
    trades["signal_candle_time"]
)

trades["entry_time"] = pd.to_datetime(
    trades["entry_time"]
)

trades["exit_time"] = pd.to_datetime(
    trades["exit_time"]
)

candles["datetime"] = pd.to_datetime(
    candles["datetime"]
)

candles = (
    candles
    .sort_values("datetime")
    .reset_index(drop=True)
)


# ==========================================================
# VALIDATION
# ==========================================================

required_trade_columns = {
    "trade_date",
    "direction",
    "signal_candle_time",
    "entry_time",
    "entry_price",
    "stop_loss",
    "initial_risk",
    "target",
    "exit_time",
    "exit_reason",
}

missing = (
    required_trade_columns
    - set(trades.columns)
)

if missing:
    raise ValueError(
        f"Missing trade columns: {sorted(missing)}"
    )


required_candle_columns = {
    "datetime",
    "open",
    "high",
    "low",
    "close",
}

missing = (
    required_candle_columns
    - set(candles.columns)
)

if missing:
    raise ValueError(
        f"Missing candle columns: {sorted(missing)}"
    )


# ==========================================================
# HELPERS
# ==========================================================

def favorable_r(
    direction,
    entry_price,
    price,
    risk,
):
    if direction == "BUY":
        return (
            price - entry_price
        ) / risk

    return (
        entry_price - price
    ) / risk


def target_touched(
    direction,
    high,
    low,
    target,
):
    if direction == "BUY":
        return high >= target

    return low <= target


def stop_touched(
    direction,
    high,
    low,
    stop,
):
    if direction == "BUY":
        return low <= stop

    return high >= stop


def pullback_touched(
    direction,
    high,
    low,
    pullback_level,
):
    if direction == "BUY":
        return low <= pullback_level

    return high >= pullback_level


# ==========================================================
# ANALYSIS
# ==========================================================

all_results = []

trade_count = len(trades)


print()
print("=" * 110)
print(
    "GARUDA â€” CORRECTED ORB/VWAP PULLBACK BEHAVIOUR ANALYSIS"
)
print("=" * 110)

print(
    f"Trades analysed : {trade_count}"
)

print()


# ==========================================================
# EACH ORIGINAL TRADE
# ==========================================================

for trade_index, trade in trades.iterrows():

    direction = str(
        trade["direction"]
    ).upper()

    entry_time = trade["entry_time"]

    exit_time = trade["exit_time"]

    entry_price = float(
        trade["entry_price"]
    )

    risk = float(
        trade["initial_risk"]
    )

    stop_loss = float(
        trade["stop_loss"]
    )

    target = float(
        trade["target"]
    )

    trade_date = str(
        trade["trade_date"]
    )

    signal_time = trade[
        "signal_candle_time"
    ]

    original_exit_reason = str(
        trade["exit_reason"]
    )


    if risk <= 0:
        continue


    # ======================================================
    # CRITICAL FIX #1
    #
    # Only candles from entry UNTIL ORIGINAL EXIT.
    #
    # No future movement after the actual trade is allowed.
    # ======================================================

    future = candles[
        (
            candles["datetime"]
            >= entry_time
        )
        &
        (
            candles["datetime"]
            <= exit_time
        )
    ].copy()


    if future.empty:
        continue


    future = (
        future
        .sort_values("datetime")
        .reset_index(drop=True)
    )


    # ======================================================
    # RUN EACH INITIAL-MOVE / PULLBACK COMBINATION
    # ======================================================

    for initial_move_r in INITIAL_MOVE_R_LEVELS:

        for pullback_r in PULLBACK_R_LEVELS:

            initial_move_reached = False

            initial_move_time = None

            initial_extreme_price = None

            initial_extreme_index = None

            initial_extreme_r = None

            pullback_detected = False

            pullback_time = None

            pullback_price = None

            pullback_depth_r = None

            target_after_pullback = False

            target_after_pullback_time = None

            stop_before_pullback = False

            stop_after_pullback = False

            stop_after_pullback_time = None

            target_before_pullback = False


            # ==================================================
            # CHRONOLOGICAL CANDLE SCAN
            # ==================================================

            for candle_index, candle in future.iterrows():

                dt = candle["datetime"]

                high = float(
                    candle["high"]
                )

                low = float(
                    candle["low"]
                )


                # ==================================================
                # PHASE 1
                #
                # WAIT FOR INITIAL FAVORABLE MOVE
                # ==================================================

                if not initial_move_reached:

                    if direction == "BUY":

                        current_favorable = (
                            high
                            - entry_price
                        )

                    else:

                        current_favorable = (
                            entry_price
                            - low
                        )


                    current_favorable_r = (
                        current_favorable
                        / risk
                    )


                    if (
                        current_favorable_r
                        >= initial_move_r
                    ):

                        initial_move_reached = True

                        initial_move_time = dt

                        initial_extreme_index = (
                            candle_index
                        )


                        if direction == "BUY":

                            initial_extreme_price = (
                                high
                            )

                        else:

                            initial_extreme_price = (
                                low
                            )


                        initial_extreme_r = (
                            current_favorable_r
                        )


                        # ------------------------------------------
                        # IMPORTANT:
                        #
                        # We DO NOT check for pullback on this
                        # same candle.
                        #
                        # The next candle must participate.
                        # ------------------------------------------

                        continue


                # ==================================================
                # PHASE 2
                #
                # INITIAL MOVE HAS OCCURRED.
                #
                # Now update the favorable extreme using the
                # current candle.
                # ==================================================

                if initial_move_reached:

                    if direction == "BUY":

                        if (
                            high
                            > initial_extreme_price
                        ):

                            initial_extreme_price = (
                                high
                            )

                            initial_extreme_index = (
                                candle_index
                            )

                    else:

                        if (
                            low
                            < initial_extreme_price
                        ):

                            initial_extreme_price = (
                                low
                            )

                            initial_extreme_index = (
                                candle_index
                            )


                    initial_extreme_r = (
                        favorable_r(
                            direction,
                            entry_price,
                            initial_extreme_price,
                            risk,
                        )
                    )


                    # ==================================================
                    # IMPORTANT:
                    #
                    # If THIS candle establishes a new extreme,
                    # it cannot simultaneously be the pullback
                    # candle.
                    # ==================================================

                    if (
                        initial_extreme_index
                        == candle_index
                    ):

                        continue


                    # ==================================================
                    # PULLBACK LEVEL
                    # ==================================================

                    if direction == "BUY":

                        pullback_level = (
                            initial_extreme_price
                            - (
                                pullback_r
                                * risk
                            )
                        )

                    else:

                        pullback_level = (
                            initial_extreme_price
                            + (
                                pullback_r
                                * risk
                            )
                        )


                    # ==================================================
                    # PHASE 3
                    #
                    # DETECT PULLBACK
                    # ==================================================

                    if not pullback_detected:

                        if pullback_touched(
                            direction,
                            high,
                            low,
                            pullback_level,
                        ):

                            pullback_detected = True

                            pullback_time = dt

                            pullback_price = (
                                pullback_level
                            )

                            pullback_depth_r = (
                                pullback_r
                            )


                            # --------------------------------------
                            # Target must occur AFTER this pullback.
                            # --------------------------------------

                            continue


                    # ==================================================
                    # PHASE 4
                    #
                    # AFTER PULLBACK
                    #
                    # We now look for continuation to 2R.
                    # ==================================================

                    if pullback_detected:

                        if target_touched(
                            direction,
                            high,
                            low,
                            target,
                        ):

                            target_after_pullback = True

                            target_after_pullback_time = (
                                dt
                            )

                            break


                        if stop_touched(
                            direction,
                            high,
                            low,
                            stop_loss,
                        ):

                            stop_after_pullback = True

                            if (
                                stop_after_pullback_time
                                is None
                            ):

                                stop_after_pullback_time = (
                                    dt
                                )


            # ======================================================
            # CHECK WHETHER ORIGINAL STOP / TARGET OCCURRED
            # BEFORE THE PULLBACK
            #
            # This is evaluated chronologically from the actual
            # candles, not using the final trade result.
            # ======================================================

            if (
                pullback_detected
                and pullback_time is not None
            ):

                before_pullback = future[
                    future["datetime"]
                    <= pullback_time
                ]


                for _, candle in before_pullback.iterrows():

                    high = float(
                        candle["high"]
                    )

                    low = float(
                        candle["low"]
                    )

                    dt = candle["datetime"]


                    if dt >= pullback_time:
                        break


                    if target_touched(
                        direction,
                        high,
                        low,
                        target,
                    ):

                        target_before_pullback = True

                        break


                    if stop_touched(
                        direction,
                        high,
                        low,
                        stop_loss,
                    ):

                        stop_before_pullback = True

                        break


            # ======================================================
            # VALID PATTERN
            # ======================================================

            valid_pullback_target = (
                initial_move_reached
                and pullback_detected
                and target_after_pullback
                and not target_before_pullback
            )


            clean_pullback_target = (
                valid_pullback_target
                and not stop_before_pullback
                and not stop_after_pullback
            )


            # ======================================================
            # STORE
            # ======================================================

            all_results.append(
                {
                    "trade_index":
                        trade_index + 1,

                    "trade_date":
                        trade_date,

                    "direction":
                        direction,

                    "signal_time":
                        signal_time,

                    "entry_time":
                        entry_time,

                    "entry_price":
                        entry_price,

                    "risk":
                        risk,

                    "stop_loss":
                        stop_loss,

                    "target":
                        target,

                    "original_exit_time":
                        exit_time,

                    "original_exit_reason":
                        original_exit_reason,

                    "initial_move_r":
                        initial_move_r,

                    "pullback_r":
                        pullback_r,

                    "initial_move_reached":
                        initial_move_reached,

                    "initial_move_time":
                        initial_move_time,

                    "initial_extreme_price":
                        initial_extreme_price,

                    "initial_extreme_r":
                        initial_extreme_r,

                    "pullback_detected":
                        pullback_detected,

                    "pullback_time":
                        pullback_time,

                    "pullback_price":
                        pullback_price,

                    "pullback_depth_r":
                        pullback_depth_r,

                    "target_after_pullback":
                        target_after_pullback,

                    "target_after_pullback_time":
                        target_after_pullback_time,

                    "target_before_pullback":
                        target_before_pullback,

                    "stop_before_pullback":
                        stop_before_pullback,

                    "stop_after_pullback":
                        stop_after_pullback,

                    "valid_pullback_target":
                        valid_pullback_target,

                    "clean_pullback_target":
                        clean_pullback_target,
                }
            )


# ==========================================================
# DATAFRAME
# ==========================================================

results = pd.DataFrame(
    all_results
)


if results.empty:

    print(
        "No analysis results generated."
    )

    raise SystemExit(0)


# ==========================================================
# SUMMARY
# ==========================================================

print()
print("=" * 125)
print(
    "CORRECTED PULLBACK BEHAVIOUR SUMMARY"
)
print("=" * 125)

print()

print(
    f"BASE TRADES : "
    f"{len(trades)}"
)

print()

print(
    f"{'INITIAL':<10}"
    f"{'PULLBACK':<10}"
    f"{'PULLBACKS':<12}"
    f"{'SESSIONS':<12}"
    f"{'THEN 2R':<12}"
    f"{'2R %':<10}"
    f"{'CLEAN 2R':<12}"
    f"{'CLEAN %':<10}"
)

print("-" * 125)


summary_rows = []


for initial_move_r in INITIAL_MOVE_R_LEVELS:

    for pullback_r in PULLBACK_R_LEVELS:

        subset = results[
            (
                results[
                    "initial_move_r"
                ]
                == initial_move_r
            )
            &
            (
                results[
                    "pullback_r"
                ]
                == pullback_r
            )
        ]


        pullbacks = subset[
            subset[
                "pullback_detected"
            ]
        ]


        target_after = subset[
            subset[
                "target_after_pullback"
            ]
        ]


        clean_target = subset[
            subset[
                "clean_pullback_target"
            ]
        ]


        pullback_count = len(
            pullbacks
        )

        session_count = (
            pullbacks[
                "trade_date"
            ]
            .nunique()
        )

        target_count = len(
            target_after
        )

        clean_count = len(
            clean_target
        )


        target_pct = (
            target_count
            / pullback_count
            * 100
            if pullback_count
            else 0.0
        )

        clean_pct = (
            clean_count
            / pullback_count
            * 100
            if pullback_count
            else 0.0
        )


        print(
            f"{initial_move_r:<10.2f}"
            f"{pullback_r:<10.2f}"
            f"{pullback_count:<12}"
            f"{session_count:<12}"
            f"{target_count:<12}"
            f"{target_pct:<10.2f}"
            f"{clean_count:<12}"
            f"{clean_pct:<10.2f}"
        )


        summary_rows.append(
            {
                "initial_move_r":
                    initial_move_r,

                "pullback_r":
                    pullback_r,

                "pullback_trades":
                    pullback_count,

                "pullback_sessions":
                    session_count,

                "target_after_pullback":
                    target_count,

                "target_after_pullback_pct":
                    target_pct,

                "clean_target":
                    clean_count,

                "clean_target_pct":
                    clean_pct,
            }
        )


print("=" * 125)


# ==========================================================
# BEST CLEAN PATTERNS
# ==========================================================

summary = pd.DataFrame(
    summary_rows
)


print()
print("=" * 125)
print(
    "BEST PATTERNS BY CLEAN 2R RATE"
)
print("=" * 125)

best = (
    summary[
        summary[
            "pullback_trades"
        ] >= 5
    ]
    .sort_values(
        [
            "clean_target_pct",
            "clean_target",
        ],
        ascending=False,
    )
    .head(15)
)


print(
    best.to_string(
        index=False
    )
)


# ==========================================================
# STANDARD 0.5 / 0.5
# ==========================================================

standard = results[
    (
        results[
            "initial_move_r"
        ]
        == 0.50
    )
    &
    (
        results[
            "pullback_r"
        ]
        == 0.50
    )
]


pullback_count = int(
    standard[
        "pullback_detected"
    ].sum()
)

target_count = int(
    standard[
        "target_after_pullback"
    ].sum()
)

clean_count = int(
    standard[
        "clean_pullback_target"
    ].sum()
)

session_count = (
    standard[
        standard[
            "pullback_detected"
        ]
    ]["trade_date"]
    .nunique()
)


print()
print("=" * 125)
print(
    "STANDARD 0.5R MOVE -> 0.5R PULLBACK -> 2R"
)
print("=" * 125)

print(
    f"Initial 0.5R move          : "
    f"{int(standard['initial_move_reached'].sum())}"
)

print(
    f"0.5R pullback              : "
    f"{pullback_count}"
)

print(
    f"Distinct sessions          : "
    f"{session_count}"
)

print(
    f"Pullback then 2R           : "
    f"{target_count}"
)

print(
    f"Clean pullback then 2R     : "
    f"{clean_count}"
)

if pullback_count:

    print(
        f"2R rate after pullback     : "
        f"{target_count / pullback_count * 100:.2f}%"
    )

    print(
        f"Clean 2R rate              : "
        f"{clean_count / pullback_count * 100:.2f}%"
    )


# ==========================================================
# EXACT CLEAN EXAMPLES
# ==========================================================

print()
print("=" * 170)
print(
    "CLEAN PULLBACK -> 2R EXAMPLES"
)
print("=" * 170)

examples = standard[
    standard[
        "clean_pullback_target"
    ]
].copy()


if examples.empty:

    print(
        "No clean examples found."
    )

else:

    print(
        examples[
            [
                "trade_date",
                "direction",
                "signal_time",
                "entry_time",
                "initial_move_time",
                "initial_extreme_price",
                "initial_extreme_r",
                "pullback_time",
                "pullback_price",
                "target_after_pullback_time",
                "original_exit_reason",
            ]
        ]
        .to_string(
            index=False
        )
    )


# ==========================================================
# SAVE
# ==========================================================

results.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 100)
print(
    f"Saved corrected analysis:"
)

print(
    OUTPUT_FILE
)

print("=" * 100)
