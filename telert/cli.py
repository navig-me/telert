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

import traceback
import argparse
import os
import subprocess
import sys
import textwrap
import time

from telert import __version__
from telert.messaging import (
    CONFIG_DIR,
    MessagingConfig,
    Provider,
    configure_provider,
    send_message,
)
from telert.monitoring.cli import setup_monitor_cli, handle_monitor_commands

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

        # List providers
        if provider == "list-providers":
            config = MessagingConfig()
            providers = config.get_providers()
            default_providers = config.get_default_providers()
            print("Providers:")
            if not providers:
                print("  (none configured)")
                return

            for provider in providers:
                if provider in default_providers:
                    if len(default_providers) > 1:
                        # Show priority order starting at 1
                        priority = default_providers.index(provider) + 1
                        marker = f" (default #{priority})"
                    else:
                        marker = " (default)"
                else:
                    marker = ""
                print(f"  {provider.value}{marker}")
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

        elif provider == "email":
            if not hasattr(a, "server"):
                sys.exit("❌ Email configuration requires --server")

            config_params = {
                "server": a.server,
                "port": a.port,
                "set_default": a.set_default,
                "add_to_defaults": a.add_to_defaults,
            }

            if hasattr(a, "username") and a.username:
                config_params["username"] = a.username

            if hasattr(a, "password") and a.password:
                config_params["password"] = a.password

            if hasattr(a, "from_addr") and a.from_addr:
                config_params["from_addr"] = a.from_addr

            if hasattr(a, "to_addrs") and a.to_addrs:
                config_params["to_addrs"] = a.to_addrs

            if hasattr(a, "subject_template") and a.subject_template:
                config_params["subject_template"] = a.subject_template

            if hasattr(a, "use_html") and a.use_html:
                config_params["use_html"] = a.use_html

            try:
                configure_provider(Provider.EMAIL, **config_params)
                print(f"✔ Email configuration saved for {a.server}")
            except ValueError as e:
                sys.exit(f"❌ {str(e)}")

        else:
            sys.exit(f"❌ Unknown provider: {provider}")
    else:
        print("Run `telert config --help` to see available options.\n")
        config = MessagingConfig()
        providers = config.get_providers()
        default_providers = config.get_default_providers()
        print("Providers:")
        if not providers:
            print("  (none configured)")
            return

        for provider in providers:
            if provider in default_providers:
                if len(default_providers) > 1:
                    # Show priority order starting at 1
                    priority = default_providers.index(provider) + 1
                    marker = f" (default #{priority})"
                else:
                    marker = " (default)"
            else:
                marker = ""
            print(f"  {provider.value}{marker}")
        return


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
        print(
            f"- Discord{default_marker}: webhook={webhook[:20]}…, username={username}{avatar_info}"
        )

    # Check Email
    email_config = config.get_provider_config(Provider.EMAIL)
    if email_config:
        # Mark as default if in default providers list
        if Provider.EMAIL.value in default_provider_names:
            # Show priority if multiple defaults
            if len(default_provider_names) > 1:
                priority = default_provider_names.index(Provider.EMAIL.value) + 1
                default_marker = f" (default #{priority})"
            else:
                default_marker = " (default)"
        else:
            default_marker = ""

        server = email_config["server"]
        port = email_config.get("port", 587)
        username = email_config.get("username", "")
        to_addrs = email_config.get("to_addrs", [])
        to_str = ", ".join(to_addrs) if to_addrs else "unknown"
        print(f"- Email{default_marker}: server={server}:{port} → {to_str}")

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
        or email_config
    ):
        print(
            "No providers configured. Use `telert config` or `telert init` to set up a provider."
        )
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
                traceback.print_exc()
                sys.exit(f"❌ Failed to send message: {str(e)}")
        else:
            # Handle multiple providers (comma-separated)
            if "," in a.provider:
                providers_to_test = []
                for p in a.provider.split(","):
                    try:
                        providers_to_test.append(Provider.from_string(p.strip()))
                    except ValueError:
                        traceback.print_exc()
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
                    traceback.print_exc()
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
            traceback.print_exc()
            sys.exit(f"❌ Failed to send message: {str(e)}")


