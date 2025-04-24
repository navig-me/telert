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
__version__ = "0.1.9"  # Fix Buy Me a Coffee button for PyPI

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