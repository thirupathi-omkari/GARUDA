def evaluate_candidates(
    strategy,
    ranked_candidates,
    universe_data,
):
    """Evaluate ranked candidates using a GARUDA strategy."""

    strategy_results = []

    print("\n" + "=" * 60)
    print("GARUDA STRATEGY ENGINE")
    print("=" * 60)

    for candidate in ranked_candidates:

        symbol = candidate["symbol"]

        dataframe = universe_data.get(symbol)

        if dataframe is None:
            print(
                f"Skipping {symbol}: "
                f"Market data unavailable."
            )
            continue

        result = strategy.evaluate(
            symbol=symbol,
            dataframe=dataframe,
        )

        strategy_results.append(result)

        print(
            f"{symbol:<15} "
            f"Signal: {result.signal}"
        )

    print("-" * 60)

    print(
        f"Input Candidates  : "
        f"{len(ranked_candidates)}"
    )

    print(
        f"Strategy Results  : "
        f"{len(strategy_results)}"
    )

    print("=" * 60)

    return strategy_results