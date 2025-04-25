#!/usr/bin/env bash
# A simulation script for telert to create a GIF for the README
# This script will simulate various telert commands without actually running them

set -e

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to simulate typing
function type_text() {
  text="$1"
  for (( i=0; i<${#text}; i++ )); do
    echo -n "${text:$i:1}"
    sleep 0.02
  done
  echo ""
  sleep 0.2
}

# Function to show a prompt and command, then "execute" it with simulated output
function simulate_command() {
  command="$1"
  comment="$2"
  output="$3"
  
  # Show the command with prompt
  echo -ne "\n${GREEN}$ ${NC}"
  type_text "${command}"
  
  if [ -n "$comment" ]; then
    echo -e "${YELLOW}# $comment${NC}"
    sleep 1
  fi
  
  # Show the simulated output
  if [ -n "$output" ]; then
    echo -e "$output"
  fi
  
  sleep 2
}

# Clear the screen
clear

# Introduction
echo -e "${RED}=== telert ===${NC}"
sleep 0.1
echo -e "${CYAN}== Command completion notifications${NC}" 
echo -e "${CYAN}== on Telegram, Slack, Teams and Desktop.${NC}"
sleep 0.5

# Simple telert run example
simulate_command "sleep 2 | telert" \
"Simple notification after command completion" \
"${CYAN}✓ Notification sent with exit code 0${NC}"

# Show basic telert run example
simulate_command "telert run --label \"Database Backup\" pg_dump -U postgres mydb > backup.sql" \
                "Run a command with a custom label" \
"Starting pg_dump...
Database dump completed successfully!
${CYAN}✓ Notification sent: Database Backup finished with exit 0 in 3s${NC}"

# Show long-running command with real-time output
simulate_command "telert run --label \"ML Training\" python train.py" \
                "Real-time output is displayed during execution" \
"Epoch 1/10: loss=0.342, accuracy=0.896
Epoch 2/10: loss=0.213, accuracy=0.923
Epoch 3/10: loss=0.187, accuracy=0.946
...
Training complete! Model saved to ./model.h5
${CYAN}✓ Notification sent: ML Training finished with exit 0 in 52s${NC}"

# Show pipeline example
simulate_command "find . -name \"*.log\" | grep \"ERROR\" | telert --provider slack \"Error check complete\"" \
                "Pipe command output to telert" \
"./logs/app.log:ERROR: Database connection failed
./logs/service.log:ERROR: Authentication timeout
${CYAN}✓ Notification sent to Slack: Error check complete${NC}"

# Show direct message example
simulate_command "telert send \"Deployment to production completed successfully!\"" \
                "Send custom notification messages" \
"${CYAN}✓ Notification sent: Deployment to production completed successfully!${NC}"

# Show failure case
simulate_command "telert run --only-fail rsync -a /src/ /backup/" \
                "Get notified only when commands fail" \
"Building file list...
File list built, starting transfer...
Transfer complete.
${GREEN}✓ Command completed successfully (no notification sent, as --only-fail was specified)${NC}"

# Show bash hook example
simulate_command "eval \"\$(telert hook -l 30)\"" \
                "Set up automatic notifications for all commands > 30s" \
"${CYAN}✓ Hook installed! All commands taking longer than 30s will now trigger notifications${NC}"
