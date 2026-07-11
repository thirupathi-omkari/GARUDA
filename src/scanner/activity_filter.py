def filter_active_instruments(
    universe_metrics,
    min_volume_ratio=1.0,
    min_volatility_pct=0.05,
):
    """Filter instruments based on activity thresholds."""

    active_instruments = {}

    print("\n" + "=" * 60)
    print("GARUDA ACTIVITY FILTER")
    print("=" * 60)

    for symbol, metrics in universe_metrics.items():

        volume_ratio = metrics["volume_ratio"]
        volatility_pct = metrics["volatility_pct"]

        passes_volume = volume_ratio >= min_volume_ratio
        passes_volatility = volatility_pct >= min_volatility_pct

        if passes_volume and passes_volatility:

            active_instruments[symbol] = metrics

            print(f"✅ {symbol:<15} PASSED")

        else:

            print(f"❌ {symbol:<15} FILTERED OUT")

    print("-" * 60)

    print(
        f"Input Instruments  : {len(universe_metrics)}"
    )

    print(
        f"Active Instruments : {len(active_instruments)}"
    )

    print("=" * 60)

    return active_instruments