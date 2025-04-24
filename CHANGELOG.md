# Changelog

All notable changes to telert will be documented in this file.

## 0.1.10 (2024-04-24)

### Improvements
- Add terminal demo SVG to documentation
- Clean up recording-related files
- Better organization of demo scripts

## 0.1.9 (2024-04-24)

### Improvements
- Fix Buy Me A Coffee button for PyPI compatibility
- Add telert-wrapper.sh script to handle shell built-ins like `source`

## 0.1.8 (2024-04-24)

### Bug Fixes
- Add timeouts to HTTP requests to prevent hanging on network issues
- Fix context manager return values for proper exception handling
- Improve size limits for command output in silent mode
- Fix provider flag handling in piped mode (supports both `--provider=slack` and `--provider slack` formats)
- Add URL validation for webhook providers

### Improvements
- Better error messages for network-related issues
- More robust handling of large command outputs

## 0.1.7 (2024-04-24)

### Bug Fixes
- Fix documentation links in README.md to use absolute GitHub URLs instead of relative paths

## 0.1.6 (2024-04-24)

### Bug Fixes
- Fix real-time output display in run mode
- Add TELERT_SILENT environment variable for controlling output display

## 0.1.5 (Earlier)

- Multi-provider support (Telegram, Teams, Slack)