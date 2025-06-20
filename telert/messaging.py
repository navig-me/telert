# \!/usr/bin/env python3
"""
Messaging providers for telert.

This module contains implementations for different messaging services:
- Telegram
- Microsoft Teams
- Email (SMTP)
- Slack
- Audio (plays sound files)
- Desktop (system notifications)
"""

from __future__ import annotations

import enum
import json
import os
import pathlib
import platform
import re
import shutil
import smtplib
import subprocess
import tempfile
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Any, Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup

# Config paths
CONFIG_DIR = pathlib.Path(os.path.expanduser("~/.config/telert"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Default resources
DATA_DIR = pathlib.Path(os.path.dirname(__file__)) / "data"
DEFAULT_SOUND_FILE = DATA_DIR / "notification.mp3"  # Simple notification sound
DEFAULT_ICON_FILE = DATA_DIR / "notification-icon.png"  # Bell icon

NOTIFY_TIMEOUT = 5  # seconds


class Provider(enum.Enum):
    """Supported messaging providers."""

    TELEGRAM = "telegram"
    TEAMS = "teams"
    SLACK = "slack"
    AUDIO = "audio"
    DESKTOP = "desktop"
    PUSHOVER = "pushover"
    ENDPOINT = "endpoint"
    DISCORD = "discord"
    EMAIL = "email"

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

        # Check environment variables first
        if provider == Provider.TELEGRAM:
            token = os.environ.get("TELERT_TELEGRAM_TOKEN") or os.environ.get(
                "TELERT_TOKEN"
            )
            chat_id = os.environ.get("TELERT_TELEGRAM_CHAT_ID") or os.environ.get(
                "TELERT_CHAT_ID"
            )
            if token and chat_id:
                return {"token": token, "chat_id": chat_id}
        elif provider == Provider.TEAMS:
            webhook_url = os.environ.get("TELERT_TEAMS_WEBHOOK")
            if webhook_url:
                return {"webhook_url": webhook_url}
        elif provider == Provider.SLACK:
            webhook_url = os.environ.get("TELERT_SLACK_WEBHOOK")
            if webhook_url:
                return {"webhook_url": webhook_url}
        elif provider == Provider.PUSHOVER:
            token = os.environ.get("TELERT_PUSHOVER_TOKEN")
            user = os.environ.get("TELERT_PUSHOVER_USER")
            if token and user:
                return {"token": token, "user": user}
        elif provider == Provider.DISCORD:
            webhook_url = os.environ.get("TELERT_DISCORD_WEBHOOK")
            username = os.environ.get("TELERT_DISCORD_USERNAME")
            avatar_url = os.environ.get("TELERT_DISCORD_AVATAR_URL")
            config = {}
            if webhook_url:
                config["webhook_url"] = webhook_url
                if username:
                    config["username"] = username
                if avatar_url:
                    config["avatar_url"] = avatar_url
                return config
        elif provider == Provider.ENDPOINT:
            webhook_url = os.environ.get("TELERT_ENDPOINT_URL")
            if webhook_url:
                config = {"url": webhook_url}
                # Optional env vars
                method = os.environ.get("TELERT_ENDPOINT_METHOD")
                if method:
                    config["method"] = method
                headers = os.environ.get("TELERT_ENDPOINT_HEADERS")
                if headers:
                    try:
                        config["headers"] = json.loads(headers)
                    except json.JSONDecodeError:
                        # Fallback to simple header if not valid JSON
                        config["headers"] = {"Authorization": headers}
                return config
        elif provider == Provider.EMAIL:
            server = os.environ.get("TELERT_EMAIL_SERVER")
            username = os.environ.get("TELERT_EMAIL_USERNAME")
            password = os.environ.get("TELERT_EMAIL_PASSWORD")
            if server:
                config = {"server": server}
                if username:
                    config["username"] = username
                if password:
                    config["password"] = password
                    
                # Optional env vars
                port = os.environ.get("TELERT_EMAIL_PORT")
                if port:
                    try:
                        config["port"] = int(port)
                    except ValueError:
                        pass
                        
                from_addr = os.environ.get("TELERT_EMAIL_FROM")
                if from_addr:
                    config["from_addr"] = from_addr
                    
                to_addrs = os.environ.get("TELERT_EMAIL_TO")
                if to_addrs:
                    config["to_addrs"] = [addr.strip() for addr in to_addrs.split(",")]
                    
                subject = os.environ.get("TELERT_EMAIL_SUBJECT_TEMPLATE")
                if subject:
                    config["subject_template"] = subject
                    
                use_html = os.environ.get("TELERT_EMAIL_HTML")
                if use_html in ("1", "true", "yes"):
                    config["use_html"] = True
                    
                return config
        elif provider == Provider.AUDIO:
            sound_file = os.environ.get("TELERT_AUDIO_FILE")
            volume_str = os.environ.get("TELERT_AUDIO_VOLUME")
            if sound_file or volume_str:
                config = {}
                if sound_file:
                    config["sound_file"] = sound_file
                if volume_str:
                    try:
                        config["volume"] = float(volume_str)
                    except ValueError:
                        config["volume"] = 1.0
                return config or self._config.get(provider.value, {})
        elif provider == Provider.DESKTOP:
            app_name = os.environ.get("TELERT_DESKTOP_APP_NAME")
            icon_path = os.environ.get("TELERT_DESKTOP_ICON")
            if app_name or icon_path:
                config = {}
                if app_name:
                    config["app_name"] = app_name
                if icon_path:
                    config["icon_path"] = icon_path
                return config or self._config.get(provider.value, {})

        # Fall back to config file
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

    def get_providers(self) -> List[Provider]:
        """Return a list of all providers that are configured.

        A provider is considered configured if configuration exists in the
        configuration file or corresponding environment variables.
        """
        configured: List[Provider] = []
        for p in Provider:
            try:
                if self.is_provider_configured(p):
                    configured.append(p)
            except Exception:
                # Ignore any provider-specific errors when checking configuration
                pass
        return configured

    def get_default_providers(self) -> List[Provider]:
        """Get the default providers if configured.

        Returns a list of Provider enums in priority order.
        """
        # Check environment variable first
        env_default = os.environ.get("TELERT_DEFAULT_PROVIDER")
        if env_default:
            try:
                # Multiple providers can be specified with comma separation
                if "," in env_default:
                    providers = []
                    for p in env_default.split(","):
                        try:
                            providers.append(Provider.from_string(p.strip()))
                        except ValueError:
                            # Skip invalid providers
                            pass
                    if providers:
                        return providers
                else:
                    # Single provider
                    return [Provider.from_string(env_default)]
            except ValueError:
                # Invalid provider, fall through to config
                pass

        # Next check config file for "defaults" array (new format)
        defaults = self._config.get("defaults", [])
        if defaults and isinstance(defaults, list):
            providers = []
            for p in defaults:
                if p in [provider.value for provider in Provider]:
                    providers.append(Provider.from_string(p))
            if providers:
                return providers

        # Finally check for legacy "default" string
        default = self._config.get("default")
        if default and default in [p.value for p in Provider]:
            return [Provider.from_string(default)]

        # If no default is set but only one provider is configured, use that
        configured = [p for p in Provider if self.is_provider_configured(p)]
        if len(configured) == 1:
            return [configured[0]]

        return []

    def get_default_provider(self) -> Optional[Provider]:
        """Get the default provider if configured (legacy support).

        Returns the first default provider or None if none configured.
        """
        providers = self.get_default_providers()
        return providers[0] if providers else None

    def set_default_providers(self, providers: List[Union[Provider, str]]):
        """Set the default providers in priority order."""
        provider_values = []
        for provider in providers:
            if isinstance(provider, str):
                provider = Provider.from_string(provider)
            provider_values.append(provider.value)

        self._config["defaults"] = provider_values
        # Maintain backwards compatibility
        if provider_values:
            self._config["default"] = provider_values[0]
        else:
            # Remove both keys if empty
            self._config.pop("defaults", None)
            self._config.pop("default", None)
        self.save()

    def set_default_provider(self, provider: Union[Provider, str]):
        """Set a single default provider (legacy support)."""
        if isinstance(provider, str):
            provider = Provider.from_string(provider)

        self.set_default_providers([provider])
        self.save()


def prepare_telegram_html(message: str) -> str:
    """
    Prepare HTML-formatted messages for Telegram.
    
    Handles parsing and escaping HTML to ensure proper Telegram message formatting.
    Only a limited subset of HTML tags are supported by Telegram: 
    b, i, u, s, code, pre, a, and some others.
    
    Args:
        message: Message text that may contain HTML formatting
        
    Returns:
        Properly formatted message for Telegram with HTML parsing mode
    """
    if not message or message.isspace():
        return message
        
    # Parse the HTML
    soup = BeautifulSoup(message, 'html.parser')
    
    # Start with empty result
    result = ""
    
    # Process all elements recursively
    def process_node(node):
        if node.name is None:  # Text node
            # Escape HTML special characters in text content
            text = node.string or ""
            # HTML mode requires escaping of <, >, & characters
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return text
            
        # Only include supported tags, strip others but keep their content
        supported_tags = ['b', 'i', 'u', 's', 'code', 'pre', 'a']
        
        if node.name in supported_tags:
            tag_content = ''.join(process_node(child) for child in node.contents)
            
            # Special handling for links
            if node.name == 'a' and node.has_attr('href'):
                return f'<a href="{node["href"]}">{tag_content}</a>'
            else:
                return f'<{node.name}>{tag_content}</{node.name}>'
        else:
            # For unsupported tags, just return their content
            return ''.join(process_node(child) for child in node.contents)
    
    # Process all top-level nodes
    for node in soup.contents:
        result += process_node(node)
        
    return result


def prepare_telegram_plain_text(message: str) -> str:
    """
    Return the message unchanged for plain-text Telegram delivery.

    When *no* ``parse_mode`` is supplied the Telegram Bot API treats the text as
    raw UTF-8. Therefore no additional character escaping is required – adding
    back-slashes would make the message look cluttered (e.g. ``\(`` and
    ``\)``). We simply return the original message so that it appears exactly
    as passed by the caller.

    Args:
        message: Message text to send as-is.

    Returns:
        The unmodified message string.
    """
    return message


def prepare_telegram_markdown(message: str) -> str:
    """
    Prepare Markdown-formatted messages for Telegram.
    
    This function ensures proper escaping and formatting for Telegram's 
    MarkdownV2 mode, which has specific requirements for escaping characters.
    
    Args:
        message: Message text that may contain Markdown formatting
        
    Returns:
        Properly formatted message for Telegram with MarkdownV2 parsing mode
    """
    if not message:
        return message
        
    # Characters that need to be escaped in MarkdownV2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    # For MarkdownV2, we need to escape special characters but preserve markdown syntax
    # This is a simplified approach - for complex markdown, consider using a proper parser
    result = ""
    i = 0
    
    while i < len(message):
        char = message[i]
        
        # Handle code blocks (``` or single `)
        if char == '`':
            # Find the matching closing backtick(s)
            if i + 2 < len(message) and message[i:i+3] == '```':
                # Code block - find closing ```
                end = message.find('```', i + 3)
                if end != -1:
                    # Include the entire code block without escaping
                    result += message[i:end+3]
                    i = end + 3
                    continue
            else:
                # Inline code - find closing `
                end = message.find('`', i + 1)
                if end != -1:
                    # Include the entire inline code without escaping
                    result += message[i:end+1]
                    i = end + 1
                    continue
        
        # Handle other markdown formatting characters
        if char in ['*', '_', '~'] and i + 1 < len(message):
            # Check for double characters (**,  __, etc.)
            if message[i:i+2] in ['**', '__']:
                # Find matching closing tag
                tag = message[i:i+2]
                end = message.find(tag, i + 2)
                if end != -1:
                    # Include the formatted text, escaping content inside
                    content = message[i+2:end]
                    escaped_content = ''.join('\\' + c if c in special_chars and c not in ['*', '_'] else c for c in content)
                    result += tag + escaped_content + tag
                    i = end + 2
                    continue
            else:
                # Single character formatting
                end = message.find(char, i + 1)
                if end != -1:
                    # Include the formatted text, escaping content inside
                    content = message[i+1:end]
                    escaped_content = ''.join('\\' + c if c in special_chars and c != char else c for c in content)
                    result += char + escaped_content + char
                    i = end + 1
                    continue
        
        # Regular character - escape if it's a special character
        if char in special_chars:
            result += '\\' + char
        else:
            result += char
        i += 1
    
    return result


class TelegramProvider:
    """Provider for Telegram messaging."""

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token
        self.chat_id = chat_id
        self.max_message_length = 4096  # Telegram's max message length

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

    def send(self, message: str, parse_mode: Optional[str] = None, max_length: int = 4096) -> bool:
        """
        Send a message via Telegram.
        
        Args:
            message: The message text to send
            parse_mode: Optional parsing mode ('HTML', 'MarkdownV2', or None for plain text)
                       If not specified, will auto-detect HTML content
            max_length: Maximum message length before switching to file mode (default: 4096)
        """
        if not (self.token and self.chat_id):
            raise ValueError("Telegram provider not configured")
            
        # Check if message exceeds maximum length
        if len(message) > max_length:
            return self.send_as_file(message)

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        # Prepare the basic payload
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }
        
        # Handle message formatting based on parse_mode
        if parse_mode:
            # Explicit parse mode specified
            if parse_mode.upper() == "HTML":
                payload["parse_mode"] = "HTML"
                payload["text"] = prepare_telegram_html(message)
            elif parse_mode.upper() in ["MARKDOWN", "MARKDOWNV2"]:
                payload["parse_mode"] = "MarkdownV2"
                payload["text"] = prepare_telegram_markdown(message)
        else:
            # Auto-detect HTML tags
            has_html = any(tag in message for tag in ['<b>', '<i>', '<u>', '<s>', '<code>', '<pre>', '<a'])
            
            # Auto-detect Markdown indicators (simplified detection)
            has_markdown = ('**' in message or '*' in message or '__' in message or '_' in message or 
                          '```' in message or '`' in message or '~~' in message)
            
            # Prioritize HTML over Markdown if both are detected
            if has_html:
                payload["parse_mode"] = "HTML"
                payload["text"] = prepare_telegram_html(message)
            elif has_markdown:
                payload["parse_mode"] = "MarkdownV2"
                payload["text"] = prepare_telegram_markdown(message)
            else:
                # Plain text - escape special characters to prevent API errors
                payload["text"] = prepare_telegram_plain_text(message)
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=20,  # 20 second timeout
            )

            if response.status_code != 200:
                error_msg = (
                    f"Telegram API error {response.status_code}: {response.text}"
                )
                raise RuntimeError(error_msg)

            return True
        except requests.exceptions.Timeout:
            raise RuntimeError("Telegram API request timed out after 20 seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Telegram API connection error - please check your network connection"
            )
            
    def send_as_file(self, content: str, filename: Optional[str] = None) -> bool:
        """
        Send content as a file via Telegram.
        
        Args:
            content: The text content to send as a file
            filename: Optional custom filename (default: telert_message.txt)
            
        Returns:
            bool: True if successful
        """
        if not (self.token and self.chat_id):
            raise ValueError("Telegram provider not configured")
            
        url = f"https://api.telegram.org/bot{self.token}/sendDocument"
        
        # Create a temporary file with the content
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Prepare the file for upload
            files = {
                'document': (
                    filename or 'telert_message.txt',
                    open(temp_file_path, 'rb'),
                    'text/plain'
                )
            }
            
            data = {
                'chat_id': self.chat_id,
                'caption': 'Message from telert (sent as file due to length)'
            }
            
            response = requests.post(
                url,
                data=data,
                files=files,
                timeout=60  # Longer timeout for file uploads
            )
            
            # Close and remove the temporary file
            files['document'][1].close()
            os.unlink(temp_file_path)
            
            if response.status_code != 200:
                error_msg = (
                    f"Telegram API error {response.status_code}: {response.text}"
                )
                raise RuntimeError(error_msg)
                
            return True
            
        except Exception as e:
            # Make sure to clean up the temp file in case of errors
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
            raise e


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
                timeout=20,  # 20 second timeout
            )

            if response.status_code not in (200, 201, 202):
                error_msg = f"Teams API error {response.status_code}: {response.text}"
                raise RuntimeError(error_msg)

            return True
        except requests.exceptions.Timeout:
            raise RuntimeError("Teams API request timed out after 20 seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Teams API connection error - please check your network connection"
            )


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
                timeout=20,  # 20 second timeout
            )

            if response.status_code != 200:
                error_msg = f"Slack API error {response.status_code}: {response.text}"
                raise RuntimeError(error_msg)

            return True
        except requests.exceptions.Timeout:
            raise RuntimeError("Slack API request timed out after 20 seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Slack API connection error - please check your network connection"
            )


