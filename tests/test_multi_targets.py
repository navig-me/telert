import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from telert import api, cli, messaging


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    for key in list(os.environ):
        if key.startswith("TELERT_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("TELERT_CONFIG", str(tmp_path / "config.json"))
    monkeypatch.setattr(messaging, "CONFIG_DIR", tmp_path / "unused-default")


def mock_discord(monkeypatch):
    post = Mock(return_value=SimpleNamespace(status_code=204))
    monkeypatch.setattr(messaging.requests, "post", post)
    return post


def test_legacy_config_unchanged_and_default_environment_override(monkeypatch):
    path = messaging.MessagingConfig().config_file
    original = {"discord": {"webhook_url": "https://example.com/old"}, "default": "discord"}
    path.write_text(json.dumps(original))
    config = messaging.MessagingConfig()
    assert config.get_default_providers() == [messaging.Provider.DISCORD]
    assert config.get_provider_config("discord:default") == original["discord"]
    post = mock_discord(monkeypatch)
    assert api.send("old") == {"DiscordProvider": True}
    assert post.call_args.args[0] == "https://example.com/old"
    monkeypatch.setenv("TELERT_DISCORD_WEBHOOK", "https://example.com/environment")
    api.send("environment", provider="discord")
    assert post.call_args.args[0] == "https://example.com/environment"
    assert json.loads(path.read_text()) == original


def test_named_targets_route_without_environment_override(monkeypatch):
    api.configure_discord("https://example.com/alerts", name="alerts")
    api.configure_discord("https://example.com/audit", instance_name="audit", set_default=False)
    monkeypatch.setenv("TELERT_DISCORD_WEBHOOK", "https://example.com/default")
    post = mock_discord(monkeypatch)
    assert api.send("alert", provider="alerts") == {"alerts": True}
    assert post.call_args.args[0] == "https://example.com/alerts"
    api.send("audit", provider="discord:audit")
    assert post.call_args.args[0] == "https://example.com/audit"
    api.send("audit", provider="discord", name="audit")
    assert post.call_args.args[0] == "https://example.com/audit"
    api.set_default_providers(["alerts", "discord:audit"])
    assert api.send("both") == {"alerts": True, "audit": True}
    assert api.is_configured("audit")
    assert api.get_config("audit")["webhook_url"] == "https://example.com/audit"
    assert {p["name"] for p in api.list_providers()} == {"discord", "alerts", "audit"}
    assert set(api.send("all", all_providers=True)) == {"DiscordProvider", "alerts", "audit"}
    stored = json.loads(messaging.MessagingConfig().config_file.read_text())
    assert stored["instances"]["alerts"] == {"type": "discord", "settings": {"webhook_url": "https://example.com/alerts"}}


@pytest.mark.parametrize("name", ["discord", "TELEGRAM", "slack", "all", "bad:name"])
def test_alias_collisions_rejected(name):
    with pytest.raises(ValueError, match="collides|Instance name"):
        api.configure_discord("https://example.com/alerts", name=name)


def test_alias_cannot_change_provider_type():
    api.configure_discord("https://example.com/alerts", name="alerts")
    with pytest.raises(ValueError, match="already used"):
        api.configure_slack("https://example.com/slack", name="alerts")


def test_unknown_target_never_falls_back(monkeypatch):
    monkeypatch.setenv("TELERT_DISCORD_WEBHOOK", "https://example.com/default")
    post = mock_discord(monkeypatch)
    with pytest.raises(RuntimeError, match="Unknown provider"):
        api.send("must not send", provider="missing")
    post.assert_not_called()


def run_cli(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["telert", *args])
    cli.main()


def test_cli_aliases_listing_status_and_defaults(monkeypatch, capsys):
    run_cli(monkeypatch, "config", "discord", "--webhook-url", "https://example.com/alerts", "--name", "alerts")
    run_cli(monkeypatch, "config", "discord", "--webhook-url", "https://example.com/audit", "--instance-name", "audit")
    run_cli(monkeypatch, "config", "set-defaults", "--providers", "alerts,discord:audit")
    run_cli(monkeypatch, "config", "list-providers")
    assert "alerts" in capsys.readouterr().out
    post = mock_discord(monkeypatch)
    run_cli(monkeypatch, "send", "test", "--provider", "discord:alerts")
    assert post.call_args.args[0] == "https://example.com/alerts"
    run_cli(monkeypatch, "status", "--provider", "audit")
    assert "audit (discord)" in capsys.readouterr().out
    assert post.call_args.args[0] == "https://example.com/audit"


def test_config_path_precedence(tmp_path, monkeypatch):
    default = messaging.CONFIG_DIR / "config.json"
    env_path = tmp_path / "environment.json"
    flag_path = tmp_path / "custom" / "flag.json"
    monkeypatch.delenv("TELERT_CONFIG")
    assert messaging.MessagingConfig().config_file == default
    monkeypatch.setenv("TELERT_CONFIG", str(env_path))
    assert messaging.MessagingConfig().config_file == env_path
    assert messaging.MessagingConfig(config_file=flag_path).config_file == flag_path
    run_cli(monkeypatch, "--config", str(flag_path), "config", "discord", "--webhook-url", "https://example.com/flag")
    assert flag_path.exists()
    assert not env_path.exists()
    assert not default.parent.exists()



def test_endpoint_display_name_remains_separate():
    api.configure_endpoint("https://example.com/endpoint", name="My API", instance_name="audit")
    assert api.get_config("audit")["name"] == "My API"


def test_environment_defaults_and_batch_configuration(monkeypatch):
    specifications = [
        {"provider": "discord", "name": "alerts", "webhook_url": "https://example.com/alerts"},
        {"provider": "discord", "instance_name": "audit", "webhook_url": "https://example.com/audit"},
    ]
    assert messaging.configure_providers(specifications, set_as_defaults=True)
    assert specifications[0]["provider"] == "discord"
    assert messaging.MessagingConfig().get_default_providers() == ["alerts", "audit"]
    monkeypatch.setenv("TELERT_DEFAULT_PROVIDER", "discord:audit,alerts")
    post = mock_discord(monkeypatch)
    assert list(api.send("both")) == ["audit", "alerts"]
    assert [call.args[0] for call in post.call_args_list] == [
        "https://example.com/audit", "https://example.com/alerts"
    ]


def test_unnamed_settings_preserved_when_creating_alias():
    api.configure_discord("https://example.com/default")
    api.configure_discord("https://example.com/alerts", name="alerts", set_default=False)
    assert api.get_config("discord")["webhook_url"] == "https://example.com/default"
    assert api.get_config()["default"] == "discord"


def test_cli_environment_config_path(tmp_path, monkeypatch):
    path = tmp_path / "env-selected.json"
    monkeypatch.setenv("TELERT_CONFIG", str(path))
    run_cli(monkeypatch, "config", "discord", "--webhook-url", "https://example.com/env")
    assert json.loads(path.read_text())["discord"]["webhook_url"] == "https://example.com/env"


def test_default_instance_spelling(monkeypatch):
    api.configure_discord("https://example.com/default", name="default")
    post = mock_discord(monkeypatch)
    assert api.send("default", provider="discord", name="default") == {"DiscordProvider": True}
    assert post.call_args.args[0] == "https://example.com/default"
