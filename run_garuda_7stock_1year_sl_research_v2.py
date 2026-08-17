import sys
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# GARUDA — 7-STOCK / 1-YEAR ORB+VWAP SL RESEARCH
#
# ONE MASTER RESEARCH FILE
#
# Stage A:
#   Download/cache 365 calendar days of 5-minute Kite data
#   in safe chunks.
#
# Stage B:
#   For each stock:
#     1. Generate/freeze the entry universe ONCE using the
#        existing ORB+VWAP transition logic and existing
#        GARUDA exit simulator with the existing ORB stop.
#     2. Replay the EXACT same frozen entries through:
#          - EXISTING ORB SL
#          - 50% ORB RANGE SL
#          - ENTRY-CANDLE VWAP SL
#     3. Target = 2R
#     4. BE = OFF
#     5. Trailing = OFF
#     6. Existing GARUDA slippage + transaction costs
#
# This is a research harness, not a replacement strategy.
# It does not place real broker orders.
# ============================================================


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))


# ============================================================
# EXISTING GARUDA COMPONENTS
# ============================================================

from broker.session_manager import create_authenticated_session
from data.instrument_resolver import resolve_instrument_token

from backtesting.backtest_trade import BacktestTrade
from backtesting.exit_simulator import simulate_trade_exit
import backtesting.exit_simulator as exit_module
from backtesting.pnl_calculator import calculate_trade_pnl
from backtesting.slippage import apply_slippage

from indicators.vwap import calculate_vwap
from strategy.session_utils import get_opening_range_data


# ============================================================
# LOCKED RESEARCH CONFIGURATION
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

LOOKBACK_DAYS = 365

# Kite 5-minute historical request ceiling is 100 days.
# Use 90-day chunks deliberately.
CHUNK_DAYS = 90
REQUEST_DELAY_SECONDS = 0.40

OPENING_START_TIME = "09:15"
OPENING_END_TIME = "09:30"

TARGET_R = 2.0
COST_RATE_PCT = 0.10
SLIPPAGE_PCT = 0.05

MIN_REQUIRED_CALENDAR_DAYS = 180

RAW_DIR = PROJECT_ROOT / "data" / "raw"
RESEARCH_DIR = PROJECT_ROOT / "data" / "research"
RESEARCH_DIR.mkdir(parents=True, exist_ok=True)


def raw_path(symbol):
    return RAW_DIR / f"{symbol}_5MIN_REAL.csv"


# ============================================================
# DATA ACQUISITION
# ============================================================

def normalize_candles(candles):
    if not candles:
        return pd.DataFrame(
            columns=[
                "datetime", "open", "high",
                "low", "close", "volume"
            ]
        )

    data = pd.DataFrame(candles)

    if "date" in data.columns:
        data = data.rename(
            columns={"date": "datetime"}
        )

    required = [
        "datetime", "open", "high",
        "low", "close", "volume"
    ]

    missing = [
        c for c in required
        if c not in data.columns
    ]

    if missing:
        raise RuntimeError(
            f"Kite response missing columns: {missing}"
        )

    data = data[required].copy()

    data["datetime"] = pd.to_datetime(
        data["datetime"],
        errors="coerce",
    )

    for column in [
        "open", "high", "low",
        "close", "volume"
    ]:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        )

    return data


def validate_market_data(data, symbol):
    if data.empty:
        raise RuntimeError(
            f"{symbol}: empty historical dataset."
        )

    if data["datetime"].isna().any():
        raise RuntimeError(
            f"{symbol}: invalid datetime."
        )

    if data[
        ["open", "high", "low", "close", "volume"]
    ].isna().any().any():
        raise RuntimeError(
            f"{symbol}: missing OHLCV."
        )

    if data["datetime"].duplicated().any():
        raise RuntimeError(
            f"{symbol}: duplicate candles remain."
        )

    if (
        (data["high"] < data["open"])
        | (data["high"] < data["close"])
        | (data["high"] < data["low"])
    ).any():
        raise RuntimeError(
            f"{symbol}: invalid high values."
        )

    if (
        (data["low"] > data["open"])
        | (data["low"] > data["close"])
        | (data["low"] > data["high"])
    ).any():
        raise RuntimeError(
            f"{symbol}: invalid low values."
        )

    if (data["volume"] < 0).any():
        raise RuntimeError(
            f"{symbol}: negative volume."
        )


