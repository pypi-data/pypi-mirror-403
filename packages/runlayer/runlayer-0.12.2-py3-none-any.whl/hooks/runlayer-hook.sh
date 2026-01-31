#!/bin/bash
# Runlayer Cursor Hook - MCP execution validation
#
# This script is installed by: runlayer setup hooks --client cursor --install --secret <key> --host <url>
# Placeholders are replaced during installation.
#
# Supported hooks:
# - beforeMCPExecution (MCP traffic validation)
#
# Security: This hook uses fail-closed behavior. If any error occurs
# (network failure, invalid response, etc.), MCP execution is blocked.

set -euo pipefail

# Configuration (replaced during installation)
RUNLAYER_API_KEY="__RUNLAYER_API_KEY__"
RUNLAYER_API_HOST="__RUNLAYER_API_HOST__"

# Fail-closed: Return deny response for any error
deny_response() {
  local message="${1:-Hook failed - MCP blocked for security}"
  echo "{\"permission\":\"deny\",\"user_message\":\"${message}\"}"
  exit 0
}

# Read input from stdin
input=$(cat) || deny_response "Failed to read hook input"

# Extract hook type
hook_type=$(echo "$input" | jq -r '.hook_event_name // empty') || deny_response "Failed to parse hook input"

case "$hook_type" in
  beforeMCPExecution)
    # Transform tool_input if it's an object (Cursor sends object, backend expects string)
    if echo "$input" | jq -e '.tool_input | type == "object"' > /dev/null 2>&1; then
      input=$(echo "$input" | jq '.tool_input = (.tool_input | tojson)') || deny_response "Failed to transform tool_input"
    fi

    # Make API request with fail-closed error handling
    # Use -f to fail on HTTP errors, -s for silent, --max-time for timeout
    response=$(curl -sf --max-time 30 -X POST "${RUNLAYER_API_HOST}/api/v1/hooks/cursor" \
      -H "Content-Type: application/json" \
      -H "x-runlayer-api-key: ${RUNLAYER_API_KEY}" \
      -d "$input" 2>/dev/null) || deny_response "Failed to contact Runlayer API"

    # Validate response is valid JSON with permission field (null is valid - means "no opinion")
    if ! echo "$response" | jq -e 'has("permission")' > /dev/null 2>&1; then
      deny_response "Invalid response from Runlayer API"
    fi

    echo "$response"
    ;;
  *)
    # Unknown hook types pass through (no blocking)
    echo "{}"
    ;;
esac