class AudioProvider:
    """Provider for audio notifications."""

    def __init__(
        self, sound_file: Optional[str] = None, volume: Optional[float] = None
    ):
        self.sound_file = sound_file or str(DEFAULT_SOUND_FILE)
        self.volume = volume or 1.0

    def configure_from_env(self) -> bool:
        """Configure from environment variables."""
        env_sound_file = os.environ.get("TELERT_AUDIO_FILE")
        if env_sound_file:
            self.sound_file = env_sound_file

        vol = os.environ.get("TELERT_AUDIO_VOLUME")
        if vol:
            try:
                self.volume = float(vol)
            except ValueError:
                self.volume = 1.0

        # Even if no env variables are set, we have a default sound file
        return True

    def configure_from_config(self, config: MessagingConfig) -> bool:
        """Configure from stored configuration."""
        provider_config = config.get_provider_config(Provider.AUDIO)
        if provider_config:
            if "sound_file" in provider_config:
                self.sound_file = provider_config.get("sound_file")
            self.volume = provider_config.get("volume", 1.0)

        # Even if no config is found, we have a default sound file
        return True

    def save_config(self, config: MessagingConfig):
        """Save configuration."""
        if self.sound_file:
            config.set_provider_config(
                Provider.AUDIO, {"sound_file": self.sound_file, "volume": self.volume}
            )

    def send(self, message: str) -> bool:
        """Play audio notification."""
        if not self.sound_file:
            self.sound_file = str(DEFAULT_SOUND_FILE)

        # Resolve the path - expanduser for user paths, or use as is for absolute paths
        if self.sound_file.startswith("~"):
            sound_file = os.path.expanduser(self.sound_file)
        else:
            sound_file = self.sound_file

        # Verify the file exists
        if not os.path.exists(sound_file):
            # If custom sound file doesn't exist, fall back to default
            if sound_file != str(DEFAULT_SOUND_FILE):
                print(
                    f"Warning: Sound file not found: {sound_file}. Using default sound."
                )
                sound_file = str(DEFAULT_SOUND_FILE)
                # If default also doesn't exist, raise error
                if not os.path.exists(sound_file):
                    raise RuntimeError(f"Default sound file not found: {sound_file}")
            else:
                raise RuntimeError(f"Sound file not found: {sound_file}")

        # Get file extension to determine type
        file_ext = os.path.splitext(sound_file)[1].lower()

        try:
            system = platform.system()

            # macOS approach
            if system == "Darwin":
                # afplay supports both WAV and MP3
                subprocess.run(["afplay", sound_file], check=True)
                return True

            # Linux approach - try multiple options
            elif system == "Linux":
                # MP3 file
                if file_ext == ".mp3":
                    # Try mpg123 first for MP3s
                    try:
                        subprocess.run(["mpg123", sound_file], check=True)
                        return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        pass

                # Try using paplay (PulseAudio)
                try:
                    subprocess.run(["paplay", sound_file], check=True)
                    return True
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass

                # Try using aplay (ALSA)
                try:
                    subprocess.run(["aplay", sound_file], check=True)
                    return True
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass

                # If we get here, we couldn't find a suitable player
                raise RuntimeError(
                    "No suitable audio player found on Linux (tried mpg123, paplay, aplay)"
                )

            # Windows approach
            elif system == "Windows":
                # For MP3 files on Windows, try to use an alternative player
                if file_ext == ".mp3":
                    try:
                        # Try with the optional playsound package first
                        try:
                            from playsound import playsound

                            playsound(sound_file)
                            return True
                        except ImportError:
                            pass

                        # Otherwise try with built-in tools
                        subprocess.run(
                            [
                                "powershell",
                                "-c",
                                f"(New-Object Media.SoundPlayer '{sound_file}').PlaySync()",
                            ],
                            check=True,
                        )
                        return True
                    except Exception:
                        # Fallback message
                        print(
                            "Warning: MP3 playback requires playsound package on Windows."
                        )
                        print("Install with: pip install telert[audio]")
                        # Continue with normal notification (no sound)
                        return True

                # For WAV files, use winsound
                import winsound

                winsound.PlaySound(sound_file, winsound.SND_FILENAME)
                return True

            else:
                raise RuntimeError(f"Unsupported platform: {system}")

        except Exception as e:
            raise RuntimeError(f"Audio playback error: {str(e)}")


