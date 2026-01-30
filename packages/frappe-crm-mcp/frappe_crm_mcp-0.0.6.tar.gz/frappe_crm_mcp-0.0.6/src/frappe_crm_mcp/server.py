"""Frappe CRM MCP Server - main entry point."""

from fastmcp import FastMCP

from frappe_crm_mcp.client import get_client
from frappe_crm_mcp.tools import (
    activities,
    contacts,
    deals,
    leads,
    meta,
    notes,
    organizations,
    statuses,
    tasks,
)

# Create the MCP server
mcp = FastMCP(name="Frappe CRM")

# Register all tools
for module in [
    deals,
    leads,
    contacts,
    organizations,
    notes,
    tasks,
    activities,
    statuses,
    meta,
]:
    module.register(mcp, get_client)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
