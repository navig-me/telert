# Docker Usage Guide for Telert

Telert provides an official Docker image that can be used in two modes:

1. **CLI Mode** - Run telert commands within a container
2. **Server Mode** - Run a notification API server that accepts HTTP requests

## Using the Docker Image

The official image is available on GitHub Container Registry:

```bash
docker pull ghcr.io/navig-me/telert:latest
```

### CLI Mode

Run telert commands directly:

```bash
# Test telert status
docker run --rm ghcr.io/navig-me/telert:latest status

# Configure a provider (using environment variables)
docker run --rm \
  -e TELERT_TELEGRAM_TOKEN=your_token \
  -e TELERT_TELEGRAM_CHAT_ID=your_chat_id \
  ghcr.io/navig-me/telert:latest config telegram --set-default

# Send a notification 
docker run --rm \
  -e TELERT_TELEGRAM_TOKEN=your_token \
  -e TELERT_TELEGRAM_CHAT_ID=your_chat_id \
  ghcr.io/navig-me/telert:latest send "Hello from Docker!"
```

For persistent configuration, mount a volume to `/root/.config/telert`:

```bash
docker run --rm \
  -v telert_config:/root/.config/telert \
  -e TELERT_TELEGRAM_TOKEN=your_token \
  -e TELERT_TELEGRAM_CHAT_ID=your_chat_id \
  ghcr.io/navig-me/telert:latest config telegram --set-default
```

### Server Mode

Run telert as a notification API server:

```bash
docker run -d --name telert-server \
  -p 8000:8000 \
  -e TELERT_TELEGRAM_TOKEN=your_token \
  -e TELERT_TELEGRAM_CHAT_ID=your_chat_id \
  -v telert_config:/root/.config/telert \
  ghcr.io/navig-me/telert:latest serve
```

Then you can send notifications via HTTP:

```bash
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from the API!"}'
```

### API Endpoints

The server mode exposes the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check, returns basic API info |
| `/status` | GET | Returns configuration status of providers |
| `/providers` | GET | Lists all configured providers |
| `/send` | POST | Sends a notification |
| `/health` | GET | Health check for container monitoring |

#### Sending Notifications

Send a notification using the `/send` endpoint:

```bash
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from the API!",
    "provider": "telegram", 
    "all_providers": false
  }'
```

Request body parameters:

- `message` (required): The message to send
- `provider`: Specific provider(s) to use (string or array of strings)
- `all_providers`: If true, sends to all configured providers (default: false)

## Using with Docker Compose

A docker-compose.yml file is included in the repository to make setup easier:

```bash
# Start the server
docker-compose up -d telert-server

# Run a CLI command
docker-compose run telert send "Hello from Docker Compose!"
```

## Environment Variables

Configure telert in Docker using environment variables:

```bash
# Set default provider
export TELERT_DEFAULT_PROVIDER="telegram,slack"

# Configure Telegram
export TELERT_TELEGRAM_TOKEN="your-bot-token"
export TELERT_TELEGRAM_CHAT_ID="your-chat-id"

# Configure Slack
export TELERT_SLACK_WEBHOOK="https://hooks.slack.com/services/..."

# Configure Discord
export TELERT_DISCORD_WEBHOOK="https://discord.com/api/webhooks/..."
```

See the [Environment Variables](https://github.com/navig-me/telert#-environment-variables) section in the main README for the complete list of supported variables.

## Building the Docker Image Locally

If you want to build the image yourself:

```bash
git clone https://github.com/navig-me/telert.git
cd telert
docker build -t telert:local .
```

## Configuration Persistence

For persistent configuration across container restarts, mount a volume to `/root/.config/telert`:

```bash
docker volume create telert_config

docker run --rm \
  -v telert_config:/root/.config/telert \
  ghcr.io/navig-me/telert:latest config telegram --token "token" --chat-id "chat-id" --set-default
```