class DesktopProvider:
    """Provider for desktop notifications."""

    def __init__(self, app_name: Optional[str] = None, icon_path: Optional[str] = None):
        self.app_name = app_name or "Telert"
        self.icon_path = icon_path or str(DEFAULT_ICON_FILE)

    def _notify_macos(self, message: str) -> bool:
        """Send a macOS notification, trying 3 helpers in order.

        • terminal-notifier  (best UX; brew install terminal-notifier)
        • osascript 'display notification …'            (fast)
        • osascript 'tell application "System Events"'  (older Macs / stricter setups)

        We surface every stderr line so you can see why it failed.
        """

        def _run(cmd: list[str]) -> bool:
            try:
                res = subprocess.run(
                    cmd,
                    timeout=NOTIFY_TIMEOUT,
                    text=True,
                    capture_output=True,
                )
                if res.returncode == 0:
                    return True
                # Non-zero exit: show why
                if res.stderr:
                    print("macOS-notify stderr:", res.stderr.strip())
            except subprocess.TimeoutExpired:
                print("macOS-notify timed-out on:", " ".join(cmd[:2]), "…")
            except FileNotFoundError:
                pass  # helper not installed
            return False

        # 1️⃣ terminal-notifier
        if shutil.which("terminal-notifier"):
            tn_cmd = [
                "terminal-notifier",
                "-title",
                self.app_name,
                "-message",
                message,
                "-sound",
                "default",
            ]
            if self.icon_path and os.path.exists(self.icon_path):
                tn_cmd += ["-appIcon", self.icon_path]
            if _run(tn_cmd):
                return True
            print(
                "Warning: Desktop notification could not be displayed using "
                "terminal-notifier. Falling back to AppleScript."
            )

        # Helper to build AppleScript command safely
        def _osascript(expr: str) -> bool:
            return _run(["osascript", "-e", expr])

        # 2️⃣ plain 'display notification'
        if _osascript(
            f"display notification {json.dumps(message)} "
            f"with title {json.dumps(self.app_name)}"
        ):
            return True

        # 3️⃣ older fallback via System Events
        if _osascript(
            f'tell application "System Events" to display notification '
            f"{json.dumps(message)} with title {json.dumps(self.app_name)}"
        ):
            return True

        print(
            "Hint: Make sure “osascript” (or your terminal app if you use terminal-notifier) "
            "has permission in  System Settings → Notifications."
        )
        return False

    def configure_from_env(self) -> bool:
        """Configure from environment variables."""
        self.app_name = os.environ.get("TELERT_DESKTOP_APP_NAME") or "Telert"
        self.icon_path = os.environ.get("TELERT_DESKTOP_ICON") or str(DEFAULT_ICON_FILE)
        return True  # Desktop notifications can work with defaults

    def configure_from_config(self, config: MessagingConfig) -> bool:
        """Configure from stored configuration."""
        provider_config = config.get_provider_config(Provider.DESKTOP)
        if provider_config:
            self.app_name = provider_config.get("app_name", "Telert")
            self.icon_path = provider_config.get("icon_path", str(DEFAULT_ICON_FILE))
            return True
        return False

    def save_config(self, config: MessagingConfig):
        """Save configuration."""
        config_data = {"app_name": self.app_name}
        if self.icon_path and self.icon_path != str(DEFAULT_ICON_FILE):
            config_data["icon_path"] = self.icon_path
        config.set_provider_config(Provider.DESKTOP, config_data)

    def send(self, message: str) -> bool:
        """Send a desktop notification."""
        system = platform.system()

        # Resolve icon path
        if not self.icon_path:
            self.icon_path = str(DEFAULT_ICON_FILE)

        # Get the actual icon path
        if self.icon_path.startswith("~"):
            icon = os.path.expanduser(self.icon_path)
        else:
            icon = self.icon_path

        # Check if custom icon exists
        if icon != str(DEFAULT_ICON_FILE) and not os.path.exists(icon):
            print(f"Warning: Icon file not found: {icon}. Using default icon.")
            icon = str(DEFAULT_ICON_FILE)
            # Check if default exists
            if not os.path.exists(icon):
                icon = None  # No icon if default is also missing

        try:
            if system == "Darwin":
                if self._notify_macos(message):
                    return True
                # fall through to raise below

            elif system == "Linux":
                if shutil.which("notify-send") is None:
                    print("Warning: Desktop notifications require notify-send on Linux")
                    return True  # keep old behaviour – don’t break the program

                cmd = ["notify-send", self.app_name, message]
                if self.icon_path:
                    cmd += ["--icon", self.icon_path]

                try:
                    subprocess.run(cmd, timeout=NOTIFY_TIMEOUT, check=True)
                    return True
                except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
                    print(f"Warning: Desktop notification could not be displayed: {e}")
                    return True

            elif system == "Windows":
                ps_script = f"""
                [Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications] > $null
                $app='{self.app_name}'
                $xml=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
                    [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $text=$xml.GetElementsByTagName('text')
                $text[0].AppendChild($xml.CreateTextNode($app))   | Out-Null
                $text[1].AppendChild($xml.CreateTextNode({json.dumps(message)})) | Out-Null
                $toast=[Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show($toast)
                """
                try:
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps_script],
                        timeout=NOTIFY_TIMEOUT,
                        check=True,
                    )
                    return True
                except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
                    print(f"Warning: Desktop notification could not be displayed: {e}")
                    return True

            # If we reach here the platform is unsupported or macOS branch failed
            raise RuntimeError(f"Desktop notifications not supported on {system}")

        except Exception as exc:
            # Preserve old behaviour: re-raise with same wording
            raise RuntimeError(f"Desktop notification error: {str(exc)}") from exc


