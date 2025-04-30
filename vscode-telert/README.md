# Telert - Notifications for Your VS Code Terminal

Never stare at a terminal waiting for your commands to finish again! Telert sends you instant notifications when long-running tasks complete, so you can focus on other work while waiting for builds, tests, or deployments. Telert works with desktop notifications, mobile devices, messaging apps (Telegram, Microsoft Teams, Slack, Discord), Pushover, and custom HTTP endpoints.

![Telert Demo](https://raw.githubusercontent.com/navig-me/telert/main/docs/telert-demo.gif)

## 🚀 Why You Need This Extension

- **Boost Your Productivity**: Run time-consuming tasks and get notified when they're done - no more checking back constantly
- **Stay In The Flow**: Get notified on your phone, desktop, or messaging apps when commands complete
- **Perfect For Remote Work**: Run commands on remote servers or cloud VMs and get notifications anywhere
- **Works With Your Tools**: Seamlessly integrates into your VS Code workflow with minimal setup
- **Cross-Platform**: Works on macOS, Windows, and Linux with multiple notification channels

## 📱 Notification Channels

Receive notifications through various channels:

- **Messaging Apps**: Telegram, Microsoft Teams, Slack, Discord
- **Mobile Devices**: Pushover notifications on Android & iOS 
- **Desktop**: Native notifications on Windows, macOS, and Linux
- **Audio**: Sound alerts for immediate attention
- **Custom APIs**: Send to any custom HTTP endpoint

## ✨ Features

- **Run & Notify**: Execute code or commands with automatic notifications when they complete
- **Live Status Bar Timer**: Monitor elapsed time while commands run
- **Context Menu Integration**: Right-click on code in the editor or files in the Explorer to run with notifications
- **One-Click Status Bar Menu**: Click the Telert bell icon in the status bar to quickly access Run, Send Output, and Configure commands
- **Command Palette Actions**: Quick access to telert commands
- **Quick Pick Configuration**: Guided UI to select your default provider and enter credentials without manually editing JSON
- **Notification Threshold**: Only notify for commands that take longer than X seconds
- **Multi-Provider Support**: Send notifications to multiple services simultaneously
- **Terminal Output Sharing**: Send the output of your last command as a notification

## ⚡ Quick Start

1. Configure your notification provider:
   - Click the Telert bell icon in the status bar and select **Configure Notification Provider**
   - Choose your provider (Telegram, Slack, Teams, etc.) and enter credentials when prompted
   - For detailed setup instructions, see the main Telert docs:
     - [Telegram](https://github.com/navig-me/telert/blob/main/docs/TELEGRAM.md)
     - [Slack](https://github.com/navig-me/telert/blob/main/docs/SLACK.md)
     - [Microsoft Teams](https://github.com/navig-me/telert/blob/main/docs/TEAMS.md)
     - [Discord](https://github.com/navig-me/telert/blob/main/docs/DISCORD.md)
     - [Pushover](https://github.com/navig-me/telert/blob/main/docs/PUSHOVER.md)

2. Run a command with notifications:
   - Click the Telert bell icon and select **Run in Integrated Terminal and Notify**
   - Or right-click in the editor or Explorer and choose **Telert: Run in Integrated Terminal and Notify**
   - Or use the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and search for **Telert: Run in Integrated Terminal and Notify**

3. (Optional) Install the Telert CLI locally (the extension will auto-install/update it for you):
   ```bash
   pip install --upgrade telert
   ```

4. View results & receive notifications on your desktop or mobile device.

---
## 🔧 Installation & Setup

### 1. Install the telert CLI tool (optional — the extension will auto-install/update it for you):

```bash
# Optional if you plan to use the CLI only; the VS Code extension will auto-install/update it
pip install --upgrade telert
```
See the Telert CLI documentation for additional commands and configuration:
[Telert CLI Docs](https://github.com/navig-me/telert#commands)

### 2. Configure your preferred notification method

You can set up your notification provider either via the telert CLI (for global use) or directly in VS Code settings (extension-only).

For detailed provider setup and required environment variables, see the main Telert documentation:
- Telegram: https://github.com/navig-me/telert/blob/main/docs/TELEGRAM.md
- Slack: https://github.com/navig-me/telert/blob/main/docs/SLACK.md
- Microsoft Teams: https://github.com/navig-me/telert/blob/main/docs/TEAMS.md
- Discord: https://github.com/navig-me/telert/blob/main/docs/DISCORD.md
- Pushover: https://github.com/navig-me/telert/blob/main/docs/PUSHOVER.md

```bash
# CLI: Send notifications to your phone via Telegram (global config)
telert config telegram --token "<your-token>" --chat-id "<your-chat-id>" --set-default
```

Or, in your VS Code `settings.json`:

```json
"telert.defaultProvider": "telegram",
"telert.environmentVariables": {
  "TELERT_TELEGRAM_TOKEN": "<your-token>",
  "TELERT_TELEGRAM_CHAT_ID": "<your-chat-id>"
}
```

For Slack, Pushover, Teams, Discord, etc., replace the above keys with the corresponding `TELERT_*` variables (e.g. `TELERT_SLACK_WEBHOOK`, `TELERT_PUSHOVER_TOKEN`, `TELERT_PUSHOVER_USER`, `TELERT_TEAMS_WEBHOOK`, `TELERT_DISCORD_WEBHOOK`, etc.).

### 3. Verify your setup:

```bash
telert status
```

## 💻 Usage Examples

### For Data Scientists & ML Engineers

Run your long model training sessions and get notified when they complete:

```python
# Train a model for hours and get notified when done
python train_model.py --epochs 100
```

### For DevOps & Cloud Engineers

Get notified when your infrastructure deployments or cloud operations finish:

```bash
# Deploy to cloud and get notified
terraform apply -auto-approve
```

### For Web Developers

Get notified when your builds, tests or deployments complete:

```bash
# Build your frontend and get notified
npm run build
```

## ⚙️ Configuration Options

Fine-tune the extension to match your workflow:

* `telert.defaultProvider`: Choose your notification method. Default is `desktop`. Valid options: `telegram`, `slack`, `teams`, `discord`, `pushover`, `desktop`, `audio`.
  To change this:
  1. Open VS Code Settings (Ctrl+, / Cmd+,), search for **Telert Default Provider**, and select your preferred option from the dropdown list of providers.
  2. Or in your `settings.json`, add:

     ```json
     "telert.defaultProvider": "slack"
     ```
* `telert.notificationThreshold`: Only notify for commands that take longer than X seconds
* `telert.environmentVariables`: An object mapping any required `TELERT_*` environment variables to values for your chosen provider(s). The extension will inject these into the shell before running the `telert` command.
  Example (Slack + Telegram):
  ```json
  "telert.environmentVariables": {
    "TELERT_SLACK_WEBHOOK": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
    "TELERT_TELEGRAM_TOKEN": "<your-telegram-bot-token>",
    "TELERT_TELEGRAM_CHAT_ID": "<your-chat-id>"
  }
  ```
  Supported keys include (but are not limited to):
  `TELERT_DEFAULT_PROVIDER`, `TELERT_TELEGRAM_TOKEN`, `TELERT_TELEGRAM_CHAT_ID`,
  `TELERT_SLACK_WEBHOOK`, `TELERT_TEAMS_WEBHOOK`, `TELERT_DISCORD_WEBHOOK`,
  `TELERT_DISCORD_USERNAME`, `TELERT_DISCORD_AVATAR_URL`, `TELERT_PUSHOVER_TOKEN`,
  `TELERT_PUSHOVER_USER`, `TELERT_DESKTOP_APP_NAME`, `TELERT_DESKTOP_ICON`,
  `TELERT_AUDIO_FILE`, `TELERT_AUDIO_VOLUME`, `TELERT_ENDPOINT_URL`, etc.
  See the main telert CLI documentation [(Environment Variables section)](https://github.com/navig-me/telert/?tab=readme-ov-file#-environment-variables) for a full list.
* `telert.statusBarTimer`: Show/hide the live timer while commands run

## 🧩 Using the Extension

### Running Code with Notifications

1. Select code in your editor (or position cursor on a line)
2. Right-click in the editor or on a file in the Explorer and select "Telert: Run in Integrated Terminal and Notify"
   - Or click the Telert bell icon in the status bar and choose "Run in Integrated Terminal and Notify"
   - Or use the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and search for "Telert: Run in Integrated Terminal and Notify"
3. Your code will run in the integrated terminal with a live timer
4. When complete, you'll receive a notification with execution time and status

### Sending Terminal Output

If you've already run a command:

1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Select "Telert: Send Last Terminal Output"
3. Enter an optional message
4. Get a notification with the terminal output

### Configuring Notifications via Quick Pick

1. Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Select **Telert: Configure Notification Provider**
3. Choose your desired provider and enter any required tokens/webhooks when prompted

## 🔗 Related Resources

- [Telert GitHub Repository](https://github.com/navig-me/telert)
- [Telert on PyPI](https://pypi.org/project/telert/)
- [Documentation](https://github.com/navig-me/telert/blob/main/README.md)

## 📝 License

This extension is licensed under the MIT License.