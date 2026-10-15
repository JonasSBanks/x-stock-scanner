from pathlib import Path

import pytest

from scanner.config import PROJECT_ROOT, ConfigError, load_config


def test_defaults_work_without_any_settings():
    config = load_config({})
    assert config.data_source == "x_playwright"
    assert config.poll_minutes == 3
    assert config.catchup_days == 7
    assert config.prune_days == 8
    assert config.headless is True
    assert config.host == "127.0.0.1"
    assert config.port == 8000


def test_relative_paths_are_inside_the_project_folder():
    config = load_config({})
    assert config.db_path == PROJECT_ROOT / "data" / "scanner.db"
    assert config.auth_state_path == PROJECT_ROOT / ".auth" / "state.json"


def test_absolute_paths_are_kept(tmp_path):
    config = load_config({"DB_PATH": str(tmp_path / "x.db")})
    assert config.db_path == tmp_path / "x.db"


@pytest.mark.parametrize("key", ["X_PASSWORD", "PASSWORD", "twitter_password"])
def test_passwords_are_refused(key):
    with pytest.raises(ConfigError, match="Passwords are never stored"):
        load_config({key: "hunter2"})


def test_polling_faster_than_one_minute_is_refused():
    with pytest.raises(ConfigError, match="POLL_MINUTES"):
        load_config({"POLL_MINUTES": "0.5"})


@pytest.mark.parametrize("days", ["0", "8"])
def test_catchup_must_be_between_1_and_7_days(days):
    with pytest.raises(ConfigError, match="CATCHUP_DAYS"):
        load_config({"CATCHUP_DAYS": days})


def test_pruning_must_keep_more_than_a_week():
    with pytest.raises(ConfigError, match="PRUNE_DAYS"):
        load_config({"PRUNE_DAYS": "7"})


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.10"])
def test_web_server_must_stay_on_this_computer(host):
    with pytest.raises(ConfigError, match="HOST"):
        load_config({"HOST": host})


@pytest.mark.parametrize("raw, expected", [("true", True), ("YES", True), ("0", False), ("false", False)])
def test_headless_accepts_common_spellings(raw, expected):
    assert load_config({"HEADLESS": raw}).headless is expected


def test_headless_rejects_nonsense():
    with pytest.raises(ConfigError, match="HEADLESS"):
        load_config({"HEADLESS": "maybe"})


def test_non_number_error_names_the_setting():
    with pytest.raises(ConfigError, match="PORT must be a whole number"):
        load_config({"PORT": "abc"})


def test_unknown_data_source_is_refused():
    with pytest.raises(ConfigError, match="DATA_SOURCE"):
        load_config({"DATA_SOURCE": "nitter"})


def test_log_level_is_case_insensitive():
    assert load_config({"LOG_LEVEL": "debug"}).log_level == "DEBUG"


def test_env_example_is_valid_and_has_every_setting():
    from dotenv import dotenv_values

    from scanner.config import DEFAULTS

    example = dotenv_values(Path(PROJECT_ROOT, ".env.example"))
    assert set(example) == set(DEFAULTS)
    load_config(example)
