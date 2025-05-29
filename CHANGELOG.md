# Changelog

## 0.1.46 (2025-05-29)
- Support multiple to emails in configure_email

## 0.1.45 (2025-05-28)
- Fix for making email fields optional

## 0.1.44 (2025-05-28)
- Fixes for email support as a notification provider

## 0.1.43 (2025-05-26)
- Fixed `telert init` command

## 0.1.42 (2025-05-26)
- Added email support as a notification provider

## 0.1.41 (2025-05-26)
- Added support for Telegram file sending for long messages (inspired by [Telepipe](https://github.com/Linuxmaster14/telepipe))

## 0.1.40 (2025-05-08)
- Added interactive `telert init` wizard for first-run setup
- Added `--quiet`, `--silent`, and `--verbose` flags to control console output

## 0.1.39 (2025-05-07)
- Fixed HTML and Markdown formatting for non-Telegram providers
- Added automatic tag stripping for providers that don't support formatting

## 0.1.38 (2025-05-06)
- Added support for HTML and Markdown messages in Telegram

## 0.1.36 (2025-05-02)
- Added Python process monitoring to VS Code extension
- Fixed issues with indentation when wrapping Python code blocks
- Enhanced smart function detection for multi-line function definitions
- Improved telert CLI installation and update logic
- Added configurable settings for process monitoring and CLI updates

## 0.1.35 (2025-05-02)
- Enhanced VSCode extension with Python function monitoring capabilities
- Added context manager and decorator right-click options in Python files
- Removed "Send Last Terminal Output" feature
- Improved marketing and discoverability for VSCode extension
- Positioned extension as a complete code command center

## 0.1.34 (2025-05-02)
- Fix issue with --version being sent on VS Code install
- Bump version to 0.1.34 across the codebase.

## 0.1.31 (2025-04-30)
- Bump version to 0.1.31 across the codebase.

## 0.1.30 (2025-04-30)
- Update Docker action

## 0.1.29 (2025-04-30)
- Dockerfile: add python3-setuptools and python3-wheel; use --no-build-isolation for pip install
- Bump project versions and references to 0.1.29 across codebase

## 0.1.28 (2025-04-30)
- Added Quick Pick configuration UI in the VS Code extension for notification providers
- VS Code extension now auto-installs and auto-updates the telert CLI
- Dockerfile: install python3-distutils to enable building wheels in slim images
- Bumped version numbers across project for release

## 0.1.27 (2025-04-30)
- Introduced consistent logo design with telert.png
- Updated VS Code extension icon and notification icons
- Enhanced Docker API with a professional web interface
- Improved API with static file serving and better user experience
- Included telert.png in package distribution
- Updated VS Code extension to version 0.1.1

## 0.1.26 (2025-04-29)
- Added Docker image with server and CLI modes
- Added GitHub Action for running commands with notifications
- Added GitLab CI template and CircleCI orb integrations
- Created VS Code extension for "Run in Terminal & Notify"
- Added detailed documentation for all new features

## 0.1.25 (2025-04-29)
- Clean docs folder

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