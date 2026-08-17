from pathlib import Path

import pandas as pd


# ============================================================
# GARUDA ORB + VWAP
# STRUCTURAL RETEST VERIFICATION V2
#
# RESEARCH ONLY
#
# IMPORTANT:
# - Does NOT modify GARUDA production code.
# - Does NOT use the old 0.5R pullback hypothesis.
# - Does NOT treat every repeated signal as a new event.
#
# EVENT:
#   ORB/VWAP break
#       ->
#   move away
#       ->
#   return/retest broken ORB level
#       ->
#   rejection
#       ->
#   continuation
#
# V2 deliberately measures the actual market behaviour first.
# Entry/SL/2R optimization comes later.
# ============================================================


ROOT = Path(__file__).resolve().parent

MARKET_FILE = (
    ROOT
    / "data"
    / "raw"
    / "INFY_5MIN_REAL.csv"
)

SIGNAL_FILE = (
    ROOT
    / "data"
    / "signal_candle_sl_2r_infy.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "orb_vwap_retest_verification_v2_infy.csv"
)


SYMBOL = "INFY"

OPENING_START = "09:15"
OPENING_END = "09:30"

# Number of candles after the breakout candle before
# another structural event can be considered.
MIN_MOVE_CANDLES = 1

# Minimum favorable distance from broken ORB level,
# expressed as a fraction of the ORB range.
#
# This is NOT used to optimize trading.
# We record several thresholds after the raw event analysis.
EXCURSION_THRESHOLDS = [
    0.00,
    0.10,
    0.25,
    0.50,
    0.75,
    1.00,
]

AUDIT_CONTEXT = 3


# ============================================================
# HELPERS
# ============================================================

def fmt_price(value):
    if value is None:
        return "NA"

    try:
        if pd.isna(value):
            return "NA"
    except Exception:
        pass

    return f"{float(value):.2f}"


def fmt_time(value):
    if value is None:
        return "NA"

    try:
        if pd.isna(value):
            return "NA"
    except Exception:
        pass

    return str(value)


def add_session_vwap(df):
    df = df.copy()

    typical_price = (
        df["high"]
        + df["low"]
        + df["close"]
    ) / 3.0

    pv = (
        typical_price
        * df["volume"]
    )

    cumulative_pv = pv.cumsum()

    cumulative_volume = (
        df["volume"]
        .cumsum()
    )

    df["vwap"] = (
        cumulative_pv
        / cumulative_volume
    )

    return df


def percentage(numerator, denominator):
    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100.0
    )


# ============================================================
# LOAD
# ============================================================

if not MARKET_FILE.exists():
    raise FileNotFoundError(
        f"Market data not found:\n{MARKET_FILE}"
    )

if not SIGNAL_FILE.exists():
    raise FileNotFoundError(
        f"Signal file not found:\n{SIGNAL_FILE}"
    )


market = pd.read_csv(
    MARKET_FILE
)

signals = pd.read_csv(
    SIGNAL_FILE
)


# ============================================================
# DATETIME
# ============================================================

market["datetime"] = pd.to_datetime(
    market["datetime"]
)

signals["signal_candle_time"] = (
    pd.to_datetime(
        signals["signal_candle_time"]
    )
)


market = (
    market
    .sort_values("datetime")
    .reset_index(drop=True)
)


signals = (
    signals
    .sort_values(
        "signal_candle_time"
    )
    .reset_index(drop=True)
)


# ============================================================
# VALIDATE
# ============================================================

required_market = {
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "volume",
}

missing_market = (
    required_market
    - set(market.columns)
)

if missing_market:
    raise ValueError(
        "Missing market columns: "
        + str(sorted(missing_market))
    )


required_signals = {
    "trade_date",
    "direction",
    "signal_candle_time",
}

missing_signals = (
    required_signals
    - set(signals.columns)
)

if missing_signals:
    raise ValueError(
        "Missing signal columns: "
        + str(sorted(missing_signals))
    )


# ============================================================
# SESSION PROCESSOR
# ============================================================

def prepare_session(session):
    session = (
        session
        .sort_values("datetime")
        .reset_index(drop=True)
    )

    session = add_session_vwap(
        session
    )

    session_time = (
        session["datetime"]
        .dt.strftime("%H:%M")
    )

    opening = session[
        (
            session_time
            >= OPENING_START
        )
        &
        (
            session_time
            < OPENING_END
        )
    ]

    if opening.empty:
        return None

    orb_high = float(
        opening["high"].max()
    )

    orb_low = float(
        opening["low"].min()
    )

    orb_range = (
        orb_high
        - orb_low
    )

    if orb_range <= 0:
        return None

    session["orb_high"] = orb_high
    session["orb_low"] = orb_low
    session["orb_range"] = orb_range

    return session


