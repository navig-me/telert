# Changelog

## 0.1.24 (2025-04-29)
- Added Discord as supported provider
- Additional handling for desktop notifications and error handling
- Fixed macOS desktop notifications (Issue #3)

## 0.1.22 (2025-04-29)
- Fixed macOS desktop notifications not appearing in WezTerm and some other terminal apps (Issue #3)
- Improved notification reliability on macOS by trying multiple methods with timeouts
- Added recommendation to use terminal-notifier on macOS for the best experience
- Enhanced error handling to prevent hangs when notification systems are unresponsive
- Added ENDPOINT.md file with detailed documentation for custom HTTP endpoints
- Improved documentation structure and readability in README.md

## 0.1.21 (2025-04-29)
- Added custom HTTP endpoint provider with configurable URLs, methods, headers, and payload templates
- Added support for variable substitution in endpoint URLs and payloads ({message}, {status_code}, etc.)
- Added configurable timeout for endpoint requests
- Added documentation for endpoint configuration via CLI and Python API

## 0.1.20 (2024-04-26)
- Added links for Replit, GitHub Actions to README and DigitalOcean, Vultr links


## 0.1.19 (2024-04-26)
- Added feedback message after telert commands run, showing which providers received the notification
- Added table of contents to README for improved documentation navigation

## 0.1.18
- Added multiple default providers support with priority ordering
- Added environment variable override for default provider with TELERT_DEFAULT_PROVIDER
- Implemented ability to send to multiple providers in the same message
- Enhanced environment variable support for all provider settings

## 0.1.17
- Added Pushover as notification provider for iOS and Android
- Added detailed documentation for Pushover configuration

## 0.1.16 and earlier
- Added Microsoft Teams support
- Added Slack support
- Added Desktop notifications support
- Added Audio notifications support
- Initial release with Telegram support