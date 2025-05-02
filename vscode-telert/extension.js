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
         * @returns {Promise<boolean>} Whether the operation was successful
         */
        async function ensureTelert() {
            console.log('[Telert] Checking for telert CLI...');
            
            try {
                // Check if telert CLI is installed
                const check = spawn('telert', ['--version'], { timeout: 5000 });
                
                return new Promise((resolve) => {
                    check.on('error', () => {
                        // telert not found, install it
                        console.log('[Telert] telert CLI not found, installing...');
                        updateTelertCli(true).then(resolve);
                    });
                    
                    check.on('close', code => {
                        if (code === 0) {
                            // telert found, update it
                            console.log('[Telert] telert CLI found, updating...');
                            updateTelertCli(false).then(resolve);
                        } else {
                            // telert not found or error, install it
                            console.log('[Telert] telert CLI check failed, installing...');
                            updateTelertCli(true).then(resolve);
                        }
                    });
                });
            } catch (error) {
                console.error('[Telert] Error checking telert CLI:', error);
                return false;
            }
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
    /**
     * Run pip install --upgrade telert, with improved error handling and fallbacks
     * @param {boolean} showNotifications Whether to show VS Code notifications during install
     * @returns {Promise<boolean>} Promise resolving to success status
     */
    function updateTelertCli(showNotifications = true) {
        return new Promise((resolve) => {
            if (showNotifications) {
                vscode.window.showInformationMessage('Updating telert CLI...');
            }
            
            // Try via python3 -m pip first (preferred method)
            console.log('[Telert] Attempting installation via python3 -m pip...');
            const installer = spawn('python3', ['-m', 'pip', 'install', '--upgrade', 'telert'], { 
                shell: true,
                timeout: 30000 // 30 second timeout
            });
            
            installer.on('error', (err) => {
                console.error('[Telert] Error spawning python3:', err);
                fallbackToPip();
            });
            
            installer.on('close', (code) => {
                if (code === 0) {
                    console.log('[Telert] telert CLI updated successfully via python3');
                    if (showNotifications) {
                        vscode.window.showInformationMessage('telert CLI updated successfully');
                    }
                    resolve(true);
                } else {
                    console.warn(`[Telert] python3 installation failed with code ${code}, trying pip fallback`);
                    fallbackToPip();
                }
            });
            
            // Fallback to regular pip if python3 -m pip fails
            function fallbackToPip() {
                console.log('[Telert] Attempting installation via pip...');
                const fallback = spawn('pip', ['install', '--upgrade', 'telert'], { 
                    shell: true,
                    timeout: 30000 // 30 second timeout
                });
                
                fallback.on('error', (err) => {
                    console.error('[Telert] Error spawning pip:', err);
                    if (showNotifications) {
                        vscode.window.showWarningMessage(
                            "Failed to update telert CLI. Please ensure 'pip' or 'python3' is on your PATH."
                        );
                    }
                    resolve(false);
                });
                
                fallback.on('close', (code2) => {
                    if (code2 === 0) {
                        console.log('[Telert] telert CLI updated successfully via pip');
                        if (showNotifications) {
                            vscode.window.showInformationMessage('telert CLI updated successfully');
                        }
                        resolve(true);
                    } else {
                        console.error(`[Telert] pip installation failed with code ${code2}`);
                        if (showNotifications) {
                            vscode.window.showWarningMessage(
                                "Failed to update telert CLI. Please ensure 'pip' or 'python3' is on your PATH."
                            );
                        }
                        resolve(false);
                    }
                });
            }
        });
    }
    
    // Check for telert updates based on extension version changes and time interval
    (function checkTelertUpdates() {
        const extensionId = 'navig.telert-vscode';
        const ext = vscode.extensions.getExtension(extensionId);
        const currentVersion = ext && ext.packageJSON && ext.packageJSON.version;
        const prevVersion = context.globalState.get('extensionVersion');
        const now = Date.now();
        const lastCheck = context.globalState.get('lastTelertUpdateTime') || 0;
        const ONE_DAY_MS = 1000 * 60 * 60 * 24;
        
        // If first run or extension version changed -> install/update CLI
        if (currentVersion && prevVersion !== currentVersion) {
            console.log('[Telert] Extension version changed or first run, updating telert CLI');
            updateTelertCli(true).then(() => {
                context.globalState.update('extensionVersion', currentVersion);
                context.globalState.update('lastTelertUpdateTime', now);
            });
        }
        // Else if it's been more than a day since last check -> update CLI
        else if (now - lastCheck > ONE_DAY_MS) {
            console.log('[Telert] Daily update check for telert CLI');
            updateTelertCli(false).then(success => {
                if (success) {
                    context.globalState.update('lastTelertUpdateTime', now);
                }
            });
        }
    })();

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
            { label: 'Wrap with notify decorator', command: 'telert.wrapWithNotifyDecorator', when: 'editorLangId == python' },
            { label: 'Monitor Python Process', command: 'telert.monitorPythonProcess', when: 'editorLangId == python' }
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
        
        // Add threshold if specified (only notify if command takes longer than N seconds)
        if (threshold && threshold > 0) {
            telertCommand += ` --min-seconds ${threshold}`;
        }
        
        // Run the command via VS Code Tasks API so we can track completion
        const args = `${telertCommand} ${command}`;
        const options = {};
        if (envVars && Object.keys(envVars).length > 0) {
            options.env = { ...process.env, ...envVars };
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
        
        let selection = editor.selection;
        let selectedText;
        
        // If no selection, try to select the current line
        if (selection.isEmpty) {
            const currentLine = editor.document.lineAt(selection.active.line);
            
            // If current line is empty or just whitespace, show error
            if (currentLine.isEmptyOrWhitespace) {
                vscode.window.showErrorMessage('Please position cursor on a non-empty line or select a code block');
                return;
            }
            
            // Create a selection for the current line
            selection = new vscode.Selection(
                currentLine.lineNumber, 0,
                currentLine.lineNumber, currentLine.text.length
            );
            selectedText = currentLine.text;
        } else {
            // Use the existing selection
            selectedText = editor.document.getText(selection);
        }
        
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
        
        // Get document and line information
        const document = editor.document;
        const importRange = new vscode.Range(0, 0, 0, 0);

        // Analyze indentation style in the document
        let indentSize = 4; // Default
        let useTabsForIndent = false;
        
        // Detect if file uses tabs for indentation
        const documentText = document.getText();
        if (documentText.match(/^\t+/m)) {
            useTabsForIndent = true;
        }
        
        // Determine current indentation level
        const leadingWhitespace = selectedText.match(/^(\s*)/)[1] || '';
        const indentChar = useTabsForIndent ? '\t' : ' ';
        const newIndent = leadingWhitespace + (useTabsForIndent ? '\t' : ' '.repeat(indentSize));
        
        // Properly indent the selected code
        const indentedCode = selectedText.split('\n').map(line => {
            if (line.trim() === '') {
                return line; // Preserve empty lines as is
            }
            // Keep the line's existing indentation, just add one more level
            if (line.startsWith(leadingWhitespace)) {
                return newIndent + line.substring(leadingWhitespace.length);
            }
            return newIndent + line.trim();
        }).join('\n');
        
        // Create the context manager with proper indentation
        const wrappedCode = `${leadingWhitespace}with telert("${label}"${telertOptions}):\n${indentedCode}`;
        
        // Perform the edits in a single transaction
        await editor.edit(editBuilder => {
            // Replace the selected text with the wrapped code
            editBuilder.replace(selection, wrappedCode);
            
            // Add the import at the top of the file if not already present
            if (!documentText.includes('from telert import telert')) {
                editBuilder.insert(importRange, 'from telert import telert\n\n');
            }
        });
    });
    
    // Register command to wrap selected function with notify decorator
    let wrapWithNotifyDecoratorDisposable = vscode.commands.registerCommand('telert.wrapWithNotifyDecorator', async function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'python') {
            vscode.window.showErrorMessage('This command only works in Python files');
            return;
        }
        
        let selection = editor.selection;
        let selectedText = '';
        let functionText = '';
        
        // Find the complete function definition - handles multi-line function signatures
        async function findCompleteFunctionDefinition(startLine) {
            const document = editor.document;
            const lineCount = document.lineCount;
            let functionStartLine = -1;
            let functionEndLine = -1;
            let insideFunction = false;
            let parenthesesCount = 0;
            let bodyIndentation = '';
            
            // Find function start (even if cursor not at "def" line)
            for (let i = startLine; i >= 0; i--) {
                const lineText = document.lineAt(i).text;
                if (lineText.trim().startsWith('def ')) {
                    functionStartLine = i;
                    break;
                }
            }
            
            // If we didn't find a function, start from current line and see if it's a function
            if (functionStartLine === -1) {
                const currentLine = document.lineAt(startLine).text;
                if (currentLine.trim().startsWith('def ')) {
                    functionStartLine = startLine;
                }
            }
            
            // If we found a function, determine where it ends
            if (functionStartLine !== -1) {
                // Start scanning from function definition line
                for (let i = functionStartLine; i < lineCount; i++) {
                    const lineText = document.lineAt(i).text;
                    
                    // Count parentheses in the signature to handle multi-line definitions
                    if (!insideFunction) {
                        for (const char of lineText) {
                            if (char === '(') parenthesesCount++;
                            if (char === ')') parenthesesCount--;
                        }
                        
                        // Function signature complete, next line should be function body
                        if (parenthesesCount === 0 && lineText.trim().endsWith(':')) {
                            insideFunction = true;
                            
                            // Determine body indentation from next line (if exists)
                            if (i+1 < lineCount) {
                                const nextLine = document.lineAt(i+1).text;
                                const match = nextLine.match(/^(\s+)/);
                                if (match) bodyIndentation = match[1];
                            }
                            continue;
                        }
                    } else {
                        // Check if still in function body based on indentation
                        if (lineText.trim() === '') continue; // Skip empty lines
                        
                        // If we hit a line with less or equal indentation than function def, we're out of the function
                        if (!lineText.startsWith(bodyIndentation)) {
                            functionEndLine = i - 1;
                            break;
                        }
                    }
                }
                
                // If we reached the end of the file and are still in the function
                if (insideFunction && functionEndLine === -1) {
                    functionEndLine = lineCount - 1;
                }
                
                // Create a selection for the entire function
                if (functionStartLine !== -1 && functionEndLine !== -1) {
                    const startPos = new vscode.Position(functionStartLine, 0);
                    const endPos = new vscode.Position(functionEndLine, document.lineAt(functionEndLine).text.length);
                    selection = new vscode.Selection(startPos, endPos);
                    return document.getText(selection);
                } else if (functionStartLine !== -1) {
                    // Just get the function definition line if we couldn't determine the end
                    const line = document.lineAt(functionStartLine);
                    selection = new vscode.Selection(functionStartLine, 0, functionStartLine, line.text.length);
                    return line.text;
                }
            }
            
            return null;
        }
        
        // If no selection or only one line is selected, try to find the entire function
        if (selection.isEmpty) {
            // Try to find a function at or near the cursor position
            functionText = await findCompleteFunctionDefinition(selection.active.line);
            
            if (!functionText) {
                vscode.window.showErrorMessage('Please position cursor on a function definition or select a function to decorate');
                return;
            }
            
            selectedText = functionText;
        } else {
            // Use the existing selection, but check if it's a complete function
            selectedText = editor.document.getText(selection);
            
            // Check if the function definition spans multiple lines but only part is selected
            const isFunctionDefStart = selectedText.trim().startsWith('def ');
            const hasClosingParenAndColon = selectedText.includes('):');
            
            if (isFunctionDefStart && !hasClosingParenAndColon) {
                // Try to find the complete function
                functionText = await findCompleteFunctionDefinition(selection.start.line);
                if (functionText) {
                    selectedText = functionText;
                }
            }
        }
        
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
        
        // Get document information
        const document = editor.document;
        const importRange = new vscode.Range(0, 0, 0, 0);
        const documentText = document.getText();

        // Determine current indentation level
        const leadingWhitespace = selectedText.match(/^(\s*)/)[1] || '';
        
        // Create the decorated code with proper indentation
        const decoratedCode = `${leadingWhitespace}@notify("${label}"${notifyOptions})\n${selectedText}`;
        
        // Perform the edits in a single transaction
        await editor.edit(editBuilder => {
            // Replace the selected text with the wrapped code
            editBuilder.replace(selection, decoratedCode);
            
            // Add the import at the top of the file if not already present
            if (!documentText.includes('from telert import notify')) {
                editBuilder.insert(importRange, 'from telert import notify\n\n');
            }
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

    // Register command to monitor a Python process
    let monitorProcessDisposable = vscode.commands.registerCommand('telert.monitorPythonProcess', async function () {
        // Get all running tasks
        const tasks = await vscode.tasks.fetchTasks({ type: 'process' });
        
        // Filter for Python processes
        const pythonTasks = tasks.filter(task => {
            const definition = task.definition;
            if (definition.command && typeof definition.command === 'string') {
                return definition.command.includes('python') || definition.command.includes('python3');
            }
            return false;
        });
        
        // If no Python processes, check for terminals with Python
        let terminalOptions = [];
        if (pythonTasks.length === 0) {
            const terminals = vscode.window.terminals;
            for (const terminal of terminals) {
                const name = terminal.name;
                if (name.toLowerCase().includes('python')) {
                    terminalOptions.push({ label: `Terminal: ${name}`, terminal });
                }
            }
        }
        
        // Prepare options for QuickPick
        const options = [
            ...pythonTasks.map(task => ({ 
                label: `Task: ${task.name || 'Unnamed Task'}`, 
                description: task.source,
                task
            })),
            ...terminalOptions
        ];
        
        // Add option for PID entry
        options.push({ label: 'Enter process ID manually', isPidOption: true });
        
        // No Python processes found
        if (options.length === 0) {
            vscode.window.showInformationMessage('No running Python processes found. Start a Python process and try again.');
            return;
        }
        
        // Show QuickPick to select a process
        const selected = await vscode.window.showQuickPick(options, {
            placeHolder: 'Select a Python process to monitor'
        });
        
        if (!selected) return; // User cancelled
        
        // Handle manual PID entry
        if (selected.isPidOption) {
            const pid = await vscode.window.showInputBox({
                placeHolder: 'Enter Python process ID (PID)',
                prompt: 'Enter the process ID of the Python process to monitor',
                validateInput: (value) => {
                    if (!/^\d+$/.test(value)) {
                        return 'Please enter a valid process ID (numbers only)';
                    }
                    return null;
                }
            });
            
            if (!pid) return; // User cancelled
            
            setupProcessMonitoring(Number(pid));
            return;
        }
        
        // Get PID from task or terminal
        let pid;
        if (selected.task) {
            // For tasks, we might need to find the PID
            vscode.window.showInformationMessage(`Monitoring ${selected.label}. Notifications will be sent when it completes.`);
            // Implementation would depend on how to get PID from task
            // This is a placeholder - actual implementation would need to be adapted
            pid = selected.task.processId;
        } else if (selected.terminal) {
            // For terminals, we might be able to get the PID
            vscode.window.showInformationMessage(`Monitoring terminal ${selected.terminal.name}. Notifications will be sent when it closes.`);
            pid = selected.terminal.processId;
        }
        
        if (pid) {
            setupProcessMonitoring(pid);
        } else {
            vscode.window.showWarningMessage('Could not determine process ID. Try entering it manually.');
        }
    });
    
    /**
     * Set up monitoring for a specific process ID
     * @param {number} pid Process ID to monitor
     */
    function setupProcessMonitoring(pid) {
        if (!pid) return;
        
        // Get configuration
        const config = vscode.workspace.getConfiguration('telert');
        const provider = config.get('defaultProvider');
        const showTimer = config.get('statusBarTimer');
        
        // Start monitoring
        vscode.window.showInformationMessage(`Monitoring Python process with PID ${pid}. Notifications will be sent when it completes.`);
        
        // Record start time for timing
        const startTime = Date.now();
        
        // Create a unique ID for this monitoring session
        const monitorId = `python-${pid}-${Date.now()}`;
        
        // Show timer in status bar if enabled
        if (showTimer) {
            statusBarItem.text = `$(eye) Monitoring PID ${pid}: 0s`;
            statusBarItem.tooltip = `Monitoring Python process ${pid}`;
            statusBarItem.show();
            
            const timerId = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                statusBarItem.text = `$(eye) PID ${pid}: ${elapsed}s`;
            }, 1000);
            
            // Store timer info
            runningTimers.set(monitorId, { 
                timerId, 
                startTime,
                pid,
                type: 'python-process'
            });
        }
        
        // Get monitoring interval from configuration or use default (5 seconds)
        const config = vscode.workspace.getConfiguration('telert');
        const monitorInterval = (config.get('processMonitorIntervalSeconds') || 5) * 1000;
        
        // Check process status periodically based on configuration
        const checkProcess = () => {
            try {
                // Use a different approach based on platform
                if (process.platform === 'win32') {
                    // Windows
                    const checker = spawn('tasklist', ['/FI', `PID eq ${pid}`, '/NH']);
                    
                    let output = '';
                    checker.stdout.on('data', (data) => {
                        output += data.toString();
                    });
                    
                    checker.on('close', (code) => {
                        if (code === 0) {
                            if (!output.includes(pid.toString())) {
                                // Process has ended
                                processEnded(pid, monitorId);
                            } else {
                                // Process still running, check again later
                                setTimeout(checkProcess, monitorInterval);
                            }
                        } else {
                            // Error checking, try again
                            setTimeout(checkProcess, monitorInterval);
                        }
                    });
                } else {
                    // Unix-like (macOS, Linux)
                    const checker = spawn('ps', ['-p', pid.toString()]);
                    
                    let output = '';
                    checker.stdout.on('data', (data) => {
                        output += data.toString();
                    });
                    
                    checker.on('close', (code) => {
                        if (code !== 0) {
                            // Process has ended (ps returns non-zero when PID not found)
                            processEnded(pid, monitorId);
                        } else {
                            // Process still running, check again later
                            setTimeout(checkProcess, monitorInterval);
                        }
                    });
                }
            } catch (error) {
                console.error(`[Telert] Error checking process ${pid}:`, error);
                // Try again later despite error
                setTimeout(checkProcess, monitorInterval);
            }
        };
        
        // Start checking process
        checkProcess();
        
        /**
         * Handle process ended event
         * @param {number} pid Process ID that ended
         * @param {string} monitorId Monitoring session ID
         */
        function processEnded(pid, monitorId) {
            // Clear timer
            if (runningTimers.has(monitorId)) {
                const { timerId, startTime } = runningTimers.get(monitorId);
                clearInterval(timerId);
                runningTimers.delete(monitorId);
                
                // Calculate duration
                const endTime = Date.now();
                const duration = Math.floor((endTime - startTime) / 1000);
                const durationStr = formatDuration(duration);
                
                // Hide status bar item if it's showing this process
                if (statusBarItem.tooltip && statusBarItem.tooltip.includes(`${pid}`)) {
                    statusBarItem.hide();
                }
                
                // Show notification
                vscode.window.showInformationMessage(`Python process ${pid} has completed after ${durationStr}`);
                
                // Send telert notification
                sendProcessNotification(pid, duration, durationStr, provider);
            }
        }
        
        /**
         * Send notification about process completion
         * @param {number} pid Process ID
         * @param {number} duration Duration in seconds
         * @param {string} durationStr Formatted duration string
         * @param {string} provider Provider to use
         */
        function sendProcessNotification(pid, duration, durationStr, provider) {
            const message = `Python process ${pid} completed after ${durationStr}`;
            
            // Prepare command
            let telertCommand = `telert send`;
            
            // Add provider if specified
            if (provider) {
                telertCommand += ` --provider ${provider}`;
            }
            
            // Send notification
            const args = `${telertCommand} "${message}"`;
            const shellExec = new vscode.ShellExecution(args);
            const taskDef = { type: 'telert' };
            const taskName = `Telert: Process ${pid} notification`;
            const task = new vscode.Task(
                taskDef, 
                vscode.TaskScope.Workspace, 
                taskName, 
                'telert', 
                shellExec
            );
            
            vscode.tasks.executeTask(task);
        }
        
        /**
         * Format duration in seconds to a human-readable string
         * @param {number} seconds Duration in seconds
         * @returns {string} Formatted duration string
         */
        function formatDuration(seconds) {
            if (seconds < 60) {
                return `${seconds} seconds`;
            } else if (seconds < 3600) {
                const minutes = Math.floor(seconds / 60);
                const remainingSeconds = seconds % 60;
                return `${minutes} minute${minutes !== 1 ? 's' : ''} ${remainingSeconds} second${remainingSeconds !== 1 ? 's' : ''}`;
            } else {
                const hours = Math.floor(seconds / 3600);
                const remainingMinutes = Math.floor((seconds % 3600) / 60);
                return `${hours} hour${hours !== 1 ? 's' : ''} ${remainingMinutes} minute${remainingMinutes !== 1 ? 's' : ''}`;
            }
        }
    }
    
    context.subscriptions.push(runDisposable);
    context.subscriptions.push(wrapWithTelertDisposable);
    context.subscriptions.push(wrapWithNotifyDecoratorDisposable);
    context.subscriptions.push(configDisposable);
    context.subscriptions.push(monitorProcessDisposable);

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