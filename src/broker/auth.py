import os

from pathlib import Path

from broker.kite_client import create_kite_client


def generate_login_url():
    """Generate the Kite Connect login URL."""

    kite = create_kite_client()

    login_url = kite.login_url()

    print("\n" + "=" * 60)
    print("GARUDA KITE AUTHENTICATION")
    print("=" * 60)
    print("\nOpen this URL in your browser:\n")
    print(login_url)
    print("\n" + "=" * 60)

    return login_url
def generate_access_token(request_token):
    """Exchange a request token for a Kite access token."""

    kite = create_kite_client()

    api_secret = os.getenv("KITE_API_SECRET")

    if not api_secret:
        raise ValueError(
            "KITE_API_SECRET not found. Check the .env file."
        )

    session_data = kite.generate_session(
        request_token,
        api_secret=api_secret,
    )

    access_token = session_data["access_token"]

    save_access_token(access_token)

    kite.set_access_token(access_token)

    print("\nAccess token generated successfully.")
    print("Authenticated Kite session created successfully.")

    return kite, access_token
def save_access_token(access_token):
    """Save the access token to a local session file."""

    project_root = Path(__file__).resolve().parents[2]

    session_directory = project_root / "data" / "session"

    session_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    token_file = session_directory / "kite_access_token.txt"

    token_file.write_text(
        access_token,
        encoding="utf-8"
    )

    print("Access token saved to local session storage.")

    return token_file