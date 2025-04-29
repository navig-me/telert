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
    "configure_providers",
    "get_config", 
    "is_configured",
    "set_default_provider",
    "set_default_providers",
    "list_providers"
]
__version__ = "0.1.22"  # Fixed macOS desktop notifications issue #3, improved documentation

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
    configure_providers,
    get_config, 
    is_configured,
    set_default_provider,
    set_default_providers,
    list_providers
)