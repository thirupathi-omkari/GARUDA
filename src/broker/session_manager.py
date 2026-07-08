import os

from pathlib import Path

from broker.kite_client import create_kite_client


def create_authenticated_session():
    """Create and verify an authenticated Kite session."""

    project_root = Path(__file__).resolve().parents[2]

    token_file = (
        project_root
        / "data"
        / "session"
        / "kite_access_token.txt"
    )

    if not token_file.exists():
        print("❌ Kite access token file not found.")
        return None

    access_token = token_file.read_text(
        encoding="utf-8"
    ).strip()

    if not access_token:
        print("❌ KITE_ACCESS_TOKEN not available.")
        return None

    kite = create_kite_client()

    kite.set_access_token(access_token)

    try:
        profile = kite.profile()

        print("\n" + "=" * 60)
        print("GARUDA SESSION MANAGER")
        print("=" * 60)

        print("✅ Access token available")
        print("✅ Kite client created")
        print("✅ Authentication verified")
        print(f"✅ Connected User : {profile.get('user_name')}")

        print("-" * 60)
        print("GARUDA Broker Session: READY")
        print("=" * 60)

        return kite

    except Exception as error:

        print("\n" + "=" * 60)
        print("GARUDA SESSION MANAGER")
        print("=" * 60)

        print("❌ Authentication failed")
        print(f"Reason: {error}")

        print("-" * 60)
        print("GARUDA Broker Session: NOT READY")
        print("=" * 60)

        return None