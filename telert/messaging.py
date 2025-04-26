# \!/usr/bin/env python3
"""
Messaging providers for telert.

This module contains implementations for different messaging services:
- Telegram
- Microsoft Teams
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
import subprocess
from typing import Any, Dict, Optional, Union

import requests

# Config paths
CONFIG_DIR = pathlib.Path(os.path.expanduser("~/.config/telert"))
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Default resources
DATA_DIR = pathlib.Path(os.path.dirname(__file__)) / "data"
DEFAULT_SOUND_FILE = DATA_DIR / "notification.mp3"  # Simple notification sound
DEFAULT_ICON_FILE = DATA_DIR / "notification-icon.png"  # Bell icon


class Provider(enum.Enum):
    """Supported messaging providers."""

    TELEGRAM = "telegram"
    TEAMS = "teams"
    SLACK = "slack"
    AUDIO = "audio"
    DESKTOP = "desktop"
    PUSHOVER = "pushover"

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
            # macOS
            if system == "Darwin":
                # Escape quotes and special characters in message
                escaped_message = message.replace('"', '\\"').replace("$", "\\$")

                # Enhanced AppleScript for better visibility
                # Use system sound to increase chances of notification being noticed
                apple_script = f'''
                display notification "{escaped_message}" with title "{self.app_name}" sound name "Submarine"
                '''

                try:
                    subprocess.run(
                        ["osascript", "-e", apple_script],
                        check=True,
                        capture_output=True,
                    )
                    return True
                except subprocess.SubprocessError:
                    # Fallback to simpler notification if the enhanced one fails
                    try:
                        simple_script = f'display notification "{escaped_message}" with title "{self.app_name}"'
                        subprocess.run(
                            ["osascript", "-e", simple_script],
                            check=True,
                            capture_output=True,
                        )
                        return True
                    except subprocess.SubprocessError:
                        # Ultimate fallback - use terminal-notifier if available
                        try:
                            subprocess.run(
                                [
                                    "terminal-notifier",
                                    "-title",
                                    self.app_name,
                                    "-message",
                                    message,
                                ],
                                check=True,
                            )
                            return True
                        except (subprocess.SubprocessError, FileNotFoundError):
                            raise RuntimeError(
                                "Could not show desktop notification on macOS"
                            )

            # Linux
            elif system == "Linux":
                # Try using notify-send (Linux)
                try:
                    cmd = ["notify-send", self.app_name, message]
                    if icon and os.path.exists(icon):
                        cmd.extend(["--icon", icon])
                    subprocess.run(cmd, check=True)
                    return True
                except (subprocess.SubprocessError, FileNotFoundError):
                    raise RuntimeError(
                        "Desktop notifications require notify-send on Linux"
                    )

            # Windows
            elif system == "Windows":
                # Use PowerShell for Windows 10+
                ps_script = f"""
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]  < /dev/null |  Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

                $app = '{self.app_name}'
                $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
                $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
                $text = $xml.GetElementsByTagName('text')
                $text[0].AppendChild($xml.CreateTextNode($app))
                $text[1].AppendChild($xml.CreateTextNode('{message}'))
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show($toast)
                """

                try:
                    subprocess.run(["powershell", "-Command", ps_script], check=True)
                    return True
                except (subprocess.SubprocessError, FileNotFoundError):
                    raise RuntimeError(
                        "Desktop notifications on Windows require PowerShell"
                    )
            else:
                raise RuntimeError(f"Desktop notifications not supported on {system}")

        except Exception as e:
            raise RuntimeError(f"Desktop notification error: {str(e)}")


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
                error_msg = f"Pushover API error {response.status_code}: {response.text}"
                raise RuntimeError(error_msg)

            return True
        except requests.exceptions.Timeout:
            raise RuntimeError("Pushover API request timed out after 20 seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Pushover API connection error - please check your network connection"
            )


def get_provider(
    provider_name: Optional[Union[Provider, str]] = None,
) -> Union[
    TelegramProvider, TeamsProvider, SlackProvider, "AudioProvider", "DesktopProvider", PushoverProvider
]:
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
        elif os.environ.get("TELERT_PUSHOVER_TOKEN") and os.environ.get("TELERT_PUSHOVER_USER"):
            provider = PushoverProvider()
            provider.configure_from_env()
            return provider
        elif os.environ.get("TELERT_AUDIO_FILE"):
            provider = AudioProvider()
            provider.configure_from_env()
            return provider
        elif os.environ.get("TELERT_DESKTOP_APP_NAME"):
            provider = DesktopProvider()
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
    elif provider_name == Provider.PUSHOVER:
        provider = PushoverProvider()
    elif provider_name == Provider.AUDIO:
        provider = AudioProvider()
    elif provider_name == Provider.DESKTOP:
        provider = DesktopProvider()
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

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # Save the configuration
    provider_instance.save_config(config)

    # Set as default if requested or if it's the first/only provider
    if kwargs.get("set_default", False) or not config.get_default_provider():
        config.set_default_provider(provider)

    return True
