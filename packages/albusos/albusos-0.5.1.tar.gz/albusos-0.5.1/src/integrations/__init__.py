"""Integrations - MCP servers for external services.

MCP servers provide tools like gmail.*, slack.*, etc.

Configure in albus.yaml:
    mcp_servers:
      - id: gmail
        command: python
        args: ["-m", "integrations.gmail.server"]

Use in pathways:
    ToolNode(tool="gmail.send_email", args={...})

Or give to agents:
    agent_builder().tool("gmail.*")
"""

__all__: list[str] = []
