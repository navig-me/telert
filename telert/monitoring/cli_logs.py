"""CLI commands for viewing and managing telert monitor logs."""

import json
from datetime import datetime
from typing import Dict

from telert.monitoring.activity_logs import MonitorLogger, LogLevel


def format_log_entry(log_entry: Dict) -> str:
    """Format a log entry for display."""
    timestamp = log_entry.get("timestamp", "")
    try:
        # Convert ISO format to readable date/time
        dt = datetime.fromisoformat(timestamp)
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        pass
    
    monitor_id = log_entry.get("monitor_id", "unknown")
    level = log_entry.get("level", "").upper()
    message = log_entry.get("message", "")
    
    # Color coding for different log levels
    if level == "ERROR":
        level = f"\033[91m{level}\033[0m"  # Red
    elif level == "WARNING":
        level = f"\033[93m{level}\033[0m"  # Yellow
    elif level == "SUCCESS":
        level = f"\033[92m{level}\033[0m"  # Green
    elif level == "FAILURE":
        level = f"\033[91m{level}\033[0m"  # Red
    else:
        level = f"\033[94m{level}\033[0m"  # Blue for INFO
    
    # Format the log entry
    formatted = f"{timestamp} [{monitor_id}] {level}: {message}"
    
    # Add details if requested and available
    details = log_entry.get("details", {})
    if details:
        details_str = json.dumps(details, indent=2)
        formatted += f"\n  Details: {details_str}"
    
    return formatted


def setup_logs_cli(subparsers):
    """Set up the activity/history CLI commands."""
    logs_parser = subparsers.add_parser(
        "activity",
        help="view and manage monitor activity history",
        description="View and manage activity logs from telert monitors",
    )
    
    logs_parser.add_argument(
        "--type",
        choices=["process", "log", "network"],
        help="filter logs by monitor type",
    )
    
    logs_parser.add_argument(
        "--id",
        help="filter logs by monitor ID",
    )
    
    logs_parser.add_argument(
        "--level",
        choices=["info", "warning", "error", "success", "failure"],
        help="filter logs by log level",
    )
    
    logs_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="maximum number of logs to display (default: 50)",
    )
    
    logs_parser.add_argument(
        "--details",
        action="store_true",
        help="show detailed information for each log entry",
    )
    
    logs_parser.add_argument(
        "--clear",
        action="store_true",
        help="clear logs (can be combined with --type and --id filters)",
    )
    
    return logs_parser


def handle_logs_command(args):
    """Handle the logs command."""
    if args.clear:
        # Clear logs
        count = MonitorLogger.clear_logs(
            monitor_type=args.type,
            monitor_id=args.id,
        )
        if count > 0:
            print(f"✅ Cleared {count} log entries.")
        else:
            print("No logs found matching the specified criteria.")
        return
    
    # Get logs
    logs = MonitorLogger.get_logs(
        monitor_type=args.type,
        monitor_id=args.id,
        level=args.level,
        limit=args.limit,
    )
    
    if not logs:
        print("No logs found matching the specified criteria.")
        return
    
    # Print logs
    for log in logs:
        print(format_log_entry(log))
        if args.details:
            details = log.get("details", {})
            if details:
                print(f"  Details: {json.dumps(details, indent=2)}")
        print()  # Add a blank line between logs
    
    print(f"Showing {len(logs)} of {len(logs)} matching logs.")
