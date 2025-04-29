# Telert - Terminal Command Notifications

Get notifications when your terminal commands complete, directly from VS Code. This extension integrates with the [telert](https://github.com/navig-me/telert) CLI tool to provide notifications for long-running commands.

![Telert Demo](https://raw.githubusercontent.com/navig-me/telert/main/docs/telert-demo.gif)

## Features

- **Run in Terminal and Notify**: Execute code or commands in the integrated terminal and get notified when they complete
- **Status Bar Timer**: Shows elapsed time while command is running
- **Send Last Terminal Output**: Send the output of the last command as a notification
- **Multiple Notification Providers**: Support for Telegram, Slack, Microsoft Teams, Discord, Pushover, and more
- **Context Menu Integration**: Right-click on code to run it with notifications
- **Command Palette Actions**: Easy access to telert commands

## Requirements

This extension requires the telert CLI tool to be installed:

```bash
pip install telert
```

Configure your preferred notification provider:

```bash
# Example for Telegram
telert config telegram --token "<your-token>" --chat-id "<your-chat-id>" --set-default

# Example for Slack
telert config slack --webhook-url "<webhook-url>" --set-default

# Or use desktop notifications
telert config desktop --app-name "VS Code" --set-default
```

## Extension Settings

This extension contributes the following settings:

* `telert.defaultProvider`: Set the default notification provider to use
* `telert.notificationThreshold`: Minimum execution time in seconds before sending notification
* `telert.environmentVariables`: Environment variables for telert configuration
* `telert.statusBarTimer`: Show timer in status bar while command is running

## Usage

### Running Code with Notifications

1. Select code in your editor (or position cursor in a file)
2. Right-click and select "Telert: Run in Integrated Terminal and Notify"
   - Or use Command Palette (Ctrl+Shift+P / Cmd+Shift+P) to find the command
3. The code will run in the integrated terminal
4. When complete, you'll receive a notification via your configured provider
5. A timer in the status bar shows the elapsed time

### Sending Last Terminal Output

If you've already run a command, you can send its output:

1. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
2. Select "Telert: Send Last Terminal Output"
3. Enter a message to include with the output
4. The last terminal output will be sent as a notification

## Configuration Examples

### Environment Variables

Configure environment variables for your notification providers:

```json
"telert.environmentVariables": {
    "TELERT_TOKEN": "your-telegram-token",
    "TELERT_CHAT_ID": "your-telegram-chat-id"
}
```

### Multiple Providers

Configure multiple notification providers:

```json
"telert.defaultProvider": "telegram,desktop",
```

## Related Links

- [telert on GitHub](https://github.com/navig-me/telert)
- [telert on PyPI](https://pypi.org/project/telert/)

## License

This extension is licensed under the MIT License.