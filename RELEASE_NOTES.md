# Release Notes for v0.1.27

## New Features

### Brand Identity Update
- Introduced consistent logo design with telert.png
- Updated VS Code extension icon and notification icons
- Enhanced Docker API with a professional web interface
- Added logo to README.md for better brand recognition

### Docker API Improvements
- Added static file serving capability to the FastAPI server
- Created a landing page with logo and API documentation
- Made the API more user-friendly with visual documentation
- Fixed server content type handling

### VS Code Extension
- Updated VS Code extension to version 0.1.1
- Improved icon with the new telert logo
- Enhanced visual consistency across platforms

### Package Improvements
- Included telert.png in package distribution
- Optimized images for different use cases and platforms
- Ensured consistent branding across all interfaces

## Previous Release (v0.1.26)

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


### VS Code Extension
The extension can be installed from the VS Code marketplace and provides:
- Command palette integration
- Right-click menu actions
- Status bar timer
- Provider configuration