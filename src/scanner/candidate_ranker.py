def rank_candidates(active_instruments):
    """Score and rank active instruments."""

    ranked_candidates = []

    for symbol, metrics in active_instruments.items():

        volume_ratio = metrics["volume_ratio"]
        volatility_pct = metrics["volatility_pct"]
        price_change_pct = metrics["price_change_pct"]

        activity_score = (
            volume_ratio
            + volatility_pct
            + abs(price_change_pct)
        )

        candidate = {
            "symbol": symbol,
            "score": activity_score,
            "volume_ratio": volume_ratio,
            "volatility_pct": volatility_pct,
            "price_change_pct": price_change_pct,
        }

        ranked_candidates.append(candidate)

    ranked_candidates.sort(
        key=lambda candidate: candidate["score"],
        reverse=True,
    )

    return ranked_candidates