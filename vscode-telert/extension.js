// The module 'vscode' contains the VS Code extensibility API
const vscode = require('vscode');
const { spawn } = require('child_process');
const path = require('path');
const os = require('os');

// Timer and last output tracking
let runningTimers = new Map();
let lastOutput = '';
let statusBarItem = null;

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Telert Extension activated');
    // Auto install/update telert CLI on activation and periodically
    try {
        const config = vscode.workspace.getConfiguration('telert');
        const autoInstall = config.get('autoInstall') !== false;
        const updateIntervalHours = config.get('autoUpdateIntervalHours') || 4;
        /**
         * Ensure telert CLI is installed or updated
         */
        function ensureTelert() {
            console.log('[Telert] Checking for telert CLI...');
            const check = spawn('telert', ['--version']);
            // If telert not found or errors, install; else update
            const install = () => {
                console.log('[Telert] Installing/updating telert CLI...');
                const installer = spawn('pip', ['install', '--upgrade', 'telert']);
                installer.stdout.on('data', d => console.log(`[Telert] ${d.toString().trim()}`));
                installer.stderr.on('data', d => console.error(`[Telert] ${d.toString().trim()}`));
                installer.on('close', code => {
                    if (code === 0) console.log('[Telert] telert CLI installation/update complete.');
                    else console.error(`[Telert] telert CLI installation/update failed (code ${code}).`);
                });
            };
            check.on('error', install);
            check.on('close', code => {
                if (code === 0) install();
                else install();
            });
        }
        if (autoInstall) {
            ensureTelert();
            if (updateIntervalHours > 0) {
                const ms = updateIntervalHours * 60 * 60 * 1000;
                const timer = setInterval(ensureTelert, ms);
                context.subscriptions.push({ dispose: () => clearInterval(timer) });
            }
        }
    } catch (e) {
        console.error('[Telert] Failed to auto-install/update CLI:', e);
    }
    // Auto-install or update telert CLI on install/update or periodic schedule
    (function autoUpdateTelert() {
        const extensionId = 'navig.telert-vscode';
        const ext = vscode.extensions.getExtension(extensionId);
        const currentVersion = ext && ext.packageJSON && ext.packageJSON.version;
        const prevVersion = context.globalState.get('extensionVersion');
        const now = Date.now();
        const lastCheck = context.globalState.get('lastTelertUpdateTime') || 0;
        const ONE_DAY_MS = 1000 * 60 * 60 * 24;
        // If first run or extension version changed -> install/update CLI
        if (currentVersion && prevVersion !== currentVersion) {
            updateTelertCli();
            context.globalState.update('extensionVersion', currentVersion);
            context.globalState.update('lastTelertUpdateTime', now);
        }
        // Else if it's been more than a year since last check -> update CLI
        else if (now - lastCheck > ONE_DAY_MS) {
            updateTelertCli();
            context.globalState.update('lastTelertUpdateTime', now);
        }
    })();

    /**
     * Run pip install --upgrade telert, with fallback
     */
    function updateTelertCli() {
        vscode.window.showInformationMessage('Updating telert CLI...');
        // Try via python3 -m pip first
        const installer = spawn('python3', ['-m', 'pip', 'install', '--upgrade', 'telert'], { shell: true });
        installer.on('close', (code) => {
            if (code === 0) {
                vscode.window.showInformationMessage('telert CLI updated successfully');
            } else {
                // Fallback to pip
                const fallback = spawn('pip', ['install', '--upgrade', 'telert'], { shell: true });
                fallback.on('close', (code2) => {
                    if (code2 === 0) {
                        vscode.window.showInformationMessage('telert CLI updated successfully');
                    } else {
                        vscode.window.showWarningMessage(
                            "Failed to update telert CLI. Please ensure 'pip' or 'python3' is on your PATH."
                        );
                    }
                });
            }
        });
    }

    // Create status bar item for timer
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left);
    context.subscriptions.push(statusBarItem);

    // Register the command to run in terminal and notify
    let runDisposable = vscode.commands.registerCommand('telert.runInTerminal', async function () {
        const editor = vscode.window.activeTextEditor;
        let command = '';

        // Get the selected text or the current file
        if (editor) {
            const selection = editor.selection;
            if (!selection.isEmpty) {
                command = editor.document.getText(selection);
            } else if (editor.document.fileName) {
                command = editor.document.fileName;
                
                // For script files, use appropriate interpreter
                const fileExt = path.extname(command).toLowerCase();
                if (fileExt === '.py') {
                    command = `python "${command}"`;
                } else if (fileExt === '.js') {
                    command = `node "${command}"`;
                } else if (fileExt === '.sh' || fileExt === '.bash') {
                    command = `bash "${command}"`;
                } else if (fileExt === '.rb') {
                    command = `ruby "${command}"`;
                } else if (fileExt === '.pl') {
                    command = `perl "${command}"`;
                } else if (fileExt === '.php') {
                    command = `php "${command}"`;
                } else {
                    // Ask user what to run
                    command = await vscode.window.showInputBox({
                        placeHolder: 'Enter command to run',
                        value: `"${command}"`,
                        prompt: 'Command to execute'
                    });
                    
                    if (!command) {
                        return; // User cancelled
                    }
                }
            }
        }

        // If no command from editor, prompt the user
        if (!command) {
            command = await vscode.window.showInputBox({
                placeHolder: 'Enter command to run',
                prompt: 'Command to execute'
            });
            
            if (!command) {
                return; // User cancelled
            }
        }

        // Get configuration
        const config = vscode.workspace.getConfiguration('telert');
        const provider = config.get('defaultProvider');
        const threshold = config.get('notificationThreshold');
        const showTimer = config.get('statusBarTimer');
        const envVars = config.get('environmentVariables');

        // Prepare telert command
        let telertCommand = 'telert run';
        
        // Add label based on command
        telertCommand += ` --label "${command.replace(/"/g, '\\"')}"`;
        
        // Add provider if specified
        if (provider) {
            telertCommand += ` --provider ${provider}`;
        }
        
        // Run the command in the integrated terminal
        const terminal = vscode.window.createTerminal('Telert');
        
        // Set environment variables if configured
        if (envVars && Object.keys(envVars).length > 0) {
            const isWindows = os.platform() === 'win32';
            
            for (const [key, value] of Object.entries(envVars)) {
                if (isWindows) {
                    terminal.sendText(`$env:${key}="${value}"`);
                } else {
                    terminal.sendText(`export ${key}="${value}"`);
                }
            }
        }
        
        terminal.show();
        
        // Start timer if enabled
        let startTime = Date.now();
        let timerId = null;
        let commandId = `${Date.now()}-${Math.floor(Math.random() * 10000)}`;
        
        if (showTimer) {
            statusBarItem.text = `$(clock) Telert: 0s`;
            statusBarItem.tooltip = `Running: ${command}`;
            statusBarItem.show();
            
            timerId = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                statusBarItem.text = `$(clock) Telert: ${elapsed}s`;
            }, 1000);
            
            runningTimers.set(commandId, {
                timerId,
                command,
                startTime
            });
        }
        
        // Send the telert command
        terminal.sendText(`${telertCommand} ${command}`);
        
        // Set up to capture output for the "Send Last Output" command
        const terminalData = [];
        
        // Clean up the timer when the terminal is closed
        const disposable = vscode.window.onDidCloseTerminal((closedTerminal) => {
            if (closedTerminal === terminal) {
                if (timerId) {
                    clearInterval(timerId);
                    runningTimers.delete(commandId);
                    
                    // Hide status bar if no more running timers
                    if (runningTimers.size === 0) {
                        statusBarItem.hide();
                    }
                }
                
                disposable.dispose();
            }
        });
    });

    // Register command to send the last terminal output
    let lastOutputDisposable = vscode.commands.registerCommand('telert.sendLastOutput', async function () {
        // Get the active terminal
        const terminal = vscode.window.activeTerminal;
        if (!terminal) {
            vscode.window.showErrorMessage('No active terminal found');
            return;
        }
        
        // Get configuration
        const config = vscode.workspace.getConfiguration('telert');
        const provider = config.get('defaultProvider');
        const envVars = config.get('environmentVariables');
        
        // Prompt for message
        const message = await vscode.window.showInputBox({
            placeHolder: 'Enter notification message',
            prompt: 'Message to send with the terminal output'
        });
        
        if (!message) {
            return; // User cancelled
        }
        
        // Prepare telert command
        let telertCommand = `telert send`;
        
        // Add provider if specified
        if (provider) {
            telertCommand += ` --provider ${provider}`;
        }
        
        // Set environment variables if configured
        if (envVars && Object.keys(envVars).length > 0) {
            const isWindows = os.platform() === 'win32';
            
            for (const [key, value] of Object.entries(envVars)) {
                if (isWindows) {
                    terminal.sendText(`$env:${key}="${value}"`);
                } else {
                    terminal.sendText(`export ${key}="${value}"`);
                }
            }
        }
        
        // Send output as a notification
        terminal.sendText(`${telertCommand} "${message}"`);
    });
    // Register command to configure notification provider via Quick Pick
    let configDisposable = vscode.commands.registerCommand('telert.configureProviders', async function () {
        // Provider options and required env vars
        const options = [
            { label: 'telegram', description: 'Telegram Bot notifications', keys: ['TELERT_TELEGRAM_TOKEN', 'TELERT_TELEGRAM_CHAT_ID'] },
            { label: 'slack', description: 'Slack channel notifications', keys: ['TELERT_SLACK_WEBHOOK'] },
            { label: 'teams', description: 'Microsoft Teams via webhook', keys: ['TELERT_TEAMS_WEBHOOK'] },
            { label: 'discord', description: 'Discord server via webhook', keys: ['TELERT_DISCORD_WEBHOOK'] },
            { label: 'pushover', description: 'Pushover mobile notifications', keys: ['TELERT_PUSHOVER_TOKEN', 'TELERT_PUSHOVER_USER'] },
            { label: 'desktop', description: 'Desktop native notifications', keys: [] },
            { label: 'audio', description: 'Audio sound alert', keys: ['TELERT_AUDIO_FILE', 'TELERT_AUDIO_VOLUME'] }
        ];
        const pick = await vscode.window.showQuickPick(options.map(o => ({ label: o.label, description: o.description })), {
            placeHolder: 'Select default Telert notification provider'
        });
        if (!pick) {
            return;
        }
        const provider = pick.label;
        // Prompt for each required env var
        const config = vscode.workspace.getConfiguration('telert');
        const existing = config.get('environmentVariables') || {};
        const newEnv = { ...existing };
        const found = options.find(o => o.label === provider);
        if (found && found.keys.length) {
            for (const key of found.keys) {
                const value = await vscode.window.showInputBox({ prompt: `Enter value for ${key}` });
                if (value !== undefined) {
                    newEnv[key] = value;
                }
            }
        }
        // Update settings
        await config.update('defaultProvider', provider, vscode.ConfigurationTarget.Global);
        await config.update('environmentVariables', newEnv, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage(`Telert provider set to '${provider}'`);
    });

    context.subscriptions.push(runDisposable);
    context.subscriptions.push(lastOutputDisposable);
    context.subscriptions.push(configDisposable);
}

function deactivate() {
    // Clean up any running timers
    for (const [id, timer] of runningTimers.entries()) {
        clearInterval(timer.timerId);
    }
    runningTimers.clear();
    
    if (statusBarItem) {
        statusBarItem.dispose();
    }
}

module.exports = {
    activate,
    deactivate
};