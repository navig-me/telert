# Recording a Demo GIF for telert

This document explains how to create a demo GIF of telert features for the README.

## Prerequisites

You'll need one of these tools installed:

### Option 1: Terminalizer (recommended)

```bash
# Install Terminalizer globally
npm install -g terminalizer

# Record your session
terminalizer record telert-demo --config terminalizer-config.yml

# Run the demo script inside the recording session
./demo-script.sh

# Exit the recording session with Ctrl+D

# Render the GIF
terminalizer render telert-demo --output telert-demo.gif
```

### Option 2: asciinema + svg-term

```bash
# Install asciinema
pip install asciinema

# Record your session
asciinema rec telert-demo.cast

# Run the demo script inside the recording session
./demo-script.sh

# Exit the recording with Ctrl+D

# Install svg-term-cli globally
npm install -g svg-term-cli

# Convert to SVG
svg-term --in telert-demo.cast --out telert-demo.svg --window --width 80 --height 24

# Use a browser or tool like svg2png to convert the SVG to a GIF/PNG
```

### Option 3: ttygif

```bash
# On macOS
brew install ttygif

# Record with ttyrec
ttyrec telert-demo

# Run the demo script inside the recording session
./demo-script.sh

# Exit with Ctrl+D

# Convert to GIF
ttygif telert-demo
```

## Adding the GIF to the README

Once you have created your GIF, add it to the README with:

```markdown
![telert demo](telert-demo.gif)
```

Place this near the top of the README, just after the introduction and before the "Quick start" section for maximum visibility.

## Tips for Good Demo GIFs

1. Keep it short (30-60 seconds max)
2. Show the most important features
3. Include clear examples that showcase real-world use cases
4. Use a clean, readable terminal theme
5. Consider adding a small pause after important commands to let users read the output
6. Make sure text is large enough to be readable when embedded in the README