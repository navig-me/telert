# 🚀 Telert – Your Ultimate Code Command Center 

**Telert is your productivity command center for Python development and terminal operations.**  
It monitors your code and commands in **real time**, tracks **execution duration**, and delivers **smart notifications** when they complete — so you can stay focused on other work instead of constantly checking back.

💡 Perfect for developers, data scientists, DevOps engineers, or anyone who needs to monitor long-running code and stay productive.

✅ **Smart Python Integration**: Wrap any Python code block or function with telert context managers or decorators in one click, auto-tracking execution time and success status.

✅ **Multi-channel notifications**: Get alerts via desktop pop-ups, mobile apps, messaging tools like **Telegram, Slack, Discord, Microsoft Teams**, or even custom HTTP webhooks.

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

- 🔄 **Monitor Your Code**: Wrap Python functions with @notify or blocks with telert() context managers
- ⏳ **Track Execution Time**: Automatically measures how long your code or commands take
- 💥 **Exception Handling**: Get notified immediately when code crashes with detailed error info
- 📳 **Smart Alerting**: Choose between "always notify" or "only on failure" for different scenarios
- 📱 **Cross-Device Support**: Get alerts on desktop, mobile, chat platforms, or custom APIs
- 💻 **Seamless VS Code Integration**: Just right-click to add monitoring to any Python code
- 💼 **Ideal for Remote Work**: Perfect for long-running tasks when you're away from your desk
- 🔧 **Highly Customizable**: Set thresholds, customize providers, configure notification content

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
| 🐍 Python Decorators | Add @notify to any Python function in one click for auto-notifications      |
| 🧩 Context Managers  | Wrap any Python code block in telert() for execution tracking               |
| 🛎️ Run & Notify      | Automatically notify when your commands or scripts complete                 |
| ⏱️ Live Timers       | Tracks elapsed time in the status bar during execution                      |
| 🚨 Error Tracking    | Get detailed notifications with tracebacks when code fails                  |
| ⚙️ Multi-provider    | Send notifications to multiple services simultaneously                      |
| 🎛️ One-click Setup   | UI-based configuration for all notification providers                       |
| 🧠 Smart Alerting    | Choose between always notifying or only on failure                          |
| 🖱️ Context Menu      | Right-click on Python code to instantly add monitoring                      |
| 🎯 Cross-platform    | Works on Windows, macOS, and Linux                                          |

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

### 🔹 Add Telert to Python Code

1. Select a Python function or code block
2. Right-click → _Telert: Wrap with notify decorator_ or _Telert: Wrap with telert context manager_
3. Choose notification options and provider
4. Get notified when your code completes or fails!

Example decorator:
```python
from telert import notify

@notify("process_data", only_fail=True)
def process_data(filename):
    # Your function code here
    return result
```

Example context manager:
```python
from telert import telert

with telert("Data processing"):
    # Your code block here
    process_large_dataset()
```

### 🔹 Run Code with Notifications

1. Right-click file → _Telert: Run in Integrated Terminal and Notify_  
2. OR: Use Command Palette  
3. OR: Click Telert bell icon in status bar

### 🔹 Configure with Quick Pick

1. Open Command Palette → _Telert: Configure Notification Provider_
2. Follow guided steps for setup

---

## 🔗 Resources

- [📦 Telert GitHub](https://github.com/navig-me/telert)
- [📚 Telert CLI Docs](https://github.com/navig-me/telert#commands)
- [📄 Full Provider Setup Guides](https://github.com/navig-me/telert/tree/main/docs)
- [🚀 Telert on PyPI](https://pypi.org/project/telert/)

## 🌟 Use Cases

### 📊 Data Scientists
- Add Telert to model training scripts to get notified when training completes or fails
- Wrap data preprocessing functions to track execution time and errors
- Monitor batch processing of large datasets with automatic alerting

### 🧪 DevOps & SRE
- Get instant notifications when pipelines complete or fail
- Monitor long-running infrastructure operations
- Track the status of scheduled tasks and deployments

### 📱 Backend/API Developers 
- Monitor API endpoints during development
- Get alerted when API tests complete
- Track long-running database operations

### 🔬 Research & Academic Computing
- Monitor simulations that run for hours or days
- Get notified when complex calculations complete
- Track experimental runs with success/failure notifications

---

## 💎 Why Developers Love Telert

> "Telert completely changed how I handle my ML training workflows. Now I can work on other tasks while my models train, knowing I'll get notified instantly when they're done." — *Data Scientist*

> "As a remote developer, I needed a way to track my builds without constantly checking. Telert lets me focus on coding while keeping me updated on all my background tasks." — *Full Stack Developer*

> "The Python integration is brilliant - I've added @notify decorators to all my critical functions. Now I get alerts when my backend tasks finish or if anything fails." — *Backend Engineer*

## 📝 License

Licensed under the [MIT License](LICENSE).
