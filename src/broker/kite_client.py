import os

from dotenv import load_dotenv
from kiteconnect import KiteConnect


load_dotenv()


def create_kite_client():
    """Create a Kite Connect client."""

    api_key = os.getenv("KITE_API_KEY")

    if not api_key:
        raise ValueError(
            "KITE_API_KEY not found. Check the .env file."
        )

    kite = KiteConnect(api_key=api_key)

    print("Kite client created successfully.")

    return kite