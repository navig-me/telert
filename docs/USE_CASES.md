# Use Cases and Tips

Telert can be used in a variety of scenarios across different domains. Here are some common use cases and helpful tips for both notification and monitoring features.

## Server Administration

- Get notified when backups complete
- Monitor critical system jobs
- Alert when disk space runs low

```bash
# Alert when disk space exceeds 90%
df -h | grep -E '[9][0-9]%' | telert "Disk space alert!"

# Monitor a system update
telert run --label "System update" apt update && apt upgrade -y
```

## Data Processing

- Monitor long-running data pipelines
- Get notified when large file operations complete
- Track ML model training progress

```python
from telert import telert, notify
import pandas as pd

@notify("Data processing")
def process_large_dataset(filename):
    df = pd.read_csv(filename)
    # Process data...
    return {"rows_processed": len(df), "outliers_removed": 15}
```

## CI/CD Pipelines

- Get notified when builds complete
- Alert on deployment failures
- Track test suite status

```bash
# In a CI/CD environment using environment variables
export TELERT_TOKEN="your-token"
export TELERT_CHAT_ID="your-chat-id"

# Alert on build completion
telert run --label "CI Build" npm run build
```

## Monitor when Code Completes (Visual Studio Code Extension)

- Monitor and notify when commands or Python code complete directly within VS Code
- Wrap Python functions or code blocks with a click and automatically receive alerts on success or failure
- Install the extension from the [Visual Studio Code Marketplace](https://marketplace.visualstudio.com/items?itemName=Navig.telert-vscode)

## Long-Running Processes

- Get notified when database migrations complete
- Monitor file uploads/downloads
- Track batch processing jobs

```bash
# Get notified when a large file download completes
telert run --label "Download" wget -q https://example.com/large-file.zip

# Monitor a database migration
telert run --label "Migration" python manage.py migrate
```

## Remote Server Monitoring

- Get alerts from remote servers without SSH sessions
- Monitor cron jobs
- Track system reboots

```bash
# Add to crontab to get notifications from scheduled tasks
0 2 * * * /path/to/backup.sh | telert --provider telegram "Daily backup complete"

# Monitor server restarts
echo 'telert send --all-providers "Server $(hostname) has rebooted"' >> /etc/rc.local
```

## Process Monitoring

- Monitor critical services and receive notifications when they stop
- Track resource usage and get alerts on high CPU/memory
- Execute automatic recovery actions

```bash
# Monitor a database server process
telert monitor process --name "postgres" --notify-on stop,high-cpu --provider slack

# Auto-restart a service when it crashes
telert monitor process --name "my-service" --notify-on stop --action "systemctl restart my-service"

# Get notified when a process uses excessive resources
telert monitor process --command "python training\.py" --cpu-threshold 90 --memory-threshold 8G --provider telegram
```

## Log File Monitoring

- Monitor application logs for errors and exceptions
- Track security logs for unauthorized access attempts
- Get notifications with context when pattern matches are found

```bash
# Watch application logs for errors
telert monitor log --file "/var/log/app.log" --pattern "ERROR|CRITICAL|EXCEPTION" --context-lines 5 --provider email

# Monitor auth logs for security incidents
telert monitor log --file "/var/log/auth.log" --pattern "Failed password|authentication failure" --provider telegram

# Watch web server logs with cooldown period
telert monitor log --file "/var/log/nginx/error.log" --pattern "\[error\]" --cooldown 300 --provider teams
```

## Network Monitoring

- Monitor API endpoints and web services
- Check database and service connectivity
- Track network latency issues

```bash
# Monitor website availability
telert monitor network --url "https://example.com" --expected-status 200 --interval 300 --provider slack

# Check database connectivity
telert monitor network --host "db.example.com" --port 5432 --type tcp --provider email

# Monitor internal service health endpoint
telert monitor network --url "http://internal-api/health" --expected-content "healthy" --method GET --provider teams
```
