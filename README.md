# telert – Alerts for Your Terminal (Telegram, Teams, Slack)

**Version 0.1.5** 📱

Telert is a lightweight utility that sends notifications to Telegram, Microsoft Teams, or Slack when your terminal commands or Python code completes. Perfect for long-running tasks, remote servers, CI pipelines, or monitoring critical code.

**Quick start:**
```bash
# Install
pip install telert

# After quick setup (see below)
long_running_command \| telert "Command finished!"
```

✅ **Key benefits:**
- Know instantly when your commands finish (even when away from your computer)
- See exactly how long commands or code took to run
- Capture success/failure status codes and tracebacks
- View command output snippets directly in your notifications
- Works with shell commands, pipelines, and Python code

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mihirk)

---

## 🚀 Quick Install

```bash
# Install from PyPI (works on any OS with Python 3.8+)
pip install telert
```

---

## 🤖 Setup Guide

Telert supports multiple messaging services. Choose one or more based on your needs.

### Telegram Setup

#### Step 1: Create Your Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Follow the prompts to name your bot (e.g., "My Server Alerts")
4. Choose a username (must end with "bot", e.g., "my_server_alerts_bot")
5. **Important:** Save the API token (looks like `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`)

#### Step 2: Initialize Chat & Get Chat ID
1. Send any message to your new bot (this is required before it can message you)
2. Get your chat ID with:
   ```bash
   curl -s "https://api.telegram.org/bot<token>/getUpdates"
   ```
3. Find the `"chat":{"id":` value in the response (e.g., `123456789`)

#### Step 3: Configure Telegram in Telert

**CLI Configuration:**
```bash
telert config telegram --token "<token>" --chat-id "<chat-id>" --set-default
telert status --provider telegram  # Test
```

**Python Configuration:**
```python
from telert import configure_telegram, send

configure_telegram("<token>", "<chat-id>")
send("✅ Telegram test", provider="telegram")
```

**Environment Variables:**
```bash
export TELERT_TOKEN="<token>"
export TELERT_CHAT_ID="<chat-id>"
```

### Microsoft Teams Setup

#### Step 1: Create Incoming Webhook
1. Open Teams and navigate to the channel where you want to receive alerts
2. Click the "..." menu next to the channel name
3. Select "Connectors"
4. Find "Incoming Webhook" and click "Configure"
5. Give it a name and optionally upload an icon
6. Click "Create" and copy the webhook URL

#### Step 2: Configure Teams in Telert

**CLI Configuration:**
```bash
telert config teams --webhook-url "<webhook-url>" --set-default
telert status --provider teams  # Test
```

**Python Configuration:**
```python
from telert import configure_teams, send

configure_teams("<webhook-url>")
send("✅ Teams test", provider="teams")
```

**Environment Variables:**
```bash
export TELERT_TEAMS_WEBHOOK="<webhook-url>"
```

### Slack Setup

#### Step 1: Create Incoming Webhook
1. Go to https://api.slack.com/apps and click "Create New App"
2. Choose "From scratch" and fill in the app name and workspace
3. Click "Incoming Webhooks" in the sidebar
4. Activate incoming webhooks and click "Add New Webhook to Workspace"
5. Choose the channel where notifications should appear
6. Copy the webhook URL that looks like `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXX`

#### Step 2: Configure Slack in Telert

**CLI Configuration:**
```bash
telert config slack --webhook-url "<webhook-url>" --set-default
telert status --provider slack  # Test
```

**Python Configuration:**
```python
from telert import configure_slack, send

configure_slack("<webhook-url>")
send("✅ Slack test", provider="slack")
```

**Environment Variables:**
```bash
export TELERT_SLACK_WEBHOOK="<webhook-url>"
```

### Managing Multiple Providers

Telert lets you configure multiple providers and set one as default:

```bash
# List configured providers
telert status

# Set a provider as default
telert config slack --webhook-url "<url>" --set-default

# Use a specific provider rather than default
telert send --provider telegram "Via Telegram"

# Python API
from telert import set_default_provider, list_providers

set_default_provider("teams")
providers = list_providers()  # Get info about configured providers
```

Telert securely stores all configuration in `~/.config/telert/config.json` unless environment variables are used.

---

## ✨ Features

| Mode           | What it does | Example |
|----------------|--------------|---------|
| **Run**        | Wraps a command, times it, sends notification with exit code. | `telert run --label "RSYNC" -- rsync -a /src /dst` |
| **Filter**     | Reads from stdin so you can pipe command output. | `long_job \| telert "compile done"` |
| **Hook**       | Generates a Bash snippet so **every** command > *N* seconds notifies automatically. | `eval "$(telert hook -l 30)"` |
| **Send**       | Low-level "send arbitrary text" helper. | `telert send --provider slack "Build complete"` |
| **Python API** | Use directly in Python code with context managers and decorators. | `from telert import telert, send, notify` |
| **Multi-provider** | Configure and use multiple messaging services (Telegram, Teams, Slack). | `telert config teams --webhook-url "..."` |

