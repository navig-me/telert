# Telert Monitoring Guide

Telert's notifications are easily pluggable into monitoring capabilities, which allow you to watch processes, log files, and network endpoints. This guide explains how to use these features to create effective monitoring setups.


## Table of Contents

- [Persistence and Startup Behavior](#persistence-and-startup-behavior)
- [Process Monitoring](#process-monitoring)
- [Log File Monitoring](#log-file-monitoring)
- [Network Monitoring](#network-monitoring)
- [Monitor Management](#monitor-management)
- [Python API for Monitoring](#python-api-for-monitoring)
- [Use Cases](#use-cases)

## Persistence and Startup Behavior

Telert stores monitor configurations in persistent files at `~/.config/telert/monitors/`. After creating a monitor, it will run until you explicitly stop it or until the system restarts.

**Important**: Monitors do not automatically restart when the system reboots. To ensure monitors run continuously, set up an autostart mechanism using your system's init system:

### Using systemd (Linux)

Create a systemd user service:

```bash
mkdir -p ~/.config/systemd/user/
cat > ~/.config/systemd/user/telert-monitors.service << EOF
[Unit]
Description=Telert Monitoring Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 -c "import time; from telert.monitoring import list_process_monitors, list_log_monitors, list_network_monitors; time.sleep(5)"
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

# Enable and start the service
systemctl --user enable telert-monitors.service
systemctl --user start telert-monitors.service
```

### Using cron (macOS/Linux)

```bash
# Add to crontab
(crontab -l 2>/dev/null; echo "@reboot sleep 30 && python3 -c 'import time; from telert.monitoring import list_process_monitors, list_log_monitors, list_network_monitors; time.sleep(5)'") | crontab -
```

## Process Monitoring

Monitor system processes by name, command, or PID and receive notifications when they stop, use excessive resources, or change state.

### Process Monitoring CLI Usage

```bash
# Monitor a process by name (e.g., web server)
telert monitor process --name "nginx" --notify-on stop,high-cpu --provider slack

# Monitor a specific process by command pattern
telert monitor process --command-pattern "python.*worker\.py" --notify-on stop,crash --provider telegram

# Monitor using a process ID
telert monitor process --pid 1234 --notify-on stop --provider email

# Monitor with resource thresholds
telert monitor process --name "postgres" --cpu-threshold 80 --memory-threshold 2G --provider telegram

# Monitor with custom action when process stops
telert monitor process --command-pattern "python.*worker\.py" --notify-on stop --action "systemctl restart my-service"

# Add a friendly name to your monitor
telert monitor process --command-pattern "ps aux | grep nginx" --monitor-name "Web Server" --notify-on stop

# List all process monitors
telert monitor process --list

# Stop monitoring a specific process
telert monitor process --stop proc-12345678
```

### Process Monitor Options

| Option | Description | Example |
|--------|-------------|---------|
| `--command-pattern` | Command pattern to match | `--command-pattern "python worker.py"` |
| `--pid` | Specific process ID to monitor | `--pid 1234` |
| `--notify-on` | Events to notify on (comma-separated) | `--notify-on stop,high-cpu,high-memory` |
| `--cpu-threshold` | CPU usage threshold (0-100) | `--cpu-threshold 80` |
| `--memory-threshold` | Memory usage threshold | `--memory-threshold 2G` |
| `--action` | Command to run when state changes | `--action "systemctl restart service"` |
| `--check-interval` | Seconds between checks (min 5) | `--check-interval 30` |
| `--monitor-name` | Friendly name for this monitor | `--monitor-name "Web Server"` |
| `--provider` | Provider(s) for notifications | `--provider "slack,email"` |

### Notification Events

- `stop`: Process terminated
- `start`: New process matching criteria started
- `crash`: Process terminated unexpectedly
- `high-cpu`: CPU usage exceeded threshold
- `high-memory`: Memory usage exceeded threshold

## Log File Monitoring

Monitor log files for specific patterns and receive notifications with context when matches are found.

### Log Monitoring CLI Usage

```bash
# Basic log monitoring for errors
telert monitor log --file "/var/log/app.log" --pattern "ERROR|CRITICAL" --provider telegram

# Advanced monitoring with context lines
telert monitor log --file "/var/log/nginx/error.log" \
  --pattern ".*\[error\].*" \
  --context-lines 5 \
  --cooldown 300 \
  --monitor-name "Nginx Errors" \
  --provider slack

# Monitor application logs with high priority
telert monitor log --file "/var/log/app.log" \
  --pattern "CRITICAL:.*" \
  --priority high \
  --provider "telegram,email" \
  --monitor-name "Critical App Errors"

# List all log monitors
telert monitor log --list

# Stop monitoring a specific log file
telert monitor log --stop log-12345678
```

### Log Monitor Options

| Option | Description | Example |
|--------|-------------|---------|
| `--file` | Log file path to monitor | `--file "/var/log/app.log"` |
| `--pattern` | Regex pattern to match | `--pattern "ERROR\|CRITICAL"` |
| `--context-lines` | Lines to include before/after match | `--context-lines 5` |
| `--cooldown` | Seconds between similar notifications | `--cooldown 300` |
| `--priority` | Priority level (low, normal, high) | `--priority high` |
| `--monitor-name` | Friendly name for this monitor | `--monitor-name "App Errors"` |
| `--provider` | Provider(s) for notifications | `--provider "telegram,email"` |

### Features

- **Rotation-aware** - Handles log file rotation correctly
- **Context capture** - Shows lines before and after matches
- **Deduplication** - Avoids sending repeated notifications for similar errors
- **Cooldown period** - Prevents notification storms

## Network Monitoring

Monitor network connectivity and services using different check types (ping, HTTP, TCP).

### Network Monitoring CLI Usage

```bash
# Basic ping monitoring
telert monitor network --host example.com --type ping --interval 60 --provider slack

# HTTP endpoint monitoring
telert monitor network --url https://api.example.com/health \
  --expected-status 200 \
  --timeout 5 \
  --monitor-name "API Health" \
  --provider telegram

# TCP port monitoring
telert monitor network --host db.example.com --port 5432 --type tcp --provider email

# Advanced HTTP monitoring with authentication
telert monitor network --url https://app.example.com/status \
  --method POST \
  --header "Authorization: Bearer token123" \
  --body '{"check": "full"}' \
  --expected-content "healthy" \
  --provider teams

# List all network monitors
telert monitor network --list

# Stop monitoring a specific endpoint
telert monitor network --stop net-12345678
```

### Network Monitor Options

| Option | Description | Example |
|--------|-------------|---------|
| `--host` | Hostname or IP to monitor | `--host example.com` |
| `--url` | URL to monitor (for HTTP checks) | `--url https://api.example.com/health` |
| `--type` | Check type (ping, http, tcp) | `--type http` |
| `--port` | Port to check (for TCP checks) | `--port 5432` |
| `--interval` | Seconds between checks (min 30) | `--interval 60` |
| `--timeout` | Seconds to wait before timeout | `--timeout 5` |
| `--expected-status` | Expected HTTP status code | `--expected-status 200` |
| `--expected-content` | Expected content in response | `--expected-content "healthy"` |
| `--method` | HTTP method to use | `--method POST` |
| `--header` | HTTP header (can use multiple) | `--header "Auth: token"` |
| `--body` | HTTP request body | `--body '{"test":true}'` |
| `--monitor-name` | Friendly name for this monitor | `--monitor-name "API Health"` |
| `--provider` | Provider(s) for notifications | `--provider "slack,email"` |

## Help Commands

Telert provides comprehensive help for all monitoring commands through the CLI:

```bash
# General monitoring help
telert monitor --help

# Process monitoring help
telert monitor process --help

# Log file monitoring help
telert monitor log --help

# Network monitoring help
telert monitor network --help
```

These commands display detailed usage information, available options, and examples for each monitoring type. The help system is fully integrated with the rest of the Telert CLI, so users can discover monitoring features alongside other capabilities.

## Monitor Management

All monitors can be listed and stopped using the CLI:

```bash
# List all monitors of a specific type
telert monitor process --list
telert monitor log --list
telert monitor network --list

# Stop a specific monitor using its ID
telert monitor process --stop proc-12345678
telert monitor log --stop log-12345678
telert monitor network --stop net-12345678
```

## Monitor Activity History

Telert keeps a detailed activity history of all monitoring operations, including when checks were performed, results, and notifications sent. This activity history helps you track and debug your monitors. You can view and manage the monitor activity history using the CLI:

```bash
# View all monitor activity (most recent first)
telert monitor activity

# View activity for a specific monitor type
telert monitor activity --type process
telert monitor activity --type log
telert monitor activity --type network

# View activity for a specific monitor by ID
telert monitor activity --id proc-12345678

# Filter activity by level
telert monitor activity --level error
telert monitor activity --level warning

# Limit the number of entries displayed
telert monitor activity --limit 10

# Show detailed information for each activity entry
telert monitor activity --details

# Clear activity history (can be combined with filters)
telert monitor activity --clear
telert monitor activity --type network --clear
telert monitor activity --id proc-12345678 --clear
```

This activity history provides valuable information for troubleshooting and understanding what your monitors are doing behind the scenes.

## Python API for Monitoring

In addition to the CLI, you can use the Python API to programmatically create and manage monitors:

```python
from telert.monitoring import (
    monitor_process, 
    monitor_log, 
    monitor_network,
    list_process_monitors,
    list_log_monitors, 
    list_network_monitors,
    stop_process_monitor, 
    stop_log_monitor,
    stop_network_monitor
)

# Monitor a process
proc_id = monitor_process(
    name="Web Server",
    process_name="nginx",
    notify_on=["stop", "high-cpu"],
    cpu_threshold=80,
    provider="slack"
)

# Monitor a log file
log_id = monitor_log(
    name="App Errors",
    file="/var/log/app.log",
    pattern="ERROR|CRITICAL",
    context_lines=3,
    provider=["email", "telegram"]
)

# Monitor network endpoint
net_id = monitor_network(
    name="API Health",
    url="https://api.example.com/health",
    check_type="http",
    expected_status=200,
    provider="teams"
)

# List active monitors
process_monitors = list_process_monitors()
log_monitors = list_log_monitors()
network_monitors = list_network_monitors()

# Stop monitors
stop_process_monitor(proc_id)
stop_log_monitor(log_id)
stop_network_monitor(net_id)
```

## Use Cases

### Service Monitoring

```bash
# Monitor critical services and restart them if they stop
telert monitor process --name "mysql" --notify-on stop --action "systemctl restart mysql" --provider "slack,email"
```

### Log Error Detection

```bash
# Monitor application logs for critical errors
telert monitor log --file "/var/log/app.log" --pattern "CRITICAL|FATAL" --context-lines 10 --provider telegram
```

### API Health Checks

```bash
# Monitor multiple API endpoints
telert monitor network --url https://api.example.com/health --expected-status 200 --interval 60 --provider slack
telert monitor network --url https://api2.example.com/status --expected-content "ok" --interval 120 --provider slack
```

### Database Connection Monitoring

```bash
# Monitor database connectivity
telert monitor network --host db.example.com --port 5432 --type tcp --interval 300 --provider email
```

### Security Monitoring

```bash
# Monitor security logs
telert monitor log --file "/var/log/auth.log" --pattern "Failed password|authentication failure" --provider "telegram,email"
```

### System Resource Monitoring

```bash
# Monitor system processes for high resource usage
telert monitor process --name "chrome" --cpu-threshold 90 --memory-threshold "4G" --provider desktop
```
