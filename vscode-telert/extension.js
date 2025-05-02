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
    
    // Create main Telert status bar menu button
    const mainStatusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    mainStatusItem.text = '$(bell) Telert';
    mainStatusItem.tooltip = 'Telert: Run & Notify, Send Output, Configure Provider';
    mainStatusItem.command = 'telert.showMenu';
    mainStatusItem.show();
    context.subscriptions.push(mainStatusItem);
    
    // Register command to show Telert quick menu
    const showMenuDisposable = vscode.commands.registerCommand('telert.showMenu', async () => {
        const items = [
            { label: 'Run in Terminal and Notify', command: 'telert.runInTerminal' },
            { label: 'Configure Notification Provider', command: 'telert.configureProviders' },
            { label: 'Wrap with telert context manager', command: 'telert.wrapWithTelert', when: 'editorLangId == python' },
            { label: 'Wrap with notify decorator', command: 'telert.wrapWithNotifyDecorator', when: 'editorLangId == python' }
        ];
        
        // Filter items based on current editor
        const editor = vscode.window.activeTextEditor;
        const isPython = editor && editor.document.languageId === 'python';
        const filteredItems = items.filter(item => !item.when || (item.when === 'editorLangId == python' && isPython));
        
        const pick = await vscode.window.showQuickPick(filteredItems.map(i => i.label), { placeHolder: 'Telert Commands' });
        if (pick) {
            const selected = filteredItems.find(i => i.label === pick);
            if (selected) {
                vscode.commands.executeCommand(selected.command);
            }
        }
    });
    context.subscriptions.push(showMenuDisposable);

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
        
        // Run the command via VS Code Tasks API so we can track completion
        const args = `${telertCommand} ${command}`;
        const options = {};
        if (envVars && Object.keys(envVars).length > 0) {
            options.env = envVars;
        }

        const shellExec = new vscode.ShellExecution(args, options);
        const taskDef = { type: 'telert' };
        const taskName = `Telert: ${command}`;
        const task = new vscode.Task(taskDef, vscode.TaskScope.Workspace, taskName, 'telert', shellExec);

        vscode.tasks.executeTask(task).then((exec) => {
            if (showTimer) {
                const startTime = Date.now();
                statusBarItem.text = `$(clock) Telert: 0s`;
                statusBarItem.tooltip = `Running: ${command}`;
                statusBarItem.show();

                const timerId = setInterval(() => {
                    const elapsed = Math.floor((Date.now() - startTime) / 1000);
                    statusBarItem.text = `$(clock) Telert: ${elapsed}s`;
                }, 1000);

                const endDisposable = vscode.tasks.onDidEndTaskProcess((e) => {
                    if (e.execution === exec) {
                        clearInterval(timerId);
                        statusBarItem.hide();
                        endDisposable.dispose();
                    }
                });
            }
        });
    });

    // Register command to wrap selected code with telert context manager
    let wrapWithTelertDisposable = vscode.commands.registerCommand('telert.wrapWithTelert', async function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'python') {
            vscode.window.showErrorMessage('This command only works in Python files');
            return;
        }
        
        const selection = editor.selection;
        if (selection.isEmpty) {
            vscode.window.showErrorMessage('Please select a code block to wrap');
            return;
        }
        
        // Get selected text
        const selectedText = editor.document.getText(selection);
        
        // Get label for telert context manager
        const label = await vscode.window.showInputBox({
            placeHolder: 'Enter label for telert context manager',
            prompt: 'Label will appear in notifications when this code completes',
            value: 'Code execution'
        });
        
        if (label === undefined) {
            return; // User cancelled
        }
        
        // Get additional options
        const options = await vscode.window.showQuickPick([
            { label: 'Default settings', description: 'Notify on completion or failure' },
            { label: 'Only notify on failure', description: 'Only send notification if code fails' },
            { label: 'Customize options', description: 'Configure additional telert parameters' }
        ], { placeHolder: 'Select notification options' });
        
        if (!options) {
            return; // User cancelled
        }
        
        // Build the context manager
        let telertOptions = '';
        if (options.label === 'Only notify on failure') {
            telertOptions = ', only_fail=True';
        } else if (options.label === 'Customize options') {
            const includeTraceback = await vscode.window.showQuickPick(
                ['Yes', 'No'],
                { placeHolder: 'Include traceback in error notifications?' }
            );
            
            const provider = await vscode.window.showQuickPick([
                { label: 'default', description: 'Use default provider from configuration' },
                { label: 'telegram', description: 'Send via Telegram' },
                { label: 'slack', description: 'Send via Slack' },
                { label: 'teams', description: 'Send via Microsoft Teams' },
                { label: 'discord', description: 'Send via Discord' },
                { label: 'desktop', description: 'Show desktop notification' },
                { label: 'pushover', description: 'Send via Pushover mobile app' },
                { label: 'audio', description: 'Play audio alert' },
                { label: 'all', description: 'Send to all configured providers' }
            ], { placeHolder: 'Select notification provider' });
            
            if (!includeTraceback || !provider) {
                return; // User cancelled
            }
            
            telertOptions = includeTraceback === 'No' ? ', include_traceback=False' : '';
            
            if (provider.label !== 'default') {
                if (provider.label === 'all') {
                    telertOptions += ', all_providers=True';
                } else {
                    telertOptions += `, provider="${provider.label}"`;
                }
            }
        }
        
        // Format the wrapped code
        const leadingWhitespace = selectedText.match(/^(\s*)/)[1];
        const indentedCode = selectedText.split('\n').map(line => {
            return line.startsWith(leadingWhitespace) ? 
                '    ' + line.substring(leadingWhitespace.length) : 
                '    ' + line;
        }).join('\n');
        
        // Create the full wrapped code
        const wrappedCode = `from telert import telert\n\nwith telert("${label}"${telertOptions}):\n${indentedCode}\n\n# Configure telert providers: https://github.com/navig-me/telert#python-api-usage`;
        
        // Replace the selected text
        await editor.edit(editBuilder => {
            editBuilder.replace(selection, wrappedCode);
        });
    });
    
    // Register command to wrap selected function with notify decorator
    let wrapWithNotifyDecoratorDisposable = vscode.commands.registerCommand('telert.wrapWithNotifyDecorator', async function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'python') {
            vscode.window.showErrorMessage('This command only works in Python files');
            return;
        }
        
        const selection = editor.selection;
        if (selection.isEmpty) {
            vscode.window.showErrorMessage('Please select a function to decorate');
            return;
        }
        
        // Get selected text
        const selectedText = editor.document.getText(selection);
        
        // Check if it starts with 'def ' (function definition)
        const isFunctionDef = selectedText.trim().startsWith('def ');
        
        if (!isFunctionDef) {
            const proceed = await vscode.window.showQuickPick(
                ['Yes, continue anyway', 'No, cancel'],
                { placeHolder: 'Selected code does not appear to be a function definition. Continue?' }
            );
            
            if (proceed !== 'Yes, continue anyway') {
                return;
            }
        }
        
        // Extract function name for the label
        let functionName = 'Function execution';
        const funcNameMatch = selectedText.match(/def\s+([a-zA-Z0-9_]+)\s*\(/);
        if (funcNameMatch && funcNameMatch[1]) {
            functionName = funcNameMatch[1];
        }
        
        // Get label for notify decorator
        const label = await vscode.window.showInputBox({
            placeHolder: 'Enter label for notify decorator',
            prompt: 'Label will appear in notifications when function completes',
            value: functionName
        });
        
        if (label === undefined) {
            return; // User cancelled
        }
        
        // Get additional options
        const options = await vscode.window.showQuickPick([
            { label: 'Default settings', description: 'Notify on completion or failure' },
            { label: 'Only notify on failure', description: 'Only send notification if function fails' },
            { label: 'Customize options', description: 'Configure additional notify parameters' }
        ], { placeHolder: 'Select notification options' });
        
        if (!options) {
            return; // User cancelled
        }
        
        // Build the decorator
        let notifyOptions = '';
        if (options.label === 'Only notify on failure') {
            notifyOptions = ', only_fail=True';
        } else if (options.label === 'Customize options') {
            const includeTraceback = await vscode.window.showQuickPick(
                ['Yes', 'No'],
                { placeHolder: 'Include traceback in error notifications?' }
            );
            
            const provider = await vscode.window.showQuickPick([
                { label: 'default', description: 'Use default provider from configuration' },
                { label: 'telegram', description: 'Send via Telegram' },
                { label: 'slack', description: 'Send via Slack' },
                { label: 'teams', description: 'Send via Microsoft Teams' },
                { label: 'discord', description: 'Send via Discord' },
                { label: 'desktop', description: 'Show desktop notification' },
                { label: 'pushover', description: 'Send via Pushover mobile app' },
                { label: 'audio', description: 'Play audio alert' },
                { label: 'all', description: 'Send to all configured providers' }
            ], { placeHolder: 'Select notification provider' });
            
            if (!includeTraceback || !provider) {
                return; // User cancelled
            }
            
            notifyOptions = includeTraceback === 'No' ? ', include_traceback=False' : '';
            
            if (provider.label !== 'default') {
                if (provider.label === 'all') {
                    notifyOptions += ', all_providers=True';
                } else {
                    notifyOptions += `, provider="${provider.label}"`;
                }
            }
        }
        
        // Create the decorated code
        const decoratedCode = `from telert import notify\n\n@notify("${label}"${notifyOptions})\n${selectedText}\n\n# Configure telert providers: https://github.com/navig-me/telert#python-api-usage`;
        
        // Replace the selected text
        await editor.edit(editBuilder => {
            editBuilder.replace(selection, decoratedCode);
        });
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
    context.subscriptions.push(wrapWithTelertDisposable);
    context.subscriptions.push(wrapWithNotifyDecoratorDisposable);
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