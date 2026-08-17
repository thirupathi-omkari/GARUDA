from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent
RESEARCH_DIR = ROOT / "data" / "research"

# Reuse the completed GARUDA ORB_50 + 2R research results.
# No new entry generation, exit simulation, slippage, or costs.
DETAIL_PATH = (
    RESEARCH_DIR
    / "garuda_7stock_1year_sl_target_matrix_detail.csv"
)

FILTERS = [
    "NO_FILTER",
    "Q1_CLOSEST",
    "Q1_Q2",
    "EXCLUDE_Q4_FARTHEST",
]


def profit_factor(pnl):
    gp = pnl[pnl > 0].sum()
    gl = abs(pnl[pnl < 0].sum())
    return gp / gl if gl > 0 else float("inf")


def max_drawdown(pnl):
    equity = pnl.cumsum()
    return float((equity.cummax() - equity).max())


def make_symbol_thresholds(df):
    # VWAP distance is not comparable in raw price points across symbols.
    # Quartiles are therefore calculated within each symbol.
    return (
        df.groupby("SYMBOL")["entry_vwap_distance"]
        .apply(lambda s: s.abs().quantile([0.25, 0.50, 0.75]))
        .unstack()
        .rename(
            columns={
                0.25: "Q1",
                0.50: "Q2",
                0.75: "Q3",
            }
        )
    )


def classify(row, thresholds):
    t = thresholds.loc[row["SYMBOL"]]
    x = abs(row["entry_vwap_distance"])

    if x <= t["Q1"]:
        return "Q1_CLOSEST"
    if x <= t["Q2"]:
        return "Q2"
    if x <= t["Q3"]:
        return "Q3"
    return "Q4_FARTHEST"


def summarize(name, df):
    pnl = df["net_pnl"].astype(float)

    return {
        "FILTER": name,
        "TRADES": len(df),
        "EXCLUDED": 1879 - len(df),
        "WIN_RATE_PCT":
            (pnl > 0).mean() * 100,
        "TOTAL_PNL":
            pnl.sum(),
        "AVG_PNL":
            pnl.mean(),
        "PROFIT_FACTOR":
            profit_factor(pnl),
        "MAX_DRAWDOWN":
            max_drawdown(pnl),
        "STOP_LOSS":
            int(
                (df["exit_reason"] == "STOP_LOSS").sum()
            ),
        "TARGET":
            int(
                (df["exit_reason"] == "TARGET").sum()
            ),
        "END_OF_DAY":
            int(
                (df["exit_reason"] == "END_OF_DAY").sum()
            ),
        "AVG_MFE_R":
            df["mfe_r"].mean(),
        "AVG_MAE_R":
            df["mae_r"].mean(),
        "AVG_ABS_VWAP_DISTANCE":
            df["entry_vwap_distance"].abs().mean(),
    }


