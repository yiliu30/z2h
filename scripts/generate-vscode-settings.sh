#!/usr/bin/env bash
set -euo pipefail

# Generate VS Code settings snippet for chat.agentSkillsLocations and
# chat.instructionsFilesLocations.
# Scans the hub for all skill and instruction directories and outputs JSON
# ready to paste into settings.json.
#
# Usage:
#   ./scripts/generate-vscode-settings.sh
#   ./scripts/generate-vscode-settings.sh --hub-path ~/workspace/z2h

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_HUB_PATH="$(dirname "$SCRIPT_DIR")"

CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

# Parse args
HUB_PATH="$DEFAULT_HUB_PATH"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --hub-path) HUB_PATH="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 [--hub-path <path>]"
            echo "  Generates VS Code chat.agentSkillsLocations and"
            echo "  chat.instructionsFilesLocations settings snippet."
            echo "  --hub-path  Path to z2h repo (default: auto-detected)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Convert absolute path to ~/ relative
to_tilde_path() {
    echo "$1" | sed "s|^$HOME|~|"
}

# Collect all skill directories (folders that directly contain SKILL.md files)
skill_locations=()

if [ -d "$HUB_PATH/skills" ]; then
    skill_locations+=("$(to_tilde_path "$HUB_PATH/skills")")
fi

# Collect instruction directories
instruction_locations=()
if [ -d "$HUB_PATH/instructions" ]; then
    instruction_locations+=("$(to_tilde_path "$HUB_PATH/instructions")")
fi

# Generate JSON
echo ""
echo -e "${CYAN}Add the following to your VS Code settings.json:${NC}"
echo ""
echo -e "${GREEN}// --- z2h: skill search paths ---${NC}"
echo '"chat.agentSkillsLocations": {'

last_idx=$(( ${#skill_locations[@]} - 1 ))
for i in "${!skill_locations[@]}"; do
    if [ "$i" -eq "$last_idx" ]; then
        echo "    \"${skill_locations[$i]}\": true"
    else
        echo "    \"${skill_locations[$i]}\": true,"
    fi
done

echo '},'

echo -e "${GREEN}// --- z2h: instruction file paths ---${NC}"
echo '"chat.instructionsFilesLocations": {'

last_idx=$(( ${#instruction_locations[@]} - 1 ))
for i in "${!instruction_locations[@]}"; do
    if [ "$i" -eq "$last_idx" ]; then
        echo "    \"${instruction_locations[$i]}\": true"
    else
        echo "    \"${instruction_locations[$i]}\": true,"
    fi
done

echo '}'
echo ""
echo -e "${CYAN}Tip: Place this inside the top-level {} of your settings.json file.${NC}"
echo -e "${CYAN}     User settings:  Ctrl+Shift+P → 'Preferences: Open User Settings (JSON)'${NC}"
echo -e "${CYAN}     Workspace:      .vscode/settings.json${NC}"
