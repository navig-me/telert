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
import re
import string
import time
from typing import Any, Dict, List, Optional, Union

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
    ENDPOINT = "endpoint"

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
            token = os.environ.get("TELERT_TELEGRAM_TOKEN") or os.environ.get("TELERT_TOKEN")
            chat_id = os.environ.get("TELERT_TELEGRAM_CHAT_ID") or os.environ.get("TELERT_CHAT_ID")
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
                timeout_seconds = 5  # Set a reasonable timeout for notification commands

                # Use a robust approach for macOS that works more consistently across terminal apps
                try:
                    # First try terminal-notifier if available (works well with many terminal apps)
                    try:
                        subprocess.run(
                            ["which", "terminal-notifier"],
                            check=True,
                            capture_output=True,
                            timeout=1
                        )
                        
                        # terminal-notifier exists, use it
                        subprocess.run(
                            [
                                "terminal-notifier",
                                "-title",
                                self.app_name,
                                "-message",
                                message,
                                "-sound",
                                "default"
                            ],
                            check=True,
                            capture_output=True,
                            timeout=timeout_seconds
                        )
                        return True
                    except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
                        # terminal-notifier not found or failed, suggest installation
                        print("Hint: For better desktop notifications on macOS, install terminal-notifier:")
                        print("      brew install terminal-notifier")
                        pass

                    # Try with direct AppleScript
                    # NSUserNotification through AppleScript
                    direct_script = f'''
                    on run argv
                        display notification "{escaped_message}" with title "{self.app_name}" sound name "Submarine"
                    end run
                    '''
                    
                    # Use a smaller timeout for this command to avoid hanging
                    try:
                        subprocess.run(
                            ["osascript", "-e", direct_script],
                            check=True,
                            capture_output=True,
                            timeout=timeout_seconds
                        )
                        return True
                    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                        # Continue to next approach
                        pass

                    # Fallback to System Events with explicit timeout
                    apple_script = f'''
                    tell application "System Events"
                        display notification "{escaped_message}" with title "{self.app_name}"
                    end tell
                    '''
                    
                    subprocess.run(
                        ["osascript", "-e", apple_script],
                        check=True,
                        capture_output=True,
                        timeout=timeout_seconds
                    )
                    return True
                    
                except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
                    # All notification methods failed, but don't block the program
                    print(f"Warning: Desktop notification could not be displayed: {str(e)}")
                    # Return True anyway since we don't want to block the program
                    return True

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
                self.headers = json.loads(os.environ.get("TELERT_ENDPOINT_HEADERS", "{}"))
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
            self.payload_template = provider_config.get("payload_template", '{"text": "{message}"}')
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
                error_msg = f"Endpoint API error {response.status_code}: {response.text}"
                raise RuntimeError(error_msg)

            return True
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Endpoint API request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Endpoint API connection error - please check your network connection"
            )
        except Exception as e:
            raise RuntimeError(f"Endpoint request failed: {str(e)}")


def get_provider(
    provider_name: Optional[Union[Provider, str]] = None,
) -> Union[
    TelegramProvider, TeamsProvider, SlackProvider, "AudioProvider", "DesktopProvider", PushoverProvider, EndpointProvider
]:
    """Get a configured messaging provider (single provider mode for backward compatibility)."""
    providers = get_providers(provider_name)
    if not providers:
        raise ValueError("No messaging provider configured")
    return providers[0]  # Return first provider for compatibility

def get_providers(
    provider_name: Optional[Union[Provider, str, List[Union[Provider, str]]]] = None,
) -> List[Union[
    TelegramProvider, TeamsProvider, SlackProvider, "AudioProvider", "DesktopProvider", PushoverProvider, EndpointProvider
]]:
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
                
        if os.environ.get("TELERT_PUSHOVER_TOKEN") and os.environ.get("TELERT_PUSHOVER_USER"):
            provider = PushoverProvider()
            if provider.configure_from_env():
                env_providers.append(provider)
                
        if os.environ.get("TELERT_AUDIO_FILE", None) is not None or os.environ.get("TELERT_AUDIO_VOLUME", None) is not None:
            provider = AudioProvider()
            if provider.configure_from_env():
                env_providers.append(provider)
                
        if os.environ.get("TELERT_DESKTOP_APP_NAME", None) is not None or os.environ.get("TELERT_DESKTOP_ICON", None) is not None:
            provider = DesktopProvider()
            if provider.configure_from_env():
                env_providers.append(provider)
                
        if os.environ.get("TELERT_ENDPOINT_URL", None) is not None:
            provider = EndpointProvider()
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
                            if isinstance(provider, {
                                Provider.TELEGRAM: TelegramProvider,
                                Provider.TEAMS: TeamsProvider,
                                Provider.SLACK: SlackProvider,
                                Provider.PUSHOVER: PushoverProvider,
                                Provider.AUDIO: AudioProvider,
                                Provider.DESKTOP: DesktopProvider,
                                Provider.ENDPOINT: EndpointProvider
                            }[p_type]):
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


def send_message(
    message: str, 
    provider: Optional[Union[Provider, str, List[Union[Provider, str]]]] = None,
    all_providers: bool = False
) -> Dict[str, bool]:
    """Send a message using the specified or default provider(s).
    
    Args:
        message: The message to send
        provider: Optional specific provider(s) to use
                 Can be a single Provider/string or a list of Providers/strings
        all_providers: If True, sends to all configured providers
                      If False (default), uses specified provider(s) or default provider(s)
    
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
                    # Skip providers that fail to configure
                    pass
    else:
        # Otherwise use specified or default providers
        providers_to_use = get_providers(provider)
    
    if not providers_to_use:
        raise ValueError("No messaging provider configured")
    
    # For backward compatibility, if there's only one provider, just call send
    if len(providers_to_use) == 1:
        result = providers_to_use[0].send(message)
        return {providers_to_use[0].__class__.__name__: result}
    
    # Send to all specified providers and collect results
    results = {}
    exceptions = []
    
    for provider_instance in providers_to_use:
        provider_name = provider_instance.__class__.__name__
        try:
            success = provider_instance.send(message)
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
    providers: List[Union[Provider, str, Dict[str, Any]]],
    set_as_defaults: bool = False
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
            timeout=timeout
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