def download_symbol(kite, symbol, from_date, to_date):
    print()
    print("=" * 90)
    print(f"KITE DATA : {symbol}")
    print("=" * 90)

    token = resolve_instrument_token(
        kite=kite,
        tradingsymbol=symbol,
        exchange=EXCHANGE,
    )

    if token is None:
        raise RuntimeError(
            f"{symbol}: instrument token unavailable."
        )

    print(
        f"Instrument token : {token}"
    )

    chunks = []
    cursor = from_date

    while cursor <= to_date:

        chunk_end = min(
            cursor + timedelta(days=CHUNK_DAYS),
            to_date,
        )

        print(
            f"Request: {cursor} -> {chunk_end}"
        )

        candles = kite.historical_data(
            instrument_token=token,
            from_date=cursor,
            to_date=chunk_end,
            interval=INTERVAL,
        )

        chunk = normalize_candles(
            candles
        )

        print(
            f"Candles: {len(chunk)}"
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

    if not chunks:
        raise RuntimeError(
            f"{symbol}: no candles returned."
        )

    data = pd.concat(
        chunks,
        ignore_index=True,
    )

    data = (
        data
        .sort_values("datetime")
        .drop_duplicates(
            subset=["datetime"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    validate_market_data(
        data,
        symbol,
    )

    path = raw_path(symbol)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data.to_csv(
        path,
        index=False,
    )

    return data


# ============================================================
# LOAD LOCAL DATA
# ============================================================

def load_symbol_data(symbol):
    path = raw_path(symbol)

    if not path.exists():
        raise FileNotFoundError(
            f"{symbol}: missing {path}"
        )

    data = pd.read_csv(path)

    if "datetime" not in data.columns:
        raise RuntimeError(
            f"{symbol}: datetime column missing."
        )

    data["datetime"] = pd.to_datetime(
        data["datetime"],
        errors="coerce",
    )

    data = (
        data
        .dropna(subset=["datetime"])
        .sort_values("datetime")
        .drop_duplicates(
            subset=["datetime"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    validate_market_data(
        data,
        symbol,
    )

    return data


# ============================================================
# SESSION PREPARATION
# ============================================================

def prepare_sessions(data):
    sessions = []

    for _, group in data.groupby(
        data["datetime"].dt.date
    ):

        session = (
            group
            .sort_values("datetime")
            .reset_index(drop=True)
        )

        if session.empty:
            continue

        # Research only regular NSE session.
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
            sessions.append(session)

    sessions.sort(
        key=lambda s: s["datetime"].iloc[0]
    )

    return sessions


# ============================================================
# SIGNAL / ENTRY UNIVERSE
#
# This reproduces the locked transition logic from the
# existing research engine:
#
# BUY:
#   close > ORB high AND close > VWAP
#
# SELL:
#   close < ORB low AND close < VWAP
#
# New signal:
#   current condition true AND previous condition false
#
# Entry:
#   next candle OPEN
#
# The entry universe is generated once using the existing
# ORB stop, then frozen for all three SL modes.
# ============================================================

def generate_frozen_entries(
    symbol,
    session,
):
    data = calculate_vwap(
        session
    )

    if data is None or data.empty:
        return []

    opening_data = get_opening_range_data(
        session_data=session,
        start_time=OPENING_START_TIME,
        end_time=OPENING_END_TIME,
    )

    if opening_data is None or opening_data.empty:
        return []

    opening_high = float(
        opening_data["high"].max()
    )

    opening_low = float(
        opening_data["low"].min()
    )

    opening_last_time = (
        opening_data["datetime"].iloc[-1]
    )

    post_orb_indices = (
        session.index[
            session["datetime"]
            > opening_last_time
        ].tolist()
    )

    if not post_orb_indices:
        return []

    scan_index = post_orb_indices[0]

    entries = []

    # --------------------------------------------------------
    # IMPORTANT:
    # For universe generation we use the EXISTING ORB stop
    # and 2R exit to reproduce the same sequential,
    # non-overlapping opportunity universe used by the
    # existing research runner.
    # --------------------------------------------------------

    while scan_index < len(session) - 1:

        signal_candle = data.iloc[
            scan_index
        ]

        signal_time = signal_candle[
            "datetime"
        ]

        signal_close = float(
            signal_candle["close"]
        )

        signal_vwap = float(
            signal_candle["vwap"]
        )

        if scan_index > 0:

            previous_candle = data.iloc[
                scan_index - 1
            ]

            previous_close = float(
                previous_candle["close"]
            )

            previous_vwap = float(
                previous_candle["vwap"]
            )

        else:

            previous_close = None
            previous_vwap = None

        current_long = (
            signal_close > opening_high
            and signal_close > signal_vwap
        )

        current_short = (
            signal_close < opening_low
            and signal_close < signal_vwap
        )

        previous_long = False
        previous_short = False

        if previous_close is not None:

            previous_long = (
                previous_close > opening_high
                and previous_close > previous_vwap
            )

            previous_short = (
                previous_close < opening_low
                and previous_close < previous_vwap
            )

        new_long = (
            current_long
            and not previous_long
        )

        new_short = (
            current_short
            and not previous_short
        )

        if not (new_long or new_short):

            scan_index += 1
            continue

        direction = (
            "BUY"
            if new_long
            else "SELL"
        )

        entry_index = (
            scan_index + 1
        )

        if entry_index >= len(session):
            break

        entry_candle = session.iloc[
            entry_index
        ]

        raw_entry = float(
            entry_candle["open"]
        )

        entry_price = apply_slippage(
            price=raw_entry,
            direction=direction,
            slippage_pct=SLIPPAGE_PCT,
            is_entry=True,
        )

        # Existing ORB stop.
        if direction == "BUY":
            stop_loss = opening_low
            initial_risk = (
                entry_price - stop_loss
            )
        else:
            stop_loss = opening_high
            initial_risk = (
                stop_loss - entry_price
            )

        if initial_risk <= 0:
            scan_index += 1
            continue

        if direction == "BUY":
            target = (
                entry_price
                + TARGET_R * initial_risk
            )
        else:
            target = (
                entry_price
                - TARGET_R * initial_risk
            )

        # Use existing GARUDA exit simulator for the baseline
        # universe sequencing.
        baseline_trade = BacktestTrade(
            symbol=symbol,
            strategy_name="ORB_VWAP",
            trade_date=entry_candle[
                "datetime"
            ].date(),
            direction=direction,
            entry_time=entry_candle[
                "datetime"
            ],
            entry_price=entry_price,
            quantity=1,
        )

        future = (
            session
            .iloc[entry_index:]
            .copy()
            .reset_index(drop=True)
        )

        baseline_trade = simulate_trade_exit(
            trade=baseline_trade,
            future_candles=future,
            stop_loss=stop_loss,
            target=target,
        )

        if baseline_trade is None:
            break

        if baseline_trade.exit_price is None:
            break

        entries.append(
            {
                "trade_date":
                    entry_candle["datetime"].date(),

                "direction":
                    direction,

                "signal_candle_time":
                    signal_time,

                "entry_candle_time":
                    entry_candle["datetime"],

                "signal_index":
                    int(scan_index),

                "entry_index":
                    int(entry_index),

                "entry_price":
                    float(entry_price),

                "orb_high":
                    opening_high,

                "orb_low":
                    opening_low,

                "signal_vwap":
                    signal_vwap,
            }
        )

        # Resume after the baseline exit.
        exit_matches = session[
            session["datetime"]
            == baseline_trade.exit_time
        ]

        if exit_matches.empty:
            exit_position = int(
                (
                    session["datetime"]
                    - pd.Timestamp(
                        baseline_trade.exit_time
                    )
                ).abs().argmin()
            )
        else:
            exit_position = int(
                exit_matches.index[0]
            )

        scan_index = (
            exit_position + 1
        )

    return entries


# ============================================================
# TRADE REPLAY
# ============================================================

def compute_excursions(
    direction,
    entry_price,
    initial_risk,
    future,
):
    if future.empty:
        return (
            None, None,
            None, None
        )

    if direction == "BUY":

        mfe = (
            float(future["high"].max())
            - entry_price
        )

        mae = (
            entry_price
            - float(future["low"].min())
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

    mfe = max(
        0.0,
        mfe,
    )

    mae = max(
        0.0,
        mae,
    )

    if initial_risk <= 0:
        return (
            mfe,
            mae,
            None,
            None,
        )

    return (
        mfe,
        mae,
        mfe / initial_risk,
        mae / initial_risk,
    )


def replay_entry(
    symbol,
    session,
    entry_record,
    sl_mode,
):
    direction = entry_record["direction"]

    entry_index = int(
        entry_record["entry_index"]
    )

    entry_candle = session.iloc[
        entry_index
    ]

    # Entry price is frozen exactly as generated in the
    # baseline universe.
    entry_price = float(
        entry_record["entry_price"]
    )

    orb_high = float(
        entry_record["orb_high"]
    )

    orb_low = float(
        entry_record["orb_low"]
    )

    data_with_vwap = calculate_vwap(
        session
    )

    entry_vwap = float(
        data_with_vwap.iloc[
            entry_index
        ]["vwap"]
    )

    if sl_mode == "ORB":

        if direction == "BUY":
            stop_loss = orb_low
            initial_risk = (
                entry_price - stop_loss
            )
        else:
            stop_loss = orb_high
            initial_risk = (
                stop_loss - entry_price
            )

    elif sl_mode == "ORB_50":

        orb_range = (
            orb_high - orb_low
        )

        if direction == "BUY":
            stop_loss = (
                entry_price
                - 0.50 * orb_range
            )
            initial_risk = (
                entry_price - stop_loss
            )
        else:
            stop_loss = (
                entry_price
                + 0.50 * orb_range
            )
            initial_risk = (
                stop_loss - entry_price
            )

    elif sl_mode == "VWAP_MIDDLE":

        stop_loss = entry_vwap

        if direction == "BUY":
            initial_risk = (
                entry_price - stop_loss
            )
        else:
            initial_risk = (
                stop_loss - entry_price
            )

    else:
        raise ValueError(
            f"Unknown SL mode: {sl_mode}"
        )

    # Do not alter an invalid VWAP hypothesis.
    if (
        not np.isfinite(initial_risk)
        or initial_risk <= 0
    ):
        return {
            "valid": False,
            "reason": "INVALID_RISK",
            "sl_mode": sl_mode,
            "trade_date":
                entry_record["trade_date"],
            "direction":
                direction,
            "entry_time":
                entry_record["entry_candle_time"],
            "entry_price":
                entry_price,
            "entry_vwap":
                entry_vwap,
            "stop_loss":
                stop_loss,
            "initial_risk":
                initial_risk,
        }

    if direction == "BUY":
        target = (
            entry_price
            + TARGET_R * initial_risk
        )
    else:
        target = (
            entry_price
            - TARGET_R * initial_risk
        )

    trade = BacktestTrade(
        symbol=symbol,
        strategy_name=(
            f"ORB_VWAP_{sl_mode}"
        ),
        trade_date=entry_record[
            "trade_date"
        ],
        direction=direction,
        entry_time=entry_record[
            "entry_candle_time"
        ],
        entry_price=entry_price,
        quantity=1,
    )

    trade.initial_stop_loss = (
        stop_loss
    )

    trade.initial_risk = (
        initial_risk
    )

    trade.target_price = (
        target
    )

    trade.target_r = TARGET_R

    future = (
        session
        .iloc[entry_index:]
        .copy()
        .reset_index(drop=True)
    )

    mfe, mae, mfe_r, mae_r = (
        compute_excursions(
            direction=direction,
            entry_price=entry_price,
            initial_risk=initial_risk,
            future=future,
        )
    )

    trade = simulate_trade_exit(
        trade=trade,
        future_candles=future,
        stop_loss=stop_loss,
        target=target,
    )

    if trade is None:
        return {
            "valid": False,
            "reason": "NO_EXIT",
            "sl_mode": sl_mode,
        }

    if trade.exit_price is None:
        return {
            "valid": False,
            "reason": "NO_EXIT_PRICE",
            "sl_mode": sl_mode,
        }

    # Fixed stop integrity:
    # BE and trailing are OFF, so a STOP_LOSS must equal the
    # original structural stop before exit slippage.
    if trade.exit_reason == "STOP_LOSS":

        if abs(
            float(trade.exit_price)
            - float(stop_loss)
        ) > 1e-9:

            raise RuntimeError(
                "FIXED STOP INTEGRITY FAILURE: "
                f"{symbol} {sl_mode} "
                f"{entry_record['entry_candle_time']} "
                f"exit={trade.exit_price} "
                f"stop={stop_loss}"
            )

    raw_exit = float(
        trade.exit_price
    )

    trade.exit_price = apply_slippage(
        price=raw_exit,
        direction=direction,
        slippage_pct=SLIPPAGE_PCT,
        is_entry=False,
    )

    trade = calculate_trade_pnl(
        trade=trade,
        cost_rate_pct=COST_RATE_PCT,
    )

    exit_matches = session[
        session["datetime"]
        == pd.Timestamp(
            trade.exit_time
        )
    ]

    if exit_matches.empty:

        exit_position = int(
            (
                session["datetime"]
                - pd.Timestamp(
                    trade.exit_time
                )
            ).abs().argmin()
        )

    else:

        exit_position = int(
            exit_matches.index[0]
        )

    exit_candle = session.iloc[
        exit_position
    ]

    if direction == "BUY":

        sl_touched = (
            float(exit_candle["low"])
            <= stop_loss
        )

        target_touched = (
            float(exit_candle["high"])
            >= target
        )

    else:

        sl_touched = (
            float(exit_candle["high"])
            >= stop_loss
        )

        target_touched = (
            float(exit_candle["low"])
            <= target
        )

    trade.same_candle_ambiguous = (
        sl_touched
        and target_touched
    )

    trade.signal_candle_time = (
        entry_record["signal_candle_time"]
    )

    signal_matches = session[
        session["datetime"]
        == pd.Timestamp(
            entry_record["signal_candle_time"]
        )
    ]

    if not signal_matches.empty:

        signal_candle = session.iloc[
            int(signal_matches.index[0])
        ]

        trade.signal_candle_open = float(
            signal_candle["open"]
        )

        trade.signal_candle_high = float(
            signal_candle["high"]
        )

        trade.signal_candle_low = float(
            signal_candle["low"]
        )

        trade.signal_candle_close = float(
            signal_candle["close"]
        )

    trade.signal_candle_vwap = float(
        entry_record["signal_vwap"]
    )

    trade.entry_candle_time = (
        entry_candle["datetime"]
    )

    trade.entry_candle_open = float(
        entry_candle["open"]
    )

    trade.entry_candle_high = float(
        entry_candle["high"]
    )

    trade.entry_candle_low = float(
        entry_candle["low"]
    )

    trade.entry_candle_close = float(
        entry_candle["close"]
    )

    trade.entry_candle_vwap = (
        entry_vwap
    )

    trade.exit_candle_time = (
        exit_candle["datetime"]
    )

    trade.exit_candle_open = float(
        exit_candle["open"]
    )

    trade.exit_candle_high = float(
        exit_candle["high"]
    )

    trade.exit_candle_low = float(
        exit_candle["low"]
    )

    trade.exit_candle_close = float(
        exit_candle["close"]
    )

    trade.mfe = mfe
    trade.mae = mae
    trade.mfe_r = mfe_r
    trade.mae_r = mae_r

    return {
        "valid": True,
        "trade": trade,
    }


# ============================================================
# SUMMARY
# ============================================================

def summarize(trades):
    if not trades:
        return {
            "TRADES": 0,
            "STOP_LOSS": 0,
            "TARGET": 0,
            "END_OF_DAY": 0,
            "WIN_RATE_PCT": 0.0,
            "TOTAL_PNL": 0.0,
            "AVG_PNL": 0.0,
            "PROFIT_FACTOR": 0.0,
            "MAX_DRAWDOWN": 0.0,
            "AVG_MFE_R": np.nan,
            "P90_MFE_R": np.nan,
            "AVG_MAE_R": np.nan,
            "P90_MAE_R": np.nan,
        }

    stop_count = sum(
        t.exit_reason == "STOP_LOSS"
        for t in trades
    )

    target_count = sum(
        t.exit_reason == "TARGET"
        for t in trades
    )

    eod_count = sum(
        t.exit_reason == "END_OF_DAY"
        for t in trades
    )

    wins = sum(
        t.net_pnl > 0
        for t in trades
    )

    total_pnl = sum(
        t.net_pnl
        for t in trades
    )

    gross_profit = sum(
        t.net_pnl
        for t in trades
        if t.net_pnl > 0
    )

    gross_loss = abs(
        sum(
            t.net_pnl
            for t in trades
            if t.net_pnl < 0
        )
    )

    pf = (
        gross_profit / gross_loss
        if gross_loss > 0
        else float("inf")
    )

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0

    for trade in trades:

        cumulative += trade.net_pnl
        peak = max(
            peak,
            cumulative,
        )

        max_dd = max(
            max_dd,
            peak - cumulative,
        )

    mfe_r = np.array(
        [
            t.mfe_r
            for t in trades
            if t.mfe_r is not None
        ],
        dtype=float,
    )

    mae_r = np.array(
        [
            t.mae_r
            for t in trades
            if t.mae_r is not None
        ],
        dtype=float,
    )

    return {
        "TRADES":
            len(trades),

        "STOP_LOSS":
            stop_count,

        "TARGET":
            target_count,

        "END_OF_DAY":
            eod_count,

        "WIN_RATE_PCT":
            wins / len(trades) * 100,

        "TOTAL_PNL":
            total_pnl,

        "AVG_PNL":
            total_pnl / len(trades),

        "PROFIT_FACTOR":
            pf,

        "MAX_DRAWDOWN":
            max_dd,

        "AVG_MFE_R":
            float(np.mean(mfe_r))
            if len(mfe_r)
            else np.nan,

        "P90_MFE_R":
            float(np.percentile(mfe_r, 90))
            if len(mfe_r)
            else np.nan,

        "AVG_MAE_R":
            float(np.mean(mae_r))
            if len(mae_r)
            else np.nan,

        "P90_MAE_R":
            float(np.percentile(mae_r, 90))
            if len(mae_r)
            else np.nan,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 120)
    print(
        "GARUDA — 7-STOCK / 1-YEAR ORB+VWAP SL RESEARCH"
    )
    print("=" * 120)

    print(
        "SL modes       : ORB | 50% ORB | VWAP-MIDDLE (invalid-risk cases reported, no fallback)"
    )

    print(
        f"Target         : {TARGET_R}R"
    )

    print(
        "BE             : OFF"
    )

    print(
        "Trailing       : OFF"
    )

    print(
        f"Window         : {LOOKBACK_DAYS} calendar days"
    )

    print(
        f"Data interval  : {INTERVAL}"
    )

    print(
        "Entry universe : frozen per symbol before SL comparison"
    )

    print("=" * 120)

    # --------------------------------------------------------
    # Force the exact exit simulator configuration used by the
    # research experiments.
    # --------------------------------------------------------
    exit_module.risk_config.break_even_enabled = False
    exit_module.risk_config.trailing_stop_enabled = False

    if (
        exit_module.risk_config.break_even_enabled
        or exit_module.risk_config.trailing_stop_enabled
    ):
        raise RuntimeError(
            "Research configuration is not fixed: "
            "BE/trailing must both be OFF."
        )

    # --------------------------------------------------------
    # Authenticate
    # --------------------------------------------------------
    print()
    print(
        "Authenticating Kite..."
    )

    kite = create_authenticated_session()

    if kite is None:
        raise RuntimeError(
            "Kite authentication unavailable."
        )

    print(
        "Kite authentication : READY"
    )

    # --------------------------------------------------------
    # Date range
    # --------------------------------------------------------
    to_date = (
        date.today()
        - timedelta(days=1)
    )

    from_date = (
        to_date
        - timedelta(days=LOOKBACK_DAYS)
    )

    print(
        f"Research dates: {from_date} -> {to_date}"
    )

    # --------------------------------------------------------
    # Download / refresh all seven datasets.
    # --------------------------------------------------------
    datasets = {}
    coverage_rows = []

    for symbol in SYMBOLS:

        try:

            data = download_symbol(
                kite=kite,
                symbol=symbol,
                from_date=from_date,
                to_date=to_date,
            )

            datasets[symbol] = data

            coverage_rows.append(
                {
                    "symbol": symbol,
                    "rows": len(data),
                    "start": data["datetime"].min(),
                    "end": data["datetime"].max(),
                    "calendar_days": (
                        data["datetime"].max()
                        - data["datetime"].min()
                    ).total_seconds()
                    / 86400.0,
                    "trading_days":
                        data["datetime"].dt.date.nunique(),
                }
            )

        except Exception as error:

            print()
            print(
                f"❌ DATA FAILURE: {symbol}"
            )
            print(
                str(error)
            )

            raise

    # --------------------------------------------------------
    # Coverage gate
    # --------------------------------------------------------
    coverage = pd.DataFrame(
        coverage_rows
    )

    print()
    print("=" * 120)
    print(
        "HISTORICAL COVERAGE"
    )
    print("=" * 120)

    print(
        coverage.to_string(
            index=False
        )
    )

    if (
        coverage["calendar_days"]
        < MIN_REQUIRED_CALENDAR_DAYS
    ).any():

        raise RuntimeError(
            "Historical coverage gate failed: "
            "at least one symbol has less than "
            f"{MIN_REQUIRED_CALENDAR_DAYS} calendar days."
        )

    # --------------------------------------------------------
    # Prepare sessions and generate frozen entry universes.
    # --------------------------------------------------------
    all_entry_records = {}
    all_session_data = {}

    for symbol in SYMBOLS:

        print()
        print("=" * 100)
        print(
            f"GENERATING FROZEN ENTRY UNIVERSE : {symbol}"
        )
        print("=" * 100)

        sessions = prepare_sessions(
            datasets[symbol]
        )

        all_session_data[symbol] = sessions

        entry_records = []

        for session in sessions:

            entries = generate_frozen_entries(
                symbol=symbol,
                session=session,
            )

            entry_records.extend(
                [
                    {
                        **entry,
                        "session_date":
                            session[
                                "datetime"
                            ].dt.date.iloc[0],
                    }
                    for entry in entries
                ]
            )

        all_entry_records[symbol] = (
            entry_records
        )

        print(
            f"Sessions : {len(sessions)}"
        )

        print(
            f"Frozen entries : {len(entry_records)}"
        )

        if not entry_records:

            raise RuntimeError(
                f"{symbol}: no frozen entries generated."
            )

        pd.DataFrame(
            entry_records
        ).to_csv(
            RESEARCH_DIR
            / f"{symbol}_frozen_entries_1y.csv",
            index=False,
        )

    # --------------------------------------------------------
    # Replay each frozen universe through the three SL modes.
    # --------------------------------------------------------
    sl_modes = [
        "ORB",
        "ORB_50",
        "VWAP_MIDDLE",
    ]

    symbol_summary_rows = []
    detailed_rows = []

    for symbol in SYMBOLS:

        sessions = all_session_data[
            symbol
        ]

        entries = all_entry_records[
            symbol
        ]

        # Map date -> session.
        session_by_date = {
            s["datetime"].dt.date.iloc[0]:
                s
            for s in sessions
        }

        print()
        print("#" * 120)
        print(
            f"SYMBOL : {symbol} | FROZEN ENTRIES : {len(entries)}"
        )
        print("#" * 120)

        mode_trades = {}

        for mode in sl_modes:

            print()
            print(
                f"  Running {mode} ..."
            )

            trades = []

            invalid_count = 0

            for entry_record in entries:

                session = session_by_date[
                    entry_record[
                        "session_date"
                    ]
                ]

                result = replay_entry(
                    symbol=symbol,
                    session=session,
                    entry_record=entry_record,
                    sl_mode=mode,
                )

                if not result["valid"]:

                    invalid_count += 1

                    if result["reason"] == "INVALID_RISK":
                        continue

                    raise RuntimeError(
                        f"{symbol} {mode}: "
                        f"{result['reason']}"
                    )

                trades.append(
                    result["trade"]
                )

            # VWAP-MIDDLE is not geometrically valid when the
            # entry-candle VWAP is on the wrong side of entry.
            #
            # IMPORTANT:
            #   - Do NOT invent a fallback stop.
            #   - Do NOT change the entry.
            #   - Do NOT silently delete the entry from the
            #     frozen universe.
            #
            # Such entries are explicitly reported as
            # VWAP_INVALID and are excluded only from the
            # VWAP-MIDDLE performance statistics because no
            # valid VWAP protective stop exists under the
            # locked hypothesis.
            if invalid_count and mode == "VWAP_MIDDLE":
                print(
                    f"  VWAP_INVALID     : {invalid_count} "
                    f"(reported separately; no fallback SL)"
                )

            expected_valid = (
                len(entries) - invalid_count
                if mode == "VWAP_MIDDLE"
                else len(entries)
            )

            if len(trades) != expected_valid:

                raise RuntimeError(
                    f"{symbol} {mode}: replay count "
                    f"{len(trades)} != expected valid entries "
                    f"{expected_valid}; frozen universe="
                    f"{len(entries)}"
                )

            mode_trades[mode] = trades

            summary = summarize(
                trades
            )

            symbol_summary_rows.append(
                {
                    "SYMBOL": symbol,
                    "SL_MODE": mode,
                    "FROZEN_ENTRIES": len(entries),
                    "VALID_ENTRIES": len(trades),
                    "INVALID_RISK_ENTRIES":
                        invalid_count
                        if mode == "VWAP_MIDDLE"
                        else 0,
                    **summary,
                }
            )

            for trade in trades:

                detailed_rows.append(
                    {
                        "SYMBOL": symbol,
                        "SL_MODE": mode,
                        "trade_date":
                            trade.trade_date,
                        "direction":
                            trade.direction,
                        "signal_candle_time":
                            trade.signal_candle_time,
                        "entry_candle_time":
                            trade.entry_candle_time,
                        "entry_price":
                            trade.entry_price,
                        "stop_loss":
                            trade.initial_stop_loss,
                        "initial_risk":
                            trade.initial_risk,
                        "target":
                            trade.target_price,
                        "target_r":
                            TARGET_R,
                        "entry_vwap":
                            getattr(
                                trade,
                                "entry_candle_vwap",
                                None,
                            ),
                        "mfe":
                            trade.mfe,
                        "mae":
                            trade.mae,
                        "mfe_r":
                            trade.mfe_r,
                        "mae_r":
                            trade.mae_r,
                        "exit_time":
                            trade.exit_time,
                        "exit_price":
                            trade.exit_price,
                        "exit_reason":
                            trade.exit_reason,
                        "same_candle_ambiguous":
                            trade.same_candle_ambiguous,
                        "gross_pnl":
                            trade.gross_pnl,
                        "costs":
                            trade.costs,
                        "net_pnl":
                            trade.net_pnl,
                    }
                )

            print(
                f"  {mode:<14}"
                f" trades={summary['TRADES']:<5}"
                f" SL={summary['STOP_LOSS']:<5}"
                f" target={summary['TARGET']:<5}"
                f" EOD={summary['END_OF_DAY']:<5}"
                f" PF={summary['PROFIT_FACTOR']:.3f}"
                f" P&L={summary['TOTAL_PNL']:.2f}"
            )

    # --------------------------------------------------------
    # Save detailed results
    # --------------------------------------------------------
    detail_df = pd.DataFrame(
        detailed_rows
    )

    summary_df = pd.DataFrame(
        symbol_summary_rows
    )

    detail_path = (
        RESEARCH_DIR
        / "garuda_7stock_1year_sl_detail.csv"
    )

    summary_path = (
        RESEARCH_DIR
        / "garuda_7stock_1year_sl_summary.csv"
    )

    detail_df.to_csv(
        detail_path,
        index=False,
    )

    summary_df.to_csv(
        summary_path,
        index=False,
    )

    # --------------------------------------------------------
    # Combined 7-stock aggregate
    # --------------------------------------------------------
    aggregate_rows = []

    for mode in sl_modes:

        mode_df = detail_df[
            detail_df["SL_MODE"] == mode
        ]

        pnl = mode_df["net_pnl"].astype(float)

        wins = (
            pnl > 0
        ).sum()

        gross_profit = pnl[
            pnl > 0
        ].sum()

        gross_loss = abs(
            pnl[
                pnl < 0
            ].sum()
        )

        pf = (
            gross_profit / gross_loss
            if gross_loss > 0
            else float("inf")
        )

        cumulative = pnl.cumsum()
        peak = cumulative.cummax()
        drawdown = (
            peak - cumulative
        )

        aggregate_rows.append(
            {
                "SL_MODE": mode,
                "FROZEN_ENTRIES":
                    int(
                        summary_df[
                            summary_df["SL_MODE"] == mode
                        ]["FROZEN_ENTRIES"].sum()
                    ),
                "VALID_ENTRIES": len(mode_df),
                "INVALID_RISK_ENTRIES":
                    int(
                        summary_df[
                            summary_df["SL_MODE"] == mode
                        ]["INVALID_RISK_ENTRIES"].sum()
                    ),
                "TRADES": len(mode_df),
                "STOP_LOSS":
                    int(
                        (
                            mode_df["exit_reason"]
                            == "STOP_LOSS"
                        ).sum()
                    ),
                "TARGET":
                    int(
                        (
                            mode_df["exit_reason"]
                            == "TARGET"
                        ).sum()
                    ),
                "END_OF_DAY":
                    int(
                        (
                            mode_df["exit_reason"]
                            == "END_OF_DAY"
                        ).sum()
                    ),
                "WIN_RATE_PCT":
                    wins / len(mode_df) * 100,
                "TOTAL_PNL":
                    pnl.sum(),
                "AVG_PNL":
                    pnl.mean(),
                "PROFIT_FACTOR":
                    pf,
                "MAX_DRAWDOWN":
                    drawdown.max(),
                "AVG_MFE_R":
                    mode_df["mfe_r"].mean(),
                "P90_MFE_R":
                    mode_df["mfe_r"].quantile(.90),
                "AVG_MAE_R":
                    mode_df["mae_r"].mean(),
                "P90_MAE_R":
                    mode_df["mae_r"].quantile(.90),
            }
        )

    aggregate_df = pd.DataFrame(
        aggregate_rows
    )

    aggregate_path = (
        RESEARCH_DIR
        / "garuda_7stock_1year_sl_aggregate.csv"
    )

    aggregate_df.to_csv(
        aggregate_path,
        index=False,
    )

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------
    print()
    print("=" * 140)
    print(
        "GARUDA — 7-STOCK / 1-YEAR FINAL SL COMPARISON"
    )
    print("=" * 140)

    print(
        summary_df.to_string(
            index=False
        )
    )

    print()
    print("=" * 140)
    print(
        "7-STOCK AGGREGATE"
    )
    print("=" * 140)

    print(
        aggregate_df.to_string(
            index=False
        )
    )

    print()
    print("=" * 140)
    print(
        "RESEARCH FILES"
    )
    print("=" * 140)

    print(
        f"Summary    : {summary_path}"
    )

    print(
        f"Detailed   : {detail_path}"
    )

    print(
        f"Aggregate  : {aggregate_path}"
    )

    print()
    print(
        "VALIDATION STATUS : COMPLETE"
    )

    print(
        "No SL recommendation is automatically promoted to production."
    )

    print(
        "VWAP-MIDDLE invalid-risk entries are reported and excluded "
        "only from VWAP-MIDDLE performance statistics; no fallback "
        "SL or entry deletion is applied."
    )

    print(
        "The output is research evidence for Phase 14.V2."
    )

    print("=" * 140)


if __name__ == "__main__":
    main()
