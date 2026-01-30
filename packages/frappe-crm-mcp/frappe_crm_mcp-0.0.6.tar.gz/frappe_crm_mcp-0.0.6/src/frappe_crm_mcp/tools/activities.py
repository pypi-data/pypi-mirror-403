"""Activity operations for Frappe CRM."""

from typing import Annotated, Any, Callable

from fastmcp import FastMCP

from frappe_crm_mcp.client import FrappeClient


def register(mcp: FastMCP, get_client: Callable[[], FrappeClient]) -> None:
    """Register activity tools with the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def activities_get(
        name: Annotated[str, "The deal or lead ID to get activities for"],
    ) -> dict[str, Any]:
        """Get the activity timeline for a deal or lead.

        Returns a comprehensive timeline including:
        - Document changes (field updates, status changes)
        - Notes
        - Tasks
        - Call logs
        - Comments
        - Attachments

        This is the "what's going on" view for any deal or lead.
        """
        client = get_client()
        result = await client.call_method(
            "crm.api.activities.get_activities",
            name=name,
        )

        # The API returns a tuple: (activities, calls, notes, tasks, attachments)
        if isinstance(result, (list, tuple)) and len(result) >= 5:
            return {
                "activities": result[0],
                "calls": result[1],
                "notes": result[2],
                "tasks": result[3],
                "attachments": result[4],
            }

        return {"raw": result}
