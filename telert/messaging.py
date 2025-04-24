#!/usr/bin/env python3
"""
Messaging providers for telert.

This module contains implementations for different messaging services:
- Telegram
- Microsoft Teams
- Slack
"""

from __future__ import annotations

import enum
import json
import os
import pathlib
from typing import Any, Dict, Optional, Union

import requests

# Config paths
CONFIG_DIR = pathlib.Path(os.path.expanduser("~/.config/telert"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class Provider(enum.Enum):
    """Supported messaging providers."""

    TELEGRAM = "telegram"
    TEAMS = "teams"
    SLACK = "slack"

    @classmethod
    def from_string(cls, value: str) -> "Provider":
        """Convert string to Provider enum."""
        try:
            return cls(value.lower())
        except ValueError:
            valid_values = ", ".join([f"'{p.value}'" for p in cls])
            raise ValueError(
                f"Invalid provider: '{value}'. Valid values are: {valid_values}"
            )

    def __str__(self) -> str:
        return self.value


class MessagingConfig:
    """Configuration manager for messaging providers."""

    def __init__(self):
        self.config_file = CONFIG_DIR / "config.json"
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file.exists():
            return {}

        try:
            return json.loads(self.config_file.read_text())
        except json.JSONDecodeError:
            # If the file is corrupt, return empty config
            return {}

    def save(self):
        """Save configuration to file."""
        self.config_file.write_text(json.dumps(self._config, indent=2))

    def get_provider_config(self, provider: Union[Provider, str]) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        if isinstance(provider, str):
            provider = Provider.from_string(provider)

        return self._config.get(provider.value, {})

    def set_provider_config(
        self, provider: Union[Provider, str], config: Dict[str, Any]
    ):
        """Set configuration for a specific provider."""
        if isinstance(provider, str):
            provider = Provider.from_string(provider)

        self._config[provider.value] = config
        self.save()

    def is_provider_configured(self, provider: Union[Provider, str]) -> bool:
        """Check if a provider is configured."""
        return bool(self.get_provider_config(provider))

    def get_default_provider(self) -> Optional[Provider]:
        """Get the default provider if configured."""
        default = self._config.get("default")
        if default and default in [p.value for p in Provider]:
            return Provider.from_string(default)

        # If no default is set but only one provider is configured, use that
        configured = [p for p in Provider if self.is_provider_configured(p)]
        if len(configured) == 1:
            return configured[0]

        return None

    def set_default_provider(self, provider: Union[Provider, str]):
        """Set the default provider."""
        if isinstance(provider, str):
            provider = Provider.from_string(provider)

        self._config["default"] = provider.value
        self.save()


class TelegramProvider:
    """Provider for Telegram messaging."""

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token
        self.chat_id = chat_id

    def configure_from_env(self) -> bool:
        """Configure from environment variables."""
        self.token = os.environ.get("TELERT_TOKEN")
        self.chat_id = os.environ.get("TELERT_CHAT_ID")
        return bool(self.token and self.chat_id)

    def configure_from_config(self, config: MessagingConfig) -> bool:
        """Configure from stored configuration."""
        provider_config = config.get_provider_config(Provider.TELEGRAM)
        if provider_config:
            self.token = provider_config.get("token")
            self.chat_id = provider_config.get("chat_id")
            return bool(self.token and self.chat_id)
        return False

    def save_config(self, config: MessagingConfig):
        """Save configuration."""
        if self.token and self.chat_id:
            config.set_provider_config(
                Provider.TELEGRAM, {"token": self.token, "chat_id": self.chat_id}
            )

    def send(self, message: str) -> bool:
        """Send a message via Telegram."""
        if not (self.token and self.chat_id):
            raise ValueError("Telegram provider not configured")

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            response = requests.post(
                url, 
                json={"chat_id": self.chat_id, "text": message},
                timeout=20  # 20 second timeout
            )
            
            if response.status_code != 200:
                error_msg = f"Telegram API error {response.status_code}: {response.text}"
                raise RuntimeError(error_msg)
                
            return True
        except requests.exceptions.Timeout:
            raise RuntimeError("Telegram API request timed out after 20 seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Telegram API connection error - please check your network connection")


class TeamsProvider:
    """
    Provider for Microsoft Teams messaging.
    
    Uses Power Automate HTTP triggers to send messages to Teams channels.
    The payload format is compatible with HTTP request triggers that post
    to Teams channels.
    """

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def configure_from_env(self) -> bool:
        """Configure from environment variables."""
        self.webhook_url = os.environ.get("TELERT_TEAMS_WEBHOOK")
        return bool(self.webhook_url)

    def configure_from_config(self, config: MessagingConfig) -> bool:
        """Configure from stored configuration."""
        provider_config = config.get_provider_config(Provider.TEAMS)
        if provider_config:
            self.webhook_url = provider_config.get("webhook_url")
            return bool(self.webhook_url)
        return False

    def save_config(self, config: MessagingConfig):
        """Save configuration."""
        if self.webhook_url:
            config.set_provider_config(
                Provider.TEAMS, {"webhook_url": self.webhook_url}
            )

    def send(self, message: str) -> bool:
        """
        Send a message to Microsoft Teams via Power Automate HTTP trigger.
        
        The payload format is compatible with Power Automate HTTP triggers
        configured to post messages to Teams channels.
        """
        if not self.webhook_url:
            raise ValueError("Teams provider not configured")

        # Format message for Teams Power Automate flow
        payload = {
            "text": message,  # Main message content
            "summary": "Telert Notification",  # Used as notification title in Teams
        }

        try:
            response = requests.post(
                self.webhook_url, 
                json=payload,
                timeout=20  # 20 second timeout
            )
            
            if response.status_code not in (200, 201, 202):
                error_msg = f"Teams API error {response.status_code}: {response.text}"
                raise RuntimeError(error_msg)
                
            return True
        except requests.exceptions.Timeout:
            raise RuntimeError("Teams API request timed out after 20 seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Teams API connection error - please check your network connection")


class SlackProvider:
    """Provider for Slack messaging."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def configure_from_env(self) -> bool:
        """Configure from environment variables."""
        self.webhook_url = os.environ.get("TELERT_SLACK_WEBHOOK")
        return bool(self.webhook_url)

    def configure_from_config(self, config: MessagingConfig) -> bool:
        """Configure from stored configuration."""
        provider_config = config.get_provider_config(Provider.SLACK)
        if provider_config:
            self.webhook_url = provider_config.get("webhook_url")
            return bool(self.webhook_url)
        return False

    def save_config(self, config: MessagingConfig):
        """Save configuration."""
        if self.webhook_url:
            config.set_provider_config(
                Provider.SLACK, {"webhook_url": self.webhook_url}
            )

    def send(self, message: str) -> bool:
        """Send a message via Slack."""
        if not self.webhook_url:
            raise ValueError("Slack provider not configured")

        # Format message for Slack
        payload = {
            "text": message
            # Could add more formatting options here
        }

        try:
            response = requests.post(
                self.webhook_url, 
                json=payload,
                timeout=20  # 20 second timeout
            )
            
            if response.status_code != 200:
                error_msg = f"Slack API error {response.status_code}: {response.text}"
                raise RuntimeError(error_msg)
                
            return True
        except requests.exceptions.Timeout:
            raise RuntimeError("Slack API request timed out after 20 seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Slack API connection error - please check your network connection")


def get_provider(
    provider_name: Optional[Union[Provider, str]] = None,
) -> Union[TelegramProvider, TeamsProvider, SlackProvider]:
    """Get a configured messaging provider."""
    config = MessagingConfig()

    # If no provider specified, use default or first configured
    if provider_name is None:
        provider_name = config.get_default_provider()
        if provider_name is None:
            # Try to use any configured provider
            for p in Provider:
                if config.is_provider_configured(p):
                    provider_name = p
                    break

    if provider_name is None:
        # If still no provider, check environment variables
        if os.environ.get("TELERT_TOKEN") and os.environ.get("TELERT_CHAT_ID"):
            provider = TelegramProvider()
            provider.configure_from_env()
            return provider
        elif os.environ.get("TELERT_TEAMS_WEBHOOK"):
            provider = TeamsProvider()
            provider.configure_from_env()
            return provider
        elif os.environ.get("TELERT_SLACK_WEBHOOK"):
            provider = SlackProvider()
            provider.configure_from_env()
            return provider
        else:
            raise ValueError("No messaging provider configured")

    # Convert string to Provider enum if needed
    if isinstance(provider_name, str):
        provider_name = Provider.from_string(provider_name)

    # Create the appropriate provider
    if provider_name == Provider.TELEGRAM:
        provider = TelegramProvider()
    elif provider_name == Provider.TEAMS:
        provider = TeamsProvider()
    elif provider_name == Provider.SLACK:
        provider = SlackProvider()
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")

    # Try to configure from environment first
    if not provider.configure_from_env():
        # Fall back to saved config
        if not provider.configure_from_config(config):
            raise ValueError(f"Provider {provider_name} is not configured")

    return provider


def send_message(message: str, provider: Optional[Union[Provider, str]] = None) -> bool:
    """Send a message using the specified or default provider."""
    return get_provider(provider).send(message)


def _validate_webhook_url(url: str) -> bool:
    """Validate that a webhook URL is properly formatted."""
    if not url.startswith(('http://', 'https://')):
        raise ValueError("Webhook URL must start with http:// or https://")
    
    # Basic URL format validation
    try:
        # Parse the URL to ensure it's valid
        parsed = requests.utils.urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError("Invalid webhook URL format")
        return True
    except Exception:
        raise ValueError("Invalid webhook URL format")


def configure_provider(provider: Union[Provider, str], **kwargs):
    """Configure a messaging provider."""
    config = MessagingConfig()

    if isinstance(provider, str):
        provider = Provider.from_string(provider)

    if provider == Provider.TELEGRAM:
        if "token" not in kwargs or "chat_id" not in kwargs:
            raise ValueError("Telegram provider requires 'token' and 'chat_id'")
            
        # Basic validation
        if not kwargs["token"] or not kwargs["chat_id"]:
            raise ValueError("Telegram token and chat_id cannot be empty")

        provider_instance = TelegramProvider(kwargs["token"], kwargs["chat_id"])

    elif provider == Provider.TEAMS:
        if "webhook_url" not in kwargs:
            raise ValueError("Teams provider requires 'webhook_url'")
            
        # Validate webhook URL format
        _validate_webhook_url(kwargs["webhook_url"])
        provider_instance = TeamsProvider(kwargs["webhook_url"])

    elif provider == Provider.SLACK:
        if "webhook_url" not in kwargs:
            raise ValueError("Slack provider requires 'webhook_url'")
            
        # Validate webhook URL format
        _validate_webhook_url(kwargs["webhook_url"])
        provider_instance = SlackProvider(kwargs["webhook_url"])

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Save the configuration
    provider_instance.save_config(config)

    # Set as default if requested or if it's the first/only provider
    if kwargs.get("set_default", False) or not config.get_default_provider():
        config.set_default_provider(provider)

    return True
