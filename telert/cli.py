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

        # Check if we're configuring defaults (new command)
        if provider == "set-defaults":
            if not hasattr(a, "providers") or not a.providers:
                sys.exit("❌ You must specify at least one provider with --providers")

            # Parse the providers list
            provider_list = []
            for p in a.providers.split(","):
                try:
                    provider_list.append(Provider.from_string(p.strip()))
                except ValueError:
                    sys.exit(f"❌ Unknown provider: {p.strip()}")

            # Set the defaults
            config = MessagingConfig()
            config.set_default_providers(provider_list)

            # Print confirmation
            providers_str = ", ".join([p.value for p in provider_list])
            print(f"✔ Default providers set: {providers_str}")

            # Exit the function since we're done
            return

        # Single provider configuration
        if provider == "discord":
            if not hasattr(a, "webhook_url"):
                sys.exit("❌ Discord configuration requires --webhook-url")
                
            config_params = {
                "webhook_url": a.webhook_url,
                "set_default": a.set_default,
                "add_to_defaults": a.add_to_defaults,
            }
            
            if hasattr(a, "username") and a.username:
                config_params["username"] = a.username
                
            if hasattr(a, "avatar_url") and a.avatar_url:
                config_params["avatar_url"] = a.avatar_url
                
            configure_provider(Provider.DISCORD, **config_params)
            print("✔ Discord configuration saved")
            
        elif provider == "telegram":
            if not (hasattr(a, "token") and hasattr(a, "chat_id")):
                sys.exit("❌ Telegram configuration requires --token and --chat-id")

            configure_provider(
                Provider.TELEGRAM,
                token=a.token,
                chat_id=a.chat_id,
                set_default=a.set_default,
                add_to_defaults=a.add_to_defaults,
            )
            print("✔ Telegram configuration saved")

        elif provider == "teams":
            if not hasattr(a, "webhook_url"):
                sys.exit("❌ Teams configuration requires --webhook-url")

            configure_provider(
                Provider.TEAMS,
                webhook_url=a.webhook_url,
                set_default=a.set_default,
                add_to_defaults=a.add_to_defaults,
            )
            print("✔ Microsoft Teams configuration saved")

        elif provider == "slack":
            if not hasattr(a, "webhook_url"):
                sys.exit("❌ Slack configuration requires --webhook-url")

            configure_provider(
                Provider.SLACK,
                webhook_url=a.webhook_url,
                set_default=a.set_default,
                add_to_defaults=a.add_to_defaults,
            )
            print("✔ Slack configuration saved")

        elif provider == "audio":
            config_params = {
                "volume": a.volume,
                "set_default": a.set_default,
                "add_to_defaults": a.add_to_defaults,
            }

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
            config_params = {
                "app_name": a.app_name,
                "set_default": a.set_default,
                "add_to_defaults": a.add_to_defaults,
            }

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
                add_to_defaults=a.add_to_defaults,
            )
            print("✔ Pushover configuration saved")

        elif provider == "endpoint":
            if not hasattr(a, "url"):
                sys.exit("❌ Endpoint configuration requires --url")

            # Build configuration params
            config_params = {
                "url": a.url,
                "set_default": a.set_default,
                "add_to_defaults": a.add_to_defaults,
            }

            if hasattr(a, "method") and a.method:
                config_params["method"] = a.method

            if hasattr(a, "payload_template") and a.payload_template:
                config_params["payload_template"] = a.payload_template

            if hasattr(a, "name") and a.name:
                config_params["name"] = a.name

            if hasattr(a, "timeout") and a.timeout:
                config_params["timeout"] = a.timeout

            # Handle headers
            headers = {}
            if hasattr(a, "header") and a.header:
                for header in a.header:
                    if ":" in header:
                        key, value = header.split(":", 1)
                        headers[key.strip()] = value.strip()
                    else:
                        sys.exit(
                            f"❌ Invalid header format: {header}. Use 'Key: Value' format."
                        )

            if headers:
                config_params["headers"] = headers

            try:
                configure_provider(Provider.ENDPOINT, **config_params)
                print(f"✔ Endpoint configuration saved: {a.name or 'Custom Endpoint'}")
            except ValueError as e:
                sys.exit(f"❌ {str(e)}")

        else:
            sys.exit(f"❌ Unknown provider: {provider}")
    else:
        # Legacy Telegram-only config for backward compatibility
        _save(a.token, a.chat_id)


