# X Stock Mention Scanner

A personal tool that watches the X (Twitter) accounts followed by one secondary X account, pulls stock tickers out of their posts, and shows which tickers are mentioned most often over the last 15 minutes, 30 minutes, 1 hour, 1 day and 1 week.

## About the developer (read this first)

- The owner is comfortable with **Python** but new to HTML/JS, git and Claude Code. Explain changes in plain language, keep the frontend simple, and point out anything they should learn rather than hiding it.
- Work in small steps. After each working step: run it, show the result, then **commit with a clear message and push**.
- The project will be shared with another person who runs it on their own computer. Everything must be set up from the README alone: no hard-coded paths, no personal settings in code.

## Features

1. **Trending (main view):** tickers ranked by mentions across all followed accounts. A window toggle selects 15m / 30m / 1h / 1d / 1w, and each row shows counts for all five windows side by side, so a ticker heating up is easy to spot.
2. **Ticker search:** counts per window for one ticker, which accounts mentioned it, and the posts, newest first.
3. **User search:** the tickers an account has mentioned recently, plus their posts.
4. Auto-refresh of the trending view.

## Key decisions already made

- **Platform:** X only.
- **Single user:** based on the following list of ONE X account.
- **Data source:** Playwright browser automation using a **secondary X account** (never the owner's main account) that follows the same people. Paid APIs were considered:
  - X's official API is pay-per-use (about $0.005 per post read) and too expensive for this.
  - Nitter/ntscraper are unreliable after X's legal action in Aug 2026.
- **Swappable data source:** all scraping lives behind one interface (`sources/base.py`), so it can later be replaced by the official X API or a third-party API by changing one file and one `.env` setting. Nothing outside `sources/` may depend on Playwright or X's page layout.
- **Runs locally** on the user's computer, not on a server.
- **Catch-up instead of 24/7 uptime:** on startup the ingestor reads back to the newest post it already has, up to 7 days, so the 1-week window stays accurate after the computer has been off.
- **Stack:**
  - Python 3.12+, FastAPI and SQLite.
  - A plain HTML + vanilla JS frontend served by FastAPI. No React, no build step.

## Scraper rules

- **Login is manual, once.** `python -m scanner.login` opens a visible browser, the user logs in themselves (including any 2FA), and the session is saved to `.auth/state.json`.
  - Never store the X password in code or `.env`.
  - Never automate login, 2FA or CAPTCHAs.
- **Read the "Following" tab** of the home timeline (chronological). Scroll back until reaching a post already in the database, or until hitting the 7-day limit.
- **Be gentle:**
  - Poll every few minutes (default 3, configurable).
  - Add small random delays and avoid parallel tabs.
  - If X shows a rate-limit message or a login wall, back off and log it clearly. Never hammer the site.
- **Expect breakage.** Keep page selectors in one place (`sources/x_playwright/selectors.py`). Log clearly when parsing fails instead of silently returning nothing.
- **For each post, capture:**
  - post id and author handle
  - text and timestamp (stored in UTC)
  - whether it is a repost or a quote

## Counting rules

- **Tickers are cashtags only** (`$AAPL`). Each must be validated against a real list of listed symbols (the NASDAQ Trader symbol files, refreshed daily and cached). Bare words like "AAPL" are not counted, because "A", "IT" and "ALL" are real tickers.
- **One post counts once per ticker:** "$TSLA $TSLA $TSLA" is 1 mention.
- **Plain reposts are not counted. Quote posts are counted.**
- **Show two numbers:** raw mentions and unique accounts. Trending sorts by unique accounts by default, so one spammy account can't dominate.
- **Open question:** crypto cashtags (`$BTC`) are ignored for now. Ask the owner before changing this.

## Data model (SQLite, `data/scanner.db`)

- `accounts(handle PK, display_name, first_seen)`
- `posts(id PK, author_handle, text, posted_at, is_repost, is_quote, scraped_at)`
- `mentions(post_id, ticker, author_handle, posted_at)`
  - primary key `(post_id, ticker)`
  - index on `(posted_at, ticker)`
  - index on `(author_handle, posted_at)`
- `state(key PK, value)`: for example, the newest post seen.

Window counts come from simple queries such as `WHERE posted_at >= now - window GROUP BY ticker`. No precomputed rollups are needed at this data size. Data older than 8 days may be pruned.

## Project structure

```
x-stock-scanner/
├── CLAUDE.md
├── README.md              # setup steps for a new user
├── requirements.txt
├── .env.example           # every setting, no secrets
├── .gitignore             # must include .env, .auth/, data/, __pycache__/, .venv/
├── run.py                 # starts ingestor loop + web server together
├── scanner/
│   ├── config.py          # loads .env
│   ├── db.py              # schema, connection, queries
│   ├── tickers.py         # cashtag extraction + symbol validation
│   ├── ingest.py          # polling loop, catch-up logic, writes posts/mentions
│   ├── login.py           # one-time manual login, saves .auth/state.json
│   ├── sources/
│   │   ├── base.py        # PostSource interface: fetch_since(last_seen) -> list[Post]
│   │   └── x_playwright/
│   │       ├── auth.py        # manual login flow (called by scanner/login.py)
│   │       ├── source.py      # drives the browser, captures timeline JSON
│   │       ├── parse.py       # raw X JSON -> Post objects (pure Python, tested)
│   │       ├── selectors.py   # every X-specific URL/selector/JSON path
│   │       └── __main__.py    # debug: print scraped posts
│   └── web/
│       ├── app.py         # FastAPI routes
│       ├── templates/     # index.html, ticker.html, user.html
│       └── static/        # app.js, style.css
└── tests/
    └── test_tickers.py    # extraction + counting rules
```

## API

- `GET /api/trending?window=1h&limit=50` returns each ticker with counts for all five windows, raw and unique.
- `GET /api/ticker/{symbol}` returns per-window counts, the accounts that mentioned it, and recent posts.
- `GET /api/user/{handle}` returns the tickers that account mentioned and its recent posts.
- `GET /api/status` returns the last successful scrape time and the last error, shown in the UI so breakage is visible.

## Build order

The owner chose to build the X data collection first (before tickers).

1. Scaffold: structure, `.gitignore`, `.env.example`, `requirements.txt` and README. Commit and push.
2. `config.py` + `login.py` (manual login, saves `.auth/state.json`).
3. Playwright source, reading X's own JSON responses (`HomeLatestTimeline`) via `page.on("response")` instead of parsing the page HTML. Save raw samples to `data/raw/`, build `parse.py` + tests against them, then scrolling/stop conditions. Print scraped posts before saving anything.
4. `db.py` schema + queries (`posts`, `accounts`, `state` first), tested with fake data.
5. `tickers.py` + tests, then `ingest.py`: polling, catch-up, writing posts and mentions to the DB.
6. FastAPI endpoints.
7. Trending page with window toggle and auto-refresh.
8. Ticker and user search pages.
9. Polish: status banner, pruning, README pass so someone else can install it.

## Never commit

`.env`, `.auth/` (the X session can log in as the secondary account), `data/` (the database), or the virtualenv.
