import asyncio
import builtins
import json
import ssl
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

import telert
from telert import cli, messaging


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    monkeypatch.setattr(messaging, "CONFIG_DIR", tmp_path)
    for key in list(__import__("os").environ):
        if key.startswith("TELERT_"):
            monkeypatch.delenv(key)


@pytest.fixture
def fake_xmpp(monkeypatch):
    instances = []

    class Client:
        event = "session_start"
        connect_error = False
        disconnect_error = False

        def __init__(self, jid, password):
            self.jid, self.password = jid, password
            self.loop = asyncio.get_running_loop()
            self.thread = threading.get_ident()
            self.handlers = {}
            self.messages = []
            self.closed = False
            self.cancelled = False
            self.presence = False
            instances.append(self)

        def add_event_handler(self, event, handler):
            self.handlers[event] = handler

        async def connect(self, **kwargs):
            self.address = kwargs
            if self.connect_error:
                raise RuntimeError(self.password)
            handler = self.handlers[self.event]
            result = handler(None)
            if asyncio.iscoroutine(result):
                await result
            # Real Slixmpp connect resolves to None, not a success boolean.
            return None

        def send_presence(self):
            self.presence = True

        def send_message(self, **kwargs):
            self.messages.append(kwargs)

        async def disconnect(self):
            if self.disconnect_error:
                raise RuntimeError(self.password)
            self.closed = True

        def cancel_connection_attempt(self):
            self.cancelled = True

        def abort(self):
            self.aborted = True

    monkeypatch.setitem(sys.modules, "slixmpp", SimpleNamespace(ClientXMPP=Client))
    return Client, instances


def provider(**kwargs):
    return messaging.XMPPProvider("sender@example.org", "supersecret", "receiver@example.org", **kwargs)


def test_api_configuration_preserves_legacy_config():
    config = messaging.MessagingConfig()
    config.config_file.write_text(json.dumps({"telegram": {"token": "old", "chat_id": "123"}, "default": "telegram"}))
    telert.configure_xmpp("sender@example.org", "supersecret", "receiver@example.org", server="xmpp.example.org", port=5223, direct_tls=True)
    stored = json.loads(config.config_file.read_text())
    assert stored["telegram"] == {"token": "old", "chat_id": "123"}
    assert stored["xmpp"]["direct_tls"] is True
    assert isinstance(messaging.get_provider("xmpp"), messaging.XMPPProvider)
    assert messaging.MessagingConfig().get_default_provider() == messaging.Provider.XMPP
    assert any(p["name"] == "xmpp" for p in telert.list_providers())


def test_partial_environment_override(monkeypatch):
    telert.configure_xmpp("sender@example.org", "saved", "receiver@example.org")
    monkeypatch.setenv("TELERT_XMPP_PASSWORD", "override")
    monkeypatch.setenv("TELERT_XMPP_PORT", "5223")
    monkeypatch.setenv("TELERT_XMPP_DIRECT_TLS", "true")
    monkeypatch.setenv("TELERT_XMPP_CA_FILE", "/tmp/ca.pem")
    result = messaging.get_provider("xmpp")
    assert (result.jid, result.password, result.port, result.direct_tls, result.ca_file) == ("sender@example.org", "override", 5223, True, "/tmp/ca.pem")
    assert json.loads(messaging.MessagingConfig().config_file.read_text())["xmpp"]["password"] == "saved"


def test_environment_only(monkeypatch):
    for key, value in {"JID": "sender@example.org", "PASSWORD": "secret", "RECIPIENT": "to@example.org", "SERVER": "xmpp.example.org"}.items():
        monkeypatch.setenv("TELERT_XMPP_" + key, value)
    result = messaging.get_providers()
    assert len(result) == 1
    assert result[0].recipient == "to@example.org"
    assert result[0].server == "xmpp.example.org"


@pytest.mark.parametrize("port", [0, 65536, "no"])
def test_invalid_port(port):
    with pytest.raises(ValueError, match="port"):
        provider(port=port).save_config(messaging.MessagingConfig())


@pytest.mark.parametrize("key,value", [("PORT", "no"), ("DIRECT_TLS", "maybe")])
def test_invalid_environment(monkeypatch, key, value):
    monkeypatch.setenv("TELERT_XMPP_" + key, value)
    with pytest.raises(ValueError, match="TELERT_XMPP_"):
        messaging.MessagingConfig().get_provider_config("xmpp")


def test_missing_dependency_is_lazy(monkeypatch):
    original = builtins.__import__

    def no_slixmpp(name, *args, **kwargs):
        if name == "slixmpp":
            raise ImportError("not installed")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_slixmpp)
    telert.configure_xmpp("sender@example.org", "secret", "to@example.org")
    with pytest.raises(ImportError, match=r"pip install 'telert\[xmpp\]'"):
        messaging.get_provider("xmpp").send("hello")


def test_send_discovery_and_cleanup(fake_xmpp):
    _, instances = fake_xmpp
    assert provider().send("hello") is True
    client = instances[0]
    assert client.address == {}
    assert client.messages == [{"mto": "receiver@example.org", "mbody": "hello", "mtype": "chat"}]
    assert client.presence and client.closed and client.cancelled and client.aborted
    assert client.enable_starttls and not client.enable_direct_tls
    assert client.ssl_context.verify_mode == ssl.CERT_REQUIRED
    assert client.ssl_context.check_hostname


def test_send_explicit_tls_server(fake_xmpp):
    _, instances = fake_xmpp
    assert provider(server="xmpp.example.org", direct_tls=True).send("hello")
    assert instances[0].address == {"host": "xmpp.example.org", "port": 5223}
    assert instances[0].enable_direct_tls and not instances[0].enable_starttls


def test_send_port_without_server(fake_xmpp):
    _, instances = fake_xmpp
    assert provider(port=1234).send("hello")
    assert instances[0].address == {"host": "example.org", "port": 1234}


def test_send_with_running_loop(fake_xmpp):
    _, instances = fake_xmpp

    async def run():
        loop = asyncio.get_running_loop()
        assert provider().send("async caller")
        assert asyncio.get_running_loop() is loop
        assert instances[0].loop is not loop
        assert instances[0].thread != threading.get_ident()

    asyncio.run(run())


def test_send_from_thread(fake_xmpp):
    with ThreadPoolExecutor(max_workers=1) as executor:
        assert executor.submit(provider().send, "thread caller").result()


@pytest.mark.parametrize("event", ["failed_auth", "connection_failed", "disconnected"])
def test_failure_events(fake_xmpp, event):
    Client, instances = fake_xmpp
    Client.event = event
    with pytest.raises(RuntimeError, match="XMPP send failed"):
        provider().send("hello")
    assert instances[0].aborted and instances[0].cancelled


@pytest.mark.parametrize("failure", ["connect_error", "disconnect_error"])
def test_transport_errors_do_not_expose_credentials(fake_xmpp, failure, capsys):
    Client, instances = fake_xmpp
    setattr(Client, failure, True)
    with pytest.raises(RuntimeError) as error:
        provider().send("hello")
    assert "supersecret" not in str(error.value)
    assert "supersecret" not in str(capsys.readouterr())
    assert instances[0].aborted


def test_cli_configuration_status_and_send(fake_xmpp, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["telert", "config", "xmpp", "--jid", "sender@example.org", "--password", "supersecret", "--recipient", "to@example.org", "--set-default"])
    cli.main()
    cli.do_status(SimpleNamespace())
    output = capsys.readouterr().out
    assert "XMPP" in output and "supersecret" not in output
    assert telert.send("hello", provider="xmpp") == {"XMPPProvider": True}
