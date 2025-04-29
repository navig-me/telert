# Telert - Notifications for Your VS Code Terminal

Never stare at a terminal waiting for your commands to finish again! Telert sends you instant notifications when long-running tasks complete, so you can focus on other work while waiting for builds, tests, or deployments.

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
- **Context Menu Integration**: Right-click on code to run with notifications
- **Command Palette Actions**: Quick access to telert commands
- **Notification Threshold**: Only notify for commands that take longer than X seconds
- **Multi-Provider Support**: Send notifications to multiple services simultaneously
- **Terminal Output Sharing**: Send the output of your last command as a notification

## 🔧 Installation & Setup

### 1. Install the telert CLI tool:

```bash
pip install telert
```

### 2. Configure your preferred notification method:

```bash
# Send notifications to your phone via Telegram
telert config telegram --token "<your-token>" --chat-id "<your-chat-id>" --set-default

# Or use Slack for team notifications
telert config slack --webhook-url "<webhook-url>" --set-default

# Or simple desktop notifications (no additional setup)
telert config desktop --app-name "VS Code" --set-default
```

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

* `telert.defaultProvider`: Choose your notification method (telegram, slack, teams, discord, pushover, desktop, audio)
* `telert.notificationThreshold`: Only notify for commands that take longer than X seconds
* `telert.environmentVariables`: Configure your notification services
* `telert.statusBarTimer`: Show/hide the live timer while commands run

## 🧩 Using the Extension

### Running Code with Notifications

1. Select code in your editor (or position cursor on a line)
2. Right-click and select "Telert: Run in Integrated Terminal and Notify"
   - Or use Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and search for "Telert"
3. Your code will run in the integrated terminal with a live timer
4. When complete, you'll receive a notification with execution time and status

### Sending Terminal Output

If you've already run a command:

1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Select "Telert: Send Last Terminal Output"
3. Enter an optional message
4. Get a notification with the terminal output

## 🔗 Related Resources

- [Telert GitHub Repository](https://github.com/navig-me/telert)
- [Telert on PyPI](https://pypi.org/project/telert/)
- [Documentation](https://github.com/navig-me/telert/blob/main/README.md)

## 📝 License

This extension is licensed under the MIT License.