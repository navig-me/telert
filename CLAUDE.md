# CLAUDE.md

Do not Commit CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Lint/Test Commands

- Install dev dependencies: `pip install -e ".[dev]"`
- Run tests: `pytest`
- Build package: `python -m build`
- Verify package: `twine check dist/*`
- Install package locally: `pip install -e .`
- Run checks before releasing: `python -m build && twine check dist/*`
- Build VS Code extension: `cd vscode-telert && vsce package`

## Code Style Guidelines

- **Imports**: Group standard library, third-party, and local imports with a blank line between groups
- **Formatting**: Follow PEP 8 style guide; use docstrings for functions, classes, and modules
- **Types**: Use type annotations for function parameters and return values as seen in api.py
- **Naming**: 
  - Classes: CamelCase (e.g., `TelegramProvider`)
  - Functions/variables: snake_case (e.g., `send_message`, `webhook_url`)
  - Constants: UPPERCASE (e.g., `DEFAULT_SOUND_FILE`)
- **Error Handling**: Use try/except blocks with specific exceptions and helpful error messages
- **Documentation**: Include docstrings with parameter descriptions and usage examples
- **Modules**: Keep functionality organized in separate modules (messaging.py, api.py, cli.py)

## Task Tracking

Completed tasks:
- [x] Task 1: Automate build and push using Github Automations on each tag for VS Code and Docker
- [x] Task 2: Improve VS Code extension documentation
- [x] Task 3: Fix the failing Example Telert Workflow
- [x] Task 4: Move Telert Action template to the telert-action repository
- [x] Task 5: Use telert.png as the official image

### Task 5 Changes:
1. Updated main README.md to display telert.png logo at the top
2. Replaced VS Code extension icon with telert.png (256x256)
3. Replaced notification icon with telert.png (128x128)
4. Added telert.png to MANIFEST.in
5. Created Docker API static files with telert.png as favicon
6. Created index.html for Docker API with telert.png logo
7. Updated server.py to serve static files and HTML index page