def do_hook(a):
    """Generate a shell hook for command notifications."""
    shell = a.shell or os.path.basename(os.environ.get("SHELL", "bash"))
    threshold = a.longer_than

    if "zsh" in shell:
        hook_script = textwrap.dedent(f"""
            # Load zsh hooks module if not already loaded
            if [[ -z "$__TELERT_HOOKS_LOADED" ]]; then
                autoload -U add-zsh-hook 2>/dev/null || {{
                    echo "Warning: add-zsh-hook not available, using fallback implementation... Please ensure zsh is properly installed and configured."
                    # Fallback for systems without zsh-hooks
                    _telert_preexec() {{
                        __TELERT_CMD__="$1"
                        __TELERT_START__=$EPOCHSECONDS
                    }}

                    _telert_precmd() {{
                        if [[ -n "$__TELERT_START__" ]]; then
                            local st=$?
                            local end=$EPOCHSECONDS
                            local duration=$((end - __TELERT_START__))
                            if (( duration >= {threshold} )); then
                                telert send "$__TELERT_CMD__ exited with $st in $(printf '%dm%02ds' $((duration/60)) $((duration%60)))"
                            fi
                            unset __TELERT_START__
                        fi
                    }}

                    # Set up hooks manually
                    preexec_functions=(_telert_preexec ${{preexec_functions[@]}})
                    precmd_functions=(_telert_precmd ${{precmd_functions[@]}})
                    export __TELERT_HOOKS_LOADED=1
                    return
                }}
            fi

            # Standard hook setup
            autoload -U zsh/datetime

            _telert_preexec() {{
                # Try multiple methods to get the command
                if [[ -n "$1" ]]; then
                    typeset -g __TELERT_CMD__="$1"
                elif [[ -n "$HISTCMD" ]] && [[ -n "${{history[$HISTCMD]}}" ]]; then
                    typeset -g __TELERT_CMD__="${{history[$HISTCMD]}}"
                else
                    # Last resort: try to get from history builtin
                    typeset -g __TELERT_CMD__="$(history -1 2>/dev/null | head -1 | sed 's/^[[:space:]]*[0-9]*[[:space:]]*//')"
                fi
                typeset -g __TELERT_START__=$EPOCHSECONDS
            }}

            _telert_precmd() {{
                if [[ -n "$__TELERT_START__" ]]; then
                    local st=$?
                    local end=$EPOCHSECONDS
                    local duration=$((end - __TELERT_START__))
                    if (( duration >= {threshold} )); then
                        telert send "$__TELERT_CMD__ exited with $st in $(printf '%dm%02ds' $((duration/60)) $((duration%60)))"
                    fi
                    unset __TELERT_START__
                    unset __TELERT_CMD__
                fi
            }}

            add-zsh-hook preexec _telert_preexec
            add-zsh-hook precmd _telert_precmd
        """).strip()
    else:  # Default to bash
        hook_script = textwrap.dedent(f"""
            telert_preexec() {{{{ export __TELERT_CMD__="$BASH_COMMAND"; export TELERT_START=$EPOCHSECONDS; }}}}
            telert_precmd()  {{{{ local st=$?; if [[ -n "$TELERT_START" ]]; then local d=$((EPOCHSECONDS-TELERT_START)); if (( d >= {threshold} )); then telert send "$__TELERT_CMD__ exited with $st in $(printf '%dm%02ds' $((d/60)) $((d%60)))"; fi; unset TELERT_START; fi; }}}}
            trap 'telert_preexec' DEBUG
            PROMPT_COMMAND="telert_precmd${{{{PROMPT_COMMAND:+;}}}}$PROMPT_COMMAND"
        """).strip()

    print(hook_script)


