#!/usr/bin/env python3
"""
telert – Send alerts from shell commands to Telegram, Teams, or Slack.
Supports multiple modes:
  • **run** mode wraps a command, captures exit status & timing.
  • **filter** mode reads stdin so you can pipe long jobs.
  • **send** mode for simple notifications.

Run `telert --help` or `telert help` for full usage.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap
import time

from telert.messaging import (
    CONFIG_DIR,
    MessagingConfig,
    Provider,
    PushoverProvider,
    configure_provider,
    send_message,
)

CFG_DIR = CONFIG_DIR
CFG_FILE = CFG_DIR / "config.json"

# ───────────────────────────────── helpers ──────────────────────────────────


# Keep these for backward compatibility
def _save(token: str, chat_id: str):
    """Legacy function to save Telegram config for backward compatibility."""
    configure_provider(
        Provider.TELEGRAM, token=token, chat_id=chat_id, set_default=True
    )
    print("✔ Configuration saved →", CFG_FILE)


def _load():
    """Legacy function to load config for backward compatibility."""
    config = MessagingConfig()
    telegram_config = config.get_provider_config(Provider.TELEGRAM)

    if not telegram_config:
        sys.exit("❌ telert is unconfigured – run `telert config …` first.")

    return telegram_config


def _send_telegram(msg: str):
    """Legacy function to send via Telegram for backward compatibility."""
    send_message(msg, Provider.TELEGRAM)


# Alias for backward compatibility, will use the default provider
def _send(msg: str):
    """Send a message using the default provider."""
    send_message(msg)


def _human(sec: float) -> str:
    """Convert seconds to human-readable format."""
    m, s = divmod(int(sec), 60)
    return f"{m} m {s} s" if m else f"{s} s"


# ────────────────────────────── sub‑commands ───────────────────────────────


def do_config(a):
    """Configure the messaging provider."""
    if hasattr(a, "provider") and a.provider:
        provider = a.provider

        if provider == "telegram":
            if not (hasattr(a, "token") and hasattr(a, "chat_id")):
                sys.exit("❌ Telegram configuration requires --token and --chat-id")

            configure_provider(
                Provider.TELEGRAM,
                token=a.token,
                chat_id=a.chat_id,
                set_default=a.set_default,
            )
            print("✔ Telegram configuration saved")

        elif provider == "teams":
            if not hasattr(a, "webhook_url"):
                sys.exit("❌ Teams configuration requires --webhook-url")

            configure_provider(
                Provider.TEAMS, webhook_url=a.webhook_url, set_default=a.set_default
            )
            print("✔ Microsoft Teams configuration saved")

        elif provider == "slack":
            if not hasattr(a, "webhook_url"):
                sys.exit("❌ Slack configuration requires --webhook-url")

            configure_provider(
                Provider.SLACK, webhook_url=a.webhook_url, set_default=a.set_default
            )
            print("✔ Slack configuration saved")

        elif provider == "audio":
            config_params = {"volume": a.volume, "set_default": a.set_default}

            if hasattr(a, "sound_file") and a.sound_file:
                config_params["sound_file"] = a.sound_file

            try:
                configure_provider(Provider.AUDIO, **config_params)
                if hasattr(a, "sound_file") and a.sound_file:
                    print("✔ Audio configuration saved with custom sound file")
                else:
                    print("✔ Audio configuration saved with default sound file")
            except ValueError as e:
                sys.exit(f"❌ {str(e)}")

        elif provider == "desktop":
            config_params = {"app_name": a.app_name, "set_default": a.set_default}

            if hasattr(a, "icon_path") and a.icon_path:
                config_params["icon_path"] = a.icon_path

            try:
                configure_provider(Provider.DESKTOP, **config_params)
                print("✔ Desktop notification configuration saved")
            except ValueError as e:
                sys.exit(f"❌ {str(e)}")
                
        elif provider == "pushover":
            if not (hasattr(a, "token") and hasattr(a, "user")):
                sys.exit("❌ Pushover configuration requires --token and --user")

            configure_provider(
                Provider.PUSHOVER,
                token=a.token,
                user=a.user,
                set_default=a.set_default,
            )
            print("✔ Pushover configuration saved")

        else:
            sys.exit(f"❌ Unknown provider: {provider}")
    else:
        # Legacy Telegram-only config for backward compatibility
        _save(a.token, a.chat_id)


def do_status(a):
    """Show status of configured providers and send a test message."""
    config = MessagingConfig()
    default_provider = config.get_default_provider()

    # Show status for all configured providers
    print("Configured providers:")

    # Check Telegram
    telegram_config = config.get_provider_config(Provider.TELEGRAM)
    if telegram_config:
        default_marker = " (default)" if default_provider == Provider.TELEGRAM else ""
        print(
            f"- Telegram{default_marker}: token={telegram_config['token'][:8]}…, chat_id={telegram_config['chat_id']}"
        )

    # Check Teams
    teams_config = config.get_provider_config(Provider.TEAMS)
    if teams_config:
        default_marker = " (default)" if default_provider == Provider.TEAMS else ""
        webhook = teams_config["webhook_url"]
        print(f"- Microsoft Teams{default_marker}: webhook={webhook[:20]}…")

    # Check Slack
    slack_config = config.get_provider_config(Provider.SLACK)
    if slack_config:
        default_marker = " (default)" if default_provider == Provider.SLACK else ""
        webhook = slack_config["webhook_url"]
        print(f"- Slack{default_marker}: webhook={webhook[:20]}…")

    # Check Audio
    audio_config = config.get_provider_config(Provider.AUDIO)
    if audio_config:
        default_marker = " (default)" if default_provider == Provider.AUDIO else ""
        sound_file = audio_config["sound_file"]
        volume = audio_config.get("volume", 1.0)
        print(f"- Audio{default_marker}: sound_file={sound_file}, volume={volume}")

    # Check Desktop
    desktop_config = config.get_provider_config(Provider.DESKTOP)
    if desktop_config:
        default_marker = " (default)" if default_provider == Provider.DESKTOP else ""
        app_name = desktop_config.get("app_name", "Telert")
        icon_info = (
            f", icon={desktop_config['icon_path']}"
            if "icon_path" in desktop_config
            else ""
        )
        print(f"- Desktop{default_marker}: app_name={app_name}{icon_info}")

    # Check Pushover
    pushover_config = config.get_provider_config(Provider.PUSHOVER)
    if pushover_config:
        default_marker = " (default)" if default_provider == Provider.PUSHOVER else ""
        token = pushover_config["token"]
        user = pushover_config["user"]
        print(f"- Pushover{default_marker}: token={token[:8]}…, user={user[:8]}…")

    # If none configured, show warning
    if not (
        telegram_config
        or teams_config
        or slack_config
        or audio_config
        or desktop_config
        or pushover_config
    ):
        print("No providers configured. Use `telert config` to set up a provider.")
        return

    # Send test message if requested
    provider_to_test = None
    if hasattr(a, "provider") and a.provider:
        try:
            provider_to_test = Provider.from_string(a.provider)
        except ValueError:
            sys.exit(f"❌ Unknown provider: {a.provider}")

    if provider_to_test:
        if not config.is_provider_configured(provider_to_test):
            sys.exit(f"❌ Provider {provider_to_test} is not configured")

        try:
            send_message("✅ telert status OK", provider_to_test)
            print(f"sent: test message via {provider_to_test.value}")
        except Exception as e:
            sys.exit(
                f"❌ Failed to send message via {provider_to_test.value}: {str(e)}"
            )
    else:
        # Use default provider
        try:
            send_message("✅ telert status OK")
            provider_name = (
                default_provider.value if default_provider else "default provider"
            )
            print(f"sent: test message via {provider_name}")
        except Exception as e:
            sys.exit(f"❌ Failed to send message: {str(e)}")


def do_hook(a):
    """Generate a shell hook for command notifications."""
    t = a.longer_than
    print(
        textwrap.dedent(f"""
        telert_preexec() {{ TELERT_CMD=\"$BASH_COMMAND\"; TELERT_START=$EPOCHSECONDS; }}
        telert_precmd()  {{ local st=$?; local d=$((EPOCHSECONDS-TELERT_START));
          if (( d >= {t} )); then telert send \"$TELERT_CMD exited $st in $(printf '%dm%02ds' $((d/60)) $((d%60)))\"; fi; }}
        trap telert_preexec DEBUG
        PROMPT_COMMAND=telert_precmd:$PROMPT_COMMAND
    """).strip()
    )


def do_send(a):
    """Send a simple message."""
    provider = None
    if hasattr(a, "provider") and a.provider:
        try:
            provider = Provider.from_string(a.provider)
        except ValueError:
            sys.exit(f"❌ Unknown provider: {a.provider}")

    try:
        send_message(a.text, provider)
    except Exception as e:
        sys.exit(f"❌ Failed to send message: {str(e)}")


def do_run(a):
    """Run a command and send notification when it completes."""
    start = time.time()

    # Check if we should suppress output
    silent_mode = os.environ.get("TELERT_SILENT") == "1"

    if silent_mode:
        # Capture output when in silent mode
        proc = subprocess.run(a.cmd, text=True, capture_output=True)
        # Output will be included only in notification
    else:
        # Show output in real-time by not capturing
        proc = subprocess.run(a.cmd, text=True)

    dur = _human(time.time() - start)
    status = proc.returncode
    label = a.label or " ".join(a.cmd)

    # Exit early if only notifying on failure and command succeeded
    if a.only_fail and status == 0:
        sys.exit(status)

    # Prepare message
    msg = a.message or f"{label} finished with exit {status} in {dur}"

    # Add captured output to notification if in silent mode
    if silent_mode and hasattr(proc, "stdout") and hasattr(proc, "stderr"):
        # Add stdout with size limits for safety
        if proc.stdout and proc.stdout.strip():
            stdout_lines = proc.stdout.splitlines()[:20]  # Limit to 20 lines
            stdout_text = "\n".join(stdout_lines)

            # Limit each line length
            if len(stdout_text) > 3900:
                stdout_text = stdout_text[:3897] + "..."

            msg += "\n\n--- stdout ---\n" + stdout_text

        # Add stderr with size limits for safety
        if proc.stderr and proc.stderr.strip():
            stderr_lines = proc.stderr.splitlines()[:20]  # Limit to 20 lines
            stderr_text = "\n".join(stderr_lines)

            # Limit each line length
            if len(stderr_text) > 3900:
                stderr_text = stderr_text[:3897] + "..."

            msg += "\n\n--- stderr ---\n" + stderr_text

    # Send message with specified provider or default
    provider = None
    if hasattr(a, "provider") and a.provider:
        try:
            provider = Provider.from_string(a.provider)
        except ValueError:
            sys.exit(f"❌ Unknown provider: {a.provider}")

    try:
        send_message(msg, provider)
    except Exception as e:
        print(f"❌ Failed to send notification: {str(e)}", file=sys.stderr)

    sys.exit(status)


# ───────────────────────────── pipeline filter ─────────────────────────────


def piped_mode():
    """Handle input from a pipeline and send notification."""
    data = sys.stdin.read()
    msg = sys.argv[1] if len(sys.argv) > 1 else "Pipeline finished"

    # Check for provider specification (supports both --provider=slack and --provider slack formats)
    provider = None
    skip_next = False
    provider_index = -1

    for i, arg in enumerate(sys.argv[1:], 1):
        if skip_next:
            skip_next = False
            continue

        # Handle --provider=slack format
        if arg.startswith("--provider="):
            provider_name = arg.split("=", 1)[1]
            provider_index = i
            try:
                provider = Provider.from_string(provider_name)
            except ValueError:
                sys.exit(f"❌ Unknown provider: {provider_name}")
            break

        # Handle --provider slack format
        if arg == "--provider":
            if i + 1 < len(sys.argv):
                provider_name = sys.argv[i + 1]
                provider_index = i
                try:
                    provider = Provider.from_string(provider_name)
                    skip_next = True
                except ValueError:
                    sys.exit(f"❌ Unknown provider: {provider_name}")
                break

    # Update message if provider was the first argument
    if provider_index == 1:
        # Skip 2 positions if using space format, 1 if using equals format
        skip = 2 if skip_next else 1
        msg = sys.argv[skip + 1] if len(sys.argv) > skip + 1 else "Pipeline finished"

    # Format the message
    if len(sys.argv) > 2 and not any(
        arg.startswith("--provider=") for arg in sys.argv[1:3]
    ):
        msg += f" (exit {sys.argv[2]})"

    if data.strip():
        msg += "\n\n--- output ---\n" + "\n".join(data.splitlines()[:20])[:3900]

    # Send the message
    try:
        send_message(msg, provider)
    except Exception as e:
        sys.exit(f"❌ Failed to send message: {str(e)}")


# ──────────────────────────────── entrypoint ───────────────────────────────


def main():
    """Main entry point for the CLI."""
    if not sys.stdin.isatty():
        piped_mode()
        return

    p = argparse.ArgumentParser(
        prog="telert",
        description="Send alerts when commands finish (supports multiple messaging providers).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sp = p.add_subparsers(dest="cmd", required=True)

    # config
    c = sp.add_parser("config", help="configure messaging providers")
    c_subparsers = c.add_subparsers(dest="provider", help="provider to configure")

    # Telegram config
    telegram_parser = c_subparsers.add_parser("telegram", help="configure Telegram")
    telegram_parser.add_argument(
        "--token", required=True, help="bot token from @BotFather"
    )
    telegram_parser.add_argument(
        "--chat-id", required=True, help="chat ID to send messages to"
    )
    telegram_parser.add_argument(
        "--set-default", action="store_true", help="set as default provider"
    )

    # Teams config
    teams_parser = c_subparsers.add_parser("teams", help="configure Microsoft Teams")
    teams_parser.add_argument(
        "--webhook-url", required=True, help="incoming webhook URL"
    )
    teams_parser.add_argument(
        "--set-default", action="store_true", help="set as default provider"
    )

    # Slack config
    slack_parser = c_subparsers.add_parser("slack", help="configure Slack")
    slack_parser.add_argument(
        "--webhook-url", required=True, help="incoming webhook URL"
    )
    slack_parser.add_argument(
        "--set-default", action="store_true", help="set as default provider"
    )

    # Audio config
    audio_parser = c_subparsers.add_parser("audio", help="configure Audio alerts")
    audio_parser.add_argument(
        "--sound-file",
        help="path to sound file (.mp3 or .wav) (default: built-in MP3 sound)",
    )
    audio_parser.add_argument(
        "--volume", type=float, default=1.0, help="volume level (0.0-1.0)"
    )
    audio_parser.add_argument(
        "--set-default", action="store_true", help="set as default provider"
    )

    # Desktop config
    desktop_parser = c_subparsers.add_parser(
        "desktop", help="configure Desktop notifications"
    )
    desktop_parser.add_argument(
        "--app-name", default="Telert", help="application name shown in notifications"
    )
    desktop_parser.add_argument(
        "--icon-path",
        help="path to icon file for the notification (default: built-in icon)",
    )
    desktop_parser.add_argument(
        "--set-default", action="store_true", help="set as default provider"
    )
    
    # Pushover config
    pushover_parser = c_subparsers.add_parser(
        "pushover", help="configure Pushover notifications"
    )
    pushover_parser.add_argument(
        "--token", required=True, help="application token from Pushover.net"
    )
    pushover_parser.add_argument(
        "--user", required=True, help="user key from Pushover.net"
    )
    pushover_parser.add_argument(
        "--set-default", action="store_true", help="set as default provider"
    )

    # Legacy Telegram config (for backward compatibility)
    c.add_argument("--token", help="(legacy) Telegram bot token")
    c.add_argument("--chat-id", help="(legacy) Telegram chat ID")

    c.set_defaults(func=do_config)

    # status
    st = sp.add_parser("status", help="show configuration and send test message")
    st.add_argument(
        "--provider",
        choices=["telegram", "teams", "slack", "audio", "desktop", "pushover"],
        help="provider to test (default: use configured default)",
    )
    st.set_defaults(func=do_status)

    # hook
    hk = sp.add_parser("hook", help="emit Bash hook for all commands")
    hk.add_argument(
        "--longer-than",
        "-l",
        type=int,
        default=10,
        help="minimum duration in seconds to trigger notification",
    )
    hk.set_defaults(func=do_hook)

    # send
    sd = sp.add_parser("send", help="send arbitrary text")
    sd.add_argument("text", help="message to send")
    sd.add_argument(
        "--provider",
        choices=["telegram", "teams", "slack", "audio", "desktop", "pushover"],
        help="provider to use (default: use configured default)",
    )
    sd.set_defaults(func=do_send)

    # run
    rn = sp.add_parser("run", help="run a command & notify when done")
    rn.add_argument("--label", "-L", help="friendly name for the command")
    rn.add_argument("--message", "-m", help="override default notification text")
    rn.add_argument(
        "--only-fail", action="store_true", help="notify only on non‑zero exit"
    )
    rn.add_argument(
        "--provider",
        choices=["telegram", "teams", "slack", "audio", "desktop", "pushover"],
        help="provider to use (default: use configured default)",
    )
    rn.add_argument(
        "cmd", nargs=argparse.REMAINDER, help="command to execute -- required"
    )
    rn.set_defaults(func=do_run)

    # help alias
    hp = sp.add_parser("help", help="show global help")
    hp.set_defaults(func=lambda _a: p.print_help())

    args = p.parse_args()
    if getattr(args, "cmd", None) == [] and getattr(args, "func", None) is do_run:
        p.error("run: missing command – use telert run -- <cmd> …")
    args.func(args)


if __name__ == "__main__":
    main()
