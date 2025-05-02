# 🚀 Telert – Smart Notifications for Your VS Code Terminal

**Telert is your productivity companion for long-running commands.**  
It tracks your terminal commands **in real time**, measures **execution duration**, and sends a **smart notification** when they complete — so you can stay focused on other work instead of constantly checking back.

💡 Perfect for developers, data scientists, DevOps engineers, or anyone running long builds, tests, or remote scripts.

✅ **Cross-platform notifications**: Get alerts via desktop pop-ups, mobile apps, messaging tools like **Telegram, Slack, Discord, Microsoft Teams**, or even custom HTTP webhooks.

<img src="https://github.com/navig-me/telert/raw/main/docs/telert-demo.gif" alt="telert demo" width="600">

---

## ⚡ Quick Start

1. **Configure Your Notification Provider**
   - Click the **Telert bell icon** in the status bar → _Configure Notification Provider_
   - Choose from Telegram, Slack, Teams, Discord, Pushover, or Desktop
   - Enter your credentials (tokens or webhooks)  
      <img src="https://raw.githubusercontent.com/navig-me/telert/main/docs/provider-options.png" alt="Provider Options" width="400">

    📘 Setup Docs:
    - [Telegram](docs/TELEGRAM.md) · [Slack](docs/SLACK.md) · [Teams](docs/TEAMS.md) · [Discord](docs/DISCORD.md) · [Pushover](docs/PUSHOVER.md)

2. **Run a Command with Notifications**
   - Click the bell icon or right-click a file → _Run in Integrated Terminal and Notify_
   - Or open Command Palette → _Telert: Run in Integrated Terminal and Notify_
   - A timer starts in the status bar, and you’ll be notified when the command finishes
      <img src="https://raw.githubusercontent.com/navig-me/telert/main/docs/integrated-terminal.png" alt="Integrated Terminal" width="400">
      <img src="https://raw.githubusercontent.com/navig-me/telert/main/docs/desktop-alert.png" alt="Desktop Alert" width="400">
      <img src="https://raw.githubusercontent.com/navig-me/telert/main/docs/telegram-alert.png" alt="Telegram Alert" width="400">

3. *(Optional)* Install CLI manually (auto-installed by extension):

   ```bash
   pip install --upgrade telert
   ```

---

## 🔥 Why Use Telert?

- ⏳ **Track Duration**: Automatically times every command
- 📳 **Get Alerted**: When done, get notified — no more tab switching
- 📱 **Cross-Device Support**: Desktop, mobile, chat platforms, or custom APIs
- 💻 **Integrated with VS Code**: One-click setup, context menus, and live timers
- 💼 **Ideal for Remote Work**: Works with local and remote terminals
- 🔧 **Customize Everything**: Thresholds, output, provider, formats

---

## 📡 Supported Notification Channels

| Type            | Providers                                                                 |
|-----------------|---------------------------------------------------------------------------|
| Messaging Apps  | Telegram, Microsoft Teams, Slack, Discord                                 |
| Mobile Devices  | Pushover (Android & iOS)                                                  |
| Desktop Alerts  | Native notifications (Windows, macOS, Linux)                             |
| Audio Alerts    | Local sound playback                                                      |
| Custom Webhooks | Send notifications to any API endpoint (`TELERT_ENDPOINT_URL`)            |

---

## ✨ Key Features

| Feature              | Description                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| 🛎️ Run & Notify      | Automatically notify when your command completes                            |
| ⏱️ Command Timer      | Tracks elapsed time live in the status bar                                  |
| 📤 Output Sharing     | Optionally send terminal output with the notification                       |
| ⚙️ Multi-provider     | Send to multiple services at once                                           |
| 🎛️ One-click Setup    | UI-based configuration for all providers                                   |
| 🧠 Smart Thresholds   | Only notify if command takes longer than a set duration                     |
| 🖱️ Context Menu UX    | Right-click to run any script with Telert directly from Explorer or Editor  |
| 🎯 Cross-platform     | Works on Windows, macOS, and Linux                                          |

---

## 🔧 Installation & Setup

### 1. Install CLI (optional)

```bash
pip install --upgrade telert
```

### 2. Configure Notification Provider

#### Option A: CLI

```bash
telert config telegram --token "<your-token>" --chat-id "<your-chat-id>" --set-default
```

#### Option B: VS Code Settings

```json
"telert.defaultProvider": "telegram",
"telert.environmentVariables": {
  "TELERT_TELEGRAM_TOKEN": "<your-token>",
  "TELERT_TELEGRAM_CHAT_ID": "<your-chat-id>"
}
```

💡 Replace variables with those for Slack, Pushover, Teams, or Discord (e.g. `TELERT_SLACK_WEBHOOK`, `TELERT_PUSHOVER_TOKEN`, etc.).

### 3. Verify

```bash
telert status
```

---

## 🧪 Usage Examples

### 🧬 Data Science & ML

```bash
python train_model.py --epochs 100
```

### 🛠️ DevOps / Infra

```bash
terraform apply -auto-approve
```

### 🌐 Web Dev

```bash
npm run build
```

---

## ⚙️ Configuration Options

| Setting                        | Description                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| `telert.defaultProvider`      | Choose notification method: `telegram`, `slack`, `teams`, etc.             |
| `telert.notificationThreshold`| Only notify for commands longer than X seconds                             |
| `telert.environmentVariables` | Inject TELERT_* variables for each provider                                |
| `telert.statusBarTimer`       | Show/hide command timer in status bar                                      |

---

## 🧩 How to Use in VS Code

### 🔹 Run Code with Notifications

1. Right-click code or file → _Telert: Run in Integrated Terminal and Notify_  
2. OR: Use Command Palette  
3. OR: Click Telert bell icon in status bar

### 🔹 Send Terminal Output as Notification

1. Run any command
2. Open Command Palette → _Telert: Send Last Terminal Output_
3. Optionally add a message

### 🔹 Configure with Quick Pick

1. Open Command Palette → _Telert: Configure Notification Provider_
2. Follow guided steps for setup

---

## 🔗 Resources

- [📦 Telert GitHub](https://github.com/navig-me/telert)
- [📚 Telert CLI Docs](https://github.com/navig-me/telert#commands)
- [📄 Full Provider Setup Guides](https://github.com/navig-me/telert/tree/main/docs)
- [🚀 Telert on PyPI](https://pypi.org/project/telert/)

---

## 📝 License

Licensed under the [MIT License](LICENSE).
