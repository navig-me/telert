#!/usr/bin/env bash
# Bash completion for telert

_telert_completion() {
    local cur prev words cword
    _init_completion || return

    # List of primary commands
    local commands="run send config status hook help"
    
    # List of providers
    local providers="telegram teams slack discord pushover audio desktop endpoint"
    
    # List of config commands
    local config_commands="telegram teams slack discord pushover audio desktop endpoint set-defaults"
    
    # Standard options for most commands
    local options="--provider --all-providers --verbose --help"

    # Handle different positions in the command line
    if [[ $cword -eq 1 ]]; then
        # Complete primary commands
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return 0
    fi

    # Handle subcommands
    case "${words[1]}" in
        run)
            # Options for 'run'
            COMPREPLY=($(compgen -W "$options --label --only-fail --message" -- "$cur"))
            ;;
        send)
            # Options for 'send'
            COMPREPLY=($(compgen -W "$options" -- "$cur"))
            ;;
        config)
            if [[ $cword -eq 2 ]]; then
                # Complete config subcommands
                COMPREPLY=($(compgen -W "$config_commands" -- "$cur"))
            elif [[ $cword -ge 3 ]]; then
                # Options based on the provider
                case "${words[2]}" in
                    telegram)
                        COMPREPLY=($(compgen -W "--token --chat-id --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    teams|slack|discord)
                        COMPREPLY=($(compgen -W "--webhook-url --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    pushover)
                        COMPREPLY=($(compgen -W "--token --user --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    audio)
                        COMPREPLY=($(compgen -W "--sound-file --volume --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    desktop)
                        COMPREPLY=($(compgen -W "--app-name --icon-path --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    endpoint)
                        COMPREPLY=($(compgen -W "--url --method --header --payload-template --name --timeout --set-default --add-to-defaults" -- "$cur"))
                        ;;
                    set-defaults)
                        COMPREPLY=($(compgen -W "--providers" -- "$cur"))
                        ;;
                esac
            fi
            ;;
        hook)
            # Options for 'hook'
            COMPREPLY=($(compgen -W "--long -l --provider --all-providers" -- "$cur"))
            ;;
        status)
            # Options for 'status'
            COMPREPLY=($(compgen -W "--provider --all-providers" -- "$cur"))
            ;;
        help)
            # Complete primary commands for help
            COMPREPLY=($(compgen -W "$commands" -- "$cur"))
            ;;
    esac

    # Handle options that expect a provider as value
    if [[ "$prev" == "--provider" ]]; then
        COMPREPLY=($(compgen -W "$providers" -- "$cur"))
        return 0
    fi

    return 0
}

complete -F _telert_completion telert