class PushoverProvider:
    """Provider for Pushover messaging."""

    def __init__(self, token: Optional[str] = None, user: Optional[str] = None):
        self.token = token
        self.user = user

    def configure_from_env(self) -> bool:
        """Configure from environment variables."""
        self.token = os.environ.get("TELERT_PUSHOVER_TOKEN")
        self.user = os.environ.get("TELERT_PUSHOVER_USER")
        return bool(self.token and self.user)

    def configure_from_config(self, config: MessagingConfig) -> bool:
        """Configure from stored configuration."""
        provider_config = config.get_provider_config(Provider.PUSHOVER)
        if provider_config:
            self.token = provider_config.get("token")
            self.user = provider_config.get("user")
            return bool(self.token and self.user)
        return False

    def save_config(self, config: MessagingConfig):
        """Save configuration."""
        if self.token and self.user:
            config.set_provider_config(
                Provider.PUSHOVER, {"token": self.token, "user": self.user}
            )

    def send(self, message: str) -> bool:
        """Send a message via Pushover."""
        if not (self.token and self.user):
            raise ValueError("Pushover provider not configured")

        url = "https://api.pushover.net/1/messages.json"
        try:
            response = requests.post(
                url,
                data={
                    "token": self.token,
                    "user": self.user,
                    "message": message,
                },
                timeout=20,  # 20 second timeout
            )

            if response.status_code != 200:
                error_msg = (
                    f"Pushover API error {response.status_code}: {response.text}"
                )
                raise RuntimeError(error_msg)

            return True
        except requests.exceptions.Timeout:
            raise RuntimeError("Pushover API request timed out after 20 seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Pushover API connection error - please check your network connection"
            )


