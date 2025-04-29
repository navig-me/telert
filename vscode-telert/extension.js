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
        terminal.sendText(`${telertCommand} -- ${command}`);
        
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

    context.subscriptions.push(runDisposable);
    context.subscriptions.push(lastOutputDisposable);
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