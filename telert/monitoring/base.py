"""Base classes and utilities for telert monitoring."""

import abc
import enum
import json
import os
import pathlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic

from telert.messaging import Provider, send_message
from telert.monitoring.activity_logs import MonitorLogger, LogLevel

# Type definitions
MonitorID = str
T = TypeVar('T')

# Monitoring data directory
MONITOR_DATA_DIR = pathlib.Path(os.path.expanduser("~/.config/telert/monitors"))
MONITOR_DATA_DIR.mkdir(parents=True, exist_ok=True)


class MonitorType(enum.Enum):
    """Types of monitors supported by telert."""
    PROCESS = "process"
    LOG = "log"
    NETWORK = "network"
    
    def __str__(self) -> str:
        return self.value


class MonitorStatus(enum.Enum):
    """Status of a monitor."""
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"
    
    def __str__(self) -> str:
        return self.value


class Monitor(abc.ABC):
    """Base class for all telert monitors."""
    
    def __init__(
        self,
        monitor_type: MonitorType,
        name: Optional[str] = None,
        provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
        enabled: bool = True,
        monitor_id: Optional[MonitorID] = None,
    ):
        """
        Initialize a new monitor.
        
        Args:
            monitor_type: The type of monitor
            name: Optional friendly name for this monitor
            provider: Provider(s) to use for notifications
            enabled: Whether this monitor is initially enabled
            monitor_id: Optional monitor ID (generated if not provided)
        """
        self.monitor_type = monitor_type
        self.name = name
        self.enabled = enabled
        self.monitor_id = monitor_id or self._generate_id()
        self.created_at = datetime.now().isoformat()
        
        # Handle provider configuration
        if provider is None:
            # Use default provider from config
            self.provider = None
        elif isinstance(provider, list):
            # Convert string providers to Provider enum
            self.provider = []
            for p in provider:
                if isinstance(p, str):
                    try:
                        self.provider.append(Provider.from_string(p))
                    except ValueError:
                        raise ValueError(f"Unknown provider: {p}")
                else:
                    self.provider.append(p)
        elif isinstance(provider, str):
            try:
                self.provider = Provider.from_string(provider)
            except ValueError:
                raise ValueError(f"Unknown provider: {provider}")
        else:
            self.provider = provider
    
    def _generate_id(self) -> MonitorID:
        """Generate a unique monitor ID."""
        prefix = self.monitor_type.value[:3]  # First 3 chars of type
        unique_id = str(uuid.uuid4())[:8]     # First 8 chars of UUID
        return f"{prefix}-{unique_id}"
    
    @abc.abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert monitor to dictionary for serialization."""
        # Base fields that all monitors should have
        return {
            "id": self.monitor_id,
            "type": self.monitor_type.value,
            "name": self.name,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "provider": self._serialize_provider(self.provider),
        }
    
    @staticmethod
    def _serialize_provider(provider):
        """Helper to serialize provider to JSON-compatible format."""
        if provider is None:
            return None
        elif isinstance(provider, list):
            return [p.value if isinstance(p, Provider) else p for p in provider]
        else:
            return provider.value if isinstance(provider, Provider) else provider
    
    def log(self, level: LogLevel, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Log a monitor event."""
        MonitorLogger.log(
            monitor_id=self.monitor_id,
            monitor_type=self.monitor_type.value,
            level=level,
            message=message,
            details=details,
        )
    
    def send_notification(self, message: str) -> None:
        """Send a notification using the configured provider(s)."""
        if not self.enabled:
            return
            
        # Add monitor name to message if available
        if self.name:
            message = f"[{self.name}] {message}"
        
        # Log the notification    
        self.log(
            level=LogLevel.INFO,
            message=f"Sending notification: {message}",
            details={"notification_text": message}
        )
            
        send_message(message, provider=self.provider)
    
    @abc.abstractmethod
    def start(self) -> None:
        """Start the monitor."""
        pass
    
    @abc.abstractmethod
    def stop(self) -> None:
        """Stop the monitor."""
        pass
    
    @abc.abstractmethod
    def status(self) -> MonitorStatus:
        """Get the current status of the monitor."""
        pass


class MonitorRegistry(Generic[T]):
    """Registry for storing and retrieving monitors."""
    
    def __init__(self, monitor_type: MonitorType):
        """
        Initialize a new monitor registry.
        
        Args:
            monitor_type: The type of monitors managed by this registry
        """
        self.monitor_type = monitor_type
        self.data_file = MONITOR_DATA_DIR / f"{monitor_type.value}_monitors.json"
        self._monitors: Dict[MonitorID, T] = {}
        self._load()
    
    def _load(self) -> None:
        """Load monitors from disk."""
        if not self.data_file.exists():
            self._monitors = {}
            return
            
        try:
            data = json.loads(self.data_file.read_text())
            # Actual monitor instantiation is handled by subclasses
            self._monitors = data
        except (json.JSONDecodeError, OSError):
            # If file is corrupt or can't be read, start with empty registry
            self._monitors = {}
    
    def save(self) -> None:
        """Save monitors to disk."""
        # Convert monitors to serializable format
        serialized = {}
        for monitor_id, monitor in self._monitors.items():
            if hasattr(monitor, 'to_dict'):
                serialized[monitor_id] = monitor.to_dict()
            else:
                serialized[monitor_id] = monitor
                
        self.data_file.write_text(json.dumps(serialized, indent=2))
    
    def register(self, monitor: T) -> MonitorID:
        """Register a new monitor."""
        monitor_id = getattr(monitor, 'monitor_id', None)
        if not monitor_id:
            raise ValueError("Monitor must have a monitor_id")
            
        self._monitors[monitor_id] = monitor
        self.save()
        return monitor_id
    
    def unregister(self, monitor_id: MonitorID) -> bool:
        """Unregister a monitor by ID."""
        if monitor_id in self._monitors:
            monitor = self._monitors[monitor_id]
            # Stop the monitor if it has a stop method
            if hasattr(monitor, 'stop') and callable(getattr(monitor, 'stop')):
                monitor.stop()
                
            del self._monitors[monitor_id]
            self.save()
            return True
        return False
    
    def get(self, monitor_id: MonitorID) -> Optional[T]:
        """Get a monitor by ID."""
        return self._monitors.get(monitor_id)
    
    def list_all(self) -> List[T]:
        """List all registered monitors."""
        return list(self._monitors.values())
    
    def clear(self) -> None:
        """Clear all monitors."""
        # Stop all monitors first
        for monitor in self._monitors.values():
            if hasattr(monitor, 'stop') and callable(getattr(monitor, 'stop')):
                monitor.stop()
                
        self._monitors.clear()
        self.save()
