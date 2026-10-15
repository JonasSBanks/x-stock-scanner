"""Loads settings from .env (see .env.example for what each one means).

Every other module gets its settings from load_config(), never from os.environ
directly, so all the safety checks below happen in one place.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

KNOWN_SOURCES = {"x_playwright"}
LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
MIN_POLL_MINUTES = 1     # be gentle with X
MAX_CATCHUP_DAYS = 7     # the longest window we show
MIN_PRUNE_DAYS = 8       # must keep more than the 1-week window

DEFAULTS = {
    "DATA_SOURCE": "x_playwright",
    "POLL_MINUTES": "3",
    "CATCHUP_DAYS": "7",
    "PRUNE_DAYS": "8",
    "HEADLESS": "true",
    "DB_PATH": "data/scanner.db",
    "AUTH_STATE_PATH": ".auth/state.json",
    "SYMBOLS_CACHE_DIR": "data/symbols",
    "HOST": "127.0.0.1",
    "PORT": "8000",
    "LOG_LEVEL": "INFO",
}


class ConfigError(Exception):
    """A setting in .env is invalid or not allowed."""


@dataclass(frozen=True)
class Config:
    data_source: str
    poll_minutes: float
    catchup_days: int
    prune_days: int
    headless: bool
    db_path: Path
    auth_state_path: Path
    symbols_cache_dir: Path
    host: str
    port: int
    log_level: str


def load_config(env: Mapping[str, str] | None = None) -> Config:
    """Read and check all settings.

    Normally reads .env, with real environment variables taking priority.
    Tests pass `env` (a plain dict) instead, so they never touch your .env.
    """
    if env is None:
        file_values = {k: v for k, v in dotenv_values(ENV_FILE).items() if v is not None}
        _reject_secrets(file_values)
        overrides = {k: os.environ[k] for k in DEFAULTS if k in os.environ}
        env = {**file_values, **overrides}
    else:
        _reject_secrets(env)

    values = {**DEFAULTS, **env}

    data_source = values["DATA_SOURCE"].strip()
    if data_source not in KNOWN_SOURCES:
        raise ConfigError(f"DATA_SOURCE must be one of {sorted(KNOWN_SOURCES)}, got {data_source!r}")

    host = values["HOST"].strip()
    if host not in LOCAL_HOSTS:
        raise ConfigError(
            f"HOST must be 127.0.0.1 or localhost so the app is only reachable from this computer, got {host!r}"
        )

    log_level = values["LOG_LEVEL"].strip().upper()
    if log_level not in LOG_LEVELS:
        raise ConfigError(f"LOG_LEVEL must be one of {sorted(LOG_LEVELS)}, got {values['LOG_LEVEL']!r}")

    return Config(
        data_source=data_source,
        poll_minutes=_number(values, "POLL_MINUTES", float, minimum=MIN_POLL_MINUTES),
        catchup_days=_number(values, "CATCHUP_DAYS", int, minimum=1, maximum=MAX_CATCHUP_DAYS),
        prune_days=_number(values, "PRUNE_DAYS", int, minimum=MIN_PRUNE_DAYS),
        headless=_bool(values, "HEADLESS"),
        db_path=_path(values, "DB_PATH"),
        auth_state_path=_path(values, "AUTH_STATE_PATH"),
        symbols_cache_dir=_path(values, "SYMBOLS_CACHE_DIR"),
        host=host,
        port=_number(values, "PORT", int, minimum=1024, maximum=65535),
        log_level=log_level,
    )


def _reject_secrets(env: Mapping[str, str]) -> None:
    # The X password must never be stored. Login is done by hand: python -m scanner.login
    bad = [k for k in env if "PASSWORD" in k.upper()]
    if bad:
        raise ConfigError(
            f"Remove {', '.join(bad)} from .env. Passwords are never stored; "
            "log in by hand with: python -m scanner.login"
        )


def _number(values, key, kind, minimum=None, maximum=None):
    raw = values[key].strip()
    try:
        number = kind(raw)
    except ValueError:
        raise ConfigError(f"{key} must be a {'whole ' if kind is int else ''}number, got {raw!r}") from None
    if minimum is not None and number < minimum:
        raise ConfigError(f"{key} must be at least {minimum}, got {number}")
    if maximum is not None and number > maximum:
        raise ConfigError(f"{key} must be at most {maximum}, got {number}")
    return number


def _bool(values, key):
    raw = values[key].strip().lower()
    if raw in {"true", "yes", "1"}:
        return True
    if raw in {"false", "no", "0"}:
        return False
    raise ConfigError(f"{key} must be true or false, got {values[key]!r}")


def _path(values, key):
    # Relative paths are relative to the project folder, not wherever you ran the command from.
    path = Path(values[key].strip())
    return path if path.is_absolute() else PROJECT_ROOT / path