def do_status(a):
    """Show status of configured providers and send a test message."""
    config = MessagingConfig()
    default_providers = config.get_default_providers()

    # Convert to list of strings for easier checks
    default_provider_names = [p.value for p in default_providers]

    # Show status for all configured providers
    print("Configured providers:")

    # Check Telegram
    telegram_config = config.get_provider_config(Provider.TELEGRAM)
    if telegram_config:
        # Mark as default if in default providers list
        if Provider.TELEGRAM.value in default_provider_names:
            # Show priority if multiple defaults
            if len(default_provider_names) > 1:
                priority = default_provider_names.index(Provider.TELEGRAM.value) + 1
                default_marker = f" (default #{priority})"
            else:
                default_marker = " (default)"
        else:
            default_marker = ""

        print(
            f"- Telegram{default_marker}: token={telegram_config['token'][:8]}…, chat_id={telegram_config['chat_id']}"
        )

    # Check Teams
    teams_config = config.get_provider_config(Provider.TEAMS)
    if teams_config:
        # Mark as default if in default providers list
        if Provider.TEAMS.value in default_provider_names:
            # Show priority if multiple defaults
            if len(default_provider_names) > 1:
                priority = default_provider_names.index(Provider.TEAMS.value) + 1
                default_marker = f" (default #{priority})"
            else:
                default_marker = " (default)"
        else:
            default_marker = ""

        webhook = teams_config["webhook_url"]
        print(f"- Microsoft Teams{default_marker}: webhook={webhook[:20]}…")

    # Check Slack
    slack_config = config.get_provider_config(Provider.SLACK)
    if slack_config:
        # Mark as default if in default providers list
        if Provider.SLACK.value in default_provider_names:
            # Show priority if multiple defaults
            if len(default_provider_names) > 1:
                priority = default_provider_names.index(Provider.SLACK.value) + 1
                default_marker = f" (default #{priority})"
            else:
                default_marker = " (default)"
        else:
            default_marker = ""

        webhook = slack_config["webhook_url"]
        print(f"- Slack{default_marker}: webhook={webhook[:20]}…")

    # Check Audio
    audio_config = config.get_provider_config(Provider.AUDIO)
    if audio_config:
        # Mark as default if in default providers list
        if Provider.AUDIO.value in default_provider_names:
            # Show priority if multiple defaults
            if len(default_provider_names) > 1:
                priority = default_provider_names.index(Provider.AUDIO.value) + 1
                default_marker = f" (default #{priority})"
            else:
                default_marker = " (default)"
        else:
            default_marker = ""

        sound_file = audio_config["sound_file"]
        volume = audio_config.get("volume", 1.0)
        print(f"- Audio{default_marker}: sound_file={sound_file}, volume={volume}")

    # Check Desktop
    desktop_config = config.get_provider_config(Provider.DESKTOP)
    if desktop_config:
        # Mark as default if in default providers list
        if Provider.DESKTOP.value in default_provider_names:
            # Show priority if multiple defaults
            if len(default_provider_names) > 1:
                priority = default_provider_names.index(Provider.DESKTOP.value) + 1
                default_marker = f" (default #{priority})"
            else:
                default_marker = " (default)"
        else:
            default_marker = ""

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
        # Mark as default if in default providers list
        if Provider.PUSHOVER.value in default_provider_names:
            # Show priority if multiple defaults
            if len(default_provider_names) > 1:
                priority = default_provider_names.index(Provider.PUSHOVER.value) + 1
                default_marker = f" (default #{priority})"
            else:
                default_marker = " (default)"
        else:
            default_marker = ""

        token = pushover_config["token"]
        user = pushover_config["user"]
        print(f"- Pushover{default_marker}: token={token[:8]}…, user={user[:8]}…")

    # Check Endpoint
    endpoint_config = config.get_provider_config(Provider.ENDPOINT)
    if endpoint_config:
        # Mark as default if in default providers list
        if Provider.ENDPOINT.value in default_provider_names:
            # Show priority if multiple defaults
            if len(default_provider_names) > 1:
                priority = default_provider_names.index(Provider.ENDPOINT.value) + 1
                default_marker = f" (default #{priority})"
            else:
                default_marker = " (default)"
        else:
            default_marker = ""

        name = endpoint_config.get("name", "Custom Endpoint")
        url = endpoint_config["url"]
        method = endpoint_config.get("method", "POST")
        timeout = endpoint_config.get("timeout", 20)
        print(
            f"- {name}{default_marker}: url={url[:30]}…, method={method}, timeout={timeout}s"
        )

    # Check Discord
    discord_config = config.get_provider_config(Provider.DISCORD)
    if discord_config:
        # Mark as default if in default providers list
        if Provider.DISCORD.value in default_provider_names:
            # Show priority if multiple defaults
            if len(default_provider_names) > 1:
                priority = default_provider_names.index(Provider.DISCORD.value) + 1
                default_marker = f" (default #{priority})"
            else:
                default_marker = " (default)"
        else:
            default_marker = ""

        webhook = discord_config["webhook_url"]
        username = discord_config.get("username", "Telert")
        avatar_info = (
            f", avatar={discord_config['avatar_url'][:20]}…"
            if "avatar_url" in discord_config
            else ""
        )
        print(f"- Discord{default_marker}: webhook={webhook[:20]}…, username={username}{avatar_info}")

    # If none configured, show warning
    if not (
        telegram_config
        or teams_config
        or slack_config
        or audio_config
        or desktop_config
        or pushover_config
        or endpoint_config
        or discord_config
    ):
        print("No providers configured. Use `telert config` to set up a provider.")
        return

    # Show environment variable information
    env_default = os.environ.get("TELERT_DEFAULT_PROVIDER")
    if env_default:
        print(f"\nEnvironment variable TELERT_DEFAULT_PROVIDER={env_default}")

    # Send test message if requested
    if hasattr(a, "provider") and a.provider:
        # Handle all-providers option
        if a.provider == "all":
            try:
                results = send_message("✅ telert status OK", all_providers=True)
                print("sent: test message to all providers")
                # Show results for each provider
                for provider_name, success in results.items():
                    status = "✅ success" if success else "❌ failed"
                    print(f"  - {provider_name}: {status}")
            except Exception as e:
                sys.exit(f"❌ Failed to send message: {str(e)}")
        else:
            # Handle multiple providers (comma-separated)
            if "," in a.provider:
                providers_to_test = []
                for p in a.provider.split(","):
                    try:
                        providers_to_test.append(Provider.from_string(p.strip()))
                    except ValueError:
                        sys.exit(f"❌ Unknown provider: {p.strip()}")

                # Send to all specified providers
                try:
                    results = send_message("✅ telert status OK", providers_to_test)
                    print("sent: test message to multiple providers")
                    # Show results for each provider
                    for provider_name, success in results.items():
                        status = "✅ success" if success else "❌ failed"
                        print(f"  - {provider_name}: {status}")
                except Exception as e:
                    sys.exit(f"❌ Failed to send message: {str(e)}")
            else:
                # Single provider
                try:
                    provider_to_test = Provider.from_string(a.provider)
                    if not config.is_provider_configured(provider_to_test):
                        sys.exit(
                            f"❌ Provider {provider_to_test.value} is not configured"
                        )

                    send_message("✅ telert status OK", provider_to_test)
                    print(f"sent: test message via {provider_to_test.value}")
                except ValueError:
                    sys.exit(f"❌ Unknown provider: {a.provider}")
                except Exception as e:
                    sys.exit(f"❌ Failed to send message via {a.provider}: {str(e)}")
    else:
        # Use default provider(s)
        try:
            if len(default_providers) > 1:
                results = send_message("✅ telert status OK")
                print("sent: test message to default providers")
                # Show results for each provider
                for provider_name, success in results.items():
                    status = "✅ success" if success else "❌ failed"
                    print(f"  - {provider_name}: {status}")
            else:
                send_message("✅ telert status OK")
                provider_name = (
                    default_provider_names[0]
                    if default_provider_names
                    else "default provider"
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
    all_providers = False

    # First check if all_providers flag is set
    if hasattr(a, "all_providers") and a.all_providers:
        all_providers = True
    # Then check for provider argument
    elif hasattr(a, "provider") and a.provider:
        # Handle all option
        if a.provider.lower() == "all":
            all_providers = True
        # Handle multiple providers (comma-separated)
        elif "," in a.provider:
            providers_to_use = []
            for p in a.provider.split(","):
                try:
                    providers_to_use.append(Provider.from_string(p.strip()))
                except ValueError:
                    sys.exit(f"❌ Unknown provider: {p.strip()}")
            provider = providers_to_use
        # Single provider
        else:
            try:
                provider = Provider.from_string(a.provider)
            except ValueError:
                sys.exit(f"❌ Unknown provider: {a.provider}")

    try:
        results = send_message(a.text, provider, all_providers)
        # Always show a basic success message
        if results:
            providers_str = ", ".join(results.keys())
            print(f"✓ Telert sent a message to: {providers_str}")

        # Show detailed results for each provider if verbose or multiple providers used
        if hasattr(a, "verbose") and a.verbose or len(results) > 1:
            for provider_name, success in results.items():
                status = "✅ success" if success else "❌ failed"
                print(f"  - {provider_name}: {status}")
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

    # Process provider options
    provider = None
    all_providers = False

    # First check if all_providers flag is set
    if hasattr(a, "all_providers") and a.all_providers:
        all_providers = True
    # Then check for provider argument
    elif hasattr(a, "provider") and a.provider:
        # Handle all option
        if a.provider.lower() == "all":
            all_providers = True
        # Handle multiple providers (comma-separated)
        elif "," in a.provider:
            providers_to_use = []
            for p in a.provider.split(","):
                try:
                    providers_to_use.append(Provider.from_string(p.strip()))
                except ValueError:
                    sys.exit(f"❌ Unknown provider: {p.strip()}")
            provider = providers_to_use
        # Single provider
        else:
            try:
                provider = Provider.from_string(a.provider)
            except ValueError:
                sys.exit(f"❌ Unknown provider: {a.provider}")

    # Send notification
    try:
        results = send_message(msg, provider, all_providers)
        if results:
            providers_str = ", ".join(results.keys())
            print(f"✓ Telert sent a message to: {providers_str}")
    except Exception as e:
        print(f"❌ Failed to send notification: {str(e)}", file=sys.stderr)

    sys.exit(status)


# ───────────────────────────── pipeline filter ─────────────────────────────


def piped_mode():
    """Handle input from a pipeline and send notification."""
    data = sys.stdin.read()
    msg = sys.argv[1] if len(sys.argv) > 1 else "Pipeline finished"

    # Check for provider specification
    # We support three formats:
    # --provider=slack
    # --provider slack
    # --provider=slack,teams
    # --provider slack,teams
    # --provider=all
    # --all-providers
    provider = None
    all_providers = False
    skip_next = False
    provider_index = -1

    for i, arg in enumerate(sys.argv[1:], 1):
        if skip_next:
            skip_next = False
            continue

        # Handle --all-providers flag
        if arg == "--all-providers":
            all_providers = True
            provider_index = i
            break

        # Handle --provider=slack format
        if arg.startswith("--provider="):
            provider_name = arg.split("=", 1)[1]
            provider_index = i

            # Check for "all" provider
            if provider_name.lower() == "all":
                all_providers = True
            # Check for multiple providers (comma-separated)
            elif "," in provider_name:
                providers_list = []
                for p in provider_name.split(","):
                    try:
                        providers_list.append(Provider.from_string(p.strip()))
                    except ValueError:
                        sys.exit(f"❌ Unknown provider: {p.strip()}")
                provider = providers_list
            # Single provider
            else:
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

                # Check for "all" provider
                if provider_name.lower() == "all":
                    all_providers = True
                    skip_next = True
                # Check for multiple providers (comma-separated)
                elif "," in provider_name:
                    providers_list = []
                    for p in provider_name.split(","):
                        try:
                            providers_list.append(Provider.from_string(p.strip()))
                        except ValueError:
                            sys.exit(f"❌ Unknown provider: {p.strip()}")
                    provider = providers_list
                    skip_next = True
                # Single provider
                else:
                    try:
                        provider = Provider.from_string(provider_name)
                        skip_next = True
                    except ValueError:
                        sys.exit(f"❌ Unknown provider: {provider_name}")
                break

    # Update message if provider was the first argument
    if provider_index == 1:
        # Skip positions based on format used
        if arg == "--all-providers":
            skip = 1
        elif arg.startswith("--provider="):
            skip = 1
        else:  # --provider <name>
            skip = 2

        msg = sys.argv[skip + 1] if len(sys.argv) > skip + 1 else "Pipeline finished"

    # Format the message
    if len(sys.argv) > 2 and not any(
        arg.startswith("--provider=") or arg == "--provider" or arg == "--all-providers"
        for arg in sys.argv[1:3]
    ):
        msg += f" (exit {sys.argv[2]})"

    if data.strip():
        msg += "\n\n--- output ---\n" + "\n".join(data.splitlines()[:20])[:3900]

    # Send the message
    try:
        results = send_message(msg, provider, all_providers)
        if results:
            providers_str = ", ".join(results.keys())
            print(f"✓ Telert sent a message to: {providers_str}")
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

    # Set defaults command (new)
    set_defaults_parser = c_subparsers.add_parser(
        "set-defaults", help="set multiple default providers in priority order"
    )
    set_defaults_parser.add_argument(
        "--providers",
        required=True,
        help="comma-separated list of providers to use as defaults, in priority order",
    )

    # Telegram config
    telegram_parser = c_subparsers.add_parser("telegram", help="configure Telegram")
    telegram_parser.add_argument(
        "--token", required=True, help="bot token from @BotFather"
    )
    telegram_parser.add_argument(
        "--chat-id", required=True, help="chat ID to send messages to"
    )
    telegram_parser.add_argument(
        "--set-default", action="store_true", help="set as the only default provider"
    )
    telegram_parser.add_argument(
        "--add-to-defaults",
        action="store_true",
        help="add to existing default providers",
    )

    # Teams config
    teams_parser = c_subparsers.add_parser("teams", help="configure Microsoft Teams")
    teams_parser.add_argument(
        "--webhook-url", required=True, help="incoming webhook URL"
    )
    teams_parser.add_argument(
        "--set-default", action="store_true", help="set as the only default provider"
    )
    teams_parser.add_argument(
        "--add-to-defaults",
        action="store_true",
        help="add to existing default providers",
    )

    # Slack config
    slack_parser = c_subparsers.add_parser("slack", help="configure Slack")
    slack_parser.add_argument(
        "--webhook-url", required=True, help="incoming webhook URL"
    )
    slack_parser.add_argument(
        "--set-default", action="store_true", help="set as the only default provider"
    )
    slack_parser.add_argument(
        "--add-to-defaults",
        action="store_true",
        help="add to existing default providers",
    )
    
    # Discord config
    discord_parser = c_subparsers.add_parser("discord", help="configure Discord")
    discord_parser.add_argument(
        "--webhook-url", required=True, help="incoming webhook URL"
    )
    discord_parser.add_argument(
        "--username", help="name to display for the webhook bot (default: Telert)"
    )
    discord_parser.add_argument(
        "--avatar-url", help="URL for the webhook bot's avatar image"
    )
    discord_parser.add_argument(
        "--set-default", action="store_true", help="set as the only default provider"
    )
    discord_parser.add_argument(
        "--add-to-defaults",
        action="store_true",
        help="add to existing default providers",
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
        "--set-default", action="store_true", help="set as the only default provider"
    )
    audio_parser.add_argument(
        "--add-to-defaults",
        action="store_true",
        help="add to existing default providers",
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
        "--set-default", action="store_true", help="set as the only default provider"
    )
    desktop_parser.add_argument(
        "--add-to-defaults",
        action="store_true",
        help="add to existing default providers",
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
        "--set-default", action="store_true", help="set as the only default provider"
    )
    pushover_parser.add_argument(
        "--add-to-defaults",
        action="store_true",
        help="add to existing default providers",
    )

    # Endpoint config
    endpoint_parser = c_subparsers.add_parser(
        "endpoint", help="configure custom HTTP endpoint notifications"
    )
    endpoint_parser.add_argument(
        "--url",
        required=True,
        help="URL to send notifications to (supports placeholders like {message}, {status_code}, {duration_seconds})",
    )
    endpoint_parser.add_argument(
        "--method",
        default="POST",
        choices=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
        help="HTTP method to use (default: POST)",
    )
    endpoint_parser.add_argument(
        "--header",
        action="append",
        help="HTTP header in 'Key: Value' format (can be specified multiple times)",
    )
    endpoint_parser.add_argument(
        "--payload-template",
        help='JSON payload template with placeholders (default: \'{"text": "{message}"}\')',
    )
    endpoint_parser.add_argument(
        "--name", default="Custom Endpoint", help="friendly name for this endpoint"
    )
    endpoint_parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="request timeout in seconds (default: 20)",
    )
    endpoint_parser.add_argument(
        "--set-default", action="store_true", help="set as the only default provider"
    )
    endpoint_parser.add_argument(
        "--add-to-defaults",
        action="store_true",
        help="add to existing default providers",
    )

    # Legacy Telegram config (for backward compatibility)
    c.add_argument("--token", help="(legacy) Telegram bot token")
    c.add_argument("--chat-id", help="(legacy) Telegram chat ID")

    c.set_defaults(func=do_config)

    # status
    st = sp.add_parser("status", help="show configuration and send test message")
    st.add_argument(
        "--provider",
        help="provider(s) to test - can be a single provider, 'all', or comma-separated list (default: use configured default)",
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
        help="provider(s) to use - can be a single provider, 'all', or comma-separated list (default: use configured default)",
    )
    sd.add_argument(
        "--all-providers",
        action="store_true",
        help="send to all configured providers",
    )
    sd.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="show detailed results for each provider",
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
        help="provider(s) to use - can be a single provider, 'all', or comma-separated list (default: use configured default)",
    )
    rn.add_argument(
        "--all-providers",
        action="store_true",
        help="send to all configured providers",
    )
    rn.add_argument(
        "cmd", nargs=argparse.REMAINDER, help="command to execute -- required"
    )
    rn.set_defaults(func=do_run)

    def do_help(_):
        p.print_help()
        
