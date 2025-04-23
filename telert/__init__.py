__all__ = [
    "__version__", 
    "telert", 
    "send", 
    "notify", 
    "configure",  # Legacy function for backward compatibility
    "configure_telegram",
    "configure_teams",
    "configure_slack",
    "get_config", 
    "is_configured",
    "set_default_provider",
    "list_providers"
]
__version__ = "0.1.6"  # Bump version for multi-provider support

from telert.api import (
    telert, 
    send, 
    notify, 
    configure,
    configure_telegram,
    configure_teams,
    configure_slack,
    get_config, 
    is_configured,
    set_default_provider,
    list_providers
)