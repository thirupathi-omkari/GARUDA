def resolve_instrument_token(
    kite,
    tradingsymbol,
    exchange="NSE",
):
    """Resolve a trading symbol to its Kite instrument token."""

    print("\nResolving instrument token...")
    print("-" * 60)

    instruments = kite.instruments(exchange)

    matches = [
        instrument
        for instrument in instruments
        if instrument["tradingsymbol"] == tradingsymbol
    ]

    if not matches:
        print(
            f"❌ Instrument not found: "
            f"{exchange}:{tradingsymbol}"
        )
        return None

    instrument = matches[0]

    instrument_token = instrument["instrument_token"]

    print(f"Exchange         : {exchange}")
    print(f"Trading Symbol   : {tradingsymbol}")
    print(f"Instrument Token : {instrument_token}")

    print("-" * 60)
    print("Instrument Resolution: SUCCESS")

    return instrument_token