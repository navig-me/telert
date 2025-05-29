"""Network monitoring for telert."""

import atexit
import json
import socket
import threading
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import requests

try:
    import ping3
    PING_AVAILABLE = True
except ImportError:
    PING_AVAILABLE = False

from telert.messaging import Provider
from telert.monitoring.base import (
    Monitor, 
    MonitorID, 
    MonitorType, 
    MonitorStatus, 
    MonitorRegistry
)
from telert.monitoring.activity_logs import LogLevel
from telert.monitoring.debug_logs import debug_log, debug_inspect


class NetworkMonitor(Monitor):
    """Monitor network connectivity and send notifications on issues."""
    
    def __init__(
        self,
        name: Optional[str] = None,
        host: Optional[str] = None,
        url: Optional[str] = None,
        port: Optional[int] = None,
        check_type: str = "ping",
        interval: int = 60,
        timeout: int = 5,
        expected_status: Optional[int] = None,
        expected_content: Optional[str] = None,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
        enabled: bool = True,
        monitor_id: Optional[MonitorID] = None,
    ):
        """
        Initialize a new network monitor.
        
        Args:
            name: Friendly name for this monitor
            host: Hostname or IP address to monitor
            url: URL to monitor (for HTTP/HTTPS checks)
            port: Port to check (for TCP checks)
            check_type: Type of check to perform (ping, http, tcp)
            interval: How often to check (in seconds)
            timeout: Timeout for checks (in seconds)
            expected_status: Expected HTTP status code
            expected_content: Expected content in HTTP response
            method: HTTP method to use (for HTTP checks)
            headers: HTTP headers to include (for HTTP checks)
            body: HTTP request body (for HTTP checks)
            provider: Provider(s) to use for notifications
            enabled: Whether this monitor is initially enabled
            monitor_id: Optional monitor ID (generated if not provided)
        """
        super().__init__(
            monitor_type=MonitorType.NETWORK,
            name=name,
            provider=provider,
            enabled=enabled,
            monitor_id=monitor_id,
        )
        
        # Validate check parameters based on check type
        self.check_type = check_type.lower()
        self._validate_check_type()
        
        # Host/URL/port validation
        if self.check_type == "http":
            if not url:
                raise ValueError("URL is required for HTTP checks")
            self.url = url
            self.host = urlparse(url).netloc
        else:
            if not host:
                raise ValueError("Host is required for ping and TCP checks")
            self.host = host
            self.url = None
            
        self.port = port
        
        # Validate TCP check has port
        if self.check_type == "tcp" and not port:
            raise ValueError("Port is required for TCP checks")
        
        # Check settings
        self.interval = max(30, interval)  # Minimum 30 seconds
        self.timeout = max(1, min(timeout, 30))  # Between 1 and 30 seconds
        
        # HTTP check settings
        self.expected_status = expected_status
        self.expected_content = expected_content
        self.method = method.upper()
        self.headers = headers or {}
        self.body = body
        
        # Internal state
        self._should_run = False
        self._monitor_thread = None
        self._last_check_time = 0
        self._last_status = None
        self._consecutive_failures = 0
        self._first_check = True
    
    def _validate_check_type(self) -> None:
        """Validate the check type."""
        valid_types = {"ping", "http", "tcp"}
        if self.check_type not in valid_types:
            raise ValueError(f"Invalid check type: {self.check_type}. "
                           f"Valid types are: {', '.join(valid_types)}")
        
        # Check if ping is available
        if self.check_type == "ping" and not PING_AVAILABLE:
            raise ValueError("Ping checks require the 'ping3' package. "
                           "Install it with 'pip install ping3'.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert monitor to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "host": self.host,
            "url": self.url,
            "port": self.port,
            "check_type": self.check_type,
            "interval": self.interval,
            "timeout": self.timeout,
            "expected_status": self.expected_status,
            "expected_content": self.expected_content,
            "method": self.method,
            "headers": self.headers,
            "body": self.body,
        })
        return data
    
    def _check_ping(self) -> Dict[str, Any]:
        """Perform a ping check."""
        if not PING_AVAILABLE:
            return {
                "success": False,
                "error": "Ping module not available",
            }
        
        try:
            # Use ping3 to send ICMP ping
            ping_time = ping3.ping(self.host, timeout=self.timeout)
            
            if ping_time is None or ping_time is False:
                return {
                    "success": False,
                    "error": "Host is unreachable",
                }
            
            return {
                "success": True,
                "latency": ping_time * 1000,  # Convert to ms
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def _check_tcp(self) -> Dict[str, Any]:
        """Perform a TCP port check."""
        sock = None
        start_time = time.time()
        
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Connect to the host:port
            sock.connect((self.host, self.port))
            
            # Calculate connection time
            connection_time = (time.time() - start_time) * 1000  # ms
            
            return {
                "success": True,
                "latency": connection_time,
            }
        except socket.timeout:
            return {
                "success": False,
                "error": f"Connection to {self.host}:{self.port} timed out",
            }
        except socket.error as e:
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            if sock:
                sock.close()
    
    def _check_http(self) -> Dict[str, Any]:
        """Perform an HTTP check."""
        try:
            # Prepare request
            start_time = time.time()
            
            # Send request
            response = requests.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                data=self.body,
                timeout=self.timeout,
                verify=True,  # Verify SSL certificates
                allow_redirects=True,
            )
            
            # Calculate request time
            request_time = (time.time() - start_time) * 1000  # ms
            
            # Check status code
            status_ok = True
            if self.expected_status and response.status_code != self.expected_status:
                status_ok = False
            
            # Check content
            content_ok = True
            if self.expected_content and self.expected_content not in response.text:
                content_ok = False
            
            # Build result
            result = {
                "success": status_ok and content_ok,
                "status_code": response.status_code,
                "latency": request_time,
                "content_length": len(response.content),
            }
            
            if not status_ok:
                result["error"] = f"Expected status {self.expected_status}, got {response.status_code}"
            elif not content_ok:
                result["error"] = "Expected content not found in response"
                
            return result
        except requests.RequestException as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def _perform_check(self) -> Dict[str, Any]:
        """Perform the appropriate check based on check type."""
        if self.check_type == "ping":
            return self._check_ping()
        elif self.check_type == "tcp":
            return self._check_tcp()
        elif self.check_type == "http":
            return self._check_http()
        else:
            return {
                "success": False,
                "error": f"Unsupported check type: {self.check_type}",
            }
    
    def _check_status_changed(self, current_status: Dict[str, Any]) -> Optional[str]:
        """Check if status changed and generate notification message."""
        debug_log(f"Checking status changes for {self.monitor_id}")
        
        if self._first_check:
            self._first_check = False
            self._last_status = current_status
            debug_log("First check, establishing baseline")
            try:
                self.log(LogLevel.INFO, "First network check completed, establishing baseline")
                debug_log("Called self.log in first check")
            except Exception as e:
                debug_log(f"Error calling self.log in first check: {e}")
            return None
        
        # Get previous success state
        prev_success = self._last_status.get("success", False) if self._last_status else False
        curr_success = current_status.get("success", False)
        
        # Status changed from success to failure
        if prev_success and not curr_success:
            self._consecutive_failures += 1
            
            # Create message with details
            target = self.url or f"{self.host}"
            if self.port and not self.url:
                target += f":{self.port}"
                
            message = f"⚠️ {self.check_type.upper()} check failed for {target}"
            
            if "error" in current_status:
                message += f"\nError: {current_status['error']}"
                
            return message
        
        # Status changed from failure to success
        elif not prev_success and curr_success:
            if self._consecutive_failures > 0:
                # Create recovery message
                target = self.url or f"{self.host}"
                if self.port and not self.url:
                    target += f":{self.port}"
                    
                message = f"✅ {self.check_type.upper()} check recovered for {target}"
                
                if "latency" in current_status:
                    message += f"\nLatency: {current_status['latency']:.2f} ms"
                
                # Reset consecutive failures
                self._consecutive_failures = 0
                
                return message
        
        # Update consecutive failures counter for ongoing failures
        if not curr_success:
            self._consecutive_failures += 1
        else:
            self._consecutive_failures = 0
            
        # No notification needed
        return None
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop that runs in a separate thread."""
        while self._should_run:
            try:
                # Perform the check
                current_status = self._perform_check()
                
                # Check for status changes
                notification = self._check_status_changed(current_status)
                if notification:
                    self.send_notification(notification)
                
                # Update last status and check time
                self._last_status = current_status
                self._last_check_time = time.time()
                
            except Exception as e:
                print(f"Error in network monitor: {e}")
            
            # Sleep until next check, but allow for clean shutdown
            sleep_until = time.time() + self.interval
            while time.time() < sleep_until and self._should_run:
                time.sleep(1)
    
    def start(self) -> None:
        """Start the network monitor."""
        debug_log(f"Starting network monitor {self.monitor_id}")
        debug_inspect(self, "NetworkMonitor")
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            # Already running
            debug_log("Monitor thread already running")
            return
        
        try:
            self.log(LogLevel.INFO, f"Starting network monitor {self.monitor_id}")
            debug_log("Called self.log successfully")
        except Exception as e:
            debug_log(f"Error calling self.log: {e}")
            
        self._should_run = True
        self._first_check = True
        self._last_status = None
        self._consecutive_failures = 0
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
        )
        self._monitor_thread.start()
    
    def stop(self) -> None:
        """Stop the network monitor."""
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


class NetworkMonitorRegistry(MonitorRegistry[NetworkMonitor]):
    """Registry for network monitors."""
    
    def __init__(self):
        super().__init__(MonitorType.NETWORK)
        # Override with proper type
        self._monitors: Dict[MonitorID, NetworkMonitor] = {}
        self._load()
    
    def _load(self) -> None:
        """Load monitors from disk."""
        if not self.data_file.exists():
            self._monitors = {}
            return
            
        try:
            data = json.loads(self.data_file.read_text())
            for monitor_id, monitor_data in data.items():
                # Create NetworkMonitor instances from the saved data
                try:
                    monitor = NetworkMonitor(
                        name=monitor_data.get("name"),
                        host=monitor_data.get("host"),
                        url=monitor_data.get("url"),
                        port=monitor_data.get("port"),
                        check_type=monitor_data.get("check_type", "ping"),
                        interval=monitor_data.get("interval", 60),
                        timeout=monitor_data.get("timeout", 5),
                        expected_status=monitor_data.get("expected_status"),
                        expected_content=monitor_data.get("expected_content"),
                        method=monitor_data.get("method", "GET"),
                        headers=monitor_data.get("headers"),
                        body=monitor_data.get("body"),
                        provider=monitor_data.get("provider"),
                        enabled=monitor_data.get("enabled", True),
                        monitor_id=monitor_id,
                    )
                    self._monitors[monitor_id] = monitor
                    
                    # Start the monitor if it's enabled
                    if monitor.enabled:
                        monitor.start()
                except Exception as e:
                    print(f"Error loading network monitor {monitor_id}: {e}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading network monitors: {e}")
            # If file is corrupt or can't be read, start with empty registry
            self._monitors = {}


# Global registry instance
_network_registry = NetworkMonitorRegistry()


def monitor_network(
    name: Optional[str] = None,
    host: Optional[str] = None,
    url: Optional[str] = None,
    port: Optional[int] = None,
    check_type: str = "ping",
    interval: int = 60,
    timeout: int = 5,
    expected_status: Optional[int] = None,
    expected_content: Optional[str] = None,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[str] = None,
    provider: Optional[Union[str, Provider, List[Union[str, Provider]]]] = None,
) -> MonitorID:
    """
    Start monitoring a network endpoint and receive notifications on issues.
    
    Args:
        name: Friendly name for this monitor
        host: Hostname or IP address to monitor
        url: URL to monitor (for HTTP/HTTPS checks)
        port: Port to check (for TCP checks)
        check_type: Type of check to perform (ping, http, tcp)
        interval: How often to check (in seconds)
        timeout: Timeout for checks (in seconds)
        expected_status: Expected HTTP status code
        expected_content: Expected content in HTTP response
        method: HTTP method to use (for HTTP checks)
        headers: HTTP headers to include (for HTTP checks)
        body: HTTP request body (for HTTP checks)
        provider: Provider(s) to use for notifications
        
    Returns:
        Monitor ID that can be used to stop monitoring
        
    Examples:
        from telert.monitoring import monitor_network
        
        # Basic ping monitoring
        monitor_id = monitor_network(
            name="Web Server",
            host="example.com",
            check_type="ping",
            interval=60,
            provider="slack"
        )
        
        # HTTP endpoint monitoring
        monitor_id = monitor_network(
            name="API Health",
            url="https://api.example.com/health",
            check_type="http",
            expected_status=200,
            timeout=5,
            provider="telegram"
        )
        
        # TCP port monitoring
        monitor_id = monitor_network(
            name="Database Connection",
            host="db.example.com",
            port=5432,
            check_type="tcp",
            provider="email"
        )
    """
    monitor = NetworkMonitor(
        name=name,
        host=host,
        url=url,
        port=port,
        check_type=check_type,
        interval=interval,
        timeout=timeout,
        expected_status=expected_status,
        expected_content=expected_content,
        method=method,
        headers=headers,
        body=body,
        provider=provider,
    )
    
    monitor_id = _network_registry.register(monitor)
    monitor.start()
    
    return monitor_id


def list_network_monitors() -> List[Dict[str, Any]]:
    """
    List all registered network monitors.
    
    Returns:
        List of monitor information dictionaries
        
    Examples:
        from telert.monitoring import list_network_monitors
        
        monitors = list_network_monitors()
        for monitor in monitors:
            print(f"{monitor['id']}: {monitor['name']} - {monitor['status']}")
    """
    result = []
    for monitor in _network_registry.list_all():
        monitor_info = monitor.to_dict()
        monitor_info["status"] = monitor.status().value
        result.append(monitor_info)
    
    return result


def stop_network_monitor(monitor_id: MonitorID) -> bool:
    """
    Stop a network monitor.
    
    Args:
        monitor_id: ID of the monitor to stop
        
    Returns:
        True if the monitor was stopped, False if not found
        
    Examples:
        from telert.monitoring import stop_network_monitor
        
        success = stop_network_monitor("net-12345678")
    """
    monitor = _network_registry.get(monitor_id)
    if not monitor:
        return False
        
    monitor.stop()
    return _network_registry.unregister(monitor_id)


# Make sure to initialize properly
def _cleanup_monitors():
    """Stop all monitors on exit."""
    for monitor in _network_registry.list_all():
        monitor.stop()

# Register cleanup function
atexit.register(_cleanup_monitors)
