from scripts.ai.codex.setup_mcp import _canonical_servers

REMOVED_MCP_SERVERS = {
    "sequential-thinking",
    "openaiDeveloperDocs",
    "needle",
    "docker-docs",
    "dockerhub",
    "pdf",
    "paper-search",
}

EXPECTED_MCP_SERVERS = {
    "memory","filesystem","fetch","github","docker","context7",
    "prometheus","grafana","brave-search","sonarqube",
    "neo4j-cypher","neo4j-memory",
    "chembl","pubchem","pubmed",
    "mermaid","ast-grep","mcp-code-interpreter"
}

WRAPPER_SCRIPT_STEMS = {
    "ast-grep": "mcp_ast_grep_wrapper",
    "mcp-code-interpreter": "mcp_code_interpreter_wrapper",
}


def test_expected_mcp_servers_present(tmp_path):
    servers = _canonical_servers(tmp_path)
    assert set(servers) == EXPECTED_MCP_SERVERS


def test_wrapper_script_stems(tmp_path):
    servers = _canonical_servers(tmp_path)
    for name, stem in WRAPPER_SCRIPT_STEMS.items():
        cmd = servers[name]
        assert stem in cmd[-1]


def test_removed_mcp_servers_absent(tmp_path):
    servers = _canonical_servers(tmp_path)
    assert REMOVED_MCP_SERVERS.isdisjoint(set(servers))
