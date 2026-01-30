"""
Test that settings work as intended.
"""

import json
import os

from tangogql.settings import get_settings
from tangogql.subscription.listener import get_listener


def test_settings_json_defaults(tmp_path):
    os.chdir(tmp_path)
    settings = get_settings()
    assert not settings.no_auth
    assert settings.secret


def test_settings_json_no_auth(tmp_path):
    os.chdir(tmp_path)
    with open("config.json", "w") as f:
        json.dump({"no_auth": True}, f)
    settings = get_settings()
    assert settings.no_auth


def test_settings_json_secret(tmp_path):
    os.chdir(tmp_path)
    with open("config.json", "w") as f:
        json.dump({"secret": "my top secret!"}, f)
    settings = get_settings()
    assert settings.secret == "my top secret!"


def test_settings_json_secret_env_override(tmp_path, monkeypatch):
    os.chdir(tmp_path)
    with open("config.json", "w") as f:
        json.dump({"secret": "my top secret!"}, f)
    monkeypatch.setenv("TANGOGQL_SECRET", "secret from environment!")
    settings = get_settings()
    assert settings.secret == "secret from environment!"


def test_settings_attribute_poll_period(monkeypatch):
    monkeypatch.setenv("TANGOGQL_ATTRIBUTE_POLL_PERIOD", 7.12)
    get_listener.cache_clear()
    listener = get_listener()
    assert listener.poll_period == 7.12