---

## 📋 Usage Guide

### Command Line Interface (CLI)

#### Run Mode
Wrap any command to receive a notification when it completes:

```bash
# Basic usage - notify when command finishes (uses default provider)
telert run -- npm run build

# Add a descriptive label
telert run --label "DB Backup" -- pg_dump -U postgres mydb > backup.sql

# Show notification only when a command fails
telert run --only-fail -- rsync -av /src/ /backup/

# Send to a specific provider
telert run --provider teams --label "ML Training" -- python train_model.py

# Custom notification message
telert run --message "Training complete! 🎉" -- python train_model.py
```

#### Filter Mode
Perfect for adding notifications to existing pipelines:

```bash
# Send notification when a pipeline completes (uses default provider)
find . -name "*.log" \| xargs grep "ERROR" \| telert "Error check complete"

# Process and notify with specific provider
cat large_file.csv \| awk '{print $3}' \| sort \| uniq -c \| telert --provider=slack "Data processing finished"
```

> **Note:** In filter mode, the exit status is not captured since commands in a pipeline run in separate processes.
> For exit status tracking, use Run mode or add explicit status checking in your script.

#### Send Mode
Send custom messages from scripts to any provider:

```bash
# Simple text message (uses default provider)
telert send "Server backup completed"

# Send to a specific provider
telert send --provider teams "Build completed"
telert send --provider slack "Deployment started"

# Send status from a script
if [ $? -eq 0 ]; then
  telert send "✅ Deployment successful"
else
  # Critical failures could go to multiple providers
  telert send --provider telegram "❌ Deployment failed with exit code $?"
  telert send --provider slack "❌ Deployment failed with exit code $?"
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

### Python API

#### Configuration
```python
from telert import (
    configure_telegram, configure_teams, configure_slack, 
    set_default_provider, is_configured, get_config, list_providers
)

# Configure one or more providers
configure_telegram("<token>", "<chat-id>")
configure_teams("<webhook-url>")
configure_slack("<webhook-url>", set_default=True)  # Set as default

# Check if specific provider is configured
if not is_configured("teams"):
    configure_teams("<webhook-url>")

# Get configuration for a specific provider
telegram_config = get_config("telegram")
print(f"Using token: {telegram_config['token'][:8]}...")

# List all providers and see which is default
providers = list_providers()
for p in providers:
    print(f"{p['name']} {'(default)' if p['is_default'] else ''}")

# Change default provider
set_default_provider("telegram")
```

#### Simple Messaging
```python
from telert import send

# Send using default provider
send("Script started")

# Send to specific provider regardless of default
send("Processing completed with 5 records updated", provider="teams")
send("Critical error detected!", provider="slack")
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
    # This will send to Teams regardless of the default provider
    teams_specific_operation()
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
```

---

## 🌿 Environment Variables

| Variable              | Effect                                      |
|-----------------------|---------------------------------------------|
| `TELERT_TOKEN`        | Telegram bot token                          |
| `TELERT_CHAT_ID`      | Telegram chat ID                            |
| `TELERT_TEAMS_WEBHOOK`| Microsoft Teams webhook URL                 |
| `TELERT_SLACK_WEBHOOK`| Slack webhook URL                           |
| `TELERT_LONG`         | Default threshold (seconds) for `hook`      |
| `TELERT_SILENT=1`     | Suppress stdout/stderr echo in `run`        |

Using environment variables is especially useful in CI/CD pipelines or containerized environments where you don't want to create a config file. When multiple provider environment variables are set, telert will try them in this order: Telegram, Teams, Slack.

---

## 💡 Use Cases and Tips

### Server Administration
- Get notified when backups complete
- Monitor critical system jobs
- Alert when disk space runs low

```bash
# Alert when disk space exceeds 90%
df -h \| grep -E '[9][0-9]%' \| telert "Disk space alert!"

# Monitor a system update
telert run --label "System update" -- apt update && apt upgrade -y
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

## 👩‍💻 Development

```bash
git clone https://github.com/navig-me/telert
cd telert
python -m pip install -e .[dev]
```

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

This project has been improved with help from:
- [Claude Code](https://claude.ai/code) - AI assistant that helped enhance documentation, create the Python API, and implement environment variable support
- All contributors who provide feedback and feature suggestions