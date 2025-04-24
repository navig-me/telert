#!/usr/bin/env bash
# telert-wrapper.sh - A wrapper for telert that handles shell built-ins
# This wrapper automatically detects shell built-ins and wraps them in bash -c
# to make them work with telert run

set -e

# Shell built-ins and other special commands that need bash -c
SHELL_BUILTINS=(
  source .
  alias bg cd command declare eval exec exit export fg
  getopts hash history jobs kill let local mapfile popd pushd
  pwd read readarray set setopt shopt test trap type typeset ulimit unalias
  unset wait
)

function is_shell_builtin() {
  local cmd="$1"
  for builtin in "${SHELL_BUILTINS[@]}"; do
    if [[ "$builtin" == "$cmd" ]]; then
      return 0
    fi
  done
  return 1
}

# If no arguments, show help
if [[ $# -eq 0 ]]; then
  echo "telert-wrapper: A wrapper for telert that handles shell built-ins"
  echo "Usage: telert-wrapper [telert options] command [args...]"
  echo "Example: telert-wrapper run --message 'Done' source my_script.sh"
  exit 0
fi

# Find the command to run
cmd_start_index=0
for ((i=0; i<$#; i++)); do
  arg="${!i}"
  next_index=$((i+1))
  
  # If we find 'run', the next argument is the command
  if [[ "$arg" == "run" && $next_index -lt $# ]]; then
    cmd_start_index=$next_index
    break
  fi
done

# If we found a command 
if [[ $cmd_start_index -gt 0 ]]; then
  cmd="${!cmd_start_index}"
  
  # Check if it's a shell builtin
  if is_shell_builtin "$cmd"; then
    # Get all telert arguments before the command
    telert_args=()
    for ((i=0; i<$cmd_start_index; i++)); do
      telert_args+=("${!i}")
    done
    
    # Get the command and all arguments after it
    command_string=""
    for ((i=$cmd_start_index; i<=$#; i++)); do
      if [[ -n "$command_string" ]]; then
        command_string+=" "
      fi
      command_string+="${!i}"
    done
    
    # Run telert with bash -c to handle shell builtins
    telert "${telert_args[@]}" bash -c "$command_string"
  else
    # Not a builtin, just pass all arguments through to telert
    telert "$@"
  fi
else
  # No run command found, just pass everything through
  telert "$@"
fi