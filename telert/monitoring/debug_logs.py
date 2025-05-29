"""Debug utility to test the logging system."""

import os
import json
from datetime import datetime

# Create a simple debug log in the user's home directory
DEBUG_LOG_PATH = os.path.expanduser("~/telert_debug.log")

def debug_log(message):
    """Write a debug message to the log file."""
    timestamp = datetime.now().isoformat()
    with open(DEBUG_LOG_PATH, "a") as f:
        f.write(f"{timestamp} - {message}\n")

def debug_inspect(obj, label="Object"):
    """Inspect an object and write details to the debug log."""
    try:
        obj_dict = vars(obj) if hasattr(obj, "__dict__") else {"type": str(type(obj))}
        debug_log(f"{label}: {json.dumps(obj_dict, default=str)}")
    except Exception as e:
        debug_log(f"Error inspecting {label}: {e}")
