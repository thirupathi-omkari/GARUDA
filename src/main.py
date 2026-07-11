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


def display_ranked_candidates(ranked_candidates):
    """Display GARUDA scanner results."""

    print("\n" + "=" * 90)
    print("GARUDA RANKED MARKET CANDIDATES")
    print("=" * 90)

    if not ranked_candidates:
        print("No active market candidates found.")
        print("=" * 90)
        return

    print(
        f"{'RANK':<8}"
        f"{'SYMBOL':<15}"
        f"{'SCORE':>12}"
        f"{'VOL RATIO':>15}"
        f"{'VOLATILITY':>18}"
        f"{'PRICE CHANGE':>18}"
    )

    print("-" * 90)

    for rank, candidate in enumerate(
        ranked_candidates,
        start=1,
    ):

        print(
            f"{rank:<8}"
            f"{candidate['symbol']:<15}"
            f"{candidate['score']:>12.4f}"
            f"{candidate['volume_ratio']:>15.2f}"
            f"{candidate['volatility_pct']:>17.4f}%"
            f"{candidate['price_change_pct']:>17.2f}%"
        )

    print("=" * 90)


def main():

    print("\n" + "=" * 90)
    print("GARUDA QUANT LAB")
    print("MARKET SCANNER APPLICATION")
    print("=" * 90)

    # Step 1: Create authenticated broker session
    kite = create_authenticated_session()

    if kite is None:
        print("\nGARUDA Startup Failed.")
        print("Reason: Authenticated broker session unavailable.")
        return

    # Step 2: Load market universe
    universe = get_test_universe()

    print(f"\nMarket Universe Loaded : {len(universe)} instruments")

    # Step 3: Define historical data period
    to_date = date.today() - timedelta(days=1)
    from_date = to_date - timedelta(days=5)

    # Step 4: Fetch real market data
    universe_data = fetch_universe_data(
        kite=kite,
        universe=universe,
        from_date=from_date,
        to_date=to_date,
        interval="5minute",
    )

    if not universe_data:
        print("\nGARUDA Scanner Failed.")
        print("Reason: No valid market data available.")
        return

    # Step 5: Calculate activity metrics
    universe_metrics = calculate_universe_metrics(
        universe_data
    )

    # Step 6: Filter active instruments
    active_instruments = filter_active_instruments(
        universe_metrics=universe_metrics,
        min_volume_ratio=1.0,
        min_volatility_pct=0.05,
    )

    # Step 7: Rank active candidates
    ranked_candidates = rank_candidates(
        active_instruments
    )

    # Step 8: Display final scanner report
    display_ranked_candidates(
        ranked_candidates
    )

    print("\n" + "=" * 90)
    print("GARUDA APPLICATION STATUS")
    print("=" * 90)

    print(f"Universe Instruments : {len(universe)}")
    print(f"Data Ready           : {len(universe_data)}")
    print(f"Metrics Calculated   : {len(universe_metrics)}")
    print(f"Active Instruments   : {len(active_instruments)}")
    print(f"Ranked Candidates    : {len(ranked_candidates)}")

    print("-" * 90)
    print("GARUDA MARKET SCANNER : SUCCESS")
    print("=" * 90)


if __name__ == "__main__":
    main()