def main():
    print()
    print("=" * 120)
    print("GARUDA — ORB+VWAP VWAP-DISTANCE FILTER RESEARCH — FIXED")
    print("=" * 120)
    print("Source          : existing GARUDA target-matrix detail")
    print("Locked cell     : ORB_50 + 2.00R")
    print("Frozen universe : 1,880 entries / 1,879 valid ORB_50 trades")
    print("BE              : OFF")
    print("Trailing        : OFF")
    print("Only variable   : entry-to-VWAP distance inclusion filter")
    print("=" * 120)

    if not DETAIL_PATH.exists():
        raise FileNotFoundError(DETAIL_PATH)

    detail = pd.read_csv(DETAIL_PATH)

    required = {
        "SYMBOL",
        "SL_MODE",
        "TARGET_R",
        "entry_price",
        "entry_vwap",
        "exit_reason",
        "net_pnl",
        "mfe_r",
        "mae_r",
    }

    missing = required - set(detail.columns)
    if missing:
        raise RuntimeError(
            "Detail file is missing required columns: "
            + ", ".join(sorted(missing))
        )

    for c in [
        "entry_price",
        "entry_vwap",
        "net_pnl",
        "mfe_r",
        "mae_r",
    ]:
        detail[c] = pd.to_numeric(
            detail[c],
            errors="coerce",
        )

    baseline = detail[
        (detail["SL_MODE"] == "ORB_50")
        & (detail["TARGET_R"] == 2.0)
    ].copy()

    if len(baseline) != 1879:
        raise RuntimeError(
            f"Expected 1,879 valid ORB_50 + 2R trades, got {len(baseline)}"
        )

    # Reconstruct exactly the entry-to-VWAP distance used by the
    # diagnostic, from the frozen research fields.
    #
    # The diagnostic defined distance directionally:
    # BUY  = entry_price - entry_vwap
    # SELL = entry_vwap - entry_price
    #
    # For filtering, we use ABSOLUTE distance because the hypothesis
    # being tested is "closer vs farther from VWAP", not direction.
    baseline["entry_vwap_distance"] = (
        baseline["entry_price"]
        - baseline["entry_vwap"]
    )

    if baseline["entry_vwap_distance"].isna().any():
        raise RuntimeError(
            "VWAP distance is missing for one or more frozen trades."
        )

    thresholds = make_symbol_thresholds(
        baseline
    )

    baseline["VWAP_DISTANCE_BUCKET"] = baseline.apply(
        lambda r: classify(r, thresholds),
        axis=1,
    )

    masks = {
        "NO_FILTER":
            pd.Series(
                True,
                index=baseline.index,
            ),
        "Q1_CLOSEST":
            baseline["VWAP_DISTANCE_BUCKET"]
            == "Q1_CLOSEST",
        "Q1_Q2":
            baseline["VWAP_DISTANCE_BUCKET"].isin(
                ["Q1_CLOSEST", "Q2"]
            ),
        "EXCLUDE_Q4_FARTHEST":
            baseline["VWAP_DISTANCE_BUCKET"].isin(
                ["Q1_CLOSEST", "Q2", "Q3"]
            ),
    }

    rows = []

    for name in FILTERS:
        filtered = baseline[
            masks[name]
        ].copy()

        if "exit_time" in filtered.columns:
            filtered["exit_time"] = pd.to_datetime(
                filtered["exit_time"],
                errors="coerce",
            )
            if "entry_candle_time" in filtered.columns:
                filtered["entry_candle_time"] = pd.to_datetime(
                    filtered["entry_candle_time"],
                    errors="coerce",
                )
                filtered = filtered.sort_values(
                    [
                        "exit_time",
                        "entry_candle_time",
                        "SYMBOL",
                    ]
                )
            else:
                filtered = filtered.sort_values(
                    ["exit_time", "SYMBOL"]
                )

        rows.append(
            summarize(
                name,
                filtered,
            )
        )

    summary = pd.DataFrame(rows)

    symbol_rows = []

    for name in FILTERS:
        filtered = baseline[
            masks[name]
        ].copy()

        for symbol, group in filtered.groupby(
            "SYMBOL",
            sort=True,
        ):
            pnl = group["net_pnl"].astype(float)

            symbol_rows.append(
                {
                    "FILTER": name,
                    "SYMBOL": symbol,
                    "TRADES": len(group),
                    "TOTAL_PNL": pnl.sum(),
                    "AVG_PNL": pnl.mean(),
                    "PROFIT_FACTOR":
                        profit_factor(pnl),
                    "WIN_RATE_PCT":
                        (pnl > 0).mean() * 100,
                    "AVG_MFE_R":
                        group["mfe_r"].mean(),
                    "AVG_MAE_R":
                        group["mae_r"].mean(),
                    "STOP_LOSS":
                        int(
                            (
                                group["exit_reason"]
                                == "STOP_LOSS"
                            ).sum()
                        ),
                    "TARGET":
                        int(
                            (
                                group["exit_reason"]
                                == "TARGET"
                            ).sum()
                        ),
                    "END_OF_DAY":
                        int(
                            (
                                group["exit_reason"]
                                == "END_OF_DAY"
                            ).sum()
                        ),
                }
            )

    symbol_summary = pd.DataFrame(
        symbol_rows
    )

    threshold_rows = (
        thresholds.reset_index()
        .rename(
            columns={
                "index": "SYMBOL"
            }
        )
    )

    detail_path = (
        RESEARCH_DIR
        / "garuda_orbvwap_vwap_distance_filter_detail_fixed.csv"
    )
    summary_path = (
        RESEARCH_DIR
        / "garuda_orbvwap_vwap_distance_filter_summary_fixed.csv"
    )
    symbol_path = (
        RESEARCH_DIR
        / "garuda_orbvwap_vwap_distance_filter_by_symbol_fixed.csv"
    )
    threshold_path = (
        RESEARCH_DIR
        / "garuda_orbvwap_vwap_distance_quartile_thresholds.csv"
    )

    baseline.to_csv(
        detail_path,
        index=False,
    )
    summary.to_csv(
        summary_path,
        index=False,
    )
    symbol_summary.to_csv(
        symbol_path,
        index=False,
    )
    threshold_rows.to_csv(
        threshold_path,
        index=False,
    )

    print()
    print("=" * 120)
    print("7-STOCK AGGREGATE")
    print("=" * 120)
    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("=" * 120)
    print("BY SYMBOL")
    print("=" * 120)
    print(
        symbol_summary.to_string(
            index=False
        )
    )

    print()
    print("=" * 120)
    print("WITHIN-SYMBOL VWAP-DISTANCE QUARTILE THRESHOLDS")
    print("=" * 120)
    print(
        threshold_rows.to_string(
            index=False
        )
    )

    print()
    print("=" * 120)
    print("OUTPUT FILES")
    print("=" * 120)
    print(f"Detail     : {detail_path}")
    print(f"Summary    : {summary_path}")
    print(f"By symbol  : {symbol_path}")
    print(f"Thresholds : {threshold_path}")

    print()
    print(
        "VALIDATION: Existing ORB_50 + 2R results reused; "
        "only VWAP-distance inclusion was changed."
    )


if __name__ == "__main__":
    main()
