#!/usr/bin/env python3
"""
Python API for telert - Send alerts from Python code to Telegram, Teams, or Slack.

This module provides functions to send notifications directly from Python.
It shares the same configuration as the CLI tool.

Usage:
    from telert import telert, send

    # Send a simple notification
    send("My script finished processing")

    # Specify a provider
    send("Hello Slack!", provider="slack")

    # Use with a context manager to time execution
    with telert("Long computation"):
        # Your code here
        result = compute_something_expensive()

    # The notification will be sent when the block exits,
    # including the execution time.
"""

from __future__ import annotations

import functools
import os
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# For backward compatibility
from telert.cli import _human
from telert.messaging import (
    MessagingConfig, 
    Provider, 
    configure_provider, 
    configure_providers,
    send_message
)

# Type variable for function return type
T = TypeVar("T")


def configure_telegram(token: str, chat_id: str, set_default: bool = True) -> None:
    """
    Configure Telert for Telegram.

    Args:
        token: The Telegram bot API token
        chat_id: The chat ID to send messages to
        set_default: Whether to set Telegram as the default provider

    Examples:
        from telert import configure_telegram

        configure_telegram("123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ", "123456789")
    """
    configure_provider(
        Provider.TELEGRAM, token=token, chat_id=chat_id, set_default=set_default
    )


def configure_teams(webhook_url: str, set_default: bool = True) -> None:
    """
    Configure Telert for Microsoft Teams using Power Automate.

    Args:
        webhook_url: The HTTP URL from your Power Automate flow trigger
        set_default: Whether to set Teams as the default provider

    Examples:
        from telert import configure_teams

        configure_teams("https://prod-00.northcentralus.logic.azure.com/workflows/...")
    """
    configure_provider(Provider.TEAMS, webhook_url=webhook_url, set_default=set_default)


def configure_slack(webhook_url: str, set_default: bool = True) -> None:
    """
    Configure Telert for Slack.

    Args:
        webhook_url: The Slack incoming webhook URL
        set_default: Whether to set Slack as the default provider

    Examples:
        from telert import configure_slack

        configure_slack("https://hooks.slack.com/services/...")
    """
    configure_provider(Provider.SLACK, webhook_url=webhook_url, set_default=set_default)


def configure_audio(
    sound_file: Optional[str] = None, volume: float = 1.0, set_default: bool = True
) -> None:
    """
    Configure Telert for audio notifications.

    Args:
        sound_file: Path to the sound file (.wav, .mp3, etc.) (default: uses built-in sound)
        volume: Volume level between 0.0 and 1.0 (default: 1.0)
        set_default: Whether to set Audio as the default provider

    Examples:
        from telert import configure_audio

        # Use the built-in sound
        configure_audio(volume=0.8)

        # Use a custom sound file
        configure_audio("/path/to/alert.wav", volume=0.8)
    """
    config = {"volume": volume, "set_default": set_default}

    if sound_file:
        config["sound_file"] = sound_file

    configure_provider(Provider.AUDIO, **config)


def configure_desktop(
    app_name: str = "Telert", icon_path: Optional[str] = None, set_default: bool = True
) -> None:
    """
    Configure Telert for desktop notifications.

    Args:
        app_name: Application name shown in notifications (default: "Telert")
        icon_path: Path to icon file for the notification (default: uses built-in icon)
        set_default: Whether to set Desktop as the default provider

    Examples:
        from telert import configure_desktop

        # Use the built-in icon
        configure_desktop("My App")

        # Use a custom icon
        configure_desktop("My App", icon_path="/path/to/icon.png")
    """
    config = {"app_name": app_name, "set_default": set_default}

    if icon_path:
        config["icon_path"] = icon_path

    configure_provider(Provider.DESKTOP, **config)


def configure_pushover(token: str, user: str, set_default: bool = True) -> None:
    """
    Configure Telert for Pushover notifications.

    Args:
        token: The Pushover application token
        user: The Pushover user key
        set_default: Whether to set Pushover as the default provider

    Examples:
        from telert import configure_pushover

        configure_pushover("a1b2c3d4e5f6g7h8i9j0", "u1v2w3x4y5z6")
    """
    configure_provider(Provider.PUSHOVER, token=token, user=user, set_default=set_default)