# ============================================================
# FIND SIGNAL EVENTS
# ============================================================

def get_signal_events(
    session,
):
    """
    Identify directional ORB + VWAP break events.

    A new event is created only when the market changes
    from not-being-broken to being-broken.

    Repeated candles continuing in the same direction
    belong to the same event.
    """

    events = []

    active_direction = None

    for idx in range(
        len(session)
    ):

        candle = session.iloc[idx]

        dt = candle["datetime"]

        close = float(
            candle["close"]
        )

        vwap = float(
            candle["vwap"]
        )

        orb_high = float(
            candle["orb_high"]
        )

        orb_low = float(
            candle["orb_low"]
        )

        # -----------------------------------------------
        # Ignore opening-range candles.
        # -----------------------------------------------

        time_string = (
            dt.strftime("%H:%M")
        )

        if time_string < OPENING_END:
            continue

        buy_condition = (
            close > orb_high
            and
            close > vwap
        )

        sell_condition = (
            close < orb_low
            and
            close < vwap
        )

        current_direction = None

        if buy_condition:
            current_direction = "BUY"

        elif sell_condition:
            current_direction = "SELL"

        # -----------------------------------------------
        # No valid break.
        # -----------------------------------------------

        if current_direction is None:
            continue

        # -----------------------------------------------
        # First break or direction changed.
        # -----------------------------------------------

        if (
            active_direction
            != current_direction
        ):

            events.append(
                {
                    "break_index": idx,
                    "break_time": dt,
                    "direction":
                        current_direction,
                    "break_close":
                        close,
                    "break_high":
                        float(candle["high"]),
                    "break_low":
                        float(candle["low"]),
                    "break_vwap":
                        vwap,
                    "orb_high":
                        orb_high,
                    "orb_low":
                        orb_low,
                    "orb_range":
                        float(candle["orb_range"]),
                }
            )

            active_direction = (
                current_direction
            )

    return events


# ============================================================
# ANALYSE ONE EVENT
# ============================================================