class DiscordProvider:
    """Provider for Discord messaging via webhooks."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        username: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ):
        self.webhook_url = webhook_url
        self.username = username or "Telert"  # Default username if not provided
        self.avatar_url = avatar_url

    def configure_from_env(self) -> bool:
        """Configure from environment variables."""
        self.webhook_url = os.environ.get("TELERT_DISCORD_WEBHOOK")

        # These are optional
        if os.environ.get("TELERT_DISCORD_USERNAME"):
            self.username = os.environ.get("TELERT_DISCORD_USERNAME")

        if os.environ.get("TELERT_DISCORD_AVATAR_URL"):
            self.avatar_url = os.environ.get("TELERT_DISCORD_AVATAR_URL")

        return bool(self.webhook_url)

    def configure_from_config(self, config: MessagingConfig) -> bool:
        """Configure from stored configuration."""
        provider_config = config.get_provider_config(Provider.DISCORD)
        if provider_config:
            self.webhook_url = provider_config.get("webhook_url")
            self.username = provider_config.get("username", "Telert")
            self.avatar_url = provider_config.get("avatar_url")
            return bool(self.webhook_url)
        return False

    def save_config(self, config: MessagingConfig):
        """Save configuration."""
        if self.webhook_url:
            config_data = {"webhook_url": self.webhook_url}

            # Only add these if they're not default values
            if self.username and self.username != "Telert":
                config_data["username"] = self.username

            if self.avatar_url:
                config_data["avatar_url"] = self.avatar_url

            config.set_provider_config(Provider.DISCORD, config_data)

    def send(self, message: str) -> bool:
        """Send a message via Discord webhook."""
        if not self.webhook_url:
            raise ValueError("Discord provider not configured")

        # Format message for Discord webhook
        payload = {
            "content": message,
        }

        # Add optional parameters if provided
        if self.username:
            payload["username"] = self.username

        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=20,  # 20 second timeout
            )

            if response.status_code not in (
                200,
                201,
                204,
            ):  # Discord returns 204 on success
                error_msg = f"Discord API error {response.status_code}: {response.text}"
                raise RuntimeError(error_msg)

            return True
        except requests.exceptions.Timeout:
            raise RuntimeError("Discord API request timed out after 20 seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Discord API connection error - please check your network connection"
            )


class EmailProvider:
    """Provider for email messaging via SMTP."""

    def __init__(
        self,
        server: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_addr: Optional[str] = None,
        to_addrs: Optional[List[str]] = None,
        subject_template: Optional[str] = None,
        use_html: bool = False,
    ):
        """Initialize SMTP email provider.
        
        Args:
            server: SMTP server address
            port: SMTP server port (default: 587 for TLS)
            username: SMTP username for authentication
            password: SMTP password for authentication
            from_addr: Sender email address
            to_addrs: List of recipient email addresses
            subject_template: Template for email subject line
            use_html: Whether to send HTML formatted emails
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.from_addr = from_addr or (username if '@' in (username or '') else None)
        self.to_addrs = to_addrs or []
        self.subject_template = subject_template or "Telert Alert: {label}"
        self.use_html = use_html
    
    def configure_from_env(self) -> bool:
        """Configure from environment variables."""
        self.server = os.environ.get("TELERT_EMAIL_SERVER", self.server)
        self.port = os.environ.get("TELERT_EMAIL_PORT", self.port)
        self.username = os.environ.get("TELERT_EMAIL_USERNAME", self.username)
        self.password = os.environ.get("TELERT_EMAIL_PASSWORD", self.password)
        self.from_addr = os.environ.get("TELERT_EMAIL_FROM", self.from_addr)
        
        to_env = os.environ.get("TELERT_EMAIL_TO", "")
        if to_env:
            self.to_addrs = [addr.strip() for addr in to_env.split(",")]
        
        self.subject_template = os.environ.get(
            "TELERT_EMAIL_SUBJECT_TEMPLATE", self.subject_template
        )
        self.use_html = os.environ.get("TELERT_EMAIL_HTML", "0") in ("1", "true", "yes")
        return bool(self.server and self.port and self.username and self.password and self.from_addr and self.to_addrs)

    def configure_from_config(self, config: MessagingConfig) -> bool:
        """Configure from stored configuration."""
        email_config = config.get_provider_config(Provider.EMAIL)
        if email_config:
            self.server = email_config.get("server", self.server)
            self.port = email_config.get("port", self.port)
            self.username = email_config.get("username", self.username)
            self.password = email_config.get("password", self.password)
            self.from_addr = email_config.get("from_addr", self.from_addr)
            self.to_addrs = email_config.get("to_addrs", self.to_addrs)
            self.subject_template = email_config.get("subject_template", self.subject_template)
            self.use_html = email_config.get("use_html", self.use_html)
            return True
        return False

    def save_config(self, config: MessagingConfig):
        """Save configuration."""
        config.set_provider_config(
            Provider.EMAIL,
            {
                "server": self.server,
                "port": self.port,
                "username": self.username,
                "password": self.password,
                "from_addr": self.from_addr,
                "to_addrs": self.to_addrs,
                "subject_template": self.subject_template,
                "use_html": self.use_html,
            },
        )

    def _format_subject(self, label: str = "Notification", status: str = "") -> str:
        """Format subject line based on template."""
        return self.subject_template.format(label=label, status=status)

    def _create_message(self, content: str, label: str = "Notification", status: str = "", 
                        attachment_content: Optional[str] = None, attachment_filename: Optional[str] = None) -> MIMEMultipart:
        """Create email message with proper formatting."""
        subject = self._format_subject(label, status)
        from_addr = self.from_addr or self.username or "telert@localhost"
        
        # Create message container
        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = ", ".join(self.to_addrs)
        msg["Subject"] = subject
        
        # Attach message body
        if self.use_html:
            msg.attach(MIMEText(content, "html"))
        else:
            msg.attach(MIMEText(content, "plain"))
        
        # Add attachment if provided
        if attachment_content and attachment_filename:
            attachment = MIMEApplication(attachment_content)
            attachment.add_header(
                "Content-Disposition", 
                f"attachment; filename={attachment_filename}"
            )
            msg.attach(attachment)
            
        return msg

    def send(self, message: str, **kwargs) -> bool:
        """Send an email notification.
        
        Args:
            message: Notification message content
            **kwargs: Additional parameters:
                - label: Command label or name
                - status: Status string (e.g., "✓ Success")
                - attachment_content: Optional file content to attach
                - attachment_filename: Optional filename for attachment
                
        Returns:
            bool: True if successful
        """
        if not self.server or not self.to_addrs:
            print("⚠️ Email not configured properly - missing server or recipients")
            return False
            
        try:
            label = kwargs.get("label", "Notification")
            status = kwargs.get("status", "")
            attachment_content = kwargs.get("attachment_content")
            attachment_filename = kwargs.get("attachment_filename")
            
            msg = self._create_message(
                message, 
                label, 
                status, 
                attachment_content, 
                attachment_filename
            )
            
            # Connect to SMTP server
            if self.port == 465:
                # SSL connection
                smtp = smtplib.SMTP_SSL(self.server, self.port, timeout=20)
            else:
                # Standard or TLS connection
                smtp = smtplib.SMTP(self.server, self.port, timeout=20)
                smtp.ehlo()
                if self.port == 587:
                    smtp.starttls()
                    smtp.ehlo()
            
            # Login if credentials provided
            if self.username and self.password:
                smtp.login(self.username, self.password)
            
            # Send the message
            smtp.sendmail(
                self.from_addr or self.username or "telert@localhost",
                self.to_addrs,
                msg.as_string()
            )
            smtp.quit()
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False

