# telert – Alerts for Your Terminal (Telegram, Teams, Slack)

**Version 0.1.9** 📱

Telert is a lightweight utility that sends notifications to Telegram, Microsoft Teams, or Slack when your terminal commands or Python code completes. Perfect for long-running tasks, remote servers, CI pipelines, or monitoring critical code.

![telert demo](https://github.com/navig-me/telert/raw/main/telert-demo.gif)

**Quick start:**
```bash
# Install
pip install telert

# After quick setup (see below)
long_running_command | telert "Command finished!"
```

✅ **Key benefits:**
- Know instantly when your commands finish (even when away from your computer)
- See exactly how long commands or code took to run
- Capture success/failure status codes and tracebacks
- View command output snippets directly in your notifications
- Works with shell commands, pipelines, and Python code

If you find this tool useful, you can [support the project on Buy Me a Coffee](https://www.buymeacoffee.com/mihirk) ☕