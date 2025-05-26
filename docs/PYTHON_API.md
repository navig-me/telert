# Python API

Telert provides a comprehensive Python API that can be used directly in your Python code for notification management.

## Configuration

```python
from telert import (
    configure_telegram, configure_teams, configure_slack, configure_discord, configure_pushover,
    configure_email, configure_audio, configure_desktop, configure_providers,
    set_default_provider, set_default_providers, 
    is_configured, get_config, list_providers
)

# Configure one or more providers
configure_telegram("<token>", "<chat-id>")
configure_teams("<webhook-url>")
configure_slack("<webhook-url>")
configure_discord("<webhook-url>")  # Basic Discord configuration
# Or with custom bot name and avatar
configure_discord("<webhook-url>", username="My Bot", avatar_url="https://example.com/avatar.png")
configure_pushover("<app-token>", "<user-key>")

# Configure email notifications
configure_email(
    server="smtp.example.com",
    port=587,
    username="user@example.com", 
    password="mypassword",
    to_addrs=["recipient@example.com"]
)
# Or with more options
configure_email(
    server="smtp.example.com",
    port=587,
    username="user@example.com", 
    password="mypassword",
    from_addr="Telert Notifications <alerts@example.com>",
    to_addrs=["admin@example.com", "alerts@example.com"],
    subject_template="Telert Alert: {label} - {status}",
    use_html=True
)

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

## Simple Messaging

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
send("Send to Discord channel", provider="discord") 
send("Send to custom HTTP endpoint", provider="endpoint")

# Check delivery results
results = send("Important message", provider=["slack", "telegram"])
for provider, success in results.items():
    if not success:
        print(f"Failed to send to {provider}")
```

## Context Manager

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
    
# Send to Discord channel
with telert("Discord notification", provider="discord"):
    # This will notify via Discord when done
    discord_specific_operation()
    
# Send to custom HTTP endpoint
with telert("API operation", provider="endpoint"):
    # This will send to your configured HTTP endpoint when done
    api_operation()
```

## Function Decorator

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
    
# Send to Discord
@notify("Discord alert", provider="discord")
def send_to_discord():
    return "This will send to Discord when done"
    
# Send to custom HTTP endpoint
@notify("API alert", provider="endpoint")
def send_to_api():
    return "This will send to your configured HTTP endpoint when done"
```
