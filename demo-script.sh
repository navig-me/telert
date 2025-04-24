#!/usr/bin/env bash
# A demo script for telert to create a GIF for the README
# This script will demonstrate various telert commands

set -e

# Color definitions
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Mock command that takes a few seconds to complete
function slow_command() {
  echo "Starting process..."
  for i in {1..5}; do
    echo "Processing step $i of 5..."
    sleep 1
  done
  echo "Process completed successfully!"
}

# Function to type text character by character
function type_text() {
  text="$1"
  for (( i=0; i<${#text}; i++ )); do
    echo -n "${text:$i:1}"
    sleep 0.05
  done
  echo ""
  sleep 0.5
}

# Function to show a command, then execute it
function show_and_execute() {
  command="$1"
  comment="$2"
  
  # Show the command with prompt
  echo -e "\n${BLUE}$ ${command}${NC}"
  if [ -n "$comment" ]; then
    echo -e "${YELLOW}# $comment${NC}"
  fi
  sleep 1
  
  # Execute the command
  eval "$command"
  sleep 2
}

# Clear the screen
clear

# Introduction
echo -e "${GREEN}=== telert Demo - Terminal Notifications Made Easy ===${NC}"
sleep 2

# Basic example - running a command with telert
show_and_execute "telert run --label \"Demo Process\" -- echo \"Running a sample process\"" "Run a command and get notified when it completes"

# Running a longer process
show_and_execute "telert run --label \"Long Process\" -- bash -c \"slow_command\"" "Works with longer running processes too"

# Show the filter mode
show_and_execute "echo 'This is sample output' | telert \"Pipeline completed\"" "Use it in pipelines too!"

# Send a direct message
show_and_execute "telert send \"Custom notification message\"" "Send custom messages directly"

# Show different providers
show_and_execute "telert send --provider telegram \"Sent specifically to Telegram\"" "Specify which messaging service to use"

# Final message
echo -e "\n${GREEN}=== That's it! Get notified when your commands complete! ===${NC}"
echo -e "${BLUE}Install telert today: pip install telert${NC}"
sleep 3