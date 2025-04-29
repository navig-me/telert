#!/bin/bash
# Script to install telert shell completions

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASH_COMPLETION_DIR="${HOME}/.local/share/bash-completion/completions"
ZSH_COMPLETION_DIR="${HOME}/.zsh/completions"
FISH_COMPLETION_DIR="${HOME}/.config/fish/completions"

# Create completion directories if they don't exist
mkdir -p "${BASH_COMPLETION_DIR}"
mkdir -p "${ZSH_COMPLETION_DIR}"
mkdir -p "${FISH_COMPLETION_DIR}"

# Copy completion files
echo "Installing telert shell completions..."

# Bash completion
cp "${SCRIPT_DIR}/telert.bash" "${BASH_COMPLETION_DIR}/telert"
echo "✓ Bash completion installed to ${BASH_COMPLETION_DIR}/telert"

# Zsh completion
cp "${SCRIPT_DIR}/telert.zsh" "${ZSH_COMPLETION_DIR}/_telert"
echo "✓ Zsh completion installed to ${ZSH_COMPLETION_DIR}/_telert"

# Fish completion
cp "${SCRIPT_DIR}/telert.fish" "${FISH_COMPLETION_DIR}/telert.fish"
echo "✓ Fish completion installed to ${FISH_COMPLETION_DIR}/telert.fish"

echo
echo "Shell completions installed. You may need to restart your shell or source your shell profile."
echo

# Instructions for different shells
echo "To enable completions in your current session:"
echo "  Bash: source ${BASH_COMPLETION_DIR}/telert"
echo "  Zsh:  Add this to your .zshrc if not already there:"
echo "        fpath=(~/.zsh/completions \$fpath)"
echo "        autoload -U compinit && compinit"
echo "  Fish: No action needed, completions should work automatically."