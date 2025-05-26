# Telegram Setup Guide for Telert

This guide provides detailed instructions for setting up Telegram with Telert.

## Creating Your Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Follow the prompts to name your bot (e.g., "My Server Alerts")
4. Choose a username (must end with "bot", e.g., "my_server_alerts_bot")
5. **Important:** Save the API token (looks like `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`)

## Finding Your Chat ID

1. Send any message to your new bot
   - This initializes the chat and is required before the bot can message you
   - Your bot won't respond at this stage (that's normal)

2. Get your chat ID using this command:
   ```bash
   curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates"
   ```
   Replace `<YOUR_TOKEN>` with the token you received from BotFather.

3. Find the `"chat":{"id":` value in the response
   - This is a number like `123456789` which is your chat ID
   - If you don't see any response, try sending another message to your bot and run the curl command again

## Configuring Telert for Telegram

### CLI Configuration

```bash
telert config telegram --token "<token>" --chat-id "<chat-id>" --set-default
telert status --provider telegram  # Test your configuration
```

### Python Configuration

```python
from telert import configure_telegram, send

configure_telegram("<token>", "<chat-id>")
send("✅ Telegram test", provider="telegram")
```

### Environment Variables

If you prefer to use environment variables (useful for CI/CD pipelines):

```bash
export TELERT_TOKEN="<token>"
export TELERT_CHAT_ID="<chat-id>"
```

## Telegram-Specific Features

### Message Formatting

Telegram supports both plain text and HTML formatting:

```bash
# HTML formatting in messages
telert send "Project build <b>completed</b> with <i>zero</i> errors"
```

Supported HTML tags include:
- `<b>` - Bold text
- `<i>` - Italic text
- `<code>` - Monospace text
- `<pre>` - Preformatted text block
- `<a href="...">` - Links

### Long Message Handling

Telegram has a 4096 character limit for text messages. Telert handles this limitation automatically:

- Messages under 4096 characters are sent as normal text messages
- Messages exceeding this limit are automatically converted to text file attachments
- The file is sent with the caption "Message from telert (sent as file due to length)"

This conversion happens seamlessly without any additional configuration required. For example:

```bash
# This long message will be automatically sent as a file if it exceeds 4096 characters
cat very_long_log.txt | telert "Log processing complete"

# Python example
from telert import send
with open('large_report.txt', 'r') as f:
    report = f.read()
    send(report)  # Will be sent as a file if too long
```

This feature is particularly useful for sending log files, error reports, or other lengthy output that would otherwise be truncated.

### Privacy Considerations

- Telegram bots can only send messages to chats where they've been added or to users who have initiated a conversation with them
- Private chats provide the most security
- For group notifications, consider creating a dedicated alerts group

### Troubleshooting

If you encounter issues:

1. **No messages being sent**:
   - Ensure you've sent at least one message to the bot first
   - Verify the token and chat ID are correct
   - Check the bot permissions with BotFather

2. **Rate limiting**:
   - Telegram has rate limits for bots (approximately 30 messages per second)
   - For high-frequency notifications, consider batching messages

3. **Bot doesn't respond**:
   - This is normal - Telert uses Telegram bots in one-way messaging mode
   - The bot is not designed to respond to your messages, only to send alerts