from __future__ import annotations

import json
from pathlib import Path


def _wrapper_command(stem: str, workspace_root: Path) -> list[str]:
    return ["bash", str(workspace_root / "scripts" / "ai" / "mcp" / f"{stem}.sh")]


def _canonical_servers(workspace_root: Path) -> dict[str, list[str]]:
    return {
        "memory": ["npx", "-y", "@modelcontextprotocol/server-memory"],
        "filesystem": ["npx", "-y", "@modelcontextprotocol/server-filesystem", str(workspace_root)],
        "fetch": ["npx", "-y", "@modelcontextprotocol/server-fetch"],
        "github": ["npx", "-y", "@modelcontextprotocol/server-github"],
        "docker": ["npx", "-y", "@docker/mcp-server"],
        "context7": ["npx", "-y", "@upstash/context7-mcp"],
        "prometheus": ["npx", "-y", "@prometheus/mcp"],
        "grafana": ["npx", "-y", "@grafana/mcp-server"],
        "brave-search": ["npx", "-y", "@brave/search-mcp-server"],
        "sonarqube": ["npx", "-y", "sonarqube-mcp-server"],
        "neo4j-cypher": ["npx", "-y", "@neo4j/mcp-cypher"],
        "neo4j-memory": ["npx", "-y", "@neo4j/mcp-memory"],
        "chembl": ["npx", "-y", "chembl-mcp"],
        "pubchem": ["npx", "-y", "pubchem-mcp"],
        "pubmed": ["npx", "-y", "pubmed-mcp"],
        "mermaid": ["npx", "-y", "@mermaid-js/mermaid-mcp-server"],
        "ast-grep": _wrapper_command("mcp_ast_grep_wrapper", workspace_root),
        "mcp-code-interpreter": _wrapper_command("mcp_code_interpreter_wrapper", workspace_root),
    }


def _render_config(workspace_root: Path) -> dict[str, dict[str, dict[str, list[str]]]]:
    servers = {name: {"command": cmd[0], "args": cmd[1:]} for name, cmd in _canonical_servers(workspace_root).items()}
    return {"mcpServers": servers}


def generate_all(workspace_root: Path) -> None:
    payload = _render_config(workspace_root)
    for rel_path in (".mcp.json", ".vscode/mcp.json", ".gemini/settings.json"):
        target = workspace_root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    generate_all(Path.cwd())