def analyse_event(
    session,
    event,
    event_number,
):

    direction = event[
        "direction"
    ]

    break_index = event[
        "break_index"
    ]

    orb_high = event[
        "orb_high"
    ]

    orb_low = event[
        "orb_low"
    ]

    orb_range = event[
        "orb_range"
    ]

    break_time = event[
        "break_time"
    ]

    break_close = event[
        "break_close"
    ]

    # --------------------------------------------------------
    # Broken level = ORB boundary.
    #
    # We intentionally do NOT freeze VWAP as the structural
    # level. VWAP is recorded separately at every stage.
    # --------------------------------------------------------

    if direction == "BUY":

        broken_level = orb_high

    else:

        broken_level = orb_low


    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    favorable_extreme = None
    favorable_extreme_time = None

    move_away = False

    retest = False
    retest_time = None
    retest_high = None
    retest_low = None
    retest_close = None
    retest_vwap = None

    rejection = False
    rejection_time = None
    rejection_close = None

    continuation = False
    continuation_time = None
    continuation_close = None

    # Structural excursion measured from broken level.
    max_excursion = 0.0

    # --------------------------------------------------------
    # WALK FORWARD
    # --------------------------------------------------------

    for idx in range(
        break_index + MIN_MOVE_CANDLES,
        len(session),
    ):

        candle = session.iloc[idx]

        dt = candle["datetime"]

        high = float(
            candle["high"]
        )

        low = float(
            candle["low"]
        )

        close = float(
            candle["close"]
        )

        vwap = float(
            candle["vwap"]
        )

        # ====================================================
        # BEFORE RETEST
        # ====================================================

        if not retest:

            if direction == "BUY":

                excursion = (
                    high
                    - broken_level
                )

                if (
                    excursion
                    > max_excursion
                ):

                    max_excursion = (
                        excursion
                    )

                    favorable_extreme = (
                        high
                    )

                    favorable_extreme_time = (
                        dt
                    )

                if (
                    high
                    > broken_level
                    and
                    high
                    > break_close
                ):

                    move_away = True


                # --------------------------------------------
                # RETEST:
                # Price returns to ORB high.
                #
                # It must have already established a
                # favorable excursion before retesting.
                # --------------------------------------------

                if (
                    move_away
                    and
                    low
                    <= broken_level
                ):

                    retest = True

                    retest_time = dt

                    retest_high = high

                    retest_low = low

                    retest_close = close

                    retest_vwap = vwap

                    continue

            else:

                excursion = (
                    broken_level
                    - low
                )

                if (
                    excursion
                    > max_excursion
                ):

                    max_excursion = (
                        excursion
                    )

                    favorable_extreme = (
                        low
                    )

                    favorable_extreme_time = (
                        dt
                    )

                if (
                    low
                    < broken_level
                    and
                    low
                    < break_close
                ):

                    move_away = True


                # --------------------------------------------
                # RETEST:
                # Price returns to ORB low.
                # --------------------------------------------

                if (
                    move_away
                    and
                    high
                    >= broken_level
                ):

                    retest = True

                    retest_time = dt

                    retest_high = high

                    retest_low = low

                    retest_close = close

                    retest_vwap = vwap

                    continue


        # ====================================================
        # AFTER RETEST
        # ====================================================

        if (
            retest
            and not rejection
        ):

            if direction == "BUY":

                # Price closes back above broken level.
                if (
                    close
                    > broken_level
                ):

                    rejection = True

                    rejection_time = dt

                    rejection_close = close

                    continue

            else:

                if (
                    close
                    < broken_level
                ):

                    rejection = True

                    rejection_time = dt

                    rejection_close = close

                    continue


        # ====================================================
        # CONTINUATION
        # ====================================================

        if (
            rejection
            and not continuation
        ):

            rejection_rows = session[
                session["datetime"]
                == rejection_time
            ]

            if rejection_rows.empty:
                continue

            rejection_candle = (
                rejection_rows.iloc[0]
            )

            rejection_high = float(
                rejection_candle["high"]
            )

            rejection_low = float(
                rejection_candle["low"]
            )

            if direction == "BUY":

                if (
                    close
                    > rejection_high
                ):

                    continuation = True

                    continuation_time = dt

                    continuation_close = close

                    break

            else:

                if (
                    close
                    < rejection_low
                ):

                    continuation = True

                    continuation_time = dt

                    continuation_close = close

                    break


    # ========================================================
    # EXCURSION NORMALIZATION
    # ========================================================

    excursion_r_orb = (
        max_excursion
        / orb_range
        if orb_range > 0
        else 0.0
    )


    # ========================================================
    # STATUS
    # ========================================================

    if not move_away:

        status = "BREAK_NO_MOVE"

    elif not retest:

        status = "MOVE_NO_RETEST"

    elif not rejection:

        status = "RETEST_NO_REJECTION"

    elif not continuation:

        status = "REJECTION_NO_CONTINUATION"

    else:

        status = "COMPLETE"


    return {
        "event_number":
            event_number,

        "direction":
            direction,

        "break_time":
            break_time,

        "break_close":
            break_close,

        "orb_high":
            orb_high,

        "orb_low":
            orb_low,

        "orb_range":
            orb_range,

        "broken_level":
            broken_level,

        "break_vwap":
            event["break_vwap"],

        "move_away":
            move_away,

        "favorable_extreme":
            favorable_extreme,

        "favorable_extreme_time":
            favorable_extreme_time,

        "max_excursion":
            max_excursion,

        "max_excursion_orb_r":
            excursion_r_orb,

        "retest":
            retest,

        "retest_time":
            retest_time,

        "retest_high":
            retest_high,

        "retest_low":
            retest_low,

        "retest_close":
            retest_close,

        "retest_vwap":
            retest_vwap,

        "rejection":
            rejection,

        "rejection_time":
            rejection_time,

        "rejection_close":
            rejection_close,

        "continuation":
            continuation,

        "continuation_time":
            continuation_time,

        "continuation_close":
            continuation_close,

        "status":
            status,
    }


# ============================================================
# BUILD EVENT DATA
# ============================================================

all_events = []

session_event_counts = []


for trade_date, day_group in market.groupby(
    market["datetime"].dt.date
):

    session = prepare_session(
        day_group
    )

    if session is None:
        continue

    events = get_signal_events(
        session
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # We don't need every event in the raw signal CSV.
    # We derive structural events directly from candles.
    # --------------------------------------------------------

    for event_number, event in enumerate(
        events,
        start=1,
    ):

        analysed = analyse_event(
            session,
            event,
            event_number,
        )

        analysed[
            "trade_date"
        ] = trade_date

        all_events.append(
            analysed
        )

    if events:

        session_event_counts.append(
            {
                "trade_date":
                    trade_date,

                "events":
                    len(events),

                "complete_events":
                    sum(
                        1
                        for event in all_events
                        if event["trade_date"]
                        == trade_date
                        and event["status"]
                        == "COMPLETE"
                    ),
            }
        )


results = pd.DataFrame(
    all_events
)


# ============================================================
# SAVE RAW RESULTS
# ============================================================

results.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 110)
print(
    "GARUDA ORB + VWAP STRUCTURAL RETEST VERIFICATION V2"
)
print("=" * 110)

