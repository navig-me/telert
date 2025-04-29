# Telert on Railway

Telert offers a ready-to-deploy Railway template that provides an HTTP API for sending notifications. This is perfect for:

- CI/CD pipelines
- Server monitoring
- Cron job alerts
- Any system that needs to send notifications via HTTP

## Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/telert)

With one click, you'll get a fully functional API for sending Telert notifications from any system that can make HTTP requests.

## How to Use

After deploying to Railway, you'll need to:

1. Configure your notification provider using environment variables (see examples below)
2. Send notifications using HTTP requests:

```bash
# Send a simple notification
curl -X POST https://your-railway-url.up.railway.app/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Build complete!"}'
  
# Send to a specific provider
curl -X POST https://your-railway-url.up.railway.app/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Urgent alert!", "provider": "telegram"}'
```

## Environment Variables

Configure your providers using environment variables in your Railway project:

### Telegram
```
TELERT_PROVIDER=telegram
TELERT_TELEGRAM_TOKEN=your_bot_token
TELERT_TELEGRAM_CHAT_ID=your_chat_id
```

### Slack
```
TELERT_PROVIDER=slack
TELERT_SLACK_WEBHOOK_URL=your_webhook_url
```

### Microsoft Teams
```
TELERT_PROVIDER=teams
TELERT_TEAMS_WEBHOOK_URL=your_webhook_url
```

### Pushover
```
TELERT_PROVIDER=pushover
TELERT_PUSHOVER_TOKEN=your_app_token
TELERT_PUSHOVER_USER=your_user_key
```

### Custom HTTP Endpoint
```
TELERT_PROVIDER=endpoint
TELERT_ENDPOINT_URL=your_webhook_url
```

## Integration Examples

The Railway deployment is perfect for integration with various CI/CD systems:

### GitHub Actions
```yaml
- name: Notify on completion
  run: |
    curl -X POST https://your-railway-url.up.railway.app/send \
      -H "Content-Type: application/json" \
      -d '{"message": "Build complete for ${{ github.repository }}"}'
```

### Jenkins Pipeline
```groovy
post {
  success {
    sh '''
      curl -X POST https://your-railway-url.up.railway.app/send \
        -H "Content-Type: application/json" \
        -d '{"message": "✅ Jenkins build successful!"}'
    '''
  }
}
```

For more details and examples, see the [full Railway template repository](https://github.com/navig-me/railway-telert-notifier).