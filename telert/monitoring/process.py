"""Process monitoring for telert."""

import json
import re
import subprocess
import threading
import time
import atexit
from typing import Any, Dict, List, Optional, Union # Callable, Set removed

# Local application imports
from telert.messaging import Provider
from telert.monitoring.base import (
    Monitor,
    MonitorID,
    MonitorStatus,
    MonitorType,
    MonitorRegistry
)
from telert.monitoring.activity_logs import LogLevel # LogLevel import from correct module

# Helper function for psutil import error
def _get_platform_help():
    import platform # Keep platform import local to this helper
    system = platform.system().lower()
    arch = platform.machine().lower()

    help_msg = []
    help_msg.append("\nInstallation instructions:")
    help_msg.append(f"- System: {system}, Architecture: {arch}")

    if system == 'darwin' and 'arm' in arch:  # Apple Silicon
        help_msg.append("\nFor Apple Silicon (M-series) users, try:")
        help_msg.append("  arch -arm64 pip install --no-cache-dir psutil")
        help_msg.append("Or for Intel compatibility:")
        help_msg.append("  arch -x86_64 pip install --no-cache-dir psutil")
    elif system == 'windows':
        help_msg.append("\nOn Windows, you might need to install Visual C++ Build Tools:")
        help_msg.append("  https://visualstudio.microsoft.com/visual-cpp-build-tools/")

    help_msg.append("\nFor other platforms, try:")
    help_msg.append("  pip install --upgrade --force-reinstall psutil")
    return "\n".join(help_msg)

# psutil import with detailed error handling
try:
    import psutil
except (ImportError, OSError) as e:
    error_msg = (
        f"Failed to import psutil: {str(e)}\n"
        "psutil is required for process monitoring. "
        f"{_get_platform_help()}"
    )
    raise ImportError(error_msg) from e

# Type aliases
ResourceThreshold = Union[int, float, str]
NotifyEvent = str


