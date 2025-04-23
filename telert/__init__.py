__all__ = [
    "__version__", 
    "telert", 
    "send", 
    "notify", 
    "configure", 
    "get_config", 
    "is_configured"
]
__version__ = "0.1.4"

from telert.api import (
    telert, 
    send, 
    notify, 
    configure, 
    get_config, 
    is_configured
)