def do_send(a):
    """Send a simple message."""
    provider = None
    all_providers = False
    parse_mode = None
    quiet_mode = hasattr(a, "quiet") and a.quiet
    silent_mode = hasattr(a, "silent") and a.silent
    verbose_mode = hasattr(a, "verbose") and a.verbose

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

    # Check if parse_mode was specified
    if hasattr(a, "parse_mode") and a.parse_mode:
        if a.parse_mode.upper() in ["HTML", "MARKDOWN", "MARKDOWNV2"]:
            parse_mode = a.parse_mode
        else:
            sys.exit(
                f"❌ Invalid parse mode: {a.parse_mode}. Use 'HTML' or 'MarkdownV2'."
            )

    try:
        results = send_message(a.text, provider, all_providers, parse_mode)

        # Handle output based on verbosity flags
        if not silent_mode:
            # Always show a basic success message if not in silent mode
            if results and not quiet_mode:
                providers_str = ", ".join(results.keys())
                print(f"✓ Telert sent a message to: {providers_str}")

            # Show detailed results based on verbosity
            if verbose_mode or (len(results) > 1 and not quiet_mode):
                for provider_name, success in results.items():
                    status = "✅ success" if success else "❌ failed"
                    print(f"  - {provider_name}: {status}")
    except Exception as e:
        traceback.print_exc()
        sys.exit(f"❌ Failed to send message: {str(e)}")


def do_run(a):
    """Run a command and send notification when it completes."""
    start = time.time()

    # Check verbosity flags
    quiet_mode = hasattr(a, "quiet") and a.quiet
    verbose_mode = hasattr(a, "verbose") and a.verbose

    # Check if we should suppress output - either from flag or env var
    silent_mode = (hasattr(a, "silent") and a.silent) or os.environ.get(
        "TELERT_SILENT"
    ) == "1"

    # If --silent flag was used, set the environment variable for compatibility
    if hasattr(a, "silent") and a.silent:
        os.environ["TELERT_SILENT"] = "1"

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

        # Only show output if not in silent mode and not in quiet mode
        if results and not silent_mode and not quiet_mode:
            providers_str = ", ".join(results.keys())
            print(f"✓ Telert sent a message to: {providers_str}")

            # Show detailed results for each provider if verbose
            if verbose_mode or (len(results) > 1 and not quiet_mode):
                for provider_name, success in results.items():
                    status_icon = "✅" if success else "❌"
                    print(
                        f"  - {provider_name}: {status_icon} {'success' if success else 'failed'}"
                    )

    except Exception as e:
        # Always show errors, regardless of modes
        print(f"❌ Failed to send notification: {str(e)}", file=sys.stderr)

    sys.exit(status)


# ───────────────────────────── pipeline filter ─────────────────────────────


def piped_mode():
    """Handle input from a pipeline and send notification."""
    # Skip version-only invocations to avoid sending unwanted notifications
    if len(sys.argv) >= 2 and sys.argv[1] == "--version":
        # No notification for version checks
        sys.exit(0)
    data = sys.stdin.read()
    # Use first argument as message if it is not a flag, else default to 'Pipeline finished'
    msg = (
        sys.argv[1]
        if (len(sys.argv) > 1 and not sys.argv[1].startswith("-"))
        else "Pipeline finished"
    )

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
    quiet_mode = False
    silent_mode = False
    verbose_mode = False

    # Check for flag arguments
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ["--quiet", "-q"]:
            quiet_mode = True
        elif arg in ["--silent", "-s"]:
            silent_mode = True
        elif arg in ["--verbose", "-v"]:
            verbose_mode = True

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
        # Only show output if not in silent mode
        if not silent_mode:
            # Show basic success message if not in quiet mode
            if results and not quiet_mode:
                providers_str = ", ".join(results.keys())
                print(f"✓ Telert sent a message to: {providers_str}")

            # Show detailed results if verbose mode or multiple providers in verbose mode
            if verbose_mode or (len(results) > 1 and not quiet_mode):
                for provider_name, success in results.items():
                    status_icon = "✅" if success else "❌"
                    print(
                        f"  - {provider_name}: {status_icon} {'success' if success else 'failed'}"
                    )
    except Exception as e:
        traceback.print_exc()
        sys.exit(f"❌ Failed to send message: {str(e)}")


