#compdef telert
# Zsh completion for telert

_telert() {
    local state line context
    local -a commands providers config_commands options

    # List of primary commands
    commands=(
        'run:Run a command and send notification on completion'
        'send:Send a notification message'
        'config:Configure notification providers'
        'status:Check notification configuration status'
        'hook:Generate shell hooks for long-running commands'
        'help:Show help'
    )
    
    # List of providers
    providers=(
        'telegram:Telegram messaging'
        'teams:Microsoft Teams messaging'
        'slack:Slack messaging'
        'discord:Discord messaging'
        'pushover:Pushover mobile notifications'
        'audio:Audio notifications'
        'desktop:Desktop notifications'
        'endpoint:Custom HTTP endpoint'
    )
    
    # List of config commands
    config_commands=(
        'telegram:Configure Telegram'
        'teams:Configure Microsoft Teams'
        'slack:Configure Slack'
        'discord:Configure Discord'
        'pushover:Configure Pushover'
        'audio:Configure audio notifications'
        'desktop:Configure desktop notifications'
        'endpoint:Configure HTTP endpoint'
        'set-defaults:Set default providers'
    )
    
    # Standard options for most commands
    options=(
        '--provider:Specify notification provider'
        '--all-providers:Use all configured providers'
        '--verbose:Show verbose output'
        '--help:Show help'
    )

    _arguments -C \
        '1: :->command' \
        '2: :->subcommand' \
        '*: :->args' && ret=0

    case $state in
        command)
            _describe -t commands 'telert commands' commands
            ;;
        subcommand)
            case "$line[1]" in
                run)
                    _arguments \
                        '--label:Label for the command' \
                        '--provider:Specify notification provider:($providers)' \
                        '--all-providers:Use all configured providers' \
                        '--only-fail:Only notify on failure' \
                        '--message:Custom notification message' \
                        '--verbose:Show verbose output'
                    ;;
                send)
                    _arguments \
                        '--provider:Specify notification provider:($providers)' \
                        '--all-providers:Use all configured providers' \
                        '--verbose:Show verbose output'
                    ;;
                config)
                    _describe -t commands 'config commands' config_commands
                    ;;
                hook)
                    _arguments \
                        '(-l --long)'{-l,--long}':Threshold in seconds for notification' \
                        '--provider:Specify notification provider:($providers)' \
                        '--all-providers:Use all configured providers'
                    ;;
                status)
                    _arguments \
                        '--provider:Specify notification provider:($providers)' \
                        '--all-providers:Show status for all providers'
                    ;;
                help)
                    _describe -t commands 'commands' commands
                    ;;
            esac
            ;;
        args)
            case "$line[1]" in
                config)
                    case "$line[2]" in
                        telegram)
                            _arguments \
                                '--token:Telegram bot token' \
                                '--chat-id:Telegram chat ID' \
                                '--set-default:Set as default provider' \
                                '--add-to-defaults:Add to default providers'
                            ;;
                        teams|slack|discord)
                            _arguments \
                                '--webhook-url:Webhook URL' \
                                '--set-default:Set as default provider' \
                                '--add-to-defaults:Add to default providers'
                            ;;
                        pushover)
                            _arguments \
                                '--token:Pushover application token' \
                                '--user:Pushover user key' \
                                '--set-default:Set as default provider' \
                                '--add-to-defaults:Add to default providers'
                            ;;
                        audio)
                            _arguments \
                                '--sound-file:Path to sound file' \
                                '--volume:Volume level (0.0-1.0)' \
                                '--set-default:Set as default provider' \
                                '--add-to-defaults:Add to default providers'
                            ;;
                        desktop)
                            _arguments \
                                '--app-name:Application name' \
                                '--icon-path:Path to icon file' \
                                '--set-default:Set as default provider' \
                                '--add-to-defaults:Add to default providers'
                            ;;
                        endpoint)
                            _arguments \
                                '--url:HTTP endpoint URL' \
                                '--method:HTTP method (GET, POST, etc.)' \
                                '--header:HTTP headers' \
                                '--payload-template:Payload template' \
                                '--name:Friendly name for endpoint' \
                                '--timeout:Request timeout in seconds' \
                                '--set-default:Set as default provider' \
                                '--add-to-defaults:Add to default providers'
                            ;;
                        set-defaults)
                            _arguments \
                                '--providers:Comma-separated list of providers'
                            ;;
                    esac
                    ;;
                run)
                    if [[ "$line[2]" == "--provider" ]]; then
                        _describe -t providers 'notification providers' providers
                    elif [[ "$words[(($CURRENT - 1))]" == "--provider" ]]; then
                        _describe -t providers 'notification providers' providers
                    fi
                    ;;
                send)
                    if [[ "$line[2]" == "--provider" ]]; then
                        _describe -t providers 'notification providers' providers
                    elif [[ "$words[(($CURRENT - 1))]" == "--provider" ]]; then
                        _describe -t providers 'notification providers' providers
                    fi
                    ;;
            esac
            ;;
    esac
}

_telert "$@"