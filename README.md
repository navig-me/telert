# telert – Telegram Alerts for Your Terminal

**Version 0.1.3** 📱

Telert is a lightweight command-line utility that sends you Telegram notifications when your terminal commands complete. Perfect for long-running tasks, remote servers, or CI pipelines.

✅ **Key benefits:**
- Know instantly when your commands finish (even when away from your computer)
- See exactly how long commands took to run
- Capture success/failure status codes
- View command output snippets directly in your notifications
- Works with any command or pipeline

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/mihirk)

---

## 🚀 Quick Install

```bash
# Install from PyPI (works on any OS with Python 3.8+)
pip install telert
```

---

## 🤖 Telegram Bot Setup Guide

### Step 1: Create Your Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Start a chat and send the command `/newbot`
3. Follow the prompts to name your bot (e.g., "My Server Alerts")
4. Choose a username for your bot (must end with "bot", e.g., "my_server_alerts_bot")
5. **Important:** Save the API token that BotFather gives you - it looks like `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`

### Step 2: Initialize Chat with Your Bot
1. Search for your new bot by the username you created
2. Send any message to the bot (e.g., "hello")
   - This step is crucial - you must send at least one message to the bot before it can send messages to you

### Step 3: Get Your Chat ID
```bash
# Replace <token> with your bot token from step 1
curl -s "https://api.telegram.org/bot<token>/getUpdates"
```

Look for the `"chat":{"id":` value in the response. For example:
```json
{"update_id":123456789,"message":{"message_id":1,"from":{"id":123456789,"is_bot":false,"first_name":"Your","last_name":"Name","username":"yourname"},"chat":{"id":123456789,"first_name":"Your","last_name":"Name","username":"yourname","type":"private"},"date":1678901234,"text":"hello"}}
```
The number after `"chat":{"id":` is your chat ID (in this example, `123456789`).

For channels, the chat ID will start with `-100`.

### Step 4: Configure Telert
```bash
# Save your bot token and chat ID
telert config --token "<your-bot-token>" --chat-id "<your-chat-id>"

# Send a test message to verify everything works
telert status
```

You should receive a "✅ telert status OK" message in Telegram.

Telert securely stores your credentials in `~/.config/telert/config.json`.

---

## ✨ Features

| Mode           | What it does | Example |
|----------------|--------------|---------|
| **Run**        | Wraps a command, times it, sends notification with exit code. | `telert run --label "RSYNC" -- rsync -a /src /dst` |
| **Filter**     | Reads from stdin so you can pipe command output. | `long_job | telert "compile done"` |
| **Hook**       | Generates a Bash snippet so **every** command > *N* seconds notifies automatically. | `eval "$(telert hook -l 30)"` |
| **Send**       | Low-level "send arbitrary text to myself" helper. | `telert send "server rebooted"` |
| **Python API** | Use directly in Python code with context managers and decorators. | `from telert import telert, send, notify` |

---

## 📋 Usage Examples

### Python API

Telert can be used directly in Python code:

```python
from telert import telert, send, notify
import time

# Simple message
send("Script started")

# Context manager to time execution
with telert("Data processing"):
    # Your code here
    time.sleep(2)
    result = [1, 2, 3, 4, 5]
    
    # You can store results to include in the notification
    with telert("Calculation") as t:
        time.sleep(1)
        t.result = {"success": True, "data": [1, 2, 3]}

# Function decorator
@notify("Database backup")
def backup_database():
    time.sleep(3)
    return "Backup completed successfully"

# Only notify on failure
@notify(only_fail=True)
def risky_operation():
    # If this raises an exception, you'll get a notification
    # Otherwise, no notification is sent
    pass
```

### Run Mode
Wrap any command to receive a notification when it completes:

```bash
# Basic usage - notify when command finishes
telert run -- npm run build

# Add a descriptive label
telert run --label "DB Backup" -- pg_dump -U postgres mydb > backup.sql

# Show notification only when a command fails
telert run --only-fail -- rsync -av /src/ /backup/

# Custom notification message
telert run --message "Training complete! 🎉" -- python train_model.py
```

### Filter Mode
Perfect for adding notifications to existing pipelines:

```bash
# Send notification when a pipeline completes
find . -name "*.log" | xargs grep "ERROR" | telert "Error check complete"

# Process and notify
cat large_file.csv | awk '{print $3}' | sort | uniq -c | telert "Data processing finished"
```

> **Note:** In filter mode, the exit status is not captured since commands in a pipeline run in separate processes.
> For exit status tracking, use Run mode or add explicit status checking in your script.

### Send Mode
Send custom messages from scripts:

```bash
# Simple text message
telert send "Server backup completed"

# Send status from a script
if [ $? -eq 0 ]; then
  telert send "✅ Deployment successful"
else
  telert send "❌ Deployment failed with exit code $?"
fi
```

### Shell Hook
Get notifications for ALL commands that take longer than a certain time:

```bash
# Configure Bash to notify for any command taking longer than 30 seconds
eval "$(telert hook -l 30)"

# Add to your .bashrc for persistent configuration
echo 'eval "$(telert hook -l 30)"' >> ~/.bashrc
```

### Help & Options
```bash
# View all available commands
telert --help

# Get help for a specific command
telert run --help
```

---

## 🌿 Environment Variables

| Variable            | Effect                                      |
|---------------------|---------------------------------------------|
| `TELERT_LONG`       | Default threshold (seconds) for `hook`.     |
| `TELERT_SILENT=1`   | Suppress stdout/stderr echo in `run`.       |

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
3. Create a new GitHub release with a tag like `v0.1.2`
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