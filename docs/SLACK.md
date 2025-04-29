# Slack Setup Guide for Telert

This guide provides detailed instructions for setting up Slack with Telert.

## Creating an Incoming Webhook in Slack

1. **Create a Slack App**:
   - Go to https://api.slack.com/apps
   - Click "Create New App"
   - Select "From scratch"
   - Enter an App Name (e.g., "Telert Notifications")
   - Select the workspace where you want to use the app
   - Click "Create App"

2. **Enable Incoming Webhooks**:
   - In the left sidebar of your app's configuration page, click "Incoming Webhooks"
   - Toggle the switch to "On" to activate incoming webhooks
   - Click "Add New Webhook to Workspace" at the bottom of the page

3. **Choose a Channel**:
   - Select the channel where you want the notifications to appear
   - You can also select "Direct Messages" to receive notifications privately
   - Click "Allow" to authorize the app

4. **Copy the Webhook URL**:
   - After authorization, you'll be redirected back to the Incoming Webhooks page
   - Find and copy the webhook URL that looks like: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXX`
   - **Important:** Keep this URL secure as it can be used to post to your channel

## Configuring Telert for Slack

### CLI Configuration

```bash
telert config slack --webhook-url "<webhook-url>" --set-default
telert status --provider slack  # Test your configuration
```

### Python Configuration

```python
from telert import configure_slack, send

configure_slack("<webhook-url>")
send("✅ Slack test", provider="slack")
```

### Environment Variables

If you prefer to use environment variables (useful for CI/CD pipelines):

```bash
export TELERT_SLACK_WEBHOOK="<webhook-url>"
```

## Slack-Specific Features

### Message Formatting

Slack supports both plain text and Markdown-style formatting:

```bash
# Basic formatting in messages
telert send --provider slack "Project build *completed* with _zero_ errors"
```

Supported formatting includes:
- `*text*` - Bold text
- `_text_` - Italic text
- `~text~` - Strikethrough text
- ``` `code` ``` - Inline code
- ```````code block`````` - Multi-line code blocks

### Message Blocks and Attachments

Telert formats notifications in a visually appealing way using Slack's Block Kit. This results in more structured messages.

### Emoji Support

Slack has excellent emoji support. You can include emojis in your messages:

```bash
telert send --provider slack ":rocket: Deployment completed! :white_check_mark:"
```

### Channel Mentions

To mention channels or users in your messages:

```bash
telert send --provider slack "Alert! Notify <!channel> about this issue."
```

### Security Considerations

- Webhook URLs should be treated like secrets
- Anyone with the webhook URL can post messages to the channel
- Consider regenerating webhook URLs periodically
- Use dedicated channels for different types of alerts

### Troubleshooting

If you encounter issues:

1. **Messages not appearing**:
   - Verify the webhook URL is correct
   - Ensure the app is still installed to your workspace
   - Check if the channel still exists

2. **Rate limiting**:
   - Slack has rate limits (Tier 1 apps: 1 message per second)
   - For high-frequency notifications, consider batching messages

3. **Message formatting not working**:
   - Check Slack's current formatting guidelines
   - Different Slack client versions may render formatting differently

4. **Webhook URL revoked**:
   - Slack admins can revoke webhook URLs
   - You may need to request a new webhook if security policies change