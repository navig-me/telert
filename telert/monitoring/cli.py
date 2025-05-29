"""CLI commands for telert monitoring."""

from telert.monitoring.process import (
    monitor_process,
    list_process_monitors,
    stop_process_monitor,
)
from telert.monitoring.log import (
    monitor_log,
    list_log_monitors,
    stop_log_monitor,
)
from telert.monitoring.network import (
    monitor_network,
    list_network_monitors,
    stop_network_monitor,
)
from telert.monitoring.cli_logs import setup_logs_cli, handle_logs_command


def setup_monitor_cli(subparsers):
    """Set up monitoring CLI commands."""
    # Main monitor command
    monitor_parser = subparsers.add_parser(
        "monitor", help="monitor processes, log files, or network endpoints"
    )
    monitor_subparsers = monitor_parser.add_subparsers(
        dest="monitor_type", help="type of monitoring"
    )
    
    # Process monitoring
    setup_process_monitor_cli(monitor_subparsers)
    
    # Log monitoring
    setup_log_monitor_cli(monitor_subparsers)
    
    # Network monitoring
    setup_network_monitor_cli(monitor_subparsers)
    
    # Logs command
    setup_logs_cli(monitor_subparsers)


def setup_process_monitor_cli(subparsers):
    """Set up process monitoring CLI commands."""
    process_parser = subparsers.add_parser(
        "process", help="monitor processes and receive notifications on state changes"
    )
    
    # Process identification
    process_group = process_parser.add_mutually_exclusive_group()
    process_group.add_argument(
        "--name", help="process name to monitor (can be a regular expression)"
    )
    process_group.add_argument(
        "--command-pattern", dest="command_pattern", help="command pattern to match (can be a regular expression)"
    )
    process_group.add_argument(
        "--pid", type=int, help="specific process ID to monitor"
    )
    
    # Notification options
    process_parser.add_argument(
        "--notify-on",
        help="comma-separated list of events to notify on (stop,start,crash,high-cpu,high-memory)",
    )
    process_parser.add_argument(
        "--cpu-threshold",
        type=float,
        help="CPU usage percentage threshold (0-100)"
    )
    process_parser.add_argument(
        "--memory-threshold",
        help="memory usage threshold (e.g., 500M, 2G)"
    )
    
    # Action options
    process_parser.add_argument(
        "--action",
        help="command to run when process state changes"
    )
    process_parser.add_argument(
        "--check-interval",
        type=int,
        default=30,
        help="how often to check process status (seconds)"
    )
    
    # Notification provider
    process_parser.add_argument(
        "--provider",
        help="provider(s) to use - can be a single provider or comma-separated list (default: use configured default)",
    )
    
    # Monitor management
    management_group = process_parser.add_mutually_exclusive_group()
    management_group.add_argument(
        "--list",
        action="store_true",
        help="list all process monitors"
    )
    management_group.add_argument(
        "--stop",
        metavar="MONITOR_ID",
        help="stop a process monitor"
    )
    
    # Friendly name
    process_parser.add_argument(
        "--monitor-name",
        help="friendly name for this monitor"
    )


def setup_log_monitor_cli(subparsers):
    """Set up log file monitoring CLI commands."""
    log_parser = subparsers.add_parser(
        "log", help="monitor log files and receive notifications on pattern matches"
    )
    
    # Log file and pattern
    log_parser.add_argument(
        "--file",
        help="path to log file to monitor"
    )
    log_parser.add_argument(
        "--pattern",
        help="regular expression pattern to match in log lines"
    )
    
    # Notification options
    log_parser.add_argument(
        "--context-lines",
        type=int,
        default=0,
        help="number of lines to include before and after the match"
    )
    log_parser.add_argument(
        "--cooldown",
        type=int,
        default=0,
        help="seconds to wait before sending similar notifications"
    )
    log_parser.add_argument(
        "--priority",
        choices=["low", "normal", "high"],
        default="normal",
        help="priority level for notifications"
    )
    
    # Notification provider
    log_parser.add_argument(
        "--provider",
        help="provider(s) to use - can be a single provider or comma-separated list (default: use configured default)",
    )
    
    # Monitor management
    management_group = log_parser.add_mutually_exclusive_group()
    management_group.add_argument(
        "--list",
        action="store_true",
        help="list all log monitors"
    )
    management_group.add_argument(
        "--stop",
        metavar="MONITOR_ID",
        help="stop a log monitor"
    )
    
    # Friendly name
    log_parser.add_argument(
        "--monitor-name",
        help="friendly name for this monitor"
    )


