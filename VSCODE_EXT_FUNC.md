# VS Code Extension: Telert Functionality Overview

This document summarizes the features and functionality provided by the `vscode-telert` extension before its complete rewrite.

## 1. Activation & Auto-Update
- **Activation Events**: The extension activates on specific commands (`telert.runInTerminal`, `telert.showMenu`, `telert.wrapWithTelert`, `telert.wrapWithNotifyDecorator`, `telert.monitorPythonProcess`, `telert.configureProviders`) and on opening Python files.
- **Automatic CLI Management**: On activation (and periodically, based on configuration), the extension checks if the Python `telert` CLI is installed (`telert --version`). If missing or outdated, it runs:
  ```bash
  python3 -m pip install --upgrade telert || pip install --upgrade telert
  ```
- **Update Interval**: Controlled by `telert.autoUpdateIntervalHours` (default 4 hours) and a daily version-check on extension version change.

## 2. Status Bar & Quick Menu
- **Status Bar Items**:
  - A left-aligned timer showing elapsed time for running commands or monitored processes.
  - A right-aligned “🔔 Telert” menu button.
- **Quick Menu**: Invoked via the status bar bell or the `telert.showMenu` command, displaying actions:
  1. Run in Terminal and Notify
  2. Configure Notification Provider
  3. Wrap with telert context manager (Python only)
  4. Wrap with notify decorator (Python only)
  5. Monitor Python Process (Python only)

## 3. Core Commands

### 3.1 Run in Terminal and Notify (`telert.runInTerminal`)
- **Purpose**: Wraps any shell command or script in the Telert CLI to send notifications on completion.
- **Behavior**:
  1. Uses the current selection; if empty, falls back to the current file path or prompts for input.
  2. Detects file extension (`.py`, `.js`, `.sh`, etc.) and automatically prefixes with the appropriate interpreter (e.g., `python file.py`).
  3. Builds:
     ```bash
     telert run --label "<command>" [--provider <provider>] [--min-seconds N] <command>
     ```
     - `--provider`: from `telert.defaultProvider` setting.
     - `--min-seconds`: from `telert.notificationThreshold` setting.
  4. Executes via VS Code Tasks API (`ShellExecution`), with optional environment variables (`telert.environmentVariables`).
  5. Displays a live timer in the status bar if `telert.statusBarTimer` is enabled.

### 3.2 Wrap with Telert Context Manager (`telert.wrapWithTelert`)
- **Purpose**: Wraps selected Python code or current line/block in a `with telert(...)` context to capture completion/failure.
- **Features**:
  - Prompts for a label and options (notify on failure only, include traceback, choose provider).
  - Inserts `from telert import telert` if missing.
  - Preserves indentation style (spaces vs. tabs) and current indent level.

### 3.3 Wrap with Notify Decorator (`telert.wrapWithNotifyDecorator`)
- **Purpose**: Decorates an existing Python function with `@notify(...)` to send a notification on function exit.
- **Features**:
  - Detects and selects multi-line function definitions or uses current selection.
  - Prompts for label/options (only on failure, include traceback, provider).
  - Inserts `from telert import notify` if missing.

### 3.4 Configure Notification Provider (`telert.configureProviders`)
- **Purpose**: Sets up environment variables and default provider for Telert CLI.
- **Behavior**:
  - QuickPick list of supported providers: `telegram`, `slack`, `teams`, `discord`, `pushover`, `desktop`, `audio`, `email`.
  - Prompts for each provider’s required `TELERT_*` environment variables (e.g., `TELERT_TELEGRAM_TOKEN`, `TELERT_TELEGRAM_CHAT_ID`).
  - Writes settings to the global VS Code configuration under `telert.environmentVariables` and `telert.defaultProvider`.

### 3.5 Monitor Python Process (`telert.monitorPythonProcess`)
- **Purpose**: Watch a running Python process (via Tasks or Terminal) and notify on exit.
- **Behavior**:
  1. Lists currently running VS Code tasks of type “process” that invoke `python`/`python3`.
  2. Also lists open terminals named “Python”.
  3. Option to manually enter a PID.
  4. Polls the OS (`ps -p PID` on Unix, `tasklist /FI PID eq PID` on Windows) every `telert.processMonitorIntervalSeconds` to detect exit.
  5. Shows a monitoring timer; on process end, hides the timer, sends an information toast, and invokes:
     ```bash
     telert send [--provider <provider>] "Python process <PID> completed after <duration>"
     ```

## 4. Configuration Settings
Defined in `package.json` under `contributes.configuration`:
| Setting                         | Type    | Default        | Description                                                  |
|---------------------------------|---------|----------------|--------------------------------------------------------------|
| `telert.defaultProvider`        | string  | `desktop`      | Default notification provider.                               |
| `telert.notificationThreshold`  | number  | `5`            | Minimum execution time (sec) before sending notification.    |
| `telert.environmentVariables`   | object  | `{}`           | Custom `TELERT_*` environment variable overrides.            |
| `telert.statusBarTimer`         | boolean | `true`         | Display a live timer in the status bar for active commands.  |
| `telert.autoInstall`            | boolean | `true`         | Automatically install/update the Telert CLI on activation.   |
| `telert.autoUpdateIntervalHours`| number  | `4`            | Hours between automatic Telert CLI update checks.            |
| `telert.processMonitorIntervalSeconds` | number | `5`      | Seconds between OS checks for monitored processes.           |

## 5. Contribution Points
- **Commands** (palette, menus):
  - `telert.runInTerminal`
  - `telert.showMenu`
  - `telert.wrapWithTelert`
  - `telert.wrapWithNotifyDecorator`
  - `telert.monitorPythonProcess`
  - `telert.configureProviders`
- **Menus**:
  - Editor context (Python-only for wrap/monitor commands)
  - Explorer context (run & show menu)
  - Terminal context (configure & show menu)

---
*This file will guide the full rewrite of the extension to ensure no functionality is missed.*