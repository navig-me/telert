# Fish completion for telert

# Main commands
complete -c telert -f
complete -c telert -n "__fish_use_subcommand" -a "run" -d "Run a command and send notification on completion"
complete -c telert -n "__fish_use_subcommand" -a "send" -d "Send a notification message"
complete -c telert -n "__fish_use_subcommand" -a "config" -d "Configure notification providers"
complete -c telert -n "__fish_use_subcommand" -a "status" -d "Check notification configuration status"
complete -c telert -n "__fish_use_subcommand" -a "hook" -d "Generate shell hooks for long-running commands"
complete -c telert -n "__fish_use_subcommand" -a "help" -d "Show help"

# Provider options
set -l telert_providers telegram teams slack discord pushover audio desktop endpoint

# Run command options
complete -c telert -n "__fish_seen_subcommand_from run" -l "label" -d "Label for the command" -r
complete -c telert -n "__fish_seen_subcommand_from run" -l "provider" -d "Specify notification provider" -r -a "$telert_providers"
complete -c telert -n "__fish_seen_subcommand_from run" -l "all-providers" -d "Use all configured providers"
complete -c telert -n "__fish_seen_subcommand_from run" -l "only-fail" -d "Only notify on failure"
complete -c telert -n "__fish_seen_subcommand_from run" -l "message" -d "Custom notification message" -r
complete -c telert -n "__fish_seen_subcommand_from run" -l "verbose" -d "Show verbose output"

# Send command options
complete -c telert -n "__fish_seen_subcommand_from send" -l "provider" -d "Specify notification provider" -r -a "$telert_providers"
complete -c telert -n "__fish_seen_subcommand_from send" -l "all-providers" -d "Use all configured providers"
complete -c telert -n "__fish_seen_subcommand_from send" -l "verbose" -d "Show verbose output"

# Config command subcommands
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "telegram" -d "Configure Telegram"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "teams" -d "Configure Microsoft Teams"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "slack" -d "Configure Slack"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "discord" -d "Configure Discord"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "pushover" -d "Configure Pushover"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "audio" -d "Configure audio notifications"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "desktop" -d "Configure desktop notifications"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "endpoint" -d "Configure HTTP endpoint"
complete -c telert -n "__fish_seen_subcommand_from config; and not __fish_seen_subcommand_from $telert_providers set-defaults" -a "set-defaults" -d "Set default providers"

# Provider-specific options
# Telegram
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from telegram" -l "token" -d "Telegram bot token" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from telegram" -l "chat-id" -d "Telegram chat ID" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from telegram" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from telegram" -l "add-to-defaults" -d "Add to default providers"

# Teams
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from teams" -l "webhook-url" -d "Teams webhook URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from teams" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from teams" -l "add-to-defaults" -d "Add to default providers"

# Slack
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from slack" -l "webhook-url" -d "Slack webhook URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from slack" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from slack" -l "add-to-defaults" -d "Add to default providers"

# Discord
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "webhook-url" -d "Discord webhook URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "username" -d "Discord webhook username" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "avatar-url" -d "Discord webhook avatar URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from discord" -l "add-to-defaults" -d "Add to default providers"

# Pushover
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from pushover" -l "token" -d "Pushover application token" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from pushover" -l "user" -d "Pushover user key" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from pushover" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from pushover" -l "add-to-defaults" -d "Add to default providers"

# Audio
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from audio" -l "sound-file" -d "Path to sound file" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from audio" -l "volume" -d "Volume level (0.0-1.0)" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from audio" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from audio" -l "add-to-defaults" -d "Add to default providers"

# Desktop
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from desktop" -l "app-name" -d "Application name" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from desktop" -l "icon-path" -d "Path to icon file" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from desktop" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from desktop" -l "add-to-defaults" -d "Add to default providers"

# Endpoint
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "url" -d "HTTP endpoint URL" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "method" -d "HTTP method (GET, POST, etc.)" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "header" -d "HTTP headers" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "payload-template" -d "Payload template" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "name" -d "Friendly name for endpoint" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "timeout" -d "Request timeout in seconds" -r
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "set-default" -d "Set as default provider"
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from endpoint" -l "add-to-defaults" -d "Add to default providers"

# Set-defaults
complete -c telert -n "__fish_seen_subcommand_from config; and __fish_seen_subcommand_from set-defaults" -l "providers" -d "Comma-separated list of providers" -r

# Hook options
complete -c telert -n "__fish_seen_subcommand_from hook" -s "l" -l "long" -d "Threshold in seconds for notification" -r
complete -c telert -n "__fish_seen_subcommand_from hook" -l "provider" -d "Specify notification provider" -r -a "$telert_providers"
complete -c telert -n "__fish_seen_subcommand_from hook" -l "all-providers" -d "Use all configured providers"

# Status options
complete -c telert -n "__fish_seen_subcommand_from status" -l "provider" -d "Specify notification provider" -r -a "$telert_providers"
complete -c telert -n "__fish_seen_subcommand_from status" -l "all-providers" -d "Show status for all providers"

# Help options
complete -c telert -n "__fish_seen_subcommand_from help" -a "run send config status hook" -d "Command to get help for"