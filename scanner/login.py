"""One-time manual login.

Run:  python -m scanner.login

Opens a browser, you log in to the secondary X account yourself, and the
session is saved to .auth/state.json so the scraper can use it.
"""
from __future__ import annotations

import sys

from scanner.config import ConfigError, load_config
from scanner.sources.x_playwright.auth import interactive_login


def main() -> int:
    try:
        config = load_config()
    except ConfigError as e:
        print(f"Settings problem in .env: {e}")
        return 1

    print("Use a SECONDARY X account here, never your main one.")

    path = config.auth_state_path
    if path.exists():
        answer = input(f"A saved login already exists at {path}. Replace it? [y/N] ")
        if answer.strip().lower() != "y":
            print("Kept the existing login.")
            return 0
        # The old file is only overwritten if the new login succeeds.

    if not interactive_login(path):
        return 1

    print(f"Login saved to {path}")
    print("This file can log in as that account: never share it or commit it to git.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