def do_init(a):
    """Run the interactive configuration wizard."""

    print("\n🔔 Welcome to telert configuration wizard! 🔔")
    print("This wizard will help you set up notification providers.\n")

    # Step 1: Choose provider(s)
    print("Available notification providers:")
    print("1. Telegram - Mobile messaging via Telegram bot")
    print("2. Microsoft Teams - Notifications in Teams channels")
    print("3. Slack - Notifications in Slack channels")
    print("4. Discord - Notifications in Discord channels")
    print("5. Pushover - Notifications for iOS/Android devices")
    print("6. Desktop - Local desktop notifications")
    print("7. Audio - Sound alerts on your computer")
    print("8. Endpoint - Custom HTTP notifications")
    print("9. Email - Notifications via email\n")

    # Get provider choices
    provider_choices = input(
        "Enter provider numbers to configure (comma-separated, e.g. 1,6,7): "
    ).strip()
    if not provider_choices:
        print("No providers selected. Exiting wizard.")
        return

    # Parse provider choices
    try:
        chosen_providers = [
            int(choice.strip()) for choice in provider_choices.split(",")
        ]
    except ValueError:
        print("❌ Invalid input. Please enter numbers separated by commas.")
        return

    # Map choices to provider enums
    provider_map = {
        1: Provider.TELEGRAM,
        2: Provider.TEAMS,
        3: Provider.SLACK,
        4: Provider.DISCORD,
        5: Provider.PUSHOVER,
        6: Provider.DESKTOP,
        7: Provider.AUDIO,
        8: Provider.ENDPOINT,
        9: Provider.EMAIL,
    }

    selected_providers = []

    # Configure each chosen provider
    for choice in chosen_providers:
        if choice not in provider_map:
            print(f"❌ Invalid provider number: {choice}")
            continue

        provider = provider_map[choice]
        print(f"\nConfiguring {provider.value}...")

        if provider == Provider.TELEGRAM:
            print("\nFor Telegram notifications, you'll need:")
            print("1. A bot token from @BotFather")
            print("2. Your chat ID")
            print(
                "Learn more: https://github.com/navig-me/telert/blob/main/docs/TELEGRAM.md"
            )

            token = input("Enter bot token: ").strip()
            chat_id = input("Enter chat ID: ").strip()

            if not token or not chat_id:
                print(
                    "❌ Both token and chat ID are required. Skipping Telegram setup."
                )
                continue

            try:
                configure_provider(provider, token=token, chat_id=chat_id)
                print("✅ Telegram configured successfully")
                selected_providers.append(provider)
            except Exception as e:
                print(f"❌ Failed to configure Telegram: {str(e)}")

        elif provider == Provider.TEAMS:
            print("\nFor Microsoft Teams notifications, you'll need:")
            print("1. A webhook URL from Power Automate")
            print(
                "Learn more: https://github.com/navig-me/telert/blob/main/docs/TEAMS.md"
            )

            webhook_url = input("Enter Teams webhook URL: ").strip()

            if not webhook_url:
                print("❌ Webhook URL is required. Skipping Teams setup.")
                continue

            try:
                configure_provider(provider, webhook_url=webhook_url)
                print("✅ Microsoft Teams configured successfully")
                selected_providers.append(provider)
            except Exception as e:
                print(f"❌ Failed to configure Microsoft Teams: {str(e)}")

        elif provider == Provider.SLACK:
            print("\nFor Slack notifications, you'll need:")
            print("1. A webhook URL from Slack")
            print(
                "Learn more: https://github.com/navig-me/telert/blob/main/docs/SLACK.md"
            )

            webhook_url = input("Enter Slack webhook URL: ").strip()

            if not webhook_url:
                print("❌ Webhook URL is required. Skipping Slack setup.")
                continue

            try:
                configure_provider(provider, webhook_url=webhook_url)
                print("✅ Slack configured successfully")
                selected_providers.append(provider)
            except Exception as e:
                print(f"❌ Failed to configure Slack: {str(e)}")

        elif provider == Provider.DISCORD:
            print("\nFor Discord notifications, you'll need:")
            print("1. A webhook URL from Discord")
            print(
                "Learn more: https://github.com/navig-me/telert/blob/main/docs/DISCORD.md"
            )

            webhook_url = input("Enter Discord webhook URL: ").strip()

            if not webhook_url:
                print("❌ Webhook URL is required. Skipping Discord setup.")
                continue

            username = input("Enter bot username (optional, default: Telert): ").strip()
            avatar_url = input("Enter bot avatar URL (optional): ").strip()

            try:
                config_params = {"webhook_url": webhook_url}
                if username:
                    config_params["username"] = username
                if avatar_url:
                    config_params["avatar_url"] = avatar_url

                configure_provider(provider, **config_params)
                print("✅ Discord configured successfully")
                selected_providers.append(provider)
            except Exception as e:
                print(f"❌ Failed to configure Discord: {str(e)}")

        elif provider == Provider.PUSHOVER:
            print("\nFor Pushover notifications, you'll need:")
            print("1. An application token from Pushover.net")
            print("2. Your user key from Pushover.net")
            print(
                "Learn more: https://github.com/navig-me/telert/blob/main/docs/PUSHOVER.md"
            )

            token = input("Enter Pushover application token: ").strip()
            user = input("Enter Pushover user key: ").strip()

            if not token or not user:
                print(
                    "❌ Both token and user key are required. Skipping Pushover setup."
                )
                continue

            try:
                configure_provider(provider, token=token, user=user)
                print("✅ Pushover configured successfully")
                selected_providers.append(provider)
            except Exception as e:
                print(f"❌ Failed to configure Pushover: {str(e)}")

        elif provider == Provider.DESKTOP:
            print("\nConfiguring desktop notifications:")

            app_name = input(
                "Enter application name (optional, default: Telert): "
            ).strip()
            icon_path = input("Enter path to icon image (optional): ").strip()

            config_params = {}
            if app_name:
                config_params["app_name"] = app_name
            if icon_path:
                config_params["icon_path"] = icon_path

            try:
                configure_provider(provider, **config_params)
                print("✅ Desktop notifications configured successfully")
                selected_providers.append(provider)
            except Exception as e:
                print(f"❌ Failed to configure desktop notifications: {str(e)}")

        elif provider == Provider.AUDIO:
            print("\nConfiguring audio notifications:")

            sound_file = input(
                "Enter path to sound file (optional, default: built-in notification): "
            ).strip()
            volume_str = input(
                "Enter volume level 0.0-1.0 (optional, default: 1.0): "
            ).strip()

            config_params = {}
            if sound_file:
                config_params["sound_file"] = sound_file
            if volume_str:
                try:
                    volume = float(volume_str)
                    if 0.0 <= volume <= 1.0:
                        config_params["volume"] = volume
                    else:
                        print(
                            "⚠️ Volume must be between 0.0 and 1.0. Using default (1.0)."
                        )
                except ValueError:
                    print("⚠️ Invalid volume format. Using default (1.0).")

            try:
                configure_provider(provider, **config_params)
                print("✅ Audio notifications configured successfully")
                selected_providers.append(provider)
            except Exception as e:
                print(f"❌ Failed to configure audio notifications: {str(e)}")

        elif provider == Provider.ENDPOINT:
            print("\nFor custom HTTP endpoint notifications, you'll need:")
            print("1. A URL to send notifications to")
            print(
                "Learn more: https://github.com/navig-me/telert/blob/main/docs/ENDPOINT.md"
            )

            url = input("Enter endpoint URL: ").strip()

            if not url:
                print("❌ URL is required. Skipping endpoint setup.")
                continue

            method = (
                input("Enter HTTP method (optional, default: POST): ").strip().upper()
            )
            payload_template = input(
                'Enter payload template (optional, default: {"text": "{message}"}): '
            ).strip()
            name = input(
                "Enter friendly name for this endpoint (optional, default: Custom Endpoint): "
            ).strip()
            timeout_str = input(
                "Enter request timeout in seconds (optional, default: 20): "
            ).strip()

            config_params = {"url": url}
            if method:
                config_params["method"] = method
            if payload_template:
                config_params["payload_template"] = payload_template
            if name:
                config_params["name"] = name
            if timeout_str:
                try:
                    timeout = int(timeout_str)
                    config_params["timeout"] = timeout
                except ValueError:
                    print("⚠️ Invalid timeout format. Using default (20s).")

            # Ask for HTTP headers
            print("\nDo you want to add HTTP headers? (y/n)")
            add_headers = input().strip().lower() == "y"

            headers = {}
            if add_headers:
                print(
                    "Enter headers in 'Key: Value' format, one per line. Enter a blank line when done."
                )
                while True:
                    header_line = input().strip()
                    if not header_line:
                        break

                    if ":" in header_line:
                        key, value = header_line.split(":", 1)
                        headers[key.strip()] = value.strip()
                    else:
                        print("⚠️ Invalid header format. Use 'Key: Value' format.")

            if headers:
                config_params["headers"] = headers

            try:
                configure_provider(provider, **config_params)
                print("✅ HTTP endpoint configured successfully")
                selected_providers.append(provider)
            except Exception as e:
                print(f"❌ Failed to configure HTTP endpoint: {str(e)}")

        elif provider == Provider.EMAIL:
            print("\nFor email notifications, you'll need:")
            print("1. SMTP server address")
            print("2. SMTP server port (optional, default: 587 for TLS)")
            print("3. SMTP username (optional)")
            print("4. SMTP password (optional)")
            print("5. Sender email address (optional)")
            print("6. Recipient email address(es) - comma separated for multiple")
            print(
                "Learn more: https://github.com/navig-me/telert/blob/main/docs/EMAIL.md"
            )

            server = input("Enter SMTP server address: ").strip()

            if not server:
                print("❌ SMTP server is required. Skipping email setup.")
                continue

            port_str = input(
                "SMTP server port (optional, default: 587 for TLS): "
            ).strip()
            if port_str:
                try:
                    port = int(port_str)
                except ValueError:
                    print("❌ Invalid port number, using default 587")
                    port = 587
            else:
                port = 587

            username = input("SMTP username (optional): ").strip()
            password = input("SMTP password (optional): ").strip()

            from_addr = input("Sender email address (optional): ").strip()
            to_addrs = input(
                "Recipient email address(es) - comma separated for multiple: "
            ).strip()

            if not to_addrs:
                print("❌ At least one recipient email address is required")
                continue

            to_list = [addr.strip() for addr in to_addrs.split(",")]

            subject_template = input(
                "Subject template (optional, default: 'Telert Alert: {label} - {status}'): "
            ).strip()
            if not subject_template:
                subject_template = "Telert Alert: {label} - {status}"

            use_html_str = (
                input("Send HTML formatted emails? (y/n, default: n): ").strip().lower()
            )
            use_html = use_html_str in ("y", "yes", "true", "1")

            config_params = {
                "server": server,
                "port": port,
                "to_addrs": to_list,
                "subject_template": subject_template,
                "use_html": use_html,
            }

            if username:
                config_params["username"] = username
            if password:
                config_params["password"] = password
            if from_addr:
                config_params["from_addr"] = from_addr

            try:
                configure_provider(provider, **config_params)
                print("✅ Email configured successfully")
                selected_providers.append(provider)
            except Exception as e:
                print(f"❌ Failed to configure email: {str(e)}")

    # Reload configuration after provider setup to ensure we have the latest state
    config = MessagingConfig()

    # Set default providers if any were configured successfully
    if selected_providers:
        # Step 2: Set defaults and order
        if len(selected_providers) > 1:
            print(
                "\nMultiple providers configured. You can set the default provider order."
            )
            print(
                "When sending notifications, providers will be tried in the specified order."
            )

            # Show configured providers
            print("Configured providers:")
            for i, p in enumerate(selected_providers, 1):
                print(f"{i}. {p.value}")

            choice = (
                input("\nUse the current order as defaults? (y/n, default: y): ")
                .strip()
                .lower()
            )

            if choice != "n":
                # Use as is
                config.set_default_providers(selected_providers)
                providers_str = ", ".join([p.value for p in selected_providers])
                print(f"✅ Default providers set: {providers_str}")
            else:
                # Ask for custom order
                print(
                    "Enter provider numbers in your preferred order (comma-separated):"
                )
                order_input = input().strip()

                try:
                    # Parse order
                    order_indices = [
                        int(idx.strip()) - 1 for idx in order_input.split(",")
                    ]
                    # Create ordered provider list
                    ordered_providers = []
                    for idx in order_indices:
                        if 0 <= idx < len(selected_providers):
                            ordered_providers.append(selected_providers[idx])

                    if ordered_providers:
                        config.set_default_providers(ordered_providers)
                        providers_str = ", ".join([p.value for p in ordered_providers])
                        print(f"✅ Default providers set: {providers_str}")
                    else:
                        # Fallback to default order if parsing fails
                        config.set_default_providers(selected_providers)
                        providers_str = ", ".join([p.value for p in selected_providers])
                        print(f"✅ Default providers set: {providers_str}")
                except ValueError:
                    # Fallback to default order if parsing fails
                    config.set_default_providers(selected_providers)
                    providers_str = ", ".join([p.value for p in selected_providers])
                    print(f"✅ Default providers set: {providers_str}")
        else:
            # Only one provider, set as default
            config.set_default_provider(selected_providers[0])
            print(f"✅ Default provider set: {selected_providers[0].value}")

        # Step 3: Offer to test configuration
        print("\nConfiguration complete! Would you like to test it now? (y/n)")
        test_choice = input().strip().lower()

        if test_choice == "y":
            print("\nSending test message...\n")
            try:
                results = send_message("✅ telert configuration test successful")

                # Show results
                for provider_name, success in results.items():
                    status = "✅ success" if success else "❌ failed"
                    print(f"  - {provider_name}: {status}")

                print("\nSetup complete! You can now use telert to send notifications.")
                print("Try running: telert run echo 'Hello, telert!'")
            except Exception as e:
                print(f"❌ Test failed: {str(e)}")
                print(
                    "\nPlease check your configuration and try again with 'telert status'."
                )
        else:
            print(
                "\nSetup complete! You can test your configuration with the 'telert status' command."
            )
    else:
        print("\n❌ No providers were successfully configured.")
        print(
            "You can try again or configure providers manually with 'telert config <provider>'."
        )