def do_completions(a):
    """Generate shell completions."""
    import os
    import pathlib
    
    # Store completions content
    bash_completion = '''#!/usr/bin/env bash
# Bash completion for telert

_telert_completion() {
    local cur prev words cword
    _init_completion || return

    # List of primary commands
    local commands="run send config status hook help completions"
    
    # List of providers
    local providers="telegram teams slack discord pushover audio desktop endpoint"
    
    # List of config commands
    local config_commands="telegram teams slack discord pushover audio desktop endpoint set-defaults"
    
    # Standard options for most commands
    local options="--provider --all-providers --verbose --help"

    # Handle different positions in the command line
    if [[ $cword -eq 1 ]]; then
        # Complete primary commands
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return 0
    fi

    # Handle subcommands
    case "${words[1]}" in
        run)
            # Options for 'run'
            COMPREPLY=($(compgen -W "$options --label --only-fail --message" -- "$cur"))
            ;;
        send)
            # Options for 'send'
            COMPREPLY=($(compgen -W "$options" -- "$cur"))
            ;;
        config)
            if [[ $cword -eq 2 ]]; then
                # Complete config subcommands
                COMPREPLY=($(compgen -W "$config_commands" -- "$cur"))
            elif [[ $cword -ge 3 ]]; then
                # Options based on the provider
                case "${words[2]}" in
                    telegram)
                        COMPREPLY=($(compgen -W "--token --chat-id --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    teams|slack|discord)
                        COMPREPLY=($(compgen -W "--webhook-url --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    pushover)
                        COMPREPLY=($(compgen -W "--token --user --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    audio)
                        COMPREPLY=($(compgen -W "--sound-file --volume --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    desktop)
                        COMPREPLY=($(compgen -W "--app-name --icon-path --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    endpoint)
                        COMPREPLY=($(compgen -W "--url --method --header --payload-template --name --timeout --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    set-defaults)
                        COMPREPLY=($(compgen -W "--providers" -- "$cur"))
                        ;;
                esac
            fi
            ;;
        hook)
            # Options for 'hook'
            COMPREPLY=($(compgen -W "--long -l --provider --all-providers" -- "$cur"))
            ;;
        status)
            # Options for 'status'
            COMPREPLY=($(compgen -W "--provider --all-providers" -- "$cur"))
            ;;
        completions)
            # Options for 'completions'
            COMPREPLY=($(compgen -W "--shell --output-dir" -- "$cur"))
            ;;
        help)
            # Complete primary commands for help
            COMPREPLY=($(compgen -W "$commands" -- "$cur"))
            ;;
    esac

    # Handle options that expect a provider as value
    if [[ "$prev" == "--provider" ]]; then
        COMPREPLY=($(compgen -W "$providers" -- "$cur"))
        return 0
    fi

    return 0
}

complete -F _telert_completion telert
'''

    zsh_completion = '''#compdef telert
# Zsh completion for telert

_telert() {
    local state line context
    local -a commands providers config_commands options

    # List of primary commands
    commands=(
        'run:Run a command and send notification on completion'
        'send:Send a notification message'
        'config:Configure notification providers'
        'status:Check notification configuration status'
        'hook:Generate shell hooks for long-running commands'
        'completions:Generate shell completions'
        'help:Show help'
    )
    
    # List of providers
    providers=(
        'telegram:Telegram messaging'
        'teams:Microsoft Teams messaging'
        'slack:Slack messaging'
        'discord:Discord messaging'
        'pushover:Pushover mobile notifications'
        'audio:Audio notifications'
        'desktop:Desktop notifications'
        'endpoint:Custom HTTP endpoint'
    )
    
    # List of config commands
    config_commands=(
        'telegram:Configure Telegram'
        'teams:Configure Microsoft Teams'
        'slack:Configure Slack'
        'discord:Configure Discord'
        'pushover:Configure Pushover'
        'audio:Configure audio notifications'
        'desktop:Configure desktop notifications'
        'endpoint:Configure HTTP endpoint'
        'set-defaults:Set default providers'
    )
    
    # Standard options for most commands
    options=(
        '--provider:Specify notification provider'
        '--all-providers:Use all configured providers'
        '--verbose:Show verbose output'
        '--help:Show help'
    )

    _arguments -C \\
        '1: :->command' \\
        '2: :->subcommand' \\
        '*: :->args' && ret=0

    case $state in
        command)
            _describe -t commands 'telert commands' commands
            ;;
        subcommand)
            case "$line[1]" in
                run)
                    _arguments \\
                        '--label:Label for the command' \\
                        '--provider:Specify notification provider:($providers)' \\
                        '--all-providers:Use all configured providers' \\
                        '--only-fail:Only notify on failure' \\
                        '--message:Custom notification message' \\
                        '--verbose:Show verbose output'
                    ;;
                send)
                    _arguments \\
                        '--provider:Specify notification provider:($providers)' \\
                        '--all-providers:Use all configured providers' \\
                        '--verbose:Show verbose output'
                    ;;
                config)
                    _describe -t commands 'config commands' config_commands
                    ;;
                hook)
                    _arguments \\
                        '(-l --long)'{-l,--long}':Threshold in seconds for notification' \\
                        '--provider:Specify notification provider:($providers)' \\
                        '--all-providers:Use all configured providers'
                    ;;
                status)
                    _arguments \\
                        '--provider:Specify notification provider:($providers)' \\
                        '--all-providers:Show status for all providers'
                    ;;
                completions)
                    _arguments \\
                        '--shell:Shell to generate completions for:(bash zsh fish all)' \\
                        '--output-dir:Directory to save completion files'
                    ;;
                help)
                    _describe -t commands 'commands' commands
                    ;;
            esac
            ;;
        args)
            case "$line[1]" in
                config)
                    case "$line[2]" in
                        telegram)
                            _arguments \\
                                '--token:Telegram bot token' \\
                                '--chat-id:Telegram chat ID' \\
                                '--set-default:Set as default provider' \\
                                '--add-to-defaults:Add to default providers'
                            ;;
                        teams|slack|discord)
                            _arguments \\
                                '--webhook-url:Webhook URL' \\
                                '--set-default:Set as default provider' \\
                                '--add-to-defaults:Add to default providers'
                            ;;
                        pushover)
                            _arguments \\
                                '--token:Pushover application token' \\
                                '--user:Pushover user key' \\
                                '--set-default:Set as default provider' \\
                                '--add-to-defaults:Add to default providers'
                            ;;
                        audio)
                            _arguments \\
                                '--sound-file:Path to sound file' \\
                                '--volume:Volume level (0.0-1.0)' \\
                                '--set-default:Set as default provider' \\
                                '--add-to-defaults:Add to default providers'
                            ;;
                        desktop)
                            _arguments \\
                                '--app-name:Application name' \\
                                '--icon-path:Path to icon file' \\
                                '--set-default:Set as default provider' \\
                                '--add-to-defaults:Add to default providers'
                            ;;
                        endpoint)
                            _arguments \\
                                '--url:HTTP endpoint URL' \\
                                '--method:HTTP method (GET, POST, etc.)' \\
                                '--header:HTTP headers' \\
                                '--payload-template:Payload template' \\
                                '--name:Friendly name for endpoint' \\
                                '--timeout:Request timeout in seconds' \\
                                '--set-default:Set as default provider' \\
                                '--add-to-defaults:Add to default providers'
                            ;;
                        set-defaults)
                            _arguments \\
                                '--providers:Comma-separated list of providers'
                            ;;
                    esac
                    ;;
                run)
                    if [[ "$line[2]" == "--provider" ]]; then
                        _describe -t providers 'notification providers' providers
                    elif [[ "$words[(($CURRENT - 1))]" == "--provider" ]]; then
                        _describe -t providers 'notification providers' providers
                    fi
                    ;;
                send)
                    if [[ "$line[2]" == "--provider" ]]; then
                        _describe -t providers 'notification providers' providers
                    elif [[ "$words[(($CURRENT - 1))]" == "--provider" ]]; then
                        _describe -t providers 'notification providers' providers
                    fi
                    ;;
            esac
            ;;
    esac
}

_telert "$@"
'''

    fish_completion = '''# Fish completion for telert

# Main commands
complete -c telert -f
complete -c telert -n "__fish_use_subcommand" -a "run" -d "Run a command and send notification on completion"
complete -c telert -n "__fish_use_subcommand" -a "send" -d "Send a notification message"
complete -c telert -n "__fish_use_subcommand" -a "config" -d "Configure notification providers"
complete -c telert -n "__fish_use_subcommand" -a "status" -d "Check notification configuration status"
complete -c telert -n "__fish_use_subcommand" -a "hook" -d "Generate shell hooks for long-running commands"
complete -c telert -n "__fish_use_subcommand" -a "completions" -d "Generate shell completions"
complete -c telert -n "__fish_use_subcommand" -a "help" -d "Show help"

# Provider options
set -l telert_providers telegram teams slack discord pushover audio desktop endpoint

# Run command options
complete -c telert -n "__fish_seen_subcommand_from run" -l "label" -d "Label for the command" -r
complete -c telert -n "__fish_seen_subcommand_from run" -l "provider" -d "Specify notification provider" -r -a "$telert_providers"
complete -c telert -n "__fish_seen_subcommand_from run" -l "all-providers" -d "Use all configured providers"
complete -c telert -n "__fish_seen_subcommand_from run" -l "only-fail" -d "Only notify on failure"
complete -c telert -n "__fish_seen_subcommand_from run" -l "message" -d "Custom notification message" -r
complete -c telert -n "__fish_seen_subcommand_from run" -l "verbose" -d "Show verbose output"

# Send command options
complete -c telert -n "__fish_seen_subcommand_from send" -l "provider" -d "Specify notification provider" -r -a "$telert_providers"
complete -c telert -n "__fish_seen_subcommand_from send" -l "all-providers" -d "Use all configured providers"
complete -c telert -n "__fish_seen_subcommand_from send" -l "verbose" -d "Show verbose output"

# Config command subcommands
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "telegram" -d "Configure Telegram"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "teams" -d "Configure Microsoft Teams"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "slack" -d "Configure Slack"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "discord" -d "Configure Discord"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "pushover" -d "Configure Pushover"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "audio" -d "Configure audio notifications"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "desktop" -d "Configure desktop notifications"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "endpoint" -d "Configure HTTP endpoint"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "set-defaults" -d "Set default providers"

# Completions command options
complete -c telert -n "__fish_seen_subcommand_from completions" -l "shell" -d "Shell to generate completions for" -r -a "bash zsh fish all"
complete -c telert -n "__fish_seen_subcommand_from completions" -l "output-dir" -d "Directory to save completion files" -r

# Provider-specific options
# Telegram
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from telegram" -l "token" -d "Telegram bot token" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from telegram" -l "chat-id" -d "Telegram chat ID" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from telegram" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from telegram" -l "add-to-defaults" -d "Add to default providers"

# Teams
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from teams" -l "webhook-url" -d "Teams webhook URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from teams" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from teams" -l "add-to-defaults" -d "Add to default providers"

# Slack
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from slack" -l "webhook-url" -d "Slack webhook URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from slack" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from slack" -l "add-to-defaults" -d "Add to default providers"

# Discord
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "webhook-url" -d "Discord webhook URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "username" -d "Discord webhook username" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "avatar-url" -d "Discord webhook avatar URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "add-to-defaults" -d "Add to default providers"

# Pushover
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from pushover" -l "token" -d "Pushover application token" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from pushover" -l "user" -d "Pushover user key" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from pushover" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from pushover" -l "add-to-defaults" -d "Add to default providers"

# Audio
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from audio" -l "sound-file" -d "Path to sound file" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from audio" -l "volume" -d "Volume level (0.0-1.0)" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from audio" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from audio" -l "add-to-defaults" -d "Add to default providers"

# Desktop
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from desktop" -l "app-name" -d "Application name" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from desktop" -l "icon-path" -d "Path to icon file" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from desktop" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from desktop" -l "add-to-defaults" -d "Add to default providers"

# Endpoint
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "url" -d "HTTP endpoint URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "method" -d "HTTP method (GET, POST, etc.)" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "header" -d "HTTP headers" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "payload-template" -d "Payload template" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "name" -d "Friendly name for endpoint" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "timeout" -d "Request timeout in seconds" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "add-to-defaults" -d "Add to default providers"

# Set-defaults
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from set-defaults" -l "providers" -d "Comma-separated list of providers" -r

# Hook options
complete -c telert -n "__fish_seen_subcommand_from hook" -s "l" -l "long" -d "Threshold in seconds for notification" -r
complete -c telert -n "__fish_seen_subcommand_from hook" -l "provider" -d "Specify notification provider" -r -a "$telert_providers"
complete -c telert -n "__fish_seen_subcommand_from hook" -l "all-providers" -d "Use all configured providers"

# Status options
complete -c telert -n "__fish_seen_subcommand_from status" -l "provider" -d "Specify notification provider" -r -a "$telert_providers"
complete -c telert -n "__fish_seen_subcommand_from status" -l "all-providers" -d "Show status for all providers"

# Help options
complete -c telert -n "__fish_seen_subcommand_from help" -a "run send config status hook" -d "Command to get help for"
'''

    # Function to get installation instructions
    def get_install_instructions(shell_type, output_path):
        if shell_type == "bash":
            return f'''To enable Bash completions, add the following to your ~/.bashrc:

echo 'source "{output_path}"' >> ~/.bashrc
# or
echo 'source "{output_path}"' >> ~/.bash_profile
'''
        elif shell_type == "zsh":
            return f'''To enable Zsh completions, add the following to your ~/.zshrc:

fpath=("{os.path.dirname(output_path)}" $fpath)
autoload -U compinit && compinit
'''
        elif shell_type == "fish":
            return f'''Fish completions should be automatically loaded once placed in:
{output_path}
'''
        return ""

    # Handle output based on shell type
    if a.shell == "all" or a.shell == "bash":
        if a.output_dir:
            output_path = os.path.join(a.output_dir, "telert")
            os.makedirs(a.output_dir, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(bash_completion)
            print(f"✓ Bash completion saved to: {output_path}")
            print(get_install_instructions("bash", output_path))
        else:
            print("# Bash completion for telert")
            print("# Save this to ~/.local/share/bash-completion/completions/telert")
            print(bash_completion)
            
    if a.shell == "all" or a.shell == "zsh":
        if a.output_dir:
            zsh_dir = os.path.join(a.output_dir, "zsh")
            os.makedirs(zsh_dir, exist_ok=True)
            output_path = os.path.join(zsh_dir, "_telert")
            with open(output_path, "w") as f:
                f.write(zsh_completion)
            print(f"✓ Zsh completion saved to: {output_path}")
            print(get_install_instructions("zsh", output_path))
        else:
            print("# Zsh completion for telert")
            print("# Save this to ~/.zsh/completions/_telert")
            print(zsh_completion)
            
    if a.shell == "all" or a.shell == "fish":
        if a.output_dir:
            fish_dir = os.path.join(a.output_dir, "fish/completions")
            os.makedirs(fish_dir, exist_ok=True)
            output_path = os.path.join(fish_dir, "telert.fish")
            with open(output_path, "w") as f:
                f.write(fish_completion)
            print(f"✓ Fish completion saved to: {output_path}")
            print(get_install_instructions("fish", output_path))
        else:
            print("# Fish completion for telert")
            print("# Save this to ~/.config/fish/completions/telert.fish")
            print(fish_completion)
            
    if not a.output_dir:
        print("\n# For automated installation, run:")
        print("telert completions --output-dir ~/.local/share/bash-completion/completions  # For Bash")
        print("telert completions --shell zsh --output-dir ~/.zsh/completions              # For Zsh")
        print("telert completions --shell fish --output-dir ~/.config/fish/completions     # For Fish")

    # help alias
    hp = sp.add_parser("help", help="show global help")
    hp.set_defaults(func=do_help)
    
    # completions generation
    comp = sp.add_parser("completions", help="generate shell completions")
    comp.add_argument(
        "--shell", 
        choices=["bash", "zsh", "fish", "all"],
        default="all",
        help="which shell completion to generate"
    )
    comp.add_argument(
        "--output-dir",
        help="directory to save completion files (default: print to stdout)"
    )
    comp.set_defaults(func=do_completions)

    args = p.parse_args()

    if getattr(args, "cmd", None) == [] and getattr(args, "func", None) is do_run:
        p.error("run: missing command – use telert run -- <cmd> …")

    args.func(args)


if __name__ == "__main__":
    main()
