# X Stock Mention Scanner

Watches the X (Twitter) accounts followed by a secondary X account, pulls stock cashtags (like `$AAPL`) out of their posts, and shows which tickers are mentioned most over the last 15 minutes, 30 minutes, 1 hour, 1 day and 1 week.

Everything runs on your own computer.

> **Status:** work in progress. Steps 5 and 6 below don't work yet.

## What you need

- **Python 3.12 or newer**: check with `python --version`
- **git**
- **A secondary X account** that follows the people you want to track. Don't use your main account, because automated browsing can get an account restricted.

## Setup

**1. Get the code**

```bash
git clone https://github.com/JonasSBanks/x-stock-scanner.git
cd x-stock-scanner
```

**2. Create a virtual environment** (a private folder of Python packages just for this project)

Windows:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You'll see `(.venv)` at the start of your terminal line. Activate it again every time you open a new terminal.

**3. Install packages and the browser**

```bash
pip install -r requirements.txt
playwright install chromium
```

**4. Create your settings file**

Windows: `copy .env.example .env`
macOS / Linux: `cp .env.example .env`

The defaults are fine. Open `.env` to see what each setting does.

**5. Log in to X once**

```bash
python -m scanner.login
```

A browser window opens. Log in to your **secondary** account yourself, including any 2FA, then go back to the terminal and press Enter. The session is saved to `.auth/state.json`. Your password is never stored.

**6. Run it**

```bash
python run.py
```

Open http://127.0.0.1:8000 in your browser.

## Running the tests

```bash
pytest
```

## Privacy

`.env`, `.auth/` and `data/` are never committed to git. `.auth/state.json` can log in as your secondary account, so don't share it.
