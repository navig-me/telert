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
    printf "%s" "${text:$i:1}"
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
  printf "%b" "\n${GREEN}$ ${NC}"
  type_text "${command}"
  
  if [ -n "$comment" ]; then
    printf "%b\n" "${YELLOW}# $comment${NC}"
    sleep 1
  fi
  
  # Show the simulated output
  if [ -n "$output" ]; then
    printf "%b\n" "$output"
  fi
  
  sleep 2
}

# Clear the screen
clear

# Introduction
clear
printf "%b\n" "${RED}=== telert ===${NC}"
sleep 0.1
printf "%b\n" "${CYAN}== Terminal & Python notifications, monitoring, and more!${NC}"
sleep 0.3
printf "%b\n" "${BLUE}Channels: Telegram, Slack, Teams, Discord, Email, Desktop, Audio, Pushover${NC}"
sleep 0.5

# Show that it is easy to install and configure
simulate_command "pip install telert && telert init" \
  "Install & configure telert in seconds!" \
  "${CYAN}✓ telert installed & ready! Configure your favorite channels in one step.${NC}"

echo "" # Add spacing

# Basic command completion notification
simulate_command "sleep 2 | telert" \
  "Get notified when any command finishes" \
  "${CYAN}✓ Notification sent: sleep 2 finished with exit 0${NC}"

echo "" # Add spacing

# Custom notification to multiple providers
simulate_command "telert send --provider 'slack,desktop' 'Deployment to production completed!'" \
  "Send a custom message to multiple providers" \
  "${CYAN}✓ Notification sent to Slack, Desktop: Deployment to production completed!${NC}"

echo "" # Add spacing

# Shell Hook: notify for all long-running commands
simulate_command "eval \"\$(telert hook -l 30)\"" \
  "Enable notifications for any command taking longer than 30 seconds" \
  "${YELLOW}Now, running a long command like 'sleep 35' triggers a notification automatically${NC}"
simulate_command "sleep 35" \
  "" \
  "${CYAN}✓ Notification sent: sleep 35 finished (took 35s)${NC}"

echo "" # Add spacing

# Log file monitoring
simulate_command "telert monitor log --file /var/log/app.log --pattern 'ERROR|CRITICAL' --provider telegram" \
  "Alert on error patterns in logs" \
  "Monitoring /var/log/app.log for pattern: ERROR|CRITICAL\n${CYAN}✓ Notification sent to Telegram: ERROR found in app.log${NC}"

echo "" # Add spacing

# Process monitoring
simulate_command "telert monitor process --name 'postgres' --command 'ps aux | grep postgres' --memory-threshold 2G" \
  "Watch a process and get alerts on memory usage" \
  "Process 'postgres' is using 2.1G RAM\n${CYAN}✓ Notification sent: postgres memory usage exceeded 2G${NC}"

echo "" # Add spacing

# Network monitoring
simulate_command "telert monitor network --host myapp.com --port 80 --type http --expected-status 200 --expected-content healthy" \
  "Monitor network endpoint health" \
  "HTTP check to myapp.com:80 returned 500\n${CYAN}✓ Notification sent: Network check failed for myapp.com${NC}"

echo "" # Add spacing

# Show Python API integration
simulate_command "python -c 'from telert import notify; notify(\"Hello from Python!\")"' \
  "Use Telert directly from Python code" \
  "${CYAN}✓ Notification sent: Hello from Python!${NC}"

echo "" # Add spacing
