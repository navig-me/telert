"""Simple logging utilities for telert monitors."""

import json
import os
import pathlib
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# Define the log directory
LOG_DIR = pathlib.Path(os.path.expanduser("~/.config/telert/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Maximum number of log entries to keep per monitor type
MAX_LOG_ENTRIES = 1000

class LogLevel(Enum):
    """Log levels for monitor logs."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    FAILURE = "failure"

    def __str__(self) -> str:
        return self.value

class MonitorLogger:
    """Logger for telert monitors."""

    @staticmethod
    def log(
        monitor_id: str,
        monitor_type: str,
        level: LogLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Log a monitor event.

        Args:
            monitor_id: ID of the monitor
            monitor_type: Type of the monitor (process, log, network)
            level: Log level
            message: Log message
            details: Additional details to include in the log entry

        Returns:
            The log entry that was created
        """
        # Create log entry
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "monitor_id": monitor_id,
            "monitor_type": monitor_type,
            "level": level.value,
            "message": message,
            "details": details or {},
        }

        # Load existing logs
        log_file = LOG_DIR / f"{monitor_type}_logs.json"
        logs = []
        
        if log_file.exists():
            try:
                content = log_file.read_text()
                if content.strip():
                    logs = json.loads(content)
            except (json.JSONDecodeError, OSError):
                # If file is corrupt or can't be read, start with empty logs
                logs = []
        else:
            # Create an empty file
            log_file.write_text("[]")

        # Add new log entry
        logs.append(log_entry)
        
        # Limit the number of logs
        if len(logs) > MAX_LOG_ENTRIES:
            logs = logs[-MAX_LOG_ENTRIES:]
        
        # Save logs
        log_file.write_text(json.dumps(logs, indent=2))
        
        return log_entry
    
    @staticmethod
    def get_logs(
        monitor_type: Optional[str] = None,
        monitor_id: Optional[str] = None,
        level: Optional[Union[LogLevel, str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve monitor logs.

        Args:
            monitor_type: Filter by monitor type (process, log, network)
            monitor_id: Filter by monitor ID
            level: Filter by log level
            limit: Maximum number of logs to return

        Returns:
            List of log entries matching the filters
        """
        # Normalize level if it's a string
        if level is not None and isinstance(level, str):
            try:
                level = LogLevel(level)
            except ValueError:
                raise ValueError(f"Invalid log level: {level}")

        # Determine which log files to load
        if monitor_type:
            log_files = [LOG_DIR / f"{monitor_type}_logs.json"]
        else:
            # Load all monitor types
            log_files = [
                LOG_DIR / "process_logs.json",
                LOG_DIR / "log_logs.json",
                LOG_DIR / "network_logs.json",
            ]
        
        # Load and filter logs
        all_logs = []
        for log_file in log_files:
            if not log_file.exists():
                continue
                
            try:
                content = log_file.read_text()
                if not content.strip():
                    continue
                    
                logs = json.loads(content)
                all_logs.extend(logs)
            except (json.JSONDecodeError, OSError):
                # Skip files that can't be read
                continue
        
        # Apply filters
        filtered_logs = []
        for log in all_logs:
            # Filter by monitor ID if specified
            if monitor_id and log.get("monitor_id") != monitor_id:
                continue
                
            # Filter by level if specified
            if level and log.get("level") != level.value:
                continue
                
            filtered_logs.append(log)
        
        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply limit
        return filtered_logs[:limit]
    
    @staticmethod
    def clear_logs(monitor_type: Optional[str] = None, monitor_id: Optional[str] = None) -> int:
        """
        Clear monitor logs.

        Args:
            monitor_type: Clear logs for this monitor type only
            monitor_id: Clear logs for this monitor ID only

        Returns:
            Number of log entries cleared
        """
        if monitor_id and not monitor_type:
            # Need to determine monitor type from ID prefix
            if monitor_id.startswith("pro"):
                monitor_type = "process"
            elif monitor_id.startswith("log"):
                monitor_type = "log"
            elif monitor_id.startswith("net"):
                monitor_type = "network"
        
        # Determine which log files to clear
        if monitor_type:
            log_files = [LOG_DIR / f"{monitor_type}_logs.json"]
        else:
            # Clear all monitor types
            log_files = [
                LOG_DIR / "process_logs.json",
                LOG_DIR / "log_logs.json",
                LOG_DIR / "network_logs.json",
            ]
        
        count = 0
        
        # Clear logs
        for log_file in log_files:
            if not log_file.exists():
                continue
                
            try:
                if monitor_id:
                    # Only clear logs for specific monitor ID
                    logs = json.loads(log_file.read_text())
                    original_count = len(logs)
                    logs = [log for log in logs if log.get("monitor_id") != monitor_id]
                    count += original_count - len(logs)
                    log_file.write_text(json.dumps(logs, indent=2))
                else:
                    # Clear all logs for this monitor type
                    try:
                        logs = json.loads(log_file.read_text())
                        count += len(logs)
                    except (json.JSONDecodeError, OSError):
                        pass
                    log_file.write_text("[]")
            except (json.JSONDecodeError, OSError):
                # Skip files that can't be read
                continue
        
        return count