def configure_discord(webhook_url: str, username: Optional[str] = None, avatar_url: Optional[str] = None, set_default: bool = True) -> None:
    """
    Configure Telert for Discord notifications.

    Args:
        webhook_url: The Discord webhook URL
        username: Optional custom name for the webhook bot (default: "Telert")
        avatar_url: Optional URL for the webhook bot's avatar image
        set_default: Whether to set Discord as the default provider

    Examples:
        from telert import configure_discord

        # Basic configuration
        configure_discord("https://discord.com/api/webhooks/...")

        # With custom bot name and avatar
        configure_discord(
            "https://discord.com/api/webhooks/...",
            username="Alert Bot", 
            avatar_url="https://example.com/avatar.png"
        )
    """
    config = {"webhook_url": webhook_url, "set_default": set_default}
    
    if username:
        config["username"] = username
        
    if avatar_url:
        config["avatar_url"] = avatar_url
        
    configure_provider(Provider.DISCORD, **config)


# Legacy function for backward compatibility
def configure(token: str, chat_id: str) -> None:
    """
    Configure Telert with Telegram bot token and chat ID.

    This is a legacy function maintained for backward compatibility.
    For new code, consider using configure_telegram(), configure_teams(),
    configure_slack(), configure_audio(), or configure_desktop() instead.

    Args:
        token: The Telegram bot API token
        chat_id: The chat ID to send messages to

    Examples:
        from telert import configure

        configure("123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ", "123456789")
    """
    configure_telegram(token, chat_id, set_default=True)


def get_config(provider: Optional[Union[str, Provider]] = None) -> Dict[str, Any]:
    """
    Get the configuration for a specific provider or all providers.

    Args:
        provider: The provider to get configuration for (optional)
                  If not provided, returns configuration for all providers

    Returns:
        A dictionary containing the provider configuration

    Examples:
        from telert import get_config

        # Get Telegram config
        telegram_config = get_config("telegram")
        if telegram_config:
            print(f"Using bot token: {telegram_config['token'][:8]}...")

        # Get all configurations
        all_config = get_config()
    """
    config = MessagingConfig()

    if provider:
        if isinstance(provider, str):
            try:
                provider = Provider.from_string(provider)
            except ValueError:
                return {}

        return config.get_provider_config(provider)
    else:
        # Return all provider configs
        result = {}
        for p in Provider:
            p_config = config.get_provider_config(p)
            if p_config:
                result[p.value] = p_config

        # Include default provider
        default = config.get_default_provider()
        if default:
            result["default"] = default.value

        return result


def is_configured(provider: Optional[Union[str, Provider]] = None) -> bool:
    """
    Check if a specific provider or any provider is configured.

    Args:
        provider: The provider to check (optional)
                  If not provided, checks if any provider is configured

    Returns:
        True if configured, False otherwise

    Examples:
        from telert import is_configured, configure_teams

        if not is_configured("teams"):
            configure_teams("https://outlook.office.com/webhook/...")
    """
    config = MessagingConfig()

    if provider:
        if isinstance(provider, str):
            try:
                provider = Provider.from_string(provider)
            except ValueError:
                return False

        return config.is_provider_configured(provider)
    else:
        # Check if any provider is configured
        for p in Provider:
            if config.is_provider_configured(p):
                return True

        # Check for environment variables
        if os.environ.get("TELERT_TOKEN") and os.environ.get("TELERT_CHAT_ID"):
            return True
        if os.environ.get("TELERT_TEAMS_WEBHOOK"):
            return True
        if os.environ.get("TELERT_SLACK_WEBHOOK"):
            return True
        if os.environ.get("TELERT_DISCORD_WEBHOOK"):
            return True

        return False


def set_default_provider(provider: Union[str, Provider]) -> None:
    """
    Set the default messaging provider.

    Args:
        provider: The provider to set as default

    Examples:
        from telert import set_default_provider

        set_default_provider("slack")
    """
    config = MessagingConfig()

    if isinstance(provider, str):
        provider = Provider.from_string(provider)

    config.set_default_provider(provider)


