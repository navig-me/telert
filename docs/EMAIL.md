# Email (SMTP) Setup Guide for Telert

This guide provides detailed instructions for setting up Email (SMTP) notifications with Telert.

## Prerequisites

To use email notifications, you'll need:

1. An SMTP server address (e.g., `smtp.gmail.com`, `smtp.office365.com`)
2. SMTP port (typically 587 for TLS, 465 for SSL, or 25 for unencrypted)
3. SMTP authentication credentials (if required)
4. Recipient email address(es)

## Configuring Telert for Email

### CLI Configuration

Basic configuration:

```bash
telert config email --server smtp.example.com --port 587 --username user@example.com --password mypassword --to recipient@example.com --set-default
telert status --provider email  # Test your configuration
```

Advanced configuration with more options:

```bash
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

### Python Configuration

Basic configuration:

```python
from telert import configure_email, send

configure_email(
    server="smtp.example.com",
    port=587,
    username="user@example.com", 
    password="mypassword",
    to_addrs=["recipient@example.com"]
)

send("✅ Email test", provider="email")
```

Advanced configuration:

```python
from telert import configure_email, send

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

send("✅ Email test with <b>HTML</b> formatting", provider="email")
```

### Environment Variables

If you prefer to use environment variables (useful for CI/CD pipelines):

```bash
export TELERT_EMAIL_SERVER="smtp.example.com"
export TELERT_EMAIL_PORT="587"
export TELERT_EMAIL_USERNAME="user@example.com"
export TELERT_EMAIL_PASSWORD="mypassword"
export TELERT_EMAIL_FROM="alerts@example.com"
export TELERT_EMAIL_TO="admin@example.com,alerts@example.com"
export TELERT_EMAIL_SUBJECT_TEMPLATE="Telert Alert: {label} - {status}"
export TELERT_EMAIL_HTML="1"  # Set to 1 for HTML formatting
```

## Email-Specific Features

### Message Formatting

Email supports both plain text and HTML formatting:

```bash
# Enable HTML formatting during configuration
telert config email --server smtp.example.com ... --html --set-default

# Send HTML-formatted messages
telert send "Project build <b>completed</b> with <i>zero</i> errors"
```

### Multiple Recipients

You can send notifications to multiple email addresses:

```bash
# Comma-separated list of recipients
telert config email --server smtp.example.com ... --to "dev1@example.com,dev2@example.com,admin@example.com"
```

### Customizing Subject Lines

The subject line can be customized using a template with variables:

```bash
telert config email --server smtp.example.com ... --subject-template "Server Alert: {label} [{status}]"
```

Available variables in the subject template:

- `{label}` - Command label or notification title
- `{status}` - Status (e.g., "Success", "Failed")

## Common SMTP Server Settings

### Gmail

```bash
telert config email --server smtp.gmail.com --port 587 --username your.email@gmail.com --password "your-app-password"
```

Note: For Gmail, you must use an "App Password" if you have 2-factor authentication enabled. You can create one in your Google Account security settings.

### Office 365

```bash
telert config email --server smtp.office365.com --port 587 --username your.email@outlook.com --password "your-password"
```

### Amazon SES

```bash
telert config email --server email-smtp.us-east-1.amazonaws.com --port 587 --username "YOUR_SES_SMTP_USERNAME" --password "YOUR_SES_SMTP_PASSWORD"
```

## Security Considerations

- Passwords are stored in your local configuration file (~/.config/telert/config.json)
- For shared environments, consider using environment variables instead
- Use TLS/SSL when possible (port 587 with TLS or 465 for SSL)
- Some email providers may require you to enable "Less secure app access" or create app-specific passwords

## Troubleshooting

If you encounter issues:

1. **Authentication failures**:

   - Verify your username and password
   - Check if your email provider requires an app-specific password
   - Some providers might block access from "less secure apps"

2. **Connection issues**:

   - Verify the SMTP server address and port
   - Check if your network/firewall allows outgoing connections on the SMTP port
   - Try using TLS (port 587) instead of SSL (port 465) or vice versa

3. **Email not delivered**:

   - Check spam/junk folders
   - Verify recipient email addresses
   - Some providers limit the number of emails you can send per day

4. **Debug mode**:

   - Run with --verbose flag for more detailed output:

     ```bash
     telert send "Test message" --provider email --verbose
     ```
