"""Manual X login with Playwright.

The user types everything (username, password, 2FA) into a visible browser.
This code only waits until X says they are logged in, then saves the session.
"""
from __future__ import annotations

import time
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from . import selectors

LOGIN_TIMEOUT_SECONDS = 600


def has_login_cookie(cookies: list[dict]) -> bool:
    """True if the browser has X's logged-in cookie."""
    return any(
        c.get("name") == selectors.AUTH_COOKIE
        and c.get("value")
        and c.get("domain", "").lstrip(".") in selectors.COOKIE_DOMAINS
        for c in cookies
    )


def interactive_login(state_path: Path) -> bool:
    """Open a browser for a manual login. Saves the session only if login succeeded."""
    with sync_playwright() as p:
        try:
            # Always visible: the user must see the window to log in themselves.
            browser = p.chromium.launch(headless=False)
        except PlaywrightError as e:
            if "Executable doesn't exist" in str(e):
                print("Playwright's browser isn't installed. Run: playwright install chromium")
                return False
            raise

        try:
            context = browser.new_context()
            page = context.new_page()
            page.goto(selectors.LOGIN_URL)
            print("A browser window has opened. Log in to your SECONDARY X account there.")
            print(f"Waiting up to {LOGIN_TIMEOUT_SECONDS // 60} minutes...")

            deadline = time.monotonic() + LOGIN_TIMEOUT_SECONDS
            while time.monotonic() < deadline:
                if has_login_cookie(context.cookies()):
                    page.wait_for_timeout(3000)  # let X finish setting its other cookies
                    state_path.parent.mkdir(parents=True, exist_ok=True)
                    context.storage_state(path=str(state_path))
                    return True
                page.wait_for_timeout(1000)

            print("Timed out waiting for login. Nothing was saved.")
            return False
        except PlaywrightError:
            print("The browser window was closed before login finished. Nothing was saved.")
            return False
        finally:
            try:
                browser.close()
            except PlaywrightError:
                pass  # already closed by the user