def main():
    """Main entry point for the CLI."""
    # Early version flag handling (bypass pipeline mode)
    if len(sys.argv) >= 2 and sys.argv[1] == "--version":
        print(f"telert {__version__}")
        return
    if not sys.stdin.isatty():
        piped_mode()
        return
    p = argparse.ArgumentParser(
        description="Send alerts from shell commands to messaging services",
        epilog="Example: telert run ls -la",
    )
    p.add_argument("--version", action="version", version=f"telert {__version__}")

    sp = p.add_subparsers(dest="command", metavar="COMMAND")

    # Add monitoring commands
    setup_monitor_cli(sp)

    # config
    c = sp.add_parser("config", help="configure messaging providers")
    config_sp = c.add_subparsers(dest="provider", help="provider type to configure")

    # Set defaults command
    set_defaults_parser = config_sp.add_parser(
        "set-defaults", help="set multiple default providers in priority order"
    )
    set_defaults_parser.add_argument(
        "--providers",
        required=True,
        help="comma-separated list of providers to use as defaults, in priority order",
    )

    # List providers command
    list_providers_parser = config_sp.add_parser(
        "list-providers", help="list all available providers"
    )

    # Telegram config
    telegram_parser = config_sp.add_parser(
        "telegram", help="configure Telegram messaging"
    )
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
    teams_parser = config_sp.add_parser("teams", help="configure Microsoft Teams")
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
    slack_parser = config_sp.add_parser("slack", help="configure Slack")
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
    discord_parser = config_sp.add_parser("discord", help="configure Discord")
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
    audio_parser = config_sp.add_parser("audio", help="configure Audio alerts")
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
    desktop_parser = config_sp.add_parser(
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
    pushover_parser = config_sp.add_parser(
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
    endpoint_parser = config_sp.add_parser(
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

    # Email configuration subparser
    email_parser = config_sp.add_parser(
        "email", help="configure email (SMTP) messaging"
    )
    email_parser.add_argument("--server", required=True, help="SMTP server address")
    email_parser.add_argument(
        "--port", type=int, default=587, help="SMTP server port (default: 587 for TLS)"
    )
    email_parser.add_argument("--username", help="SMTP username for authentication")
    email_parser.add_argument("--password", help="SMTP password for authentication")
    email_parser.add_argument("--from", dest="from_addr", help="sender email address")
    email_parser.add_argument(
        "--to",
        dest="to_addrs",
        help="recipient email address(es) - comma separated for multiple",
    )
    email_parser.add_argument(
        "--subject-template",
        default="Telert Alert: {label} - {status}",
        help="template for email subject line (default: 'Telert Alert: {label} - {status}')",
    )
    email_parser.add_argument(
        "--html",
        dest="use_html",
        action="store_true",
        help="send HTML formatted emails",
    )
    email_parser.add_argument(
        "--set-default", action="store_true", help="set as the only default provider"
    )
    email_parser.add_argument(
        "--add-to-defaults",
        action="store_true",
        help="add to existing default providers",
    )

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
    hk.add_argument(
        "--shell",
        choices=["bash", "zsh"],
        help="specify the shell type (default: auto-detect from $SHELL)",
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
        "--parse-mode",
        choices=["HTML", "MarkdownV2"],
        help="message formatting mode (Telegram only)",
    )
    sd.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="show detailed results for each provider",
    )
    sd.add_argument("--quiet", "-q", action="store_true", help="reduce console output")
    sd.add_argument(
        "--silent", "-s", action="store_true", help="show no output except errors"
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
        "--quiet",
        "-q",
        action="store_true",
        help="reduce console output while still displaying command output",
    )
    rn.add_argument(
        "--silent",
        "-s",
        action="store_true",
        help="suppress command output in console (same as TELERT_SILENT=1)",
    )
    rn.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="show detailed output about notification delivery",
    )
    rn.add_argument("cmd", nargs=argparse.REMAINDER, help="command to execute required")
    rn.set_defaults(func=do_run)

    def do_help(_):
        p.print_help()

    # help alias
    hp = sp.add_parser("help", help="show global help")
    hp.set_defaults(func=do_help)

    # init (wizard)
    init = sp.add_parser("init", help="run interactive setup wizard")
    init.set_defaults(func=do_init)

    args = p.parse_args()

    if getattr(args, "cmd", None) == [] and getattr(args, "func", None) is do_run:
        p.error("run: missing command – use telert run <cmd> …")

    # Handle monitor commands
    if getattr(args, "command", None) == "monitor":
        handle_monitor_commands(args)
    elif hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