class EndpointProvider:
    """Provider for custom HTTP endpoint messaging."""

    def __init__(
        self,
        url: Optional[str] = None,
        method: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        payload_template: Optional[str] = None,
        name: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.url = url
        self.method = method or "POST"
        self.headers = headers or {}
        self.payload_template = payload_template or '{"text": "{message}"}'
        self.name = name or "Custom Endpoint"
        self.timeout = timeout or 20  # Default timeout: 20 seconds

    def configure_from_env(self) -> bool:
        """Configure from environment variables."""
        self.url = os.environ.get("TELERT_ENDPOINT_URL")

        if os.environ.get("TELERT_ENDPOINT_METHOD"):
            self.method = os.environ.get("TELERT_ENDPOINT_METHOD")

        if os.environ.get("TELERT_ENDPOINT_HEADERS"):
            try:
                self.headers = json.loads(
                    os.environ.get("TELERT_ENDPOINT_HEADERS", "{}")
                )
            except json.JSONDecodeError:
                # Invalid JSON, fallback to empty headers
                self.headers = {}

        if os.environ.get("TELERT_ENDPOINT_PAYLOAD"):
            self.payload_template = os.environ.get("TELERT_ENDPOINT_PAYLOAD")

        if os.environ.get("TELERT_ENDPOINT_NAME"):
            self.name = os.environ.get("TELERT_ENDPOINT_NAME")

        if os.environ.get("TELERT_ENDPOINT_TIMEOUT"):
            try:
                self.timeout = int(os.environ.get("TELERT_ENDPOINT_TIMEOUT", "20"))
            except ValueError:
                # Invalid timeout, use default
                self.timeout = 20

        return bool(self.url)

    def configure_from_config(self, config: MessagingConfig) -> bool:
        """Configure from stored configuration."""
        provider_config = config.get_provider_config(Provider.ENDPOINT)
        if provider_config:
            self.url = provider_config.get("url")
            self.method = provider_config.get("method", "POST")
            self.headers = provider_config.get("headers", {})
            self.payload_template = provider_config.get(
                "payload_template", '{"text": "{message}"}'
            )
            self.name = provider_config.get("name", "Custom Endpoint")
            self.timeout = provider_config.get("timeout", 20)
            return bool(self.url)
        return False

    def save_config(self, config: MessagingConfig):
        """Save configuration."""
        if self.url:
            config.set_provider_config(
                Provider.ENDPOINT,
                {
                    "url": self.url,
                    "method": self.method,
                    "headers": self.headers,
                    "payload_template": self.payload_template,
                    "name": self.name,
                    "timeout": self.timeout,
                },
            )

    def _replace_placeholders(self, template: str, message: str) -> str:
        """Replace placeholders in the template with actual values."""
        # Basic placeholders
        replacements = {
            "message": message,
            "status_code": "0",  # Default values for non-run contexts
            "duration_seconds": "0",
        }

        # Get current timestamp
        replacements["timestamp"] = str(int(time.time()))

        # Use a safer string formatting approach than direct format()
        result = template
        for key, value in replacements.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, value)

        return result

    def send(self, message: str) -> bool:
        """Send a message via the custom endpoint."""
        if not self.url:
            raise ValueError("Endpoint provider not configured")

        # Format URL if it contains placeholders
        url = self._replace_placeholders(self.url, message)

        # Prepare payload from template
        if self.payload_template:
            try:
                payload_str = self._replace_placeholders(self.payload_template, message)
                # Check if payload is valid JSON
                try:
                    payload = json.loads(payload_str)
                except json.JSONDecodeError:
                    # If not JSON, use as raw string body
                    payload = payload_str
            except Exception as e:
                raise RuntimeError(f"Failed to format payload template: {str(e)}")
        else:
            # Default to simple JSON with message
            payload = {"text": message}

        try:
            # Send the request based on the method
            if self.method.upper() == "GET":
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                )
            elif self.method.upper() == "POST":
                # Determine if we're sending JSON or form data
                if isinstance(payload, dict):
                    response = requests.post(
                        url,
                        json=payload,
                        headers=self.headers,
                        timeout=self.timeout,
                    )
                else:
                    # Raw string payload
                    response = requests.post(
                        url,
                        data=payload,
                        headers=self.headers,
                        timeout=self.timeout,
                    )
            else:
                # For other methods like PUT, DELETE, etc.
                response = requests.request(
                    self.method.upper(),
                    url,
                    json=payload if isinstance(payload, dict) else None,
                    data=None if isinstance(payload, dict) else payload,
                    headers=self.headers,
                    timeout=self.timeout,
                )

            # Check for successful response (2xx status codes)
            if response.status_code < 200 or response.status_code >= 300:
                error_msg = (
                    f"Endpoint API error {response.status_code}: {response.text}"
                )
                raise RuntimeError(error_msg)

            return True
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Endpoint API request timed out after {self.timeout} seconds"
            )
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Endpoint API connection error - please check your network connection"
            )
        except Exception as e:
            raise RuntimeError(f"Endpoint request failed: {str(e)}")


def get_provider(
    provider_name: Optional[Union[Provider, str]] = None,
) -> Union[
    TelegramProvider,
    TeamsProvider,
    SlackProvider,
    "AudioProvider",
    "DesktopProvider",
    PushoverProvider,
    EndpointProvider,
    DiscordProvider,
    EmailProvider,
]:
    """Get a configured messaging provider (single provider mode for backward compatibility)."""
    providers = get_providers(provider_name)
    if not providers:
        raise ValueError("No messaging provider configured")
    return providers[0]  # Return first provider for compatibility


