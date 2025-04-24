# telert Demo

This document provides information about the demonstration files included in this repository.

## Demo Files

- `telert-demo.svg`: Terminal recording showing telert in action
- `demo-simulation.sh`: Script used to create the demo (simulates telert commands)
- `demo-script.sh`: Alternative script that runs actual telert commands

## Running the Demo Scripts

These scripts are intended primarily for demonstration purposes, but you can run them to see how telert works:

```bash
# Run the simulation (doesn't require telert to be configured)
./demo-simulation.sh

# Run the actual script (requires telert to be configured)
./demo-script.sh
```

## Demo Features Shown

The demo showcases key telert features:

1. Running commands with labels and getting notifications on completion
2. Monitoring long-running processes 
3. Using telert in pipelines
4. Sending direct notification messages
5. Specifying different messaging providers
6. Using conditional notifications (--only-fail)
7. Setting up shell hooks

## Creating Your Own Demo

If you'd like to create your own demo recording, we recommend using either:

1. asciinema + svg-term (for terminal SVG recordings)
2. Screen recording software + a GIF converter (for animated GIFs)