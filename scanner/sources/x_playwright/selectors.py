"""Everything that depends on X's website lives here.

When X changes something and scraping breaks, this is the first file to check.
"""

LOGIN_URL = "https://x.com/i/flow/login"
HOME_URL = "https://x.com/home"

# X sets this cookie only once you are fully logged in (after any 2FA).
AUTH_COOKIE = "auth_token"
COOKIE_DOMAINS = {"x.com", "twitter.com"}
