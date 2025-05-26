# Use Cases and Tips

Telert can be used in a variety of scenarios across different domains. Here are some common use cases and helpful tips.

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
