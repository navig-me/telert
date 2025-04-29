# Release Notes for v0.1.26

## New Features

### Docker Integration
- Added Docker image with CLI and server mode support
- Added server.py for API endpoint functionality
- Created comprehensive Docker documentation
- Published to GitHub Container Registry (ghcr.io/navig-me/telert)

### GitHub Action and CI Integrations
- Added GitHub Action for running commands with notifications
- Created GitLab CI template for easy pipeline integration
- Developed CircleCI orb for notification support
- Added detailed CI/CD integration documentation

### Shell Completions
- Added shell completion generation command (telert completions)
- Implemented completions for Bash, Zsh, and Fish shells
- Created installation scripts for easy setup
- Added documentation for shell completions

### VS Code Extension
- Added VS Code extension for "Run in Terminal & Notify"
- Implemented status bar timer for running commands
- Added "Send Last Terminal Output" feature
- Created configuration options for notification providers and thresholds

## Usage Examples

### Docker Usage
```bash
# CLI mode
docker run --rm ghcr.io/navig-me/telert:latest send "Hello from Docker!"

# Server mode
docker run -d -p 8000:8000 ghcr.io/navig-me/telert:latest serve
```

### GitHub Actions
```yaml
- name: Run tests with notification
  uses: navig-me/telert/actions/run@v1
  with:
    command: npm test
    label: Run Tests
    provider: telegram
    token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    chat-id: ${{ secrets.TELEGRAM_CHAT_ID }}
```

### Shell Completions
```bash
# Generate and install completions
telert completions --shell bash > ~/.local/share/bash-completion/completions/telert
```

### VS Code Extension
The extension can be installed from the VS Code marketplace and provides:
- Command palette integration
- Right-click menu actions
- Status bar timer
- Provider configuration