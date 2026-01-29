import platform
import os

def get_system_info():
    """Returns basic system info to log during the void creation."""
    return {
        "os": platform.system(),
        "arch": platform.machine(),
        "user": os.getlogin() if hasattr(os, 'getlogin') else "Unknown"
    }
