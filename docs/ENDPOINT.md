# Custom HTTP Endpoint Setup for Telert

The Custom HTTP Endpoint provider allows you to send notifications to any HTTP service with fully configurable URL, headers, and payload templates. This makes it possible to integrate Telert with virtually any service that accepts HTTP requests.

## Configuration

### Basic Configuration

```bash
# Basic configuration with default POST method
telert config endpoint --url "https://api.example.com/notify" --set-default
```

### Advanced Configuration

```bash
# Advanced configuration with all options
telert config endpoint \
  --url "https://api.example.com/notify/{status_code}" \
  --method POST \
  --header "Authorization: Bearer abc123" \
  --header "X-Custom: Value" \
  --payload-template '{"text": "{message}", "status": "{status_code}", "time": "{duration_seconds}"}' \
  --name "My Notification Service" \
  --timeout 30 \
  --set-default
```

## Configuration Options

| Option | Description |
|--------|-------------|
| `--url` | The URL to send the request to (required) |
| `--method` | HTTP method to use (GET, POST, PUT, DELETE, etc.) - default: POST |
| `--header` | HTTP header in 'Key: Value' format (can be specified multiple times) |
| `--payload-template` | Template for the request body (default: `{"text": "{message}"}`)
| `--name` | Friendly name for this endpoint (default: "Custom Endpoint") |
| `--timeout` | Request timeout in seconds (default: 20) |
| `--set-default` | Set this provider as the default |

## Template Placeholders

The endpoint provider supports these placeholders in both URL and payload templates:

- `{message}` - The notification message
- `{status_code}` - Exit status of the command (when using run mode)
- `{duration_seconds}` - Time taken by the command in seconds (when using run mode)
- `{timestamp}` - Current Unix timestamp

## Examples

### Discord Webhook

```bash
telert config endpoint \
  --url "https://discord.com/api/webhooks/your-webhook-id/your-webhook-token" \
  --payload-template '{"content": "{message}"}' \
  --name "Discord" \
  --set-default
```

### Custom API with Authentication

```bash
telert config endpoint \
  --url "https://api.example.com/notifications" \
  --method POST \
  --header "Authorization: Bearer your-token-here" \
  --header "Content-Type: application/json" \
  --payload-template '{"message": "{message}", "app": "telert", "timestamp": "{timestamp}"}' \
  --name "Custom API" \
  --set-default
```

### Webhooks with Status Information

```bash
# This example sends the command's exit status and execution time
telert config endpoint \
  --url "https://hooks.example.com/services/your-webhook-path" \
  --payload-template '{"text": "Command completed with status {status_code} in {duration_seconds} seconds", "message": "{message}"}' \
  --name "Status Webhook" \
  --set-default
```

## Non-JSON Payloads

For non-JSON payloads, provide a plain text template and set the appropriate Content-Type header:

```bash
telert config endpoint \
  --url "https://api.example.com/text-endpoint" \
  --header "Content-Type: text/plain" \
  --payload-template "Status: {status_code}\nMessage: {message}\nTime: {duration_seconds}s" \
  --name "Text API" \
  --set-default
```

## Environment Variables

You can also configure the endpoint provider using environment variables:

```bash
export TELERT_ENDPOINT_URL="https://api.example.com/notify"
export TELERT_ENDPOINT_METHOD="POST"
export TELERT_ENDPOINT_HEADERS='{"Authorization": "Bearer token", "Content-Type": "application/json"}'
export TELERT_ENDPOINT_PAYLOAD='{"text": "{message}"}'
export TELERT_ENDPOINT_NAME="My API"
export TELERT_ENDPOINT_TIMEOUT="30"
```

## Using from Python

```python
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

# Send a message
from telert import send
send("Hello from Python!", provider="endpoint")
```
