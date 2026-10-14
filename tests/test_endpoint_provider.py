"""Regression tests for custom endpoint payload rendering."""

import unittest
from unittest.mock import Mock, patch

from telert.messaging import EndpointProvider


class EndpointProviderTests(unittest.TestCase):
    def send_with_mock(self, message, *, payload_template=None, method="POST", url=None):
        kwargs = dict(
            url=url or "https://example.invalid/notify",
            method=method,
        )
        if payload_template is not None:
            kwargs["payload_template"] = payload_template
        provider = EndpointProvider(**kwargs)
        with patch(
            "telert.messaging.requests.post", return_value=Mock(status_code=200)
        ) as post:
            with patch(
                "telert.messaging.requests.request", return_value=Mock(status_code=200)
            ) as request:
                self.assertTrue(provider.send(message))
        return post, request

    def test_default_json_payload_escapes_special_characters(self):
        messages = [
            'build finished',
            'build failed: "module not found"',
            "C:\\Users\\admin\\project\\main.py",
            "Traceback:\n  File \"app.py\", line 1\r\n\tError\b\0",
            "Ошибка сборки 🚀 é 漢字",
            "literal {status_code} and {timestamp} in log output",
        ]
        for message in messages:
            with self.subTest(message=repr(message)):
                post, _ = self.send_with_mock(message)
                call = post.call_args.kwargs
                self.assertIn("json", call)
                self.assertNotIn("data", call)
                self.assertEqual(call["json"], {"text": message})

    def test_nested_json_array_string_key_and_unquoted_number(self):
        template = (
            '{"text": "{message}", "status": {status_code}, '
            '"nested": {"items": ["{message}", "Alert: {message}"]}, '
            '"key_{status_code}": true}'
        )
        message = 'hello "world"\nC:\\Temp'
        post, _ = self.send_with_mock(message, payload_template=template)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["text"], message)
        self.assertEqual(payload["status"], 0)
        self.assertIs(type(payload["status"]), int)
        self.assertEqual(payload["nested"]["items"], [message, "Alert: " + message])
        self.assertTrue(payload["key_0"])

    def test_plain_text_templates_send_raw_data_without_escaping(self):
        message = 'failed "build"\nline two {status_code}'
        post, _ = self.send_with_mock(
            message, payload_template="Alert: {message} ({status_code})"
        )
        payload = post.call_args.kwargs
        self.assertNotIn("json", payload)
        self.assertEqual(payload["data"], "Alert: " + message + " (0)")

    def test_bare_message_template_remains_plain_text(self):
        message = 'literal "quotes" and\nnewline'
        post, _ = self.send_with_mock(message, payload_template="{message}")
        self.assertEqual(post.call_args.kwargs["data"], message)

    def test_bare_scalar_templates_preserve_wire_text(self):
        # A JSON-looking message must stay raw text for a bare template.
        for message in ("42", "true", "null", '{"a": 1}', "[1, 2]"):
            with self.subTest(message=message):
                post, _ = self.send_with_mock(message, payload_template="{message}")
                self.assertEqual(post.call_args.kwargs["data"], message)
                self.assertIs(type(post.call_args.kwargs["data"]), str)

        for template, expected in (
            ("{status_code}", "0"),
            ("{duration_seconds}", "0"),
        ):
            with self.subTest(template=template):
                post, _ = self.send_with_mock("something", payload_template=template)
                self.assertEqual(post.call_args.kwargs["data"], expected)

    def test_quoted_plain_text_template_preserves_its_quotes(self):
        post, _ = self.send_with_mock(
            "disk full", payload_template='"Alert: {message}"'
        )
        self.assertEqual(post.call_args.kwargs["data"], '"Alert: disk full"')

    def test_unquoted_message_placeholder_is_always_a_json_string(self):
        for message in ('{"admin": true}', "[1, 2]", "true", "null", "42"):
            with self.subTest(message=message):
                post, _ = self.send_with_mock(
                    message, payload_template='{"raw": {message}}'
                )
                self.assertEqual(post.call_args.kwargs["json"], {"raw": message})

    def test_unquoted_message_placeholder_in_key_does_not_crash(self):
        post, _ = self.send_with_mock(
            "[1, 2]", payload_template="{{message}: 1}"
        )
        self.assertEqual(post.call_args.kwargs["json"], {"[1, 2]": 1})

    def test_timestamp_is_consistent_across_url_and_payload(self):
        provider = EndpointProvider(
            url="https://example.invalid/{timestamp}",
            payload_template='{"timestamp": {timestamp}, "text": "{message}"}',
        )
        with patch("telert.messaging.time.time", side_effect=[100, 101]) as now:
            with patch(
                "telert.messaging.requests.post",
                return_value=Mock(status_code=200),
            ) as post:
                self.assertTrue(provider.send("test"))
        self.assertEqual(post.call_args.args[0], "https://example.invalid/100")
        self.assertEqual(post.call_args.kwargs["json"]["timestamp"], 100)
        now.assert_called_once()

    def test_url_placeholders_not_json_escaped(self):
        url = "https://example.invalid/notify/{status_code}"
        post, _ = self.send_with_mock('failed "quoted"', url=url)
        self.assertEqual(post.call_args.args[0], "https://example.invalid/notify/0")
        self.assertEqual(post.call_args.kwargs["json"]["text"], 'failed "quoted"')

    def test_json_array_payload_uses_json_transport(self):
        template = '["{message}", {"status": {status_code}}]'
        message = 'build "failed"\\nnext line'
        post, _ = self.send_with_mock(message, payload_template=template)
        self.assertEqual(post.call_args.kwargs["json"], [message, {"status": 0}])
        self.assertNotIn("data", post.call_args.kwargs)

    def test_escaped_quotes_in_json_template(self):
        template = r'{"text": "\"{message}\"", "extra": "a\\b"}'
        message = 'backslash \\\\ quote " and newline\\n'
        post, _ = self.send_with_mock(message, payload_template=template)
        self.assertEqual(post.call_args.kwargs["json"]["text"], '"' + message + '"')
        self.assertEqual(post.call_args.kwargs["json"]["extra"], "a\\b")

    def test_unknown_placeholders_are_preserved(self):
        template = '{"text": "{message}", "unknown": "{not_supported}"}'
        post, _ = self.send_with_mock("hello", payload_template=template)
        self.assertEqual(
            post.call_args.kwargs["json"],
            {"text": "hello", "unknown": "{not_supported}"},
        )

    def test_put_uses_json_payload_for_special_characters(self):
        message = 'Quote "line"\nnext'
        _, request = self.send_with_mock(message, method="PUT")
        call = request.call_args
        self.assertEqual(call.args, ("PUT", "https://example.invalid/notify"))
        self.assertEqual(call.kwargs["json"], {"text": message})
        self.assertIsNone(call.kwargs["data"])


if __name__ == "__main__":
    unittest.main()
