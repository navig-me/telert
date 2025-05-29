"""Log file monitoring for telert."""

import atexit
import json
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Union

from telert.messaging import Provider
from telert.monitoring.base import (
    Monitor, 
    MonitorID, 
    MonitorType, 
    MonitorStatus, 
    MonitorRegistry
)


class LogMonitor(Monitor):
    """Monitor log files for specific patterns and send notifications."""
    
    def __init__(
        self,
        file: str,
        pattern: str,
        name: Optional[str] = None,
        context_lines: int = 0,
        cooldown: int = 0,
        priority: str = "normal",
        provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
        enabled: bool = True,
        monitor_id: Optional[MonitorID] = None,
    ):
        """
        Initialize a new log file monitor.
        
        Args:
            file: Path to the log file to monitor
            pattern: Regular expression pattern to match in log lines
            name: Friendly name for this monitor
            context_lines: Number of lines to include before and after the match
            cooldown: Seconds to wait before sending similar notifications
            priority: Priority level (low, normal, high)
            provider: Provider(s) to use for notifications
            enabled: Whether this monitor is initially enabled
            monitor_id: Optional monitor ID (generated if not provided)
        """
        super().__init__(
            monitor_type=MonitorType.LOG,
            name=name,
            provider=provider,
            enabled=enabled,
            monitor_id=monitor_id,
        )
        
        # Validate the log file
        self.file = os.path.abspath(os.path.expanduser(file))
        if not os.path.isfile(self.file) and not os.path.isdir(os.path.dirname(self.file)):
            raise ValueError(f"Log file path is invalid: {file}")
        
        # Validate pattern
        try:
            self.pattern = pattern
            self._pattern_re = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regular expression pattern: {e}")
        
        # Configuration
        self.context_lines = max(0, context_lines)
        self.cooldown = max(0, cooldown)
        
        # Validate priority
        valid_priorities = {"low", "normal", "high"}
        if priority not in valid_priorities:
            raise ValueError(f"Invalid priority: {priority}. Valid options are: {', '.join(valid_priorities)}")
        self.priority = priority
        
        # Internal state
        self._should_run = False
        self._monitor_thread = None
        self._last_notification_time = 0
        self._last_position = 0
        self._last_inode = None
        self._processed_hashes = set()
        self._context_buffer = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert monitor to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "file": self.file,
            "pattern": self.pattern,
            "context_lines": self.context_lines,
            "cooldown": self.cooldown,
            "priority": self.priority,
        })
        return data
    
    def _check_file_changed(self) -> bool:
        """Check if the log file has changed (rotated)."""
        try:
            stat = os.stat(self.file)
            current_inode = stat.st_ino
            
            # If we don't have a previous inode, just store it
            if self._last_inode is None:
                self._last_inode = current_inode
                return False
                
            # Check if inode changed (file was rotated)
            if self._last_inode != current_inode:
                self._last_inode = current_inode
                self._last_position = 0
                return True
                
            return False
        except OSError:
            # File doesn't exist yet, reset position
            self._last_position = 0
            self._last_inode = None
            return False
    
    def _hash_match(self, match, context):
        """Create a hash of the match to detect duplicates."""
        # Use a simple hash of the match line and context
        match_text = match.group(0)
        context_text = "\n".join(context)
        return hash(f"{match_text}|{context_text}")
    
    def _process_match(self, line, line_number, all_lines):
        """Process a matching line and send a notification."""
        # Check if we've already processed this match (deduplication)
        match = self._pattern_re.search(line)
        if not match:
            return
            
        # Extract context lines
        context_start = max(0, line_number - self.context_lines)
        context_end = min(len(all_lines), line_number + self.context_lines + 1)
        context = all_lines[context_start:context_end]
        
        # Create a hash for deduplication
        match_hash = self._hash_match(match, context)
        if match_hash in self._processed_hashes:
            return
            
        # Check cooldown period
        current_time = time.time()
        if current_time - self._last_notification_time < self.cooldown:
            return
            
        # Add to processed hashes and update notification time
        self._processed_hashes.add(match_hash)
        self._last_notification_time = current_time
        
        # Build notification message
        message = f"Pattern match in {os.path.basename(self.file)}: {match.group(0)}"
        
        # Add context if available
        if context:
            context_str = "\n".join([f"{i+context_start+1}: {line}" for i, line in enumerate(context)])
            message += f"\n\nContext:\n{context_str}"
        
        # Send the notification
        self.send_notification(message)
        
        # Limit the size of the processed hashes set
        if len(self._processed_hashes) > 1000:
            self._processed_hashes = set(list(self._processed_hashes)[-500:])
    
    def _read_new_lines(self):
        """Read new lines from the log file."""
        if not os.path.exists(self.file):
            return []
            
        try:
            with open(self.file, "r", encoding="utf-8", errors="replace") as f:
                # Seek to the last position
                f.seek(self._last_position, 0)
                
                # Read new lines
                new_lines = f.readlines()
                
                # Update the position
                self._last_position = f.tell()
                
                return [line.rstrip() for line in new_lines]
        except Exception as e:
            print(f"Error reading log file {self.file}: {e}")
            return []
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        while self._should_run:
            try:
                # Check if file was rotated
                rotated = self._check_file_changed()
                if rotated:
                    self._processed_hashes.clear()
                
                # Read new lines
                new_lines = self._read_new_lines()
                if not new_lines:
                    # Sleep before checking again
                    time.sleep(1)
                    continue
                
                # Update context buffer
                self._context_buffer.extend(new_lines)
                
                # Keep buffer size reasonable
                max_buffer = max(1000, self.context_lines * 2)
                if len(self._context_buffer) > max_buffer:
                    self._context_buffer = self._context_buffer[-max_buffer:]
                
                # Process each new line
                for i, line in enumerate(new_lines):
                    if self._pattern_re.search(line):
                        # Calculate the index in the context buffer
                        buffer_index = len(self._context_buffer) - len(new_lines) + i
                        self._process_match(line, buffer_index, self._context_buffer)
            
            except Exception as e:
                print(f"Error in log monitor: {e}")
            
            # Sleep briefly before checking again
            time.sleep(0.5)
    
    def start(self) -> None:
        """Start the log monitor."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            # Already running
            return
            
        self._should_run = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
        )
        self._monitor_thread.start()
    
    def stop(self) -> None:
        """Stop the log monitor."""
        self._should_run = False
        if self._monitor_thread:
            # Give the thread time to exit gracefully
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
    
    def status(self) -> MonitorStatus:
        """Get the current status of the monitor."""
        if not self._should_run:
            return MonitorStatus.STOPPED
            
        if not self._monitor_thread or not self._monitor_thread.is_alive():
            return MonitorStatus.FAILED
            
        return MonitorStatus.RUNNING


class LogMonitorRegistry(MonitorRegistry[LogMonitor]):
    """Registry for log file monitors."""
    
    def __init__(self):
        super().__init__(MonitorType.LOG)
        # Override with proper type
        self._monitors: Dict[MonitorID, LogMonitor] = {}
        self._load()
    
    def _load(self) -> None:
        """Load monitors from disk."""
        if not self.data_file.exists():
            self._monitors = {}
            return
            
        try:
            data = json.loads(self.data_file.read_text())
            for monitor_id, monitor_data in data.items():
                # Create LogMonitor instances from the saved data
                try:
                    monitor = LogMonitor(
                        file=monitor_data.get("file"),
                        pattern=monitor_data.get("pattern"),
                        name=monitor_data.get("name"),
                        context_lines=monitor_data.get("context_lines", 0),
                        cooldown=monitor_data.get("cooldown", 0),
                        priority=monitor_data.get("priority", "normal"),
                        provider=monitor_data.get("provider"),
                        enabled=monitor_data.get("enabled", True),
                        monitor_id=monitor_id,
                    )
                    self._monitors[monitor_id] = monitor
                    
                    # Start the monitor if it's enabled
                    if monitor.enabled:
                        monitor.start()
                except Exception as e:
                    print(f"Error loading log monitor {monitor_id}: {e}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading log monitors: {e}")
            # If file is corrupt or can't be read, start with empty registry
            self._monitors = {}


# Global registry instance
_log_registry = LogMonitorRegistry()


def monitor_log(
    file: str,
    pattern: str,
    name: Optional[str] = None,
    context_lines: int = 0,
    cooldown: int = 0,
    priority: str = "normal",
    provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
) -> MonitorID:
    """
    Start monitoring a log file for pattern matches.
    
    Args:
        file: Path to the log file to monitor
        pattern: Regular expression pattern to match in log lines
        name: Friendly name for this monitor
        context_lines: Number of lines to include before and after the match
        cooldown: Seconds to wait before sending similar notifications
        priority: Priority level (low, normal, high)
        provider: Provider(s) to use for notifications
        
    Returns:
        Monitor ID that can be used to stop monitoring
        
    Examples:
        from telert.monitoring import monitor_log
        
        # Basic log monitoring
        monitor_id = monitor_log(
            file="/var/log/app.log",
            pattern="ERROR|CRITICAL",
            provider="slack"
        )
        
        # Advanced log monitoring
        monitor_id = monitor_log(
            name="Nginx Errors",
            file="/var/log/nginx/error.log",
            pattern=r"\\[error\\].*",
            context_lines=5,
            cooldown=300,  # seconds between similar notifications
            provider=["email", "teams"]
        )
    """
    monitor = LogMonitor(
        file=file,
        pattern=pattern,
        name=name,
        context_lines=context_lines,
        cooldown=cooldown,
        priority=priority,
        provider=provider,
    )
    
    monitor_id = _log_registry.register(monitor)
    monitor.start()
    
    return monitor_id


def list_log_monitors() -> List[Dict[str, Any]]:
    """
    List all registered log file monitors.
    
    Returns:
        List of monitor information dictionaries
        
    Examples:
        from telert.monitoring import list_log_monitors
        
        monitors = list_log_monitors()
        for monitor in monitors:
            print(f"{monitor['id']}: {monitor['name']} - {monitor['status']}")
    """
    result = []
    for monitor in _log_registry.list_all():
        monitor_info = monitor.to_dict()
        monitor_info["status"] = monitor.status().value
        result.append(monitor_info)
    
    return result


def stop_log_monitor(monitor_id: MonitorID) -> bool:
    """
    Stop a log file monitor.
    
    Args:
        monitor_id: ID of the monitor to stop
        
    Returns:
        True if the monitor was stopped, False if not found
        
    Examples:
        from telert.monitoring import stop_log_monitor
        
        success = stop_log_monitor("log-12345678")
    """
    monitor = _log_registry.get(monitor_id)
    if not monitor:
        return False
        
    monitor.stop()
    return _log_registry.unregister(monitor_id)


# Make sure to initialize properly
def _cleanup_monitors():
    """Stop all monitors on exit."""
    for monitor in _log_registry.list_all():
        monitor.stop()

# Register cleanup function
atexit.register(_cleanup_monitors)
