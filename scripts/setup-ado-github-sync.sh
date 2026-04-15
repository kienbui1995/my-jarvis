#!/usr/bin/env bash
set -euo pipefail

# One-time setup: Create ADO pipeline variable group with GitHub credentials.
# Usage: ADO_PAT=your_ado_pat ./scripts/setup-ado-github-sync.sh
#
# You need an ADO Personal Access Token with scope: Build (Read & Execute), Variable Groups (Read, Create & Manage)
# Create at: https://dev.azure.com/taureauai/_usersSettings/tokens

ADO_ORG="taureauai"
ADO_PROJECT="POC"
ADO_API="https://dev.azure.com/${ADO_ORG}/${ADO_PROJECT}/_apis"

if [[ -z "${ADO_PAT:-}" ]]; then
    echo "❌ Set ADO_PAT environment variable first:"
    echo "   ADO_PAT=your_ado_pat ./scripts/setup-ado-github-sync.sh"
    exit 1
fi

AUTH=$(echo -n ":${ADO_PAT}" | base64)

echo "Creating variable group 'github-sync'..."
curl -s -X POST \
  -H "Authorization: Basic ${AUTH}" \
  -H "Content-Type: application/json" \
  "${ADO_API}/distributedtask/variablegroups?api-version=7.0" \
  -d '{
    "name": "github-sync",
    "description": "GitHub sync credentials for community edition",
    "type": "Vsts",
    "variables": {
      "GITHUB_PAT": {
        "value": "'"${GITHUB_PAT}"'",
        "isSecret": true
      },
      "GITHUB_REPO": {
        "value": "kienbui1995/my-jarvis",
        "isSecret": false
      }
    }
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'✅ Variable group created: id={d.get(\"id\",\"?\")}') if 'id' in d else print(f'❌ Error: {d}')"

echo ""
echo "Next: Add 'group: github-sync' to azure-pipelines.yml variables section."
echo "Or set variables directly in pipeline UI: ADO → Pipelines → my-jarvis → Edit → Variables"