print(
    f"Market sessions analysed : "
    f"{market['datetime'].dt.date.nunique()}"
)

print(
    f"Structural break events  : "
    f"{len(results)}"
)

print()


if results.empty:

    print(
        "NO STRUCTURAL EVENTS FOUND."
    )

    raise SystemExit(0)


break_count = len(results)

move_count = int(
    results[
        "move_away"
    ].sum()
)

retest_count = int(
    results[
        "retest"
    ].sum()
)

rejection_count = int(
    results[
        "rejection"
    ].sum()
)

continuation_count = int(
    results[
        "continuation"
    ].sum()
)


print("=" * 100)
print(
    "RAW STRUCTURAL EVENT RESULTS"
)
print("=" * 100)

print(
    f"Break events                  : "
    f"{break_count}"
)

print(
    f"Move away                     : "
    f"{move_count} "
    f"({percentage(move_count, break_count):.2f}%)"
)

print(
    f"Retest broken ORB level       : "
    f"{retest_count} "
    f"({percentage(retest_count, break_count):.2f}%)"
)

print(
    f"Retest -> rejection            : "
    f"{rejection_count} "
    f"({percentage(rejection_count, retest_count):.2f}% of retests)"
)

print(
    f"Rejection -> continuation      : "
    f"{continuation_count} "
    f"({percentage(continuation_count, rejection_count):.2f}% of rejections)"
)

print()


# ============================================================
# SESSION COUNTS
# ============================================================

print("=" * 100)
print(
    "SESSION-LEVEL RESULTS"
)
print("=" * 100)

session_summary = (
    results
    .groupby("trade_date")
    .agg(
        EVENTS=(
            "event_number",
            "count",
        ),

        COMPLETE=(
            "continuation",
            "sum",
        ),
    )
    .reset_index()
)

print(
    session_summary.to_string(
        index=False
    )
)


print()

print(
    f"Distinct sessions with event       : "
    f"{session_summary['trade_date'].nunique()}"
)

print(
    f"Distinct sessions with complete     : "
    f"{int((session_summary['COMPLETE'] > 0).sum())}"
)


# ============================================================
# BUY / SELL
# ============================================================

print()
print("=" * 100)
print(
    "BUY / SELL STRUCTURAL EVENTS"
)
print("=" * 100)

side_summary = (
    results
    .groupby("direction")
    .agg(
        EVENTS=(
            "event_number",
            "count",
        ),

        MOVE_AWAY=(
            "move_away",
            "sum",
        ),

        RETEST=(
            "retest",
            "sum",
        ),

        REJECTION=(
            "rejection",
            "sum",
        ),

        CONTINUATION=(
            "continuation",
            "sum",
        ),
    )
    .reset_index()
)

print(
    side_summary.to_string(
        index=False
    )
)


# ============================================================
# EXCURSION DISTRIBUTION
# ============================================================

print()
print("=" * 110)
print(
    "FAVORABLE EXCURSION FROM BROKEN ORB LEVEL"
)
print("=" * 110)

excursion = results[
    "max_excursion_orb_r"
].dropna()


if not excursion.empty:

    print(
        f"Mean excursion / ORB range   : "
        f"{excursion.mean():.3f}"
    )

    print(
        f"Median                        : "
        f"{excursion.median():.3f}"
    )

    print(
        f"P25                           : "
        f"{excursion.quantile(0.25):.3f}"
    )

    print(
        f"P75                           : "
        f"{excursion.quantile(0.75):.3f}"
    )

    print(
        f"P90                           : "
        f"{excursion.quantile(0.90):.3f}"
    )


# ============================================================
# EXCURSION THRESHOLD TABLE
#
# This is descriptive.
# It does not change the event classification.
# ============================================================

print()
print("=" * 120)
print(
    "RETEST / CONTINUATION BY FAVORABLE EXCURSION THRESHOLD"
)
print("=" * 120)

threshold_rows = []


for threshold in EXCURSION_THRESHOLDS:

    subset = results[
        results[
            "max_excursion_orb_r"
        ]
        >= threshold
    ]

    n = len(subset)

    if n == 0:
        continue

    retests = int(
        subset[
            "retest"
        ].sum()
    )

    rejections = int(
        subset[
            "rejection"
        ].sum()
    )

    continuations = int(
        subset[
            "continuation"
        ].sum()
    )

    threshold_rows.append(
        {
            "MIN_EXCURSION_ORB_R":
                threshold,

            "EVENTS":
                n,

            "RETEST":
                retests,

            "RETEST_PCT":
                percentage(
                    retests,
                    n,
                ),

            "REJECTION":
                rejections,

            "REJECTION_PCT":
                percentage(
                    rejections,
                    retests,
                ),

            "CONTINUATION":
                continuations,

            "CONTINUATION_PCT":
                percentage(
                    continuations,
                    rejections,
                ),
        }
    )