def set_default_providers(providers: List[Union[str, Provider]]) -> None:
    """
    Set multiple default messaging providers in priority order.

    Args:
        providers: List of providers to set as defaults, in priority order

    Examples:
        from telert import set_default_providers

        # First try Slack, then fall back to Desktop notifications
        set_default_providers(["slack", "desktop"])
    """
    config = MessagingConfig()
    provider_enums = []

    for p in providers:
        if isinstance(p, str):
            try:
                provider_enums.append(Provider.from_string(p))
            except ValueError:
                # Skip invalid providers
                pass
        else:
            provider_enums.append(p)

    if provider_enums:
        config.set_default_providers(provider_enums)


def list_providers() -> List[Dict[str, Any]]:
    """
    List all configured providers.

    Returns:
        A list of dictionaries with provider information

    Examples:
        from telert import list_providers

        providers = list_providers()
        for p in providers:
            print(f"{p['name']} {'(default)' if p['is_default'] else ''}")
    """
    config = MessagingConfig()
    default = config.get_default_provider()
    result = []

    for p in Provider:
        if config.is_provider_configured(p):
            provider_config = config.get_provider_config(p)
            info = {
                "name": p.value,
                "is_default": (default == p),
                "config": provider_config,
            }
            result.append(info)

    return result


def send(
    message: str, 
    provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
    all_providers: bool = False
) -> Dict[str, bool]:
    """
    Send a message using configured provider(s).

    Args:
        message: The message text to send
        provider: The specific provider(s) to use (optional)
                 Can be a single provider or list of providers
                 If not provided, uses the default provider(s)
        all_providers: If True, sends to all configured providers

    Returns:
        A dictionary mapping provider names to success status

    Examples:
        from telert import send

        # Use default provider(s)
        send("Hello from Python!")

        # Specify a single provider
        send("Hello Teams!", provider="teams")
        
        # Send to multiple specific providers
        send("Important message", provider=["slack", "telegram"])
        
        # Send to all configured providers
        send("Critical alert", all_providers=True)

    Environment Variables:
        TELERT_DEFAULT_PROVIDER: Override default provider(s), comma-separated for multiple
        TELERT_TOKEN, TELERT_CHAT_ID: Override Telegram configuration
        TELERT_TEAMS_WEBHOOK: Override Teams configuration
        TELERT_SLACK_WEBHOOK: Override Slack configuration
        TELERT_DISCORD_WEBHOOK: Override Discord webhook URL
        TELERT_DISCORD_USERNAME: Override Discord bot name
        TELERT_DISCORD_AVATAR_URL: Override Discord bot avatar URL
        TELERT_PUSHOVER_TOKEN, TELERT_PUSHOVER_USER: Override Pushover configuration
        TELERT_AUDIO_FILE, TELERT_AUDIO_VOLUME: Override Audio configuration
        TELERT_DESKTOP_APP_NAME, TELERT_DESKTOP_ICON: Override Desktop configuration
    """
    try:
        # Convert string providers to Provider enums
        if provider is not None:
            if isinstance(provider, list):
                normalized_providers = []
                for p in provider:
                    if isinstance(p, str):
                        try:
                            normalized_providers.append(Provider.from_string(p))
                        except ValueError:
                            raise ValueError(f"Unknown provider: {p}")
                    else:
                        normalized_providers.append(p)
                provider = normalized_providers
            elif isinstance(provider, str):
                provider = Provider.from_string(provider)

        # Send the message
        return send_message(message, provider, all_providers)
    except Exception as e:
        raise RuntimeError(f"Failed to send message: {str(e)}")


