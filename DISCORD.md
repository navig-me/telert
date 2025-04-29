# Setting Up Discord Notifications with Telert

Telert supports sending notifications to Discord channels using webhooks. This guide will walk you through the setup process.

## Prerequisites

- A Discord account
- Administrative permissions for a Discord server or a channel where you want to receive the notifications

## Setup Steps

### 1. Create a Discord Webhook

1. Open Discord and navigate to the server where you want to receive notifications
2. Right-click on the text channel where you want to receive notifications
3. Select **Edit Channel**
4. Click on the **Integrations** tab
5. Click on **Webhooks**
6. Click on **New Webhook**
7. (Optional) Customize the webhook name and avatar image
8. Click **Copy Webhook URL** to copy the webhook URL to your clipboard
9. Click **Save**

### 2. Configure Telert to Use Discord

After copying the webhook URL, configure Telert to use it:

```bash
# Basic configuration with default bot name (Telert)
telert config discord --webhook-url "https://discord.com/api/webhooks/..."

# With custom bot name and avatar
telert config discord \
  --webhook-url "https://discord.com/api/webhooks/..." \
  --username "My Alert Bot" \
  --avatar-url "https://example.com/my-bot-avatar.png"

# Set as default provider
telert config discord --webhook-url "https://discord.com/api/webhooks/..." --set-default

# Add to existing default providers
telert config discord --webhook-url "https://discord.com/api/webhooks/..." --add-to-defaults
```

### 3. Test the Configuration

```bash
# Test with default configuration
telert status

# Or test specifically the Discord provider
telert status --provider discord
```

## Using Discord Notifications

```bash
# Use Discord for a specific notification
telert send --provider discord "Test message to Discord!"

# Run a command and notify via Discord when done
telert run --provider discord --label "Database Backup" pg_dump -U postgres mydb > backup.sql

# Pipe command output to Discord
long_running_command | telert --provider discord "Command finished!"
```

## Environment Variables

You can also configure Telert to use Discord through environment variables:

```bash
# Set Discord webhook URL
export TELERT_DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."

# Optional: Set custom bot name
export TELERT_DISCORD_USERNAME="My Alert Bot"

# Optional: Set custom bot avatar URL
export TELERT_DISCORD_AVATAR_URL="https://example.com/my-bot-avatar.png"

# Make Discord the default provider
export TELERT_DEFAULT_PROVIDER="discord"

# Make Discord one of multiple default providers
export TELERT_DEFAULT_PROVIDER="discord,desktop,audio"
```

## Troubleshooting

If you're experiencing issues with Discord notifications:

1. Verify that the webhook URL is correct and that the webhook still exists in Discord
2. Check your network connection
3. Make sure your messages don't exceed Discord's rate limits or message length limits
4. Verify that the channel where you created the webhook still exists and the bot has permission to post there

## Additional Options

Discord webhooks support additional customization options, such as:

- **Username**: The name that appears for the bot message (set with `--username`)
- **Avatar URL**: A URL pointing to an image for the bot's avatar (set with `--avatar-url`)

These options allow you to customize how your notifications appear in Discord.