def get_providers(
    provider_name: Optional[Union[Provider, str, List[Union[Provider, str]]]] = None,
) -> List[
    Union[
        TelegramProvider,
        TeamsProvider,
        SlackProvider,
        "AudioProvider",
        "DesktopProvider",
        PushoverProvider,
        EndpointProvider,
        DiscordProvider,
        EmailProvider,
    ]
]:
    """Get a list of configured messaging providers.

    Args:
        provider_name: Optional specific provider(s) to use.
                      Can be a single Provider or string, or a list of Providers/strings.
                      If None, will use default providers.

    Returns:
        A list of configured provider instances in priority order.
    """
    config = MessagingConfig()
    result_providers = []

    # Convert input to list of Provider enums
    provider_names = []

    if provider_name is None:
        # Use default providers if none specified
        provider_names = config.get_default_providers()
    elif isinstance(provider_name, list):
        # If a list was provided, convert to Provider enums
        for p in provider_name:
            if isinstance(p, str):
                try:
                    provider_names.append(Provider.from_string(p))
                except ValueError:
                    # Skip invalid providers
                    pass
            else:
                provider_names.append(p)
    else:
        # Single provider specified
        if isinstance(provider_name, str):
            provider_name = Provider.from_string(provider_name)
        provider_names = [provider_name]

    # If we have specific providers to use, create and configure them
    if provider_names:
        for provider_enum in provider_names:
            # Create provider instance
            if provider_enum == Provider.TELEGRAM:
                provider = TelegramProvider()
            elif provider_enum == Provider.TEAMS:
                provider = TeamsProvider()
            elif provider_enum == Provider.SLACK:
                provider = SlackProvider()
            elif provider_enum == Provider.PUSHOVER:
                provider = PushoverProvider()
            elif provider_enum == Provider.AUDIO:
                provider = AudioProvider()
            elif provider_enum == Provider.DESKTOP:
                provider = DesktopProvider()
            elif provider_enum == Provider.ENDPOINT:
                provider = EndpointProvider()
            elif provider_enum == Provider.DISCORD:
                provider = DiscordProvider()
            elif provider_enum == Provider.EMAIL:
                provider = EmailProvider()
            else:
                continue  # Skip unsupported providers

            # Try to configure from environment first
            if provider.configure_from_env():
                result_providers.append(provider)
            # Fall back to saved config
            elif provider.configure_from_config(config):
                result_providers.append(provider)

    # If no providers have been specified or successfully configured,
    # check environment variables to create providers on-the-fly
    if not result_providers:
        env_providers = []

        # Check each provider's environment variables
        if os.environ.get("TELERT_TOKEN") and os.environ.get("TELERT_CHAT_ID"):
            provider = TelegramProvider()
            if provider.configure_from_env():
                env_providers.append(provider)

        if os.environ.get("TELERT_TEAMS_WEBHOOK"):
            provider = TeamsProvider()
            if provider.configure_from_env():
                env_providers.append(provider)

        if os.environ.get("TELERT_SLACK_WEBHOOK"):
            provider = SlackProvider()
            if provider.configure_from_env():
                env_providers.append(provider)

        if os.environ.get("TELERT_PUSHOVER_TOKEN") and os.environ.get(
            "TELERT_PUSHOVER_USER"
        ):
            provider = PushoverProvider()
            if provider.configure_from_env():
                env_providers.append(provider)

        if (
            os.environ.get("TELERT_AUDIO_FILE", None) is not None
            or os.environ.get("TELERT_AUDIO_VOLUME", None) is not None
        ):
            provider = AudioProvider()
            if provider.configure_from_env():
                env_providers.append(provider)

        if (
            os.environ.get("TELERT_DESKTOP_APP_NAME", None) is not None
            or os.environ.get("TELERT_DESKTOP_ICON", None) is not None
        ):
            provider = DesktopProvider()
            if provider.configure_from_env():
                env_providers.append(provider)

        if os.environ.get("TELERT_ENDPOINT_URL", None) is not None:
            provider = EndpointProvider()
            if provider.configure_from_env():
                env_providers.append(provider)

        if os.environ.get("TELERT_DISCORD_WEBHOOK", None) is not None:
            provider = DiscordProvider()
            if provider.configure_from_env():
                env_providers.append(provider)

        if os.environ.get("TELERT_EMAIL_SERVER", None) is not None:
            provider = EmailProvider()
            if provider.configure_from_env():
                env_providers.append(provider)

        # If multiple providers are configured via env vars, check for preference order
        if env_providers:
            # If TELERT_DEFAULT_PROVIDER is set, reorder the providers accordingly
            env_default = os.environ.get("TELERT_DEFAULT_PROVIDER")
            if env_default and "," in env_default:
                # Get the order of providers from the environment variable
                ordered_types = []
                for p in env_default.split(","):
                    try:
                        ordered_types.append(Provider.from_string(p.strip()))
                    except ValueError:
                        pass

                # Reorder providers based on the specified order
                if ordered_types:
                    result_providers = []
                    # First add providers in the specified order
                    for p_type in ordered_types:
                        for provider in env_providers:
                            if isinstance(
                                provider,
                                {
                                    Provider.TELEGRAM: TelegramProvider,
                                    Provider.TEAMS: TeamsProvider,
                                    Provider.SLACK: SlackProvider,
                                    Provider.PUSHOVER: PushoverProvider,
                                    Provider.AUDIO: AudioProvider,
                                    Provider.DESKTOP: DesktopProvider,
                                    Provider.ENDPOINT: EndpointProvider,
                                    Provider.DISCORD: DiscordProvider,
                                    Provider.EMAIL: EmailProvider,
                                }[p_type],
                            ):
                                result_providers.append(provider)
                                break

                    # Then add any remaining providers not in the specified order
                    for provider in env_providers:
                        if provider not in result_providers:
                            result_providers.append(provider)
            else:
                # Use providers in the order they were discovered
                result_providers = env_providers

    return result_providers


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text while preserving the content.
    
    Args:
        text: Text containing HTML tags
        
    Returns:
        Text with HTML tags removed
    """
    if not text:
        return text
    
    # Use BeautifulSoup to strip HTML tags while preserving content
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()


def strip_markdown(text: str) -> str:
    """Remove Markdown formatting from text while preserving the content.
    
    Args:
        text: Text containing Markdown formatting
        
    Returns:
        Text with Markdown formatting removed
    """
    if not text:
        return text
    
    # Replace common Markdown patterns with their content
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    
    # Italic
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Code
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Strikethrough
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    
    # Links
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'\1', text)
    
    return text


def send_message(
    message: str,
    provider: Optional[Union[Provider, str, List[Union[Provider, str]]]] = None,
    all_providers: bool = False,
    parse_mode: Optional[str] = None,
) -> Dict[str, bool]:
    """Send a message using the specified or default provider(s).

    Args:
        message: The message to send
        provider: Optional specific provider(s) to use
                 Can be a single Provider/string or a list of Providers/strings
        all_providers: If True, sends to all configured providers
                      If False (default), uses specified provider(s) or default provider(s)
        parse_mode: Optional parsing mode for formatted messages ('HTML', 'MarkdownV2')
                   Currently only affects Telegram messages, for other providers formatting
                   is stripped unless the provider explicitly supports it

    Returns:
        A dictionary mapping provider names to success status
    """
    # If all_providers flag is True, get all configured providers
    if all_providers:
        config = MessagingConfig()
        providers_to_use = []
        for p in Provider:
            if config.is_provider_configured(p):
                try:
                    provider_instance = get_provider(p)
                    providers_to_use.append(provider_instance)
                except ValueError:
                    pass
    else:
        providers_to_use = get_providers(provider)

    if not providers_to_use:
        raise ValueError("No messaging provider configured")

    # Detect formatting in the message
    has_html = any(tag in message for tag in ['<b>', '<i>', '<u>', '<s>', '<code>', '<pre>', '<a'])
    has_markdown = ('**' in message or '*' in message or '__' in message or '_' in message or 
                  '```' in message or '`' in message or '~~' in message)
    
    # For backward compatibility, if there's only one provider, just call send
    if len(providers_to_use) == 1:
        provider_instance = providers_to_use[0]
        # Check if the provider is Telegram
        if isinstance(provider_instance, TelegramProvider):
            # If parse_mode is specified, use it directly
            if parse_mode:
                result = provider_instance.send(message, parse_mode)
            # Otherwise let Telegram's auto-detection handle it
            else:
                result = provider_instance.send(message)
        # For other providers, strip formatting if present and no explicit handling
        else:
            processed_message = message
            # If message has formatting, strip it for providers that don't support it
            if has_html:
                processed_message = strip_html_tags(message)
            elif has_markdown:
                processed_message = strip_markdown(message)
            # Send the processed message
            result = provider_instance.send(processed_message)
            
        return {providers_to_use[0].__class__.__name__: result}

    # Send to all specified providers and collect results
    results = {}
    exceptions = []

    for provider_instance in providers_to_use:
        provider_name = provider_instance.__class__.__name__
        try:
            # Check if the provider is Telegram
            if isinstance(provider_instance, TelegramProvider):
                # If parse_mode is specified, use it directly
                if parse_mode:
                    success = provider_instance.send(message, parse_mode)
                # Otherwise let Telegram's auto-detection handle it
                else:
                    success = provider_instance.send(message)
            # For other providers, strip formatting if present and no explicit handling
            else:
                processed_message = message
                # If message has formatting, strip it for providers that don't support it
                if has_html:
                    processed_message = strip_html_tags(message)
                elif has_markdown:
                    processed_message = strip_markdown(message)
                # Send the processed message
                success = provider_instance.send(processed_message)
                
            results[provider_name] = success
        except Exception as e:
            results[provider_name] = False
            exceptions.append(f"{provider_name}: {str(e)}")

    # If all providers failed, raise an exception with details
    if not any(results.values()):
        raise RuntimeError(f"All providers failed: {'; '.join(exceptions)}")

    return results


def _validate_webhook_url(url: str) -> bool:
    """Validate that a webhook URL is properly formatted."""
    if not url.startswith(("http://", "https://")):
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


def configure_providers(
    providers: List[Union[Provider, str, Dict[str, Any]]], set_as_defaults: bool = False
) -> bool:
    """Configure multiple messaging providers at once.

    Args:
        providers: A list of providers to configure. Each item can be:
                 - A Provider enum
                 - A provider name string
                 - A dict with "provider" key and provider-specific options
        set_as_defaults: If True, sets these providers as defaults in the order provided

    Returns:
        True if successful

    Example:
        configure_providers([
            {"provider": "telegram", "token": "123", "chat_id": "456"},
            {"provider": "slack", "webhook_url": "https://hooks.slack.com/..."},
            {"provider": "audio"}
        ], set_as_defaults=True)
    """
    config = MessagingConfig()
    configured_providers = []

    for p in providers:
        provider_enum = None
        provider_config = {}

        # Parse the provider specifications
        if isinstance(p, dict):
            # Dict format: {"provider": "name", ...options}
            if "provider" not in p:
                continue

            provider_name = p.pop("provider")
            try:
                if isinstance(provider_name, str):
                    provider_enum = Provider.from_string(provider_name)
                else:
                    provider_enum = provider_name
            except ValueError:
                continue  # Skip invalid providers

            provider_config = p  # Remaining options
        else:
            # Simple provider name or enum
            try:
                if isinstance(p, str):
                    provider_enum = Provider.from_string(p)
                else:
                    provider_enum = p
            except ValueError:
                continue  # Skip invalid providers

        # Configure this provider
        try:
            configure_provider(provider_enum, **provider_config)
            configured_providers.append(provider_enum)
        except Exception:
            # Skip providers that fail to configure
            pass

    # Set as defaults if requested
    if set_as_defaults and configured_providers:
        config.set_default_providers(configured_providers)

    return len(configured_providers) > 0


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

    elif provider == Provider.AUDIO:
        # Sound file is optional (default will be used if not provided)
        sound_file = kwargs.get("sound_file")

        # If a custom sound file is provided, validate it
        if sound_file:
            # Validate sound file exists if provided
            if not os.path.exists(os.path.expanduser(sound_file)):
                raise ValueError(f"Sound file not found: {sound_file}")

        provider_instance = AudioProvider(
            sound_file=sound_file, volume=kwargs.get("volume", 1.0)
        )

    elif provider == Provider.DESKTOP:
        app_name = kwargs.get("app_name", "Telert")
        icon_path = kwargs.get("icon_path")

        # Validate icon if provided
        if icon_path and not os.path.exists(os.path.expanduser(icon_path)):
            raise ValueError(f"Icon file not found: {icon_path}")

        provider_instance = DesktopProvider(app_name=app_name, icon_path=icon_path)

    elif provider == Provider.PUSHOVER:
        if "token" not in kwargs or "user" not in kwargs:
            raise ValueError("Pushover provider requires 'token' and 'user'")

        # Basic validation
        if not kwargs["token"] or not kwargs["user"]:
            raise ValueError("Pushover token and user cannot be empty")

        provider_instance = PushoverProvider(kwargs["token"], kwargs["user"])

    elif provider == Provider.DISCORD:
        if "webhook_url" not in kwargs:
            raise ValueError("Discord provider requires 'webhook_url'")

        # Validate webhook URL format
        _validate_webhook_url(kwargs["webhook_url"])

        # Create the provider instance
        provider_instance = DiscordProvider(
            webhook_url=kwargs["webhook_url"],
            username=kwargs.get("username"),
            avatar_url=kwargs.get("avatar_url"),
        )

    elif provider == Provider.ENDPOINT:
        if "url" not in kwargs:
            raise ValueError("Endpoint provider requires 'url'")

        # Validate URL format
        _validate_webhook_url(kwargs["url"])

        # Build the provider instance with all optional parameters
        method = kwargs.get("method", "POST")
        headers = kwargs.get("headers", {})
        payload_template = kwargs.get("payload_template", '{"text": "{message}"}')
        name = kwargs.get("name", "Custom Endpoint")
        timeout = kwargs.get("timeout", 20)

        # Validate method
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"]:
            raise ValueError(f"Invalid HTTP method: {method}")

        provider_instance = EndpointProvider(
            url=kwargs["url"],
            method=method,
            headers=headers,
            payload_template=payload_template,
            name=name,
            timeout=timeout,
        )
        
    elif provider == Provider.EMAIL:
        if "server" not in kwargs:
            raise ValueError("Email provider requires 'server'")
            
        # Get required parameters
        server = kwargs["server"]
        port = kwargs.get("port", 587)
        username = kwargs.get("username")
        password = kwargs.get("password")
        
        # Get optional parameters
        from_addr = kwargs.get("from_addr")
        to_addrs = kwargs.get("to_addrs", [])
        
        # Convert to_addrs from string if provided as comma-separated string
        if isinstance(to_addrs, str):
            to_addrs = [addr.strip() for addr in to_addrs.split(",")]
            
        subject_template = kwargs.get("subject_template", "Telert Alert: {label} - {status}")
        use_html = kwargs.get("use_html", False)
        
        # Validate port is a valid integer
        try:
            port = int(port)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid port number: {port}")
            
        # Create provider instance
        provider_instance = EmailProvider(
            server=server,
            port=port,
            username=username,
            password=password,
            from_addr=from_addr,
            to_addrs=to_addrs,
            subject_template=subject_template,
            use_html=use_html,
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Save the configuration
    provider_instance.save_config(config)

    # Handle default provider setting
    if kwargs.get("set_default", False):
        # Check if we should add to existing defaults or replace them
        if kwargs.get("add_to_defaults", False):
            # Add to existing defaults
            current_defaults = config.get_default_providers()
            if provider not in current_defaults:
                config.set_default_providers(current_defaults + [provider])
        else:
            # Set as the only default
            config.set_default_provider(provider)
    elif not config.get_default_providers():
        # If no defaults exist, set this as default
        config.set_default_provider(provider)

    return True
