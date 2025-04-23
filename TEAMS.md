# Microsoft Teams Setup Guide for Telert

This guide provides detailed instructions for setting up Microsoft Teams with Telert using Power Automate (previously known as Microsoft Flow).

## Creating a Teams Workflow with Power Automate

1. **Access Power Automate**:
   - Go to [flow.microsoft.com](https://flow.microsoft.com)
   - Sign in with your Microsoft account

2. **Create a new instant cloud flow**:
   - Click on "Create" in the left sidebar
   - Select "Instant cloud flow"
   - Name your flow (e.g., "Telert Notifications")
   - Under "Choose how to trigger this flow", select "When a HTTP request is received"
   - Click "Create"

3. **Configure the HTTP trigger**:
   - In the HTTP trigger step, you'll need to define a JSON schema for the incoming payload
   - Use this schema for compatibility with Telert:
   ```json
   {
     "type": "object",
     "properties": {
       "text": {
         "type": "string"
       },
       "summary": {
         "type": "string"
       }
     }
   }
   ```

4. **Add a Post message step**:
   - Click "+ New step"
   - Search for "Post message in a chat or channel"
   - Select the Teams connection
   - Choose the team and channel where you want to post messages
   - In the Message field, use this expression: `@{triggerBody()?['text']}`

5. **Save the flow and get the HTTP POST URL**:
   - Save your flow
   - After saving, the HTTP POST URL will be generated in the trigger step
   - **Important:** Copy this URL and keep it secure

## Configuring Telert for Teams

### CLI Configuration

```bash
telert config teams --webhook-url "<flow-http-url>" --set-default
telert status --provider teams  # Test your configuration
```

### Python Configuration

```python
from telert import configure_teams, send

configure_teams("<flow-http-url>")
send("✅ Teams test", provider="teams")
```

### Environment Variables

If you prefer to use environment variables (useful for CI/CD pipelines):

```bash
export TELERT_TEAMS_WEBHOOK="<flow-http-url>"
```

## Teams-Specific Features

### Message Formatting

Microsoft Teams supports Markdown formatting in messages:

```bash
# Markdown formatting in messages
telert send --provider teams "Project build **completed** with *zero* errors"
```

Supported Markdown syntax in Teams includes:
- `**text**` - Bold text
- `*text*` - Italic text
- `~~text~~` - Strikethrough text
- ``` `code` ``` - Inline code
- `[Link text](URL)` - Hyperlinks

### Advanced Message Customization

For more advanced message formatting, you can customize your Power Automate flow:
- Use Adaptive Cards for rich interactive messages
- Format messages with headers, tables, and other HTML elements
- Include dynamic content from other sources

### Security Considerations

- HTTP trigger URLs should be treated like secrets
- Anyone with the Flow's HTTP URL can trigger messages to the channel
- For high-security environments, consider using additional authentication in your flow
- Use dedicated team channels for different types of notifications

### Organization Policies

Some Microsoft Teams organizations have governance policies:
- Power Automate flows might require administrative approval
- Some organizations restrict which connectors can be used
- Check with your IT department if you encounter permission issues

### Troubleshooting

If you encounter issues:

1. **Messages not appearing**:
   - Verify the Flow HTTP URL is correct
   - Check your flow run history for errors
   - Ensure the flow is turned on and has the correct permissions

2. **Rate limiting**:
   - Microsoft Power Automate has rate limits that may vary by license
   - For high-frequency notifications, consider batching messages

3. **Flow errors**:
   - Use the Power Automate monitoring tools to check for flow failures
   - Consider adding error handling to your flow for more reliable delivery