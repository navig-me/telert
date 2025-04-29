# telert – Alerts for Your Terminal

**Version 0.1.22** 

[![GitHub Stars](https://img.shields.io/github/stars/navig-me/telert?style=social)](https://github.com/navig-me/telert/stargazers)
[![PyPI version](https://img.shields.io/pypi/v/telert)](https://pypi.org/project/telert/)
[![Downloads](https://static.pepy.tech/personalized-badge/telert?period=month&units=international_system&left_color=grey&right_color=blue&left_text=downloads)](https://pepy.tech/project/telert)
[![License](https://img.shields.io/github/license/navig-me/telert)](https://github.com/navig-me/telert/blob/main/LICENSE)
[![Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-Use%20this%20Action-blue?logo=github)](https://github.com/marketplace/actions/telert-run)

## 📱 Overview

Telert is a lightweight utility that sends notifications when your terminal commands or Python code completes. It supports multiple notification channels:

- **Messaging Apps**: Telegram, Microsoft Teams, Slack
- **Mobile Devices**: Pushover (Android & iOS)
- **Local Notifications**: Desktop notifications, Audio alerts
- **Custom Integrations**: HTTP endpoints for any service

Perfect for long-running tasks, remote servers, CI pipelines, or monitoring critical code.

Telert can also be deployed as an API on [Replit](https://replit.com/@mihir95/Telert-CLI-Notifier), [Railway](https://railway.com/template/A_kYXt?referralCode=vj4bEA), [Render](https://render.com/deploy?repo=https://github.com/navig-me/telert-notifier) or [Fly.io](https://github.com/navig-me/telert-notifier?tab=readme-ov-file#-deploy-manually-on-flyio) with one-click deployments.

<img src="https://github.com/navig-me/telert/raw/main/telert-demo.svg" alt="telert demo" width="800">

## 📋 Table of Contents
- [Installation & Quick Start](#-installation--quick-start)
- [Notification Providers](#-notification-providers)
  - [Telegram](#telegram-setup)
  - [Microsoft Teams](#microsoft-teams-setup)
  - [Slack](#slack-setup)
  - [Pushover](#pushover-setup)
  - [Custom HTTP Endpoints](#custom-http-endpoint-setup)
  - [Audio Alerts](#audio-alerts-setup)
  - [Desktop Notifications](#desktop-notifications-setup)
  - [Managing Multiple Providers](#managing-multiple-providers)
- [Features](#-features)
- [Usage Guide](#-usage-guide)
  - [Command Line Interface](#command-line-interface-cli)
  - [Python API](#python-api)
- [API Deployment to Cloud Platforms](#-api-deployment-to-cloud-platforms)
- [Troubleshooting](#-troubleshooting)
- [Environment Variables](#-environment-variables)
- [Use Cases](#-use-cases-and-tips)
- [Contributing](#-contributing--license)

## 🚀 Installation & Quick Start

```bash
# Install from PyPI (works on any OS with Python 3.8+)
pip install telert

# Configure a notification provider (example with desktop notifications)
telert config desktop --app-name "My App" --set-default

# Test your configuration
telert status

# Basic usage - pipe command output
long_running_command | telert "Command finished!"

# Or wrap a command to capture status and timing
telert run --label "Database Backup" pg_dump -U postgres mydb > backup.sql
```

### Key benefits

- 📱 Get notified when commands finish (even when away from your computer)
- ⏱️ See exactly how long commands or code took to run
- 🚦 Capture success/failure status codes and tracebacks
- 📃 View command output snippets directly in your notifications
- 🔄 Works with shell commands, pipelines, and Python code

## 📲 Notification Providers

Telert supports multiple notification services. Choose one or more based on your needs:

### Telegram Setup

Telegram uses the official Bot API for reliable delivery.

```bash
# After creating a bot with @BotFather and getting your chat ID
telert config telegram --token "<token>" --chat-id "<chat-id>" --set-default
telert status  # Test your configuration
```

[**Detailed Telegram Setup Guide**](https://github.com/navig-me/telert/blob/main/TELEGRAM.md)

### Microsoft Teams Setup

Teams integration uses Power Automate (Microsoft Flow) to deliver notifications.

```bash
# After creating a HTTP trigger flow in Power Automate
telert config teams --webhook-url "<flow-http-url>" --set-default
telert status  # Test your configuration
```

[**Detailed Microsoft Teams Setup Guide**](https://github.com/navig-me/telert/blob/main/TEAMS.md)

### Slack Setup

Slack integration uses incoming webhooks for channel notifications.

```bash
# After creating a webhook at api.slack.com
telert config slack --webhook-url "<webhook-url>" --set-default
telert status  # Test your configuration
```

[**Detailed Slack Setup Guide**](https://github.com/navig-me/telert/blob/main/SLACK.md)

### Pushover Setup

Pushover provides mobile notifications to Android and iOS devices.

```bash
# After signing up at pushover.net and creating an app
telert config pushover --token "<app-token>" --user "<user-key>" --set-default
telert status  # Test your configuration
```

[**Detailed Pushover Setup Guide**](https://github.com/navig-me/telert/blob/main/PUSHOVER.md)

### Custom HTTP Endpoint Setup

Send to any HTTP service with configurable URLs, headers, and payload templates.

```bash
# Basic configuration
telert config endpoint --url "https://api.example.com/notify" --set-default

# Advanced configuration example
telert config endpoint \
  --url "https://api.example.com/notify/{status_code}" \
  --method POST \
  --header "Authorization: Bearer abc123" \
  --payload-template '{"text": "{message}"}' \
  --name "My Service" \
  --set-default
```

[**Detailed Custom Endpoint Guide**](https://github.com/navig-me/telert/blob/main/ENDPOINT.md)

### Audio Alerts Setup

Play a sound notification when your command completes.

```bash
# Use the built-in sound
telert config audio --set-default

# Or use a custom sound file with volume control
telert config audio --sound-file "/path/to/alert.wav" --volume 0.8 --set-default
```

Works on all platforms; for MP3 support on Windows: `pip install telert[audio]`

### Desktop Notifications Setup

Show notifications in your operating system's notification center.

```bash
# Configure with default icon
telert config desktop --app-name "My App" --set-default

# Or with custom icon
telert config desktop --app-name "My App" --icon-path "/path/to/icon.png" --set-default
```

**macOS users**: Install terminal-notifier for better reliability: `brew install terminal-notifier`  
**Linux users**: Install notify-send: `sudo apt install libnotify-bin` (Debian/Ubuntu)

### Managing Multiple Providers

Configure and use multiple notification services at once:

```bash
# Set multiple default providers in priority order
telert config set-defaults --providers "slack,desktop,audio"

# Add a provider to existing defaults without replacing them
telert config audio --sound-file "/path/to/sound.mp3" --add-to-defaults

# Send to multiple providers 
telert send --provider "slack,telegram" "Multi-provider message"

# Send to all configured providers
telert send --all-providers "Important alert!"
```

Configuration is stored in `~/.config/telert/config.json` and can be overridden with environment variables.

---

## ✨ Features

| Mode           | What it does | Example |
|----------------|--------------|---------|
| **Run**        | Wraps a command, times it, sends notification with exit code. | `telert run --label "RSYNC" -- rsync -a /src /dst` |
| **Filter**     | Reads from stdin so you can pipe command output. | `long_job \| telert "compile done"` |
| **Hook**       | Generates a Bash snippet so **every** command > *N* seconds notifies automatically. | `eval "$(telert hook -l 30)"` |
| **Send**       | Low-level "send arbitrary text" helper. | `telert send --provider slack "Build complete"` |
| **Python API** | Use directly in Python code with context managers and decorators. | `from telert import telert, send, notify` |
| **Multi-provider** | Configure and use multiple notification services (Telegram, Teams, Slack, Pushover, Audio, Desktop). | `telert config desktop --app-name "My App"` |

---

## 📋 Usage Guide

### Command Line Interface (CLI)

> **Note**: When using the `run` command, do not use double dashes (`--`) to separate telert options from the command to run. The correct syntax is `telert run [options] command`, not `telert run [options] -- command`.

#### Run Mode
Wrap any command to receive a notification when it completes:

```bash
# Basic usage - notify when command finishes (uses default provider)
telert run npm run build

# Add a descriptive label
telert run --label "DB Backup" pg_dump -U postgres mydb > backup.sql

# Show notification only when a command fails
telert run --only-fail rsync -av /src/ /backup/

# Send to a specific provider
telert run --provider teams --label "ML Training" python train_model.py

# Send to multiple specific providers
telert run --provider "slack,telegram" --label "CI Build" make all

# Send to all configured providers
telert run --all-providers --label "Critical Backup" backup.sh

# Custom notification message
telert run --message "Training complete! 🎉" python train_model.py

# Run in silent mode (output only in notification, not displayed in terminal)
TELERT_SILENT=1 telert run python long_process.py
```

Command output is shown in real-time by default. Use `TELERT_SILENT=1` environment variable if you want to capture output for the notification but not display it in the terminal.

#### Filter Mode
Perfect for adding notifications to existing pipelines:

```bash
# Send notification when a pipeline completes (uses default provider)
find . -name "*.log" | xargs grep "ERROR" | telert "Error check complete"

# Process and notify with specific provider
cat large_file.csv | awk '{print $3}' | sort | uniq -c | telert --provider slack "Data processing finished"

# Send to multiple providers
find /var/log -name "*.err" | grep -i "critical" | telert --provider "telegram,desktop" "Critical errors found"

# Send to all providers
backup.sh | telert --all-providers "Database backup complete"
```

> **Note:** In filter mode, the exit status is not captured since commands in a pipeline run in separate processes.
> For exit status tracking, use Run mode or add explicit status checking in your script.

#### Send Mode
Send custom messages from scripts to any provider:

```bash
# Simple text message (uses default provider(s))
telert send "Server backup completed"

# Send to a specific provider
telert send --provider teams "Build completed"
telert send --provider slack "Deployment started"

# Send to multiple specific providers at once
telert send --provider "telegram,slack,desktop" "Critical alert!"

# Send to all configured providers
telert send --all-providers "System restart required"

# Show details of message delivery with verbose flag
telert send --all-providers --verbose "Message sent to all providers"

# Send status from a script
if [ $? -eq 0 ]; then
  telert send "✅ Deployment successful"
else
  # Send failure notification to all providers
  telert send --all-providers "❌ Deployment failed with exit code $?"
fi
```

#### Shell Hook
Get notifications for ALL commands that take longer than a certain time:

```bash
# Configure Bash to notify for any command taking longer than 30 seconds
eval "$(telert hook -l 30)"

# Add to your .bashrc for persistent configuration
echo 'eval "$(telert hook -l 30)"' >> ~/.bashrc
```

#### CLI Help
```bash
# View all available commands
telert --help

# Get help for a specific command
telert run --help
```

### Using Shell Built-ins with telert

When using `telert run` with shell built-in commands like `source`, you'll need to wrap them in a bash call:

```bash
# This will fail
telert run source deploy.sh

# This works
telert run bash -c "source deploy.sh"
```

For convenience, we provide a wrapper script that automatically handles shell built-ins:

```bash
# Download the wrapper script
curl -o ~/bin/telert-wrapper https://raw.githubusercontent.com/navig-me/telert/main/telert-wrapper.sh
chmod +x ~/bin/telert-wrapper

# Now you can use shell built-ins directly
telert-wrapper run source deploy.sh
```

### Python API

#### Configuration
```python
from telert import (
    configure_telegram, configure_teams, configure_slack, configure_pushover,
    configure_audio, configure_desktop, configure_providers,
    set_default_provider, set_default_providers, 
    is_configured, get_config, list_providers
)

# Configure one or more providers
configure_telegram("<token>", "<chat-id>")
configure_teams("<webhook-url>")
configure_slack("<webhook-url>")
configure_pushover("<app-token>", "<user-key>")
configure_audio()  # Uses built-in sound
# Or with custom sound: configure_audio("/path/to/alert.wav", volume=0.8)

# Configure custom HTTP endpoint
from telert.messaging import Provider, configure_provider
configure_provider(
    Provider.ENDPOINT,
    url="https://api.example.com/notify",
    method="POST",
    headers={"Authorization": "Bearer abc123"},
    payload_template='{"text": "{message}"}',
    name="My API",
    timeout=30
)

# Configure provider and add to existing defaults (without replacing them)
configure_desktop("My App", add_to_defaults=True)  # Uses built-in icon

# Configure multiple providers at once
configure_providers([
    {"provider": "telegram", "token": "<token>", "chat_id": "<chat-id>"},
    {"provider": "slack", "webhook_url": "<webhook-url>"},
    {"provider": "audio"}
], set_as_defaults=True)  # Optionally set these as defaults in the given order

# Check if specific provider is configured
if not is_configured("audio"):
    configure_audio("/path/to/bell.wav")

# Get configuration for a specific provider
desktop_config = get_config("desktop")
print(f"Using app name: {desktop_config['app_name']}")

# List all providers and see which is default
providers = list_providers()
for p in providers:
    print(f"{p['name']} {'(default)' if p['is_default'] else ''}")

# Set a single default provider
set_default_provider("audio")

# Set multiple default providers in priority order
set_default_providers(["slack", "desktop", "audio"])
```

#### Simple Messaging
```python
from telert import send

# Send using default provider(s)
send("Script started")  # Uses default providers in configured priority order

# Send to specific provider
send("Processing completed with 5 records updated", provider="teams")

# Send to multiple specific providers
send("Critical error detected!", provider=["slack", "telegram"])

# Send to all configured providers
send("Major system error", all_providers=True)

# Provider-specific examples
send("Send to mobile device", provider="pushover")
send("Play a sound alert", provider="audio")
send("Show a desktop notification", provider="desktop")
send("Send to custom HTTP endpoint", provider="endpoint")

# Check delivery results
results = send("Important message", provider=["slack", "telegram"])
for provider, success in results.items():
    if not success:
        print(f"Failed to send to {provider}")
```

#### Context Manager
The `telert` context manager times code execution and sends a notification when the block completes:

```python
from telert import telert
import time

# Basic usage
with telert("Data processing"):
    # Your long-running code here
    time.sleep(5)

# Include results in the notification
with telert("Calculation") as t:
    result = sum(range(1000000))
    t.result = {"sum": result, "status": "success"}

# Only notify on failure
with telert("Critical operation", only_fail=True):
    # This block will only send a notification if an exception occurs
    risky_function()
    
# Specify a provider
with telert("Teams notification", provider="teams"):
    # This will notify via Teams regardless of the default provider
    teams_specific_operation()
    
# Send to multiple providers
with telert("Important calculation", provider=["slack", "telegram"]):
    # This will send to both Slack and Telegram
    important_calculation()
    
# Send to all configured providers
with telert("Critical operation", all_providers=True):
    # This will send to all configured providers
    critical_function()
    
# Use audio notifications
with telert("Long calculation", provider="audio"):
    # This will play a sound when done
    time.sleep(5)
    
# Use desktop notifications
with telert("Database backup", provider="desktop"):
    # This will show a desktop notification when done
    backup_database()
    
# Send to mobile device
with telert("Long-running task", provider="pushover"):
    # This will send to Pushover when done
    time.sleep(60)
    
# Send to custom HTTP endpoint
with telert("API operation", provider="endpoint"):
    # This will send to your configured HTTP endpoint when done
    api_operation()
```

#### Function Decorator
The `notify` decorator makes it easy to monitor functions:

```python
from telert import notify

# Basic usage - uses function name as the label
@notify()
def process_data():
    # Code that might take a while
    return "Processing complete"

# Custom label and only notify on failure
@notify("Database backup", only_fail=True)
def backup_database():
    # This will only send a notification if it raises an exception
    return "Backup successful"

# Function result will be included in the notification
@notify("Calculation")
def calculate_stats(data):
    return {"mean": sum(data)/len(data), "count": len(data)}

# Send notification to specific provider
@notify("Slack alert", provider="slack")
def slack_notification_function():
    return "This will be sent to Slack"
    
# Send to multiple providers
@notify("Important function", provider=["telegram", "desktop"])
def important_function():
    return "This will be sent to both Telegram and Desktop"
    
# Send to all configured providers
@notify("Critical function", all_providers=True)
def critical_function():
    return "This will be sent to all providers"
    
# Use audio notifications
@notify("Audio alert", provider="audio")
def play_sound_on_completion():
    return "This will play a sound when done"
    
# Use desktop notifications
@notify("Desktop alert", provider="desktop")
def show_desktop_notification():
    return "This will show a desktop notification when done"
    
# Send to mobile device
@notify("Mobile alert", provider="pushover")
def send_mobile_notification():
    return "This will send to Pushover when done"
    
# Send to custom HTTP endpoint
@notify("API alert", provider="endpoint")
def send_to_api():
    return "This will send to your configured HTTP endpoint when done"
```

## 🌐 API Deployment to Cloud Platforms

Telert can be deployed as a notification API on cloud platforms like [Replit](https://replit.com/@mihir95/Telert-CLI-Notifier), [Railway](https://railway.com/template/A_kYXt?referralCode=vj4bEA), [Render](https://render.com/deploy?repo=https://github.com/navig-me/telert-notifier) or [Fly.io](https://github.com/navig-me/telert-notifier?tab=readme-ov-file#-deploy-manually-on-flyio). This is useful for CI/CD pipelines or services that can make HTTP requests but can't install Python.

[![Run on Replit](https://replit.com/badge/github/navig-me/telert-replit)](https://replit.com/@mihir95/Telert-CLI-Notifier)
[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/A_kYXt?referralCode=vj4bEA)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/navig-me/telert-notifier)

Click on any of the buttons above or use the [Deployment Templates](https://github.com/navig-me/telert-notifier) to deploy your own instance.

Once deployed, you can send notifications by making HTTP requests to your API:

```bash
curl -X POST https://your-deployment-url.example.com/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Build complete!"}'
```

For more details on deployment options and configuration, see the [telert-notifier repository](https://github.com/navig-me/telert-notifier).

## 🔧 Troubleshooting

### Desktop Notifications Issues

- **macOS**: If desktop notifications aren't working:
  - Install terminal-notifier: `brew install terminal-notifier`
  - Check notification permissions in System Preferences → Notifications
  - Ensure your terminal app (iTerm2, Terminal, VS Code) has notification permissions

- **Linux**: 
  - Install notify-send: `sudo apt install libnotify-bin` (Debian/Ubuntu)
  - Ensure your desktop environment supports notifications

- **Windows**:
  - PowerShell must be allowed to run scripts
  - Check Windows notification settings

### Connection Issues

- If you're getting connection errors with Telegram, Teams, or Slack:
  - Verify network connectivity
  - Check if your token/webhook URLs are correct
  - Ensure firewall rules allow outbound connections

### Audio Issues

- **No sound playing**:
  - Check if your system's volume is muted
  - Install required audio players (macOS: built-in, Linux: mpg123/paplay/aplay, Windows: winsound/playsound)
  - For MP3 support on Windows: `pip install telert[audio]`


---
## 🌿 Environment Variables

### Configuration Variables

| Variable                  | Effect                                      |
|---------------------------|---------------------------------------------|
| `TELERT_DEFAULT_PROVIDER` | Set default provider(s) to use (comma-separated for multiple) |
| `TELERT_TOKEN` or `TELERT_TELEGRAM_TOKEN` | Telegram bot token         |
| `TELERT_CHAT_ID` or `TELERT_TELEGRAM_CHAT_ID` | Telegram chat ID       |
| `TELERT_TEAMS_WEBHOOK`    | Microsoft Teams Power Automate HTTP URL     |
| `TELERT_SLACK_WEBHOOK`    | Slack webhook URL                           |
| `TELERT_PUSHOVER_TOKEN`   | Pushover application token                  |
| `TELERT_PUSHOVER_USER`    | Pushover user key                           |
| `TELERT_AUDIO_FILE`       | Path to sound file for audio notifications  |
| `TELERT_AUDIO_VOLUME`     | Volume level for audio notifications (0.0-1.0) |
| `TELERT_DESKTOP_APP_NAME` | Application name for desktop notifications  |
| `TELERT_DESKTOP_ICON`     | Path to icon file for desktop notifications |
| `TELERT_ENDPOINT_URL`     | URL for custom HTTP endpoint notifications   |
| `TELERT_ENDPOINT_METHOD`  | HTTP method to use (default: POST)           |
| `TELERT_ENDPOINT_HEADERS` | JSON string of headers for HTTP requests      |
| `TELERT_ENDPOINT_PAYLOAD` | Payload template for HTTP requests           |
| `TELERT_ENDPOINT_NAME`    | Friendly name for the custom endpoint        |
| `TELERT_ENDPOINT_TIMEOUT` | Request timeout in seconds (default: 20)     |

### Runtime Variables

| Variable          | Effect                                            |
|-------------------|---------------------------------------------------|
| `TELERT_LONG`     | Default threshold (seconds) for `hook`            |
| `TELERT_SILENT=1` | Capture and include command output in notification, but don't display in real-time |

### Example Usage

```bash
# Set multiple default providers (will use in fallback order)
export TELERT_DEFAULT_PROVIDER="slack,audio,desktop"

# Configure Telegram via environment
export TELERT_TELEGRAM_TOKEN="your-bot-token"
export TELERT_TELEGRAM_CHAT_ID="your-chat-id"

# Configure Slack
export TELERT_SLACK_WEBHOOK="https://hooks.slack.com/services/..."

# Configure desktop notifications
export TELERT_DESKTOP_APP_NAME="MyApp"

# Send a message (will use default providers in order)
telert send "Environment variable configuration works!"
```

Using environment variables is especially useful in CI/CD pipelines or containerized environments where you don't want to create a config file. Environment variables take precedence over the configuration file, making them perfect for temporary overrides.

---

## 💡 Use Cases and Tips

### Server Administration
- Get notified when backups complete
- Monitor critical system jobs
- Alert when disk space runs low

```bash
# Alert when disk space exceeds 90%
df -h | grep -E '[9][0-9]%' | telert "Disk space alert!"

# Monitor a system update
telert run --label "System update" apt update && apt upgrade -y
```

### Data Processing
- Monitor long-running data pipelines
- Get notified when large file operations complete
- Track ML model training progress

```python
from telert import telert, notify
import pandas as pd

@notify("Data processing")
def process_large_dataset(filename):
    df = pd.read_csv(filename)
    # Process data...
    return {"rows_processed": len(df), "outliers_removed": 15}
```

### CI/CD Pipelines
- Get notified when builds complete
- Alert on deployment failures
- Track test suite status

```bash
# In a CI/CD environment using environment variables
export TELERT_TOKEN="your-token"
export TELERT_CHAT_ID="your-chat-id"

# Alert on build completion
telert run --label "CI Build" -- npm run build
```

---

### Releasing to PyPI
 
 The project is automatically published to PyPI when a new GitHub release is created:
 
 1. Update version in both `pyproject.toml` and `telert/__init__.py`
 2. Commit the changes and push to main
 3. Create a new GitHub release with a tag like `v0.1.3`
 4. The GitHub Actions workflow will automatically build and publish to PyPI
 
 To manually publish to PyPI if needed:
 
 ```bash
 # Install build tools
 pip install build twine
 
 # Build the package
 python -m build
 
 # Upload to PyPI
 twine upload dist/*
 ```

---

## 🤝 Contributing / License

PRs & issues welcome!  
Licensed under the MIT License – see `LICENSE`.

## 👏 Acknowledgements

This project has been improved with help from all contributors who provide feedback and feature suggestions. If you find this tool useful, consider [supporting the project on Buy Me a Coffee](https://www.buymeacoffee.com/mihirk) ☕

### Need a VPS for Your Projects?

Try these providers with generous free credits:

- [Vultr](https://www.vultr.com/?ref=9752934-9J) — $100 free credits
- [DigitalOcean](https://m.do.co/c/cdf2b5a182f2) — $200 free credits
