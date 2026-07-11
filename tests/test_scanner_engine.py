import sys
from pathlib import Path
from datetime import date, timedelta


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))


from broker.session_manager import create_authenticated_session
from scanner.market_universe import get_test_universe
from scanner.scanner_engine import fetch_universe_data
from scanner.activity_metrics import calculate_universe_metrics
from scanner.activity_filter import filter_active_instruments
from scanner.candidate_ranker import rank_candidates


def main():

    print("=" * 60)
    print("GARUDA SCANNER ENGINE TEST")
    print("=" * 60)

    kite = create_authenticated_session()

    if kite is None:
        print("\n❌ Test Failed: Authenticated session unavailable.")
        return

    universe = get_test_universe()

    to_date = date.today() - timedelta(days=1)
    from_date = to_date - timedelta(days=5)

    universe_data = fetch_universe_data(
        kite=kite,
        universe=universe,
        from_date=from_date,
        to_date=to_date,
        interval="5minute",
    )
    universe_metrics = calculate_universe_metrics(
        universe_data
    )
    active_instruments = filter_active_instruments(
        universe_metrics=universe_metrics,
        min_volume_ratio=1.0,
        min_volatility_pct=0.05,
    )
    ranked_candidates = rank_candidates(
        active_instruments
    )


    print("\n" + "=" * 100)
    print("GARUDA MULTI-STOCK ACTIVITY METRICS")
    print("=" * 100)

    print(
        f"{'SYMBOL':<15}"
        f"{'AVG VOLUME':>15}"
        f"{'RECENT VOL':>15}"
        f"{'VOL RATIO':>12}"
        f"{'RANGE %':>12}"
        f"{'PRICE %':>12}"
        f"{'VOLATILITY':>15}"
    )

    print("-" * 100)

    for symbol, metrics in universe_metrics.items():

        print(
            f"{symbol:<15}"
            f"{metrics['average_volume']:>15.2f}"
            f"{metrics['recent_volume']:>15.2f}"
            f"{metrics['volume_ratio']:>12.2f}"
            f"{metrics['average_candle_range_pct']:>12.2f}"
            f"{metrics['price_change_pct']:>12.2f}"
            f"{metrics['volatility_pct']:>15.4f}"
        )

    print("=" * 100)

    print("\n" + "=" * 60)
    print("GARUDA ACTIVE INSTRUMENTS")
    print("=" * 60)

    if active_instruments:

        for symbol, metrics in active_instruments.items():

            print(
                f"{symbol:<15}"
                f"Volume Ratio: {metrics['volume_ratio']:.2f}  "
                f"Volatility: {metrics['volatility_pct']:.4f}%"
            )

    else:

        print("No instruments passed the activity filter.")

    print("=" * 60)

    print("\n" + "=" * 60)
    print("GARUDA SCANNER DATA RESULTS")
    print("=" * 60)

    for symbol, dataframe in universe_data.items():

        print(
            f"{symbol:<15} "
            f"Candles: {len(dataframe)}"
        )

    print("-" * 60)

    if len(universe_data) == len(universe):
        print("Multi-Stock Data Test : SUCCESS")
    else:
        print("Multi-Stock Data Test : PARTIAL SUCCESS")

    print("=" * 60)

    if len(universe_metrics) == len(universe_data):
        print("Multi-Stock Metrics Test : SUCCESS")
    else:
        print("Multi-Stock Metrics Test : FAILED")

    if len(active_instruments) <= len(universe_metrics):
        print("Real Activity Filter Test : SUCCESS")
    else:
        print("Real Activity Filter Test : FAILED")
    
    print("\n" + "=" * 80)
    print("GARUDA RANKED CANDIDATES")
    print("=" * 80)

    print(
        f"{'RANK':<8}"
        f"{'SYMBOL':<15}"
        f"{'SCORE':>12}"
        f"{'VOL RATIO':>15}"
        f"{'VOLATILITY':>15}"
        f"{'PRICE CHANGE':>18}"
    )

    print("-" * 80)

    for rank, candidate in enumerate(
        ranked_candidates,
        start=1,
    ):

        print(
            f"{rank:<8}"
            f"{candidate['symbol']:<15}"
            f"{candidate['score']:>12.4f}"
            f"{candidate['volume_ratio']:>15.2f}"
            f"{candidate['volatility_pct']:>15.4f}"
            f"{candidate['price_change_pct']:>18.2f}"
        )

    print("=" * 80)

    if len(ranked_candidates) == len(active_instruments):
        print("Real Candidate Ranking Test : SUCCESS")
    else:
        print("Real Candidate Ranking Test : FAILED")

if __name__ == "__main__":
    main()