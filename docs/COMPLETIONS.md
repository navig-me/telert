# Shell Completions for Telert

Telert supports shell completions for Bash, Zsh, and Fish, making it easier to use the CLI by providing tab-completion for commands, options, and arguments.

## Generating Completions

Telert can generate shell completion scripts for different shells:

```bash
# Generate and show completions for all shells
telert completions

# Generate for a specific shell
telert completions --shell bash
telert completions --shell zsh
telert completions --shell fish

# Save completions to a directory
telert completions --output-dir ~/.local/share/bash-completion/completions
telert completions --shell zsh --output-dir ~/.zsh/completions
telert completions --shell fish --output-dir ~/.config/fish/completions
```

## Installation

### Bash

1. Generate the completion script:

   ```bash
   mkdir -p ~/.local/share/bash-completion/completions
   telert completions --shell bash --output-dir ~/.local/share/bash-completion/completions
   ```

2. Add to your `~/.bashrc` or `~/.bash_profile`:

   ```bash
   # Enable telert completions
   if [ -f ~/.local/share/bash-completion/completions/telert ]; then
       source ~/.local/share/bash-completion/completions/telert
   fi
   ```

3. Restart your shell or source your profile:

   ```bash
   source ~/.bashrc
   # or
   source ~/.bash_profile
   ```

### Zsh

1. Create the completion directory if it doesn't exist:

   ```bash
   mkdir -p ~/.zsh/completions
   ```

2. Generate the completion script:

   ```bash
   telert completions --shell zsh --output-dir ~/.zsh/completions
   ```

3. Add to your `~/.zshrc`:

   ```bash
   # Add custom completions directory to fpath
   fpath=(~/.zsh/completions $fpath)
   
   # Initialize completions system
   autoload -U compinit && compinit
   ```

4. Restart your shell or source your `.zshrc`:

   ```bash
   source ~/.zshrc
   ```

### Fish

1. Create the completion directory if it doesn't exist:

   ```bash
   mkdir -p ~/.config/fish/completions
   ```

2. Generate the completion script:

   ```bash
   telert completions --shell fish --output-dir ~/.config/fish/completions
   ```

3. Fish automatically loads completions from this directory, so no further action is needed.

## What Completions Provide

With shell completions installed, you'll get:

- Tab-completion for all telert commands (`run`, `send`, `config`, etc.)
- Completion for command options (`--provider`, `--label`, etc.)
- Provider name suggestions when using `--provider` option
- Configuration option suggestions for each provider

## Quick Installation Script

For convenience, you can install all shell completions with a single command:

```bash
# For Bash
telert completions --shell bash --output-dir ~/.local/share/bash-completion/completions && \
echo 'source ~/.local/share/bash-completion/completions/telert' >> ~/.bashrc

# For Zsh
mkdir -p ~/.zsh/completions && \
telert completions --shell zsh --output-dir ~/.zsh/completions && \
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc && \
echo 'autoload -U compinit && compinit' >> ~/.zshrc

# For Fish
mkdir -p ~/.config/fish/completions && \
telert completions --shell fish --output-dir ~/.config/fish/completions
```

## Using the Pre-packaged Completions

Instead of generating the completions, you can also use the pre-packaged completion scripts in the telert repository:

```bash
# Clone the repository
git clone https://github.com/navig-me/telert.git
cd telert

# Install completions for your shell
cp packaging/completions/telert.bash ~/.local/share/bash-completion/completions/telert
cp packaging/completions/telert.zsh ~/.zsh/completions/_telert
cp packaging/completions/telert.fish ~/.config/fish/completions/telert.fish

# Or use the provided installation script
bash packaging/completions/install-completions.sh
```