class ProcessMonitor(Monitor):
    """Monitor system processes and send notifications on state changes."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        process_name: Optional[str] = None,
        command: Optional[str] = None,
        pid: Optional[int] = None,
        notify_on: Optional[List[str]] = None,
        cpu_threshold: Optional[ResourceThreshold] = None,
        memory_threshold: Optional[ResourceThreshold] = None,
        action: Optional[str] = None,
        check_interval: int = 30,
        provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
        enabled: bool = True,
        monitor_id: Optional[MonitorID] = None,
    ):
        """
        Initialize a new process monitor.
        
        Args:
            name: Friendly name for this monitor
            process_name: Name of the process to monitor (can be regex)
            command: Command pattern to match against processes
            pid: Specific process ID to monitor
            notify_on: Events to notify on (stop, start, crash, high-cpu, high-memory)
            cpu_threshold: CPU usage threshold percentage (0-100)
            memory_threshold: Memory usage threshold (can be number or string like "2G")
            action: Command to run when process state changes
            check_interval: How often to check process status (in seconds)
            provider: Provider(s) to use for notifications
            enabled: Whether this monitor is initially enabled
            monitor_id: Optional monitor ID (generated if not provided)
        """
        super().__init__(
            monitor_type=MonitorType.PROCESS,
            name=name,
            provider=provider,
            enabled=enabled,
            monitor_id=monitor_id,
        )
        
        # Process identification parameters
        if not any([process_name, command, pid]):
            raise ValueError("At least one of process_name, command, or pid must be provided")
            
        self.process_name = process_name
        self.command = command
        self.pid = pid
        
        # Notification parameters
        self.notify_on = notify_on or ["stop", "crash"]
        self._validate_notify_events(self.notify_on)
        
        # Resource threshold parameters
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = self._parse_memory_threshold(memory_threshold) if memory_threshold else None
        
        # Action and monitoring parameters
        self.action = action
        self.check_interval = max(5, check_interval)  # Minimum 5 seconds
        
        # Monitoring state
        self._should_run = False
        self._monitor_thread = None
        self._last_status = {}
        self._first_check = True
        self._last_check_time = 0
        
    def _validate_notify_events(self, events: List[str]) -> None:
        """Validate notification event types."""
        valid_events = {"start", "stop", "crash", "high-cpu", "high-memory"}
        invalid_events = set(events) - valid_events
        if invalid_events:
            raise ValueError(f"Invalid notification events: {', '.join(invalid_events)}. "
                            f"Valid events are: {', '.join(valid_events)}")
    
    def _parse_memory_threshold(self, threshold: ResourceThreshold) -> int:
        """Parse memory threshold to bytes."""
        if isinstance(threshold, (int, float)):
            return int(threshold)
            
        if not isinstance(threshold, str):
            raise ValueError(f"Invalid memory threshold: {threshold}")
            
        # Parse string values like "2G", "500M", etc.
        threshold = threshold.upper()
        match = re.match(r"^(\d+(?:\.\d+)?)([KMGT])?B?$", threshold)
        if not match:
            raise ValueError(f"Invalid memory threshold format: {threshold}")
            
        value, unit = match.groups()
        value = float(value)
        
        # Convert to bytes based on unit
        if unit == "K":
            return int(value * 1024)
        elif unit == "M":
            return int(value * 1024 * 1024)
        elif unit == "G":
            return int(value * 1024 * 1024 * 1024)
        elif unit == "T":
            return int(value * 1024 * 1024 * 1024 * 1024)
        else:
            return int(value)  # Assume bytes if no unit
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert monitor to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "process_name": self.process_name,
            "command": self.command,
            "pid": self.pid,
            "notify_on": self.notify_on,
            "cpu_threshold": self.cpu_threshold,
            "memory_threshold": self.memory_threshold,
            "action": self.action,
            "check_interval": self.check_interval,
        })
        return data
    
    def _find_matching_processes(self) -> List[psutil.Process]:
        """Find all processes matching the configured criteria."""
        self.log(LogLevel.INFO, f"Checking processes with criteria: name={self.process_name}, command={self.command}, pid={self.pid}")
        matching_processes = []
        
        # Check by PID first (most specific)
        if self.pid is not None:
            try:
                process = psutil.Process(self.pid)
                matching_processes.append(process)
                return matching_processes
            except psutil.NoSuchProcess:
                # PID not found, will return empty list
                pass
        
        # Check all processes for name or command match
        for process in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Match by process name (can be regex)
                if self.process_name:
                    if re.search(self.process_name, process.name(), re.IGNORECASE):
                        matching_processes.append(process)
                        continue
                
                # Match by command
                if self.command:
                    cmdline = " ".join(process.cmdline())
                    if cmdline and re.search(self.command, cmdline, re.IGNORECASE):
                        matching_processes.append(process)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process might have terminated or we don't have access
                continue
                
        return matching_processes
    
    def _check_process_resources(self, process: psutil.Process) -> Dict[str, Any]:
        """Check process resource usage and return status."""
        try:
            # Get CPU and memory info
            cpu_percent = process.cpu_percent(interval=0.1)
            memory_info = process.memory_info()
            memory_bytes = memory_info.rss
            
            return {
                "pid": process.pid,
                "running": True,
                "cpu_percent": cpu_percent,
                "memory_bytes": memory_bytes,
                "high_cpu": self.cpu_threshold is not None and cpu_percent > self.cpu_threshold,
                "high_memory": self.memory_threshold is not None and memory_bytes > self.memory_threshold,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {
                "pid": process.pid,
                "running": False,
                "cpu_percent": 0,
                "memory_bytes": 0,
                "high_cpu": False,
                "high_memory": False,
            }
    
    def _run_action(self) -> None:
        """Run the configured action command."""
        if not self.action:
            return
            
        try:
            subprocess.run(
                self.action,
                shell=True,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            self.send_notification(f"Failed to run action command: {e}")
    
    def _process_state_changed(self, old_status: Dict[int, Dict], new_status: Dict[int, Dict]) -> List[str]:
        """Check if process state changed and generate notification messages."""
        if self._first_check:
            self._first_check = False
            self.log(LogLevel.INFO, "First process check completed, establishing baseline.")
            return []
            
        notifications = []
        
        # Check for stopped or crashed processes
        for pid, last_info in old_status.items():
            if pid not in new_status or not new_status[pid].get("running"):
                event_type = "stopped" 
                
                if event_type in self.notify_on or ("stop" in self.notify_on and event_type == "stopped") or ("crash" in self.notify_on and event_type == "crashed"):
                    process_name = last_info.get("name", f"PID {pid}")
                    msg = f"Process {event_type}: {process_name} (PID {pid})"
                    notifications.append(msg)
                    self.log(LogLevel.FAILURE, msg, {"pid": pid, "process_name": process_name, "event": event_type})
                    if self.action:
                        self.log(LogLevel.INFO, f"Running action for {event_type} event on {process_name}: {self.action}")
                        self._run_action()
        
        # Check for newly started processes
        for pid, current_info in new_status.items():
            if current_info.get("running") and pid not in old_status: # Process is running and wasn't in old_status
                if "start" in self.notify_on:
                    process_name = current_info.get("name", f"PID {pid}")
                    msg = f"Process started: {process_name} (PID {pid})"
                    notifications.append(msg)
                    self.log(LogLevel.SUCCESS, msg, {"pid": pid, "process_name": process_name, "event": "start"})
                    if self.action:
                        self.log(LogLevel.INFO, f"Running action for start event on {process_name}: {self.action}")
                        self._run_action()

        # Check for resource threshold violations on currently running processes
        for pid, current_proc_status in new_status.items():
            if current_proc_status.get("running"):
                process_name = current_proc_status.get("name", f"PID {pid}")
                
                # Check CPU threshold
                if current_proc_status.get("high_cpu") and "high-cpu" in self.notify_on:
                    if not old_status.get(pid, {}).get("high_cpu"): # Notify only on transition into high CPU state
                        cpu_percent = current_proc_status.get("cpu_percent", 0.0)
                        msg = f"High CPU usage: {process_name} (PID {pid}) is at {cpu_percent:.1f}%"
                        notifications.append(msg)
                        self.log(LogLevel.WARNING, msg, {"pid": pid, "process_name": process_name, "cpu_percent": cpu_percent, "event": "high-cpu"})
                        if self.action:
                            self.log(LogLevel.INFO, f"Running action for high-cpu event on {process_name}: {self.action}")
                            self._run_action()
                
                # Check memory threshold
                if current_proc_status.get("high_memory") and "high-memory" in self.notify_on:
                    if not old_status.get(pid, {}).get("high_memory"): # Notify only on transition into high memory state
                        memory_bytes = current_proc_status.get("memory_bytes", 0)
                        memory_mb = memory_bytes / (1024 * 1024)
                        msg = f"High memory usage: {process_name} (PID {pid}) is using {memory_mb:.1f}MB"
                        notifications.append(msg)
                        self.log(LogLevel.WARNING, msg, {"pid": pid, "process_name": process_name, "memory_bytes": memory_bytes, "event": "high-memory"})
                        if self.action:
                            self.log(LogLevel.INFO, f"Running action for high-memory event on {process_name}: {self.action}")
                            self._run_action()
        return notifications
        
    def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in a separate thread."""
        while self._should_run:
            try:
                processes = self._find_matching_processes()
                
                # Build new status dictionary
                new_status = {}
                for proc in processes:
                    try:
                        # Get process information
                        proc_info = {
                            "pid": proc.pid,
                            "name": proc.name(),
                            "cmdline": proc.cmdline(),
                            "running": proc.is_running(),
                        }
                        
                        # Add resource information
                        resources = self._check_process_resources(proc)
                        proc_info.update(resources)
                        
                        # Store in new status
                        new_status[proc.pid] = proc_info
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process disappeared or we don't have access
                        continue
                
                # Check for state changes and send notifications
                notifications = self._process_state_changed(self._last_status, new_status)
                for msg in notifications:
                    self.send_notification(msg)
                
                # Update last status
                self._last_status = new_status
                self._last_check_time = time.time()
                
                # If no matching processes and we should notify on stop
                if not processes and "stop" in self.notify_on and not self._first_check:
                    # Avoid sending repeated notifications by checking if we already notified
                    if self._last_status:
                        self.send_notification(
                            f"No matching processes found for: "
                            f"{self.process_name or self.command or f'PID {self.pid}'}"
                        )
                        
                        # Run action if configured
                        if self.action:
                            self._run_action()
                    
                    # Clear last status to avoid sending repeated notifications
                    self._last_status = {}
                    
            except Exception as e:
                # Log the exception but keep the monitor running
                self.log(LogLevel.ERROR, f"Error in process monitor: {e}", exc_info=True)
            
            # Sleep until next check
            time.sleep(self.check_interval)
        
    def start(self) -> None:
        """Start the process monitor."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self.log(LogLevel.INFO, f"Process monitor {self.monitor_id} already running.")
            return
            
        self._should_run = True
        self._first_check = True
        self._last_status = {}
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
        )
        self._monitor_thread.start()
    
    def stop(self) -> None:
        """Stop the process monitor."""
        self.log(LogLevel.INFO, f"Stopping process monitor {self.monitor_id}")
        self._should_run = False
        if self._monitor_thread:
            # Give the thread time to exit gracefully
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None
            self.log(LogLevel.SUCCESS, f"Process monitor {self.monitor_id} stopped")
    
    def status(self) -> MonitorStatus:
        """Get the current status of the monitor."""
        if not self._should_run:
            return MonitorStatus.STOPPED
            
        if not self._monitor_thread or not self._monitor_thread.is_alive():
            return MonitorStatus.FAILED
            
        return MonitorStatus.RUNNING


class ProcessMonitorRegistry(MonitorRegistry[ProcessMonitor]):
    """Registry for process monitors."""
    
    def __init__(self):
        super().__init__(MonitorType.PROCESS)
        # Override with proper type
        self._monitors: Dict[MonitorID, ProcessMonitor] = {}
        self._load()
    
    def _load(self) -> None:
        """Load monitors from disk."""
        if not self.data_file.exists():
            self._monitors = {}
            return
            
        try:
            data = json.loads(self.data_file.read_text())
            for monitor_id, monitor_data in data.items():
                # Create ProcessMonitor instances from the saved data
                try:
                    monitor = ProcessMonitor(
                        name=monitor_data.get("name"),
                        process_name=monitor_data.get("process_name"),
                        command=monitor_data.get("command"),
                        pid=monitor_data.get("pid"),
                        notify_on=monitor_data.get("notify_on"),
                        cpu_threshold=monitor_data.get("cpu_threshold"),
                        memory_threshold=monitor_data.get("memory_threshold"),
                        action=monitor_data.get("action"),
                        check_interval=monitor_data.get("check_interval", 30),
                        provider=monitor_data.get("provider"),
                        enabled=monitor_data.get("enabled", True),
                        monitor_id=monitor_id,
                    )
                    self._monitors[monitor_id] = monitor
                    
                    # Start the monitor if it's enabled
                    if monitor.enabled:
                        monitor.start()
                except Exception as e:
                    print(f"Error loading process monitor {monitor_id}: {e}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading process monitors: {e}")
            # If file is corrupt or can't be read, start with empty registry
            self._monitors = {}


# Global registry instance
_process_registry = ProcessMonitorRegistry()


def monitor_process(
    name: Optional[str] = None,
    process_name: Optional[str] = None,
    command: Optional[str] = None,
    pid: Optional[int] = None,
    notify_on: Optional[List[str]] = None,
    cpu_threshold: Optional[ResourceThreshold] = None,
    memory_threshold: Optional[ResourceThreshold] = None,
    action: Optional[str] = None,
    check_interval: int = 30,
    provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
) -> MonitorID:
    """
    Start monitoring a process and receive notifications on state changes.
    
    Args:
        name: Friendly name for this monitor
        process_name: Name of the process to monitor (can be regex)
        command: Command pattern to match against processes
        pid: Specific process ID to monitor
        notify_on: Events to notify on (stop, start, crash, high-cpu, high-memory)
        cpu_threshold: CPU usage threshold percentage (0-100)
        memory_threshold: Memory usage threshold (can be number or string like "2G")
        action: Command to run when process state changes
        check_interval: How often to check process status (in seconds)
        provider: Provider(s) to use for notifications
        
    Returns:
        Monitor ID that can be used to stop monitoring
        
    Examples:
        from telert.monitoring import monitor_process
        
        # Monitor a process by name
        monitor_id = monitor_process(
            name="Web Server",
            process_name="nginx",
            notify_on=["stop", "high-cpu"],
            cpu_threshold=80,
            provider="slack"
        )
        
        # Monitor with resource thresholds
        monitor_id = monitor_process(
            name="Database",
            process_name="postgres",
            cpu_threshold=80,
            memory_threshold="2G",
            check_interval=30,
            provider="email"
        )
    """
    monitor = ProcessMonitor(
        name=name,
        process_name=process_name,
        command=command,
        pid=pid,
        notify_on=notify_on,
        cpu_threshold=cpu_threshold,
        memory_threshold=memory_threshold,
        action=action,
        check_interval=check_interval,
        provider=provider,
    )
    
    monitor_id = _process_registry.register(monitor)
    monitor.start()
    
    return monitor_id


def list_process_monitors() -> List[Dict[str, Any]]:
    """
    List all registered process monitors.
    
    Returns:
        List of monitor information dictionaries
        
    Examples:
        from telert.monitoring import list_process_monitors
        
        monitors = list_process_monitors()
        for monitor in monitors:
            print(f"{monitor['id']}: {monitor['name']} - {monitor['status']}")
    """
    result = []
    for monitor in _process_registry.list_all():
        monitor_info = monitor.to_dict()
        monitor_info["status"] = monitor.status().value
        result.append(monitor_info)
    
    return result


def stop_process_monitor(monitor_id: MonitorID) -> bool:
    """
    Stop a process monitor.
    
    Args:
        monitor_id: ID of the monitor to stop
        
    Returns:
        True if the monitor was stopped, False if not found
        
    Examples:
        from telert.monitoring import stop_process_monitor
        
        success = stop_process_monitor("proc-12345678")
    """
    monitor = _process_registry.get(monitor_id)
    if not monitor:
        return False
        
    monitor.stop()
    return _process_registry.unregister(monitor_id)


# Make sure to initialize properly

def _cleanup_monitors():
    """Stop all monitors on exit."""
    for monitor in _process_registry.list_all():
        monitor.stop()

# Register cleanup function
atexit.register(_cleanup_monitors)
