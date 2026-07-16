import os
from pathlib import Path

from broker.auth import (
    generate_access_token,
    generate_login_url,
)

from broker.kite_client import create_kite_client


def _verify_session(kite):
    """Verify the current Kite session."""

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


def _authenticate_with_request_token():
    """Interactive authentication."""

    generate_login_url()

    print()
    request_token = input(
        "Paste Request Token : "
    ).strip()

    if not request_token:
        raise RuntimeError(
            "Request Token not supplied."
        )

    kite, _ = generate_access_token(
        request_token
    )

    return _verify_session(kite)


def create_authenticated_session():
    """
    Create and verify an authenticated session.

    If token is missing or expired,
    automatically guide the user
    through Kite login.
    """

    project_root = Path(__file__).resolve().parents[2]

    token_file = (
        project_root
        / "data"
        / "session"
        / "kite_access_token.txt"
    )

    # --------------------------------------------------
    # NO TOKEN
    # --------------------------------------------------

    if not token_file.exists():

        print("\nNo saved access token found.")
        print("Starting Kite login...\n")

        return _authenticate_with_request_token()

    access_token = token_file.read_text(
        encoding="utf-8"
    ).strip()

    if not access_token:

        print("\nSaved access token is empty.")
        print("Starting Kite login...\n")

        return _authenticate_with_request_token()

    kite = create_kite_client()

    kite.set_access_token(
        access_token
    )

    # --------------------------------------------------
    # VERIFY TOKEN
    # --------------------------------------------------

    try:

        return _verify_session(kite)

    except Exception:

        print("\nSaved access token expired.")
        print("Starting Kite login...\n")

        return _authenticate_with_request_token()