def setup_network_monitor_cli(subparsers):
    """Set up network monitoring CLI commands."""
    network_parser = subparsers.add_parser(
        "network", help="monitor network endpoints and receive notifications on issues"
    )
    
    # Target identification
    target_group = network_parser.add_mutually_exclusive_group()
    target_group.add_argument(
        "--host",
        help="hostname or IP address to monitor"
    )
    target_group.add_argument(
        "--url",
        help="URL to monitor (for HTTP/HTTPS checks)"
    )
    
    # Check options
    network_parser.add_argument(
        "--type",
        dest="check_type",
        choices=["ping", "http", "tcp"],
        default="ping",
        help="type of check to perform"
    )
    network_parser.add_argument(
        "--port",
        type=int,
        help="port to check (required for TCP checks)"
    )
    network_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="how often to check (seconds)"
    )
    network_parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="timeout for checks (seconds)"
    )
    
    # HTTP check options
    http_group = network_parser.add_argument_group("HTTP check options")
    http_group.add_argument(
        "--expected-status",
        type=int,
        help="expected HTTP status code"
    )
    http_group.add_argument(
        "--expected-content",
        help="expected content in HTTP response"
    )
    http_group.add_argument(
        "--method",
        default="GET",
        help="HTTP method to use"
    )
    http_group.add_argument(
        "--header",
        dest="headers",
        action="append",
        help="HTTP header in format 'key: value' (can be specified multiple times)"
    )
    http_group.add_argument(
        "--body",
        help="HTTP request body"
    )
    
    # Notification provider
    network_parser.add_argument(
        "--provider",
        help="provider(s) to use - can be a single provider or comma-separated list (default: use configured default)",
    )
    
    # Monitor management
    management_group = network_parser.add_mutually_exclusive_group()
    management_group.add_argument(
        "--list",
        action="store_true",
        help="list all network monitors"
    )
    management_group.add_argument(
        "--stop",
        metavar="MONITOR_ID",
        help="stop a network monitor"
    )
    
    # Friendly name
    network_parser.add_argument(
        "--monitor-name",
        help="friendly name for this monitor"
    )


def handle_process_monitor(args):
    """Handle process monitoring commands."""
    # List monitors
    if args.list:
        monitors = list_process_monitors()
        if not monitors:
            print("No process monitors configured.")
            return
        
        print(f"Found {len(monitors)} process monitors:")
        for monitor in monitors:
            name_display = f" ({monitor['name']})" if monitor['name'] else ""
            process_info = []
            if monitor['process_name']:
                process_info.append(f"name={monitor['process_name']}")
            if monitor['command']:
                process_info.append(f"cmd={monitor['command']}")
            if monitor['pid']:
                process_info.append(f"pid={monitor['pid']}")
                
            process_str = ", ".join(process_info)
            print(f"  {monitor['id']}{name_display}: {process_str} - {monitor['status']}")
        return
    
    # Stop a monitor
    if args.stop:
        if stop_process_monitor(args.stop):
            print(f"✅ Process monitor {args.stop} stopped.")
        else:
            print(f"❌ Process monitor {args.stop} not found.")
        return
    
    # Start a new monitor
    if not (args.name or args.command_pattern or args.pid):
        print("❌ You must specify at least one of --name, --command, or --pid.")
        return
    
    # Parse notify-on events
    notify_on = None
    if args.notify_on:
        notify_on = [event.strip() for event in args.notify_on.split(",")]
    
    # Parse provider
    provider = None
    if args.provider:
        if "," in args.provider:
            provider = [p.strip() for p in args.provider.split(",")]
        else:
            provider = args.provider
    
    try:
        monitor_id = monitor_process(
            name=args.monitor_name,
            process_name=args.name,
            command=args.command_pattern,
            pid=args.pid,
            notify_on=notify_on,
            cpu_threshold=args.cpu_threshold,
            memory_threshold=args.memory_threshold,
            action=args.action,
            check_interval=args.check_interval,
            provider=provider,
        )
        print(f"✅ Process monitor started with ID: {monitor_id}")
    except Exception as e:
        print(f"❌ Failed to start process monitor: {e}")


def handle_log_monitor(args):
    """Handle log file monitoring commands."""
    # List monitors
    if args.list:
        monitors = list_log_monitors()
        if not monitors:
            print("No log monitors configured.")
            return
        
        print(f"Found {len(monitors)} log monitors:")
        for monitor in monitors:
            name_display = f" ({monitor['name']})" if monitor['name'] else ""
            print(f"  {monitor['id']}{name_display}: {monitor['file']} - {monitor['status']}")
        return
    
    # Stop a monitor
    if args.stop:
        if stop_log_monitor(args.stop):
            print(f"✅ Log monitor {args.stop} stopped.")
        else:
            print(f"❌ Log monitor {args.stop} not found.")
        return
    
    # Start a new monitor
    if not args.file or not args.pattern:
        print("❌ You must specify both --file and --pattern.")
        return
    
    # Parse provider
    provider = None
    if args.provider:
        if "," in args.provider:
            provider = [p.strip() for p in args.provider.split(",")]
        else:
            provider = args.provider
    
    try:
        monitor_id = monitor_log(
            file=args.file,
            pattern=args.pattern,
            name=args.monitor_name,
            context_lines=args.context_lines,
            cooldown=args.cooldown,
            priority=args.priority,
            provider=provider,
        )
        print(f"✅ Log monitor started with ID: {monitor_id}")
    except Exception as e:
        print(f"❌ Failed to start log monitor: {e}")


def handle_network_monitor(args):
    """Handle network monitoring commands."""
    # List monitors
    if args.list:
        monitors = list_network_monitors()
        if not monitors:
            print("No network monitors configured.")
            return
        
        print(f"Found {len(monitors)} network monitors:")
        for monitor in monitors:
            name_display = f" ({monitor['name']})" if monitor['name'] else ""
            target = monitor['url'] or monitor['host']
            if monitor['port'] and not monitor['url']:
                target += f":{monitor['port']}"
            print(f"  {monitor['id']}{name_display}: {monitor['check_type']} {target} - {monitor['status']}")
        return
    
    # Stop a monitor
    if args.stop:
        if stop_network_monitor(args.stop):
            print(f"✅ Network monitor {args.stop} stopped.")
        else:
            print(f"❌ Network monitor {args.stop} not found.")
        return
    
    # Start a new monitor
    if args.check_type == "http" and not args.url:
        print("❌ HTTP checks require --url.")
        return
    
    if args.check_type in ("ping", "tcp") and not args.host:
        print(f"❌ {args.check_type.upper()} checks require --host.")
        return
    
    if args.check_type == "tcp" and not args.port:
        print("❌ TCP checks require --port.")
        return
    
    # Parse headers
    headers = {}
    if args.headers:
        for header in args.headers:
            if ":" not in header:
                print(f"❌ Invalid header format: {header}. Use 'key: value'.")
                return
                
            key, value = header.split(":", 1)
            headers[key.strip()] = value.strip()
    
    # Parse provider
    provider = None
    if args.provider:
        if "," in args.provider:
            provider = [p.strip() for p in args.provider.split(",")]
        else:
            provider = args.provider
    
    try:
        monitor_id = monitor_network(
            name=args.monitor_name,
            host=args.host,
            url=args.url,
            port=args.port,
            check_type=args.check_type,
            interval=args.interval,
            timeout=args.timeout,
            expected_status=args.expected_status,
            expected_content=args.expected_content,
            method=args.method,
            headers=headers if headers else None,
            body=args.body,
            provider=provider,
        )
        print(f"✅ Network monitor started with ID: {monitor_id}")
    except Exception as e:
        print(f"❌ Failed to start network monitor: {e}")


def handle_monitor_commands(args):
    """Handle all monitoring commands."""
    if not hasattr(args, "monitor_type") or not args.monitor_type:
        print("❌ Please specify a monitor type (process, log, network, or activity).")
        return
    
    if args.monitor_type == "process":
        handle_process_monitor(args)
    elif args.monitor_type == "log":
        handle_log_monitor(args)
    elif args.monitor_type == "network":
        handle_network_monitor(args)
    elif args.monitor_type == "activity":
        handle_logs_command(args)
    else:
        print(f"❌ Unknown monitor type: {args.monitor_type}")
