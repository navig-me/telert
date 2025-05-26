# telert – Alerts for Your Terminal

[English](https://github.com/navig-me/telert/blob/main/README.md) | [हिन्दी](https://github.com/navig-me/telert/blob/main/README.hi.md) | [中文 (简体)](https://github.com/navig-me/telert/blob/main/README.zh-CN.md) | [Español](https://github.com/navig-me/telert/blob/main/README.es.md)

<p align="center">
  <img src="https://github.com/navig-me/telert/raw/main/telert.png" alt="telert logo" width="150">
</p>

**Version 0.1.42**

[![GitHub Stars](https://img.shields.io/github/stars/navig-me/telert?style=social)](https://github.com/navig-me/telert/stargazers)
[![PyPI version](https://img.shields.io/pypi/v/telert)](https://pypi.org/project/telert/)
[![Downloads](https://static.pepy.tech/personalized-badge/telert?period=month&units=international_system&left_color=grey&right_color=blue&left_text=downloads)](https://pepy.tech/project/telert)
[![License](https://img.shields.io/github/license/navig-me/telert)](https://github.com/navig-me/telert/blob/main/LICENSE)
[![Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-Use%20this%20Action-blue?logo=github)](https://github.com/marketplace/actions/telert-run)
[![VS Code Marketplace](https://vsmarketplacebadges.dev/version/Navig.telert-vscode.svg?subject=VS%20Code%20Marketplace&style=flat-square)](https://marketplace.visualstudio.com/items?itemName=Navig.telert-vscode)


## 📱 Overview

Telert is a lightweight utility that sends notifications when your terminal commands or Python code completes. It supports multiple notification channels:

- **Messaging Apps**: Telegram, Microsoft Teams, Slack, Discord
- **Email**: SMTP email notifications
- **Mobile Devices**: Pushover (Android & iOS)
- **Local Notifications**: Desktop notifications, Audio alerts
- **Custom Integrations**: HTTP endpoints for any service

Simple to use:

```bash
# Run a command and get notified when it finishes
telert run npm build

# Or pipe any command output for notification
find . -name "*.log" | telert "Log files found!"
```

Perfect for long-running tasks, remote servers, CI pipelines, or monitoring critical code.

Use it as a CLI tool, Python library, or a notification API. Telert is available:

- As a Python package: `pip install telert`
- As a Docker image: `docker pull ghcr.io/navig-me/telert:latest`
- As a cloud-hosted API on [Replit](https://replit.com/@mihir95/Telert-CLI-Notifier), [Railway](https://railway.com/template/A_kYXt?referralCode=vj4bEA), [Render](https://render.com/deploy?repo=https://github.com/navig-me/telert-notifier) or [Fly.io](https://github.com/navig-me/telert-notifier?tab=readme-ov-file#-deploy-manually-on-flyio) with one-click deployments.


<img src="https://github.com/navig-me/telert/raw/main/docs/telert-demo.svg" alt="telert demo" width="600">


## 📋 Table of Contents
- [Installation & Quick Start](#-installation--quick-start)
- [Notification Providers](#-notification-providers)
  - [Telegram](#telegram-setup)
  - [Microsoft Teams](#microsoft-teams-setup)
  - [Slack](#slack-setup)
  - [Discord](#discord-setup)
  - [Email](#email-setup)
  - [Pushover](#pushover-setup)
  - [Custom HTTP Endpoints](#custom-http-endpoint-setup)
  - [Audio Alerts](#audio-alerts-setup)
  - [Desktop Notifications](#desktop-notifications-setup)
  - [Managing Multiple Providers](#managing-multiple-providers)
- [Features](#-features)
- [Usage Guide](#-usage-guide)
  - [Command Line Interface](#command-line-interface-cli)
  - [Python API](#python-api)
  - [Docker Usage](#docker-usage)
- [API Deployment to Cloud Platforms](#-api-deployment-to-cloud-platforms)
- [Troubleshooting](#-troubleshooting)
- [Environment Variables](#-environment-variables)
- [Message Formatting](#-message-formatting)
- [Use Cases](#-use-cases-and-tips)
- [Contributing](#-contributing--license)

## Documentation

For more detailed information, please refer to the [docs](https://github.com/navig-me/telert/blob/main/docs/) directory:

- [Environment Variables](https://github.com/navig-me/telert/blob/main/docs/ENVIRONMENT_VARIABLES.md)
- [Message Formatting](https://github.com/navig-me/telert/blob/main/docs/MESSAGE_FORMATTING.md)
- [Python API Reference](https://github.com/navig-me/telert/blob/main/docs/PYTHON_API.md)
- [Use Cases & Tips](https://github.com/navig-me/telert/blob/main/docs/USE_CASES.md)
- [Telegram Setup](https://github.com/navig-me/telert/blob/main/docs/TELEGRAM.md)
- [Microsoft Teams Setup](https://github.com/navig-me/telert/blob/main/docs/TEAMS.md)
- [Slack Setup](https://github.com/navig-me/telert/blob/main/docs/SLACK.md)
- [Discord Setup](https://github.com/navig-me/telert/blob/main/docs/DISCORD.md)
- [Email Setup](https://github.com/navig-me/telert/blob/main/docs/EMAIL.md)
- [Pushover Setup](https://github.com/navig-me/telert/blob/main/docs/PUSHOVER.md)
- [Custom HTTP Endpoint Guide](https://github.com/navig-me/telert/blob/main/docs/ENDPOINT.md)
- [Docker Usage](https://github.com/navig-me/telert/blob/main/docs/DOCKER.md)
- [CI/CD Integrations](https://github.com/navig-me/telert/blob/main/docs/CI-CD.md)

## 🚀 Installation & Quick Start

```bash
# Install from PyPI (works on any OS with Python 3.8+)
pip install telert

# Interactive setup wizard - easiest way to get started
telert init

# Or configure a notification provider manually
telert config desktop --app-name "My App" --set-default

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

Telegram uses the official Bot API for reliable delivery. Messages exceeding Telegram's character limit (4096 characters) are automatically sent as text files.

```bash
# After creating a bot with @BotFather and getting your chat ID
telert config telegram --token "<token>" --chat-id "<chat-id>" --set-default
telert status  # Test your configuration
```

[**Detailed Telegram Setup Guide**](https://github.com/navig-me/telert/blob/main/docs/TELEGRAM.md)

### Microsoft Teams Setup

Teams integration uses Power Automate (Microsoft Flow) to deliver notifications.

```bash
# After creating a HTTP trigger flow in Power Automate
telert config teams --webhook-url "<flow-http-url>" --set-default
telert status  # Test your configuration
```

[**Detailed Microsoft Teams Setup Guide**](https://github.com/navig-me/telert/blob/main/docs/TEAMS.md)

### Slack Setup

Slack integration uses incoming webhooks for channel notifications.

```bash
# After creating a webhook at api.slack.com
telert config slack --webhook-url "<webhook-url>" --set-default
telert status  # Test your configuration
```

[**Detailed Slack Setup Guide**](https://github.com/navig-me/telert/blob/main/docs/SLACK.md)

### Discord Setup

Discord integration uses webhooks to send messages to channels.

```bash
# After creating a webhook in Discord
telert config discord --webhook-url "<webhook-url>" --set-default
telert status  # Test your configuration

# Optionally customize the bot name and avatar
telert config discord --webhook-url "<webhook-url>" --username "My Bot" --avatar-url "<avatar-image-url>" --set-default
```

[**Detailed Discord Setup Guide**](https://github.com/navig-me/telert/blob/main/docs/DISCORD.md)

### Email Setup

Email integration uses standard SMTP protocol to send notifications.

```bash
# Basic configuration
telert config email --server smtp.example.com --port 587 --username user@example.com --password mypassword --to recipient@example.com --set-default
telert status  # Test your configuration

# Advanced configuration
telert config email \
  --server smtp.example.com \
  --port 587 \
  --username user@example.com \
  --password mypassword \
  --from "Telert Notifications <alerts@example.com>" \
  --to "admin@example.com,alerts@example.com" \
  --subject-template "Telert Alert: {label} - {status}" \
  --html \
  --set-default
```

[**Detailed Email Setup Guide**](https://github.com/navig-me/telert/blob/main/docs/EMAIL.md)

### Pushover Setup

Pushover provides mobile notifications to Android and iOS devices.

```bash
# After signing up at pushover.net and creating an app
telert config pushover --token "<app-token>" --user "<user-key>" --set-default
telert status  # Test your configuration
```

[**Detailed Pushover Setup Guide**](https://github.com/navig-me/telert/blob/main/docs/PUSHOVER.md)

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

[**Detailed Custom Endpoint Guide**](https://github.com/navig-me/telert/blob/main/docs/ENDPOINT.md)

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
| **Run**        | Wraps a command, times it, sends notification with exit code. | `telert run --label "RSYNC" rsync -a /src /dst` |
| **Filter**     | Reads from stdin so you can pipe command output. | `long_job \| telert "compile done"` |
| **Hook**       | Generates a Bash snippet so **every** command > *N* seconds notifies automatically. | `eval "$(telert hook -l 30)"` |
| **Send**       | Low-level "send arbitrary text" helper. | `telert send --provider slack "Build complete"` |
| **Python API** | Use directly in Python code with context managers and decorators. | `from telert import telert, send, notify` |
| **GitHub Action** | Run commands in GitHub Actions with notifications. | `uses: navig-me/telert/actions/run@v1` |
| **CI Integration** | GitLab CI templates and CircleCI orbs for notifications. | `extends: .telert-notify` |
| **Docker** | Run as CLI tool or notification API server in Docker. | `docker run ghcr.io/navig-me/telert:latest` |
| **Multi-provider** | Configure and use multiple notification services (Telegram, Teams, Slack, Pushover, Audio, Desktop). | `telert config desktop --app-name "My App"` |

---

## 📋 Usage Guide

### Command Line Interface (CLI)

> **Note**: When using the `run` command, do not use double dashes (`--`) to separate telert options from the command to run. The correct syntax is `telert run [options] command`, not `telert run [options] command`.

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

Telert provides a comprehensive Python API for notification management that includes:

- **Configuration functions** for setting up notification providers
- **Simple messaging** with the `send()` function for quick notifications
- **Context manager** with `with telert():` for timing code execution
- **Function decorator** with `@notify()` for monitoring function calls

```python
# Simple example of sending a notification
from telert import send
send("Script completed successfully!")

# Using the context manager
from telert import telert
with telert("Data processing"):
    # Your long-running code here
    process_large_dataset()

# Using the function decorator
from telert import notify
@notify("Database backup")
def backup_database():
    # Backup code here
    return "Backup completed"  # Result included in notification
```

[**View the complete Python API reference**](https://github.com/navig-me/telert/blob/main/docs/PYTHON_API.md)

### Docker Usage

Telert is available as a Docker image that can be used in both CLI and server modes.

#### Pull the Official Image

```bash
docker pull ghcr.io/navig-me/telert:latest
```

#### CLI Mode Examples

```bash
# Test telert status
docker run --rm ghcr.io/navig-me/telert:latest status

# Configure and send a notification
docker run --rm \
  -e TELERT_TELEGRAM_TOKEN=your_token \
  -e TELERT_TELEGRAM_CHAT_ID=your_chat_id \
  ghcr.io/navig-me/telert:latest send "Hello from Docker!"
```

#### Server Mode Example

```bash
# Run telert as a notification API server
docker run -d --name telert-server \
  -p 8000:8000 \
  -e TELERT_TELEGRAM_TOKEN=your_token \
  -e TELERT_TELEGRAM_CHAT_ID=your_chat_id \
  ghcr.io/navig-me/telert:latest serve

# Send a notification via the API
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from the API!"}'
```

For more detailed information on Docker usage, including configuration persistence and API endpoints, see the [Docker documentation](https://github.com/navig-me/telert/blob/main/docs/DOCKER.md).

### GitHub Actions Integration

Telert can be used in GitHub Actions workflows to run commands and receive notifications when they complete:

```yaml
- name: Run tests with notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm test
    label: Run Tests
    provider: telegram
    token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
```

#### Inputs

| Input | Description | Required |
|-------|-------------|----------|
| `command` | The command to run | Yes |
| `label` | Label to identify the command | No |
| `provider` | Notification provider to use | No |
| `all-providers` | Send to all configured providers | No |
| `only-fail` | Only notify on failure | No |
| `message` | Custom notification message | No |
| `token` | Telegram/Pushover token | No |
| `chat-id` | Telegram chat ID | No |
| `webhook-url` | Webhook URL for Teams/Slack/Discord | No |
| `user-key` | Pushover user key | No |

For more examples and detailed usage, see the [CI/CD Integrations documentation](https://github.com/navig-me/telert/blob/main/docs/CI-CD.md).

### GitLab CI Integration

Telert provides a GitLab CI template for easy integration:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/navig-me/telert/main/.github/actions/run/gitlab-ci-template.yml'

build:
  extends: .telert-notify
  variables:
    TELERT_COMMAND: "npm run build"
    TELERT_LABEL: "Build Project"
    TELERT_PROVIDER: "telegram"
  script:
    - npm run build
```

### CircleCI Orb

Telert is also available as a CircleCI Orb:

```yaml
version: 2.1
orbs:
  telert: telert/notify@1.0.0

jobs:
  build:
    docker:
      - image: cimg/node:16.13
    steps:
      - checkout
      - telert/run-notify:
          command: "npm run build"
          label: "Build Project"
          provider: "telegram"
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

Telert can be configured using environment variables, which is especially useful in CI/CD pipelines or containerized environments. Key variables include:

- `TELERT_DEFAULT_PROVIDER` - Set default provider(s) to use
- Provider-specific variables for Telegram, Teams, Slack, Discord, Pushover, etc.
- Runtime variables like `TELERT_SILENT=1` for output control

Environment variables take precedence over the configuration file, making them perfect for temporary overrides.

[**See all environment variables**](https://github.com/navig-me/telert/blob/main/docs/ENVIRONMENT_VARIABLES.md)

---
## 📝 Message Formatting

Telert provides formatting options for messages with different levels of support across providers:

- **Telegram** fully supports rich formatting with both HTML and Markdown syntax
- **Other providers** (Slack, Teams, Discord, Pushover) receive appropriately formatted messages with tags stripped
- Automatic cross-platform compatibility ensures readable messages on all platforms

Telert intelligently handles the formatting based on each provider's capabilities. You only need to format your message once, and Telert ensures it displays properly across all providers.

[**Learn more about message formatting**](https://github.com/navig-me/telert/blob/main/docs/MESSAGE_FORMATTING.md)

---

## 💡 Use Cases and Tips

Telert is versatile and useful in various scenarios:

- **Server Administration**: Get notified when backups complete, monitor system jobs, alert on disk space issues
- **Data Processing**: Track long-running data pipelines, ML model training, and large file operations
- **CI/CD Pipelines**: Get notifications for build completions, deployment failures, and test results
- **VS Code Integration**: Monitor and notify when commands or code complete directly within VS Code
- **Long-Running Processes**: Get notified when database migrations, file transfers, or batch jobs complete
- **Remote Server Monitoring**: Receive alerts from cron jobs, system reboots, and automated tasks

[**Explore all use cases and examples**](https://github.com/navig-me/telert/blob/main/docs/USE_CASES.md)


---

### Releasing to PyPI
 
 The project is automatically published to PyPI when a new GitHub release is created:
 
 1. Update version in both `pyproject.toml`, `README.md` and `telert/__init__.py`
 2. Commit the changes and push to main
 3. Create a new GitHub release with a tag like `v0.1.34`
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
