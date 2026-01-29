#!/bin/bash
# OpenWebUI Bootstrap Verification Script
#
# This script is used for debugging the openwebui-bootstrap tool.
# It copies the original blank database (webui.db) from the resources directory
# to /tmp and runs the bootstrap tool on it with debug logging enabled.
#
# The webui.db file is an original blank database created by Open WebUI,
# serving as a template to test correct functionality. This allows for
# isolated testing without affecting the production database.
#
# YOU MUST NOT USE THIS WITH DRY-RUN IN ORDER TO TRACK ISSUES DOWN. THE DATABASE WILL BE RESTORED UPON EACH CALL!
#
# Usage:
#   ./verify-bootstrap.sh [options]
#
# Options:
#   --reset          Reset database before applying configuration
#   --dry-run        Dry run mode - test without making changes
#   Any other options will be forwarded to openwebui-bootstrap
#
# The script will always set --log-level to debug for detailed debugging output.

# Exit on error
set -e

# Copy database file to /tmp (force overwrite if it exists)
echo "Copying webui-0.7.2.db to /tmp..."
cp -f "$(dirname "$0")/webui-0.7.2.db" /tmp/webui.db

# Parse command line arguments
# We need to handle --log-level specially (always override to debug)
# and forward all other arguments

# Initialize arrays for arguments
declare -a other_args=()

# Process arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --log-level)
            # Skip log-level argument and its value since we override it
            shift 2
            ;;
        --log-level=*)
            # Skip log-level with embedded value
            shift
            ;;
        *)
            # Forward all other arguments
            other_args+=("$1")
            shift
            ;;
    esac
done

# Run openwebui-bootstrap with debug logging
echo "Running openwebui-bootstrap with debug logging..."
echo "Config: $(dirname "$0")/openwebui-config.yaml"
echo "Database: /tmp/webui.db"
echo "Additional arguments: ${other_args[*]}"

uv run openwebui-bootstrap \
    --config "$(dirname "$0")/openwebui-config.yaml" \
    --database-path /tmp/webui.db \
    --log-level debug \
    "${other_args[@]}"
