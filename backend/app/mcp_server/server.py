from app.mcp_server.tools import MCP_TOOLS

MCP_TOOL_REGISTRY = {
    "server_name": "autonomous-fpa-mcp",
    "transport": "http-json",
    "security": "RBAC + audit log before tool execution",
    "tools": MCP_TOOLS,
}


def describe_mcp_server() -> dict:
    return MCP_TOOL_REGISTRY
