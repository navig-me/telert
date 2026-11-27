from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

from telert.messaging import DesktopProvider, NOTIFY_TIMEOUT


@pytest.mark.parametrize(
    "message,title",
    [
        ('Build done ✅ café "q" \\ back', 'Café ✅ "title" \\'),
        ("First line\nSecond line ✅", "Telert"),
        ("Empty-ish title", " "),
        ("-e foo", "Telert"),
    ],
)
@pytest.mark.parametrize("use_system_events", [False, True])
def test_macos_fallback_passes_text_as_argv(message, title, use_system_events):
    provider = DesktopProvider(app_name=title)
    results = [CompletedProcess([], 0, stdout="", stderr="")]
    if use_system_events:
        results.insert(0, CompletedProcess([], 1, stdout="", stderr="unavailable"))

    with patch("telert.messaging.shutil.which", return_value=None) as which, patch(
        "telert.messaging.subprocess.run", side_effect=results
    ) as run:
        assert provider._notify_macos(message)

    which.assert_called_once_with("terminal-notifier")
    statements = ["display notification (item 1 of argv) with title (item 2 of argv)"]
    if use_system_events:
        statements.append(
            'tell application "System Events" to display notification (item 1 of argv) '
            "with title (item 2 of argv)"
        )
    assert run.call_count == len(statements)
    for call, statement in zip(run.call_args_list, statements):
        assert call.args == (
            [
                "osascript", "-e", "on run argv", "-e", statement, "-e", "end run",
                "--", message, title,
            ],
        )
        assert message not in "\n".join(call.args[0][1:7])
        assert call.kwargs == {
            "timeout": NOTIFY_TIMEOUT, "text": True, "capture_output": True,
        }
