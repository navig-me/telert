# Environment Variables

Telert can be configured using environment variables, which is especially useful in CI/CD pipelines or containerized environments where you don't want to create a config file. Environment variables take precedence over the configuration file, making them perfect for temporary overrides.

## Configuration Variables

| Variable                  | Effect                                      |
|---------------------------|---------------------------------------------|
| `TELERT_DEFAULT_PROVIDER` | Set default provider(s) to use (comma-separated for multiple) |
| `TELERT_TOKEN` or `TELERT_TELEGRAM_TOKEN` | Telegram bot token         |
| `TELERT_CHAT_ID` or `TELERT_TELEGRAM_CHAT_ID` | Telegram chat ID       |
| `TELERT_TEAMS_WEBHOOK`    | Microsoft Teams Power Automate HTTP URL     |
| `TELERT_SLACK_WEBHOOK`    | Slack webhook URL                           |
| `TELERT_DISCORD_WEBHOOK`  | Discord webhook URL                         |
| `TELERT_DISCORD_USERNAME` | Discord webhook bot name (default: Telert)  |
| `TELERT_DISCORD_AVATAR_URL` | Discord webhook bot avatar URL           |
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

## Runtime Variables

| Variable          | Effect                                            |
|-------------------|---------------------------------------------------|
| `TELERT_LONG`     | Default threshold (seconds) for `hook`            |
| `TELERT_SILENT=1` | Capture and include command output in notification, but don't display in real-time |

## Example Usage

```bash
# Set multiple default providers (will use in fallback order)
export TELERT_DEFAULT_PROVIDER="slack,audio,desktop"

# Configure Telegram via environment
export TELERT_TELEGRAM_TOKEN="your-bot-token"
export TELERT_TELEGRAM_CHAT_ID="your-chat-id"

# Configure Slack
export TELERT_SLACK_WEBHOOK="https://hooks.slack.com/services/..."

# Configure Discord
export TELERT_DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."
export TELERT_DISCORD_USERNAME="Alert Bot"  # Optional

# Configure desktop notifications
export TELERT_DESKTOP_APP_NAME="MyApp"

# Send a message (will use default providers in order)
telert send "Environment variable configuration works!"
```
