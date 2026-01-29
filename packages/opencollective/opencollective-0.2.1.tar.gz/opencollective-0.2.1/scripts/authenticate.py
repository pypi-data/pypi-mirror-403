#!/usr/bin/env python3
"""Authenticate with OpenCollective and save token."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from opencollective import OAuth2Handler

# OAuth app credentials (PolicyEngine Expense Manager)
CLIENT_ID = "b53b3cd0bca2f7534494"
CLIENT_SECRET = "2cc1c5fdca31f62d13cd65c73c0ab6d40c8dd28e"
TOKEN_FILE = os.path.expanduser("~/.config/opencollective/token.json")


def main():
    auth = OAuth2Handler(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri="http://localhost:8080/callback",
        token_file=TOKEN_FILE,
    )

    # Check if we already have a valid token
    token = auth.load_token()
    if token:
        print("Found existing token!")
        print(f"Access token: {token.get('access_token', 'N/A')[:20]}...")
        return

    # Get authorization URL
    auth_url = auth.get_authorization_url(scope="expenses")
    print(f"\nOpen this URL in your browser to authorize:\n\n{auth_url}\n")
    print("After authorizing, you'll be redirected to localhost:8080/callback")
    print("Copy the 'code' parameter from the URL and paste it below:\n")

    code = input("Authorization code: ").strip()

    if not code:
        print("No code provided. Exiting.")
        return

    # Exchange code for token
    try:
        token_data = auth.exchange_code(code)
        print(f"\nSuccess! Token saved to {TOKEN_FILE}")
        print(f"Access token: {token_data.get('access_token', 'N/A')[:20]}...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
