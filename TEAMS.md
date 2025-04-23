# Microsoft Teams Setup Guide for Telert

This guide provides detailed instructions for setting up Microsoft Teams with Telert.

## Creating an Incoming Webhook in Teams

1. **Navigate to the desired channel**:
   - Open Microsoft Teams
   - Go to the channel where you want to receive notifications
   - Click the "..." (more options) menu next to the channel name

2. **Configure the webhook**:
   - Select "Connectors" from the dropdown menu
   - In the Connectors dialog, search for "Incoming Webhook"
   - Click "Configure" next to Incoming Webhook

3. **Set up the webhook details**:
   - Provide a name for your webhook (e.g., "Server Alerts")
   - Optionally upload an icon image
   - Click "Create"

4. **Save the webhook URL**:
   - After creation, you'll be provided with a webhook URL
   - This URL looks like: `https://outlook.office.com/webhook/...`
   - **Important:** Copy this URL and keep it secure

## Configuring Telert for Teams

### CLI Configuration

```bash
telert config teams --webhook-url "<webhook-url>" --set-default
telert status --provider teams  # Test your configuration
```

### Python Configuration

```python
from telert import configure_teams, send

configure_teams("<webhook-url>")
send("✅ Teams test", provider="teams")
```

### Environment Variables

If you prefer to use environment variables (useful for CI/CD pipelines):

```bash
export TELERT_TEAMS_WEBHOOK="<webhook-url>"
```

## Teams-Specific Features

### Message Formatting

Microsoft Teams supports Markdown formatting in messages:

```bash
# Markdown formatting in messages
telert send --provider teams "Project build **completed** with *zero* errors"
```

Supported Markdown syntax includes:
- `**text**` - Bold text
- `*text*` - Italic text
- `~~text~~` - Strikethrough text
- ``` `code` ``` - Inline code
- `[Link text](URL)` - Hyperlinks

### Message Cards

Teams supports rich message cards with more advanced formatting. Telert automatically formats your notifications in a visually appealing way.

### Security Considerations

- Webhook URLs should be treated like secrets
- Anyone with the webhook URL can post messages to the channel
- Consider regenerating webhook URLs periodically
- For highly sensitive environments, use dedicated teams/channels

### Organization Policies

Some Microsoft Teams organizations have restrictions on webhooks:
- Webhooks might need to be approved by an administrator
- Some organizations disable incoming webhooks entirely
- Check with your IT department if you encounter issues

### Troubleshooting

If you encounter issues:

1. **Messages not appearing**:
   - Verify the webhook URL is correct
   - Ensure the webhook is still active (webhooks can expire)
   - Check if your organization allows incoming webhooks

2. **Rate limiting**:
   - Microsoft Teams has rate limits that may vary by organization
   - For high-frequency notifications, consider batching messages

3. **Channel renamed or deleted**:
   - If the target channel is renamed or deleted, you'll need to create a new webhook