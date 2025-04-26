__all__ = [
    "__version__", 
    "telert", 
    "send", 
    "notify", 
    "configure",  # Legacy function for backward compatibility
    "configure_telegram",
    "configure_teams",
    "configure_slack",
    "configure_audio",
    "configure_desktop",
    "configure_pushover",
    "get_config", 
    "is_configured",
    "set_default_provider",
    "list_providers"
]
__version__ = "0.1.17"  # Add Pushover notification provider

from telert.api import (
    telert, 
    send, 
    notify, 
    configure,
    configure_telegram,
    configure_teams,
    configure_slack,
    configure_audio,
    configure_desktop,
    configure_pushover,
    get_config, 
    is_configured,
    set_default_provider,
    list_providers
)