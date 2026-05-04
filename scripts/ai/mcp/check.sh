#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CONFIG="${ROOT_DIR}/.mcp.json"

required=(
  memory filesystem fetch github docker context7
  prometheus grafana brave-search sonarqube
  neo4j-cypher neo4j-memory chembl pubchem pubmed
  mermaid ast-grep mcp-code-interpreter
)

for name in "${required[@]}"; do
  if ! jq -e --arg n "$name" '.mcpServers[$n]' "$CONFIG" >/dev/null; then
    echo "Missing MCP server: $name"
    exit 1
  fi
done

echo "MCP config check passed"