class telert:
    """
    Context manager for sending notifications.

    When used as a context manager, it will time the code execution and
    send a notification when the block exits, including the execution time
    and any exceptions that were raised.

    Examples:
        # Basic usage with default message
        with telert():
            do_something_lengthy()

        # Custom message
        with telert("Database backup"):
            backup_database()

        # Handle return value
        with telert("Processing data") as t:
            result = process_data()
            t.result = result  # This will be included in the notification

        # Specify provider
        with telert("Teams message", provider="teams"):
            run_teams_task()
            
        # Send to multiple providers
        with telert("Important task", provider=["slack", "telegram"]):
            important_function()
            
        # Send to all configured providers
        with telert("Critical task", all_providers=True):
            critical_function()
    """

    def __init__(
        self,
        label: Optional[str] = None,
        only_fail: bool = False,
        include_traceback: bool = True,
        callback: Optional[Callable[[str], Any]] = None,
        provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
        all_providers: bool = False,
    ):
        """
        Initialize a telert context manager.

        Args:
            label: Optional label to identify this operation in the notification
            only_fail: If True, only send notification on failure (exception)
            include_traceback: If True, include traceback in notification when an exception occurs
            callback: Optional callback function to run with the notification message
            provider: Optional provider(s) to use for notifications
                     Can be a single provider or list of providers
            all_providers: If True, sends to all configured providers
        """
        self.label = label or "Python task"
        self.only_fail = only_fail
        self.include_traceback = include_traceback
        self.callback = callback
        self.result = None
        self.start_time = None
        self.exception = None
        self.all_providers = all_providers

        # Convert provider string to enum if needed
        self.provider = None
        if provider is not None:
            if isinstance(provider, list):
                # Convert a list of providers
                self.provider = []
                for p in provider:
                    if isinstance(p, str):
                        try:
                            self.provider.append(Provider.from_string(p))
                        except ValueError:
                            raise ValueError(f"Unknown provider: {p}")
                    else:
                        self.provider.append(p)
            elif isinstance(provider, str):
                try:
                    self.provider = Provider.from_string(provider)
                except ValueError:
                    raise ValueError(f"Unknown provider: {provider}")
            else:
                self.provider = provider

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = _human(time.time() - self.start_time)

        if exc_type is not None:
            self.exception = exc_val
            status = "failed"

            if self.include_traceback:
                tb = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
                message = (
                    f"{self.label} {status} in {duration}\n\n--- traceback ---\n{tb}"
                )
            else:
                message = f"{self.label} {status} in {duration}: {exc_val}"

            send(message, self.provider, self.all_providers)
            return False  # Re-raise the exception

        status = "completed"

        # Only send notification on success if only_fail is False
        if not self.only_fail:
            message = f"{self.label} {status} in {duration}"

            # Include the result if it was set
            if self.result is not None:
                result_str = str(self.result)
                if len(result_str) > 1000:
                    result_str = result_str[:997] + "..."
                message += f"\n\n--- result ---\n{result_str}"

            send(message, self.provider, self.all_providers)

        # If a callback was provided, call it with the message
        if self.callback and not self.only_fail:
            self.callback(message)

        return True  # Don't re-raise exception on success


def notify(
    label: Optional[str] = None,
    only_fail: bool = False,
    include_traceback: bool = True,
    provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
    all_providers: bool = False,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to send notifications when a function completes.

    Args:
        label: Optional label to identify this operation in the notification
        only_fail: If True, only send notification on failure (exception)
        include_traceback: If True, include traceback in notification when an exception occurs
        provider: Optional provider(s) to use for notifications
                 Can be a single provider or list of providers
        all_providers: If True, sends to all configured providers

    Returns:
        A decorator function

    Examples:
        @notify("Database backup")
        def backup_database():
            # Your code here

        @notify(only_fail=True)
        def critical_operation():
            # Your code here

        @notify(provider="teams")
        def teams_function():
            # This will notify via Teams
            
        @notify(provider=["slack", "telegram"])
        def multi_provider_function():
            # This will notify via both Slack and Telegram
            
        @notify(all_providers=True)
        def critical_function():
            # This will notify via all configured providers
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Use the function name if no label is provided
            func_label = label or func.__name__

            with telert(
                func_label,
                only_fail,
                include_traceback,
                provider=provider,
                all_providers=all_providers
            ) as t:
                result = func(*args, **kwargs)
                t.result = result
                return result

        return wrapper

    return decorator