threshold_df = pd.DataFrame(
    threshold_rows
)


print(
    threshold_df.to_string(
        index=False
    )
)


# ============================================================
# COMPLETE EVENTS
# ============================================================

complete = results[
    results[
        "status"
    ]
    == "COMPLETE"
].copy()


print()
print("=" * 130)
print(
    "COMPLETE STRUCTURAL RETEST EVENTS"
)
print("=" * 130)


if complete.empty:

    print(
        "No complete structural events found."
    )

else:

    display_columns = [
        "trade_date",
        "direction",
        "break_time",
        "broken_level",
        "break_close",
        "favorable_extreme",
        "max_excursion_orb_r",
        "retest_time",
        "retest_high",
        "retest_low",
        "retest_close",
        "retest_vwap",
        "rejection_time",
        "rejection_close",
        "continuation_time",
        "continuation_close",
    ]

    print(
        complete[
            display_columns
        ].to_string(
            index=False
        )
    )


# ============================================================
# RAW EVENT AUDIT
# ============================================================

print()
print("=" * 130)
print(
    "ALL STRUCTURAL EVENTS"
)
print("=" * 130)

display_columns = [
    "trade_date",
    "event_number",
    "direction",
    "break_time",
    "broken_level",
    "break_close",
    "max_excursion",
    "max_excursion_orb_r",
    "retest",
    "retest_time",
    "retest_vwap",
    "rejection",
    "rejection_time",
    "continuation",
    "continuation_time",
    "status",
]

print(
    results[
        display_columns
    ].to_string(
        index=False
    )
)


# ============================================================
# CANDLE WINDOW
# ============================================================

def print_window(
    session,
    center_time,
    label,
):

    if center_time is None:
        return

    matches = session[
        session["datetime"]
        == pd.Timestamp(
            center_time
        )
    ]

    if matches.empty:
        return

    center_idx = matches.index[0]

    positions = list(
        session.index
    )

    position = positions.index(
        center_idx
    )

    start = max(
        0,
        position - AUDIT_CONTEXT,
    )

    end = min(
        len(session),
        position
        + AUDIT_CONTEXT
        + 1,
    )

    window = session.iloc[
        start:end
    ]

    print()
    print(
        "-" * 120
    )

    print(
        f"{label} : {center_time}"
    )

    print(
        "-" * 120
    )

    print(
        window[
            [
                "datetime",
                "open",
                "high",
                "low",
                "close",
                "vwap",
                "orb_high",
                "orb_low",
            ]
        ].to_string(
            index=False,
            float_format=lambda x:
                f"{x:.2f}",
        )
    )


# ============================================================
# DETAILED AUDIT OF FIRST 10 COMPLETE EVENTS
# ============================================================

print()
print("=" * 120)
print(
    "DETAILED CANDLE AUDIT — FIRST 10 COMPLETE EVENTS"
)
print("=" * 120)


for _, event in complete.head(
    10
).iterrows():

    trade_date = event[
        "trade_date"
    ]

    direction = event[
        "direction"
    ]

    print()
    print(
        "#" * 120
    )

    print(
        f"{trade_date} "
        f"{direction}"
    )

    print(
        f"ORB LOW    : "
        f"{fmt_price(event['orb_low'])}"
    )

    print(
        f"ORB HIGH   : "
        f"{fmt_price(event['orb_high'])}"
    )

    print(
        f"BROKEN LVL : "
        f"{fmt_price(event['broken_level'])}"
    )

    session = prepare_session(
        market[
            market["datetime"].dt.date
            == trade_date
        ]
    )

    if session is None:
        continue

    print_window(
        session,
        event["break_time"],
        "BREAK",
    )

    print_window(
        session,
        event["favorable_extreme_time"],
        "FAVORABLE EXTREME",
    )

    print_window(
        session,
        event["retest_time"],
        "RETEST",
    )

    print_window(
        session,
        event["rejection_time"],
        "REJECTION",
    )

    print_window(
        session,
        event["continuation_time"],
        "CONTINUATION",
    )


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 110)
print(
    "V2 VERIFICATION COMPLETE"
)
print("=" * 110)

print(
    f"Saved:"
)

print(
    OUTPUT_FILE
)

print("=" * 110)