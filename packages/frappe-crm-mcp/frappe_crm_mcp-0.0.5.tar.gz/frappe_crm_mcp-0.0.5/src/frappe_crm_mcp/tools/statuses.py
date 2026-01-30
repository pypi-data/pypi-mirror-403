"""Status management for Frappe CRM pipelines."""

from typing import Annotated, Any, Callable

from fastmcp import FastMCP

from frappe_crm_mcp.client import FrappeClient

COLORS = "black, gray, blue, green, red, pink, orange, amber, yellow, cyan, teal, violet, purple"
DEAL_TYPES = "Open, Ongoing, On Hold, Won, Lost"


def register(mcp: FastMCP, get_client: Callable[[], FrappeClient]) -> None:
    """Register status management tools with the MCP server."""

    # Deal Statuses

    @mcp.tool(annotations={"readOnlyHint": True})
    async def deal_statuses_list() -> list[dict[str, Any]]:
        """List all deal statuses in the pipeline.

        Returns statuses with their type, position, probability, and color.
        """
        client = get_client()
        return await client.get_list(
            "CRM Deal Status",
            fields=["name", "type", "position", "probability", "color"],
            order_by="position asc",
            limit=100,
        )

    @mcp.tool(annotations={"readOnlyHint": False})
    async def deal_statuses_create(
        status: Annotated[str, "Status name (e.g., 'Qualification', 'Proposal')"],
        type: Annotated[str, f"Status type: {DEAL_TYPES}"] = "Open",
        position: Annotated[int, "Position in pipeline (lower = earlier)"] = 1,
        probability: Annotated[int, "Default win probability percentage (0-100)"] = 0,
        color: Annotated[str, f"Color for UI: {COLORS}"] = "gray",
    ) -> dict[str, Any]:
        """Create a new deal status for the pipeline.

        Returns the created status.
        """
        client = get_client()
        return await client.create_doc(
            "CRM Deal Status",
            {
                "deal_status": status,
                "type": type,
                "position": position,
                "probability": probability,
                "color": color,
            },
        )

    @mcp.tool(annotations={"readOnlyHint": False})
    async def deal_statuses_update(
        name: Annotated[str, "The status name to update"],
        type: Annotated[str | None, f"Status type: {DEAL_TYPES}"] = None,
        position: Annotated[int | None, "Position in pipeline"] = None,
        probability: Annotated[int | None, "Default win probability (0-100)"] = None,
        color: Annotated[str | None, f"Color: {COLORS}"] = None,
    ) -> dict[str, Any]:
        """Update a deal status.

        Only provided fields will be updated.
        """
        client = get_client()
        data = {
            k: v
            for k, v in {
                "type": type,
                "position": position,
                "probability": probability,
                "color": color,
            }.items()
            if v is not None
        }

        if not data:
            return await client.get_doc("CRM Deal Status", name)

        return await client.update_doc("CRM Deal Status", name, data)

    # Lead Statuses

    @mcp.tool(annotations={"readOnlyHint": True})
    async def lead_statuses_list() -> list[dict[str, Any]]:
        """List all lead statuses in the pipeline.

        Returns statuses with their position and color.
        """
        client = get_client()
        return await client.get_list(
            "CRM Lead Status",
            fields=["name", "position", "color"],
            order_by="position asc",
            limit=100,
        )

    @mcp.tool(annotations={"readOnlyHint": False})
    async def lead_statuses_create(
        status: Annotated[str, "Status name (e.g., 'New', 'Contacted', 'Qualified')"],
        position: Annotated[int, "Position in pipeline (lower = earlier)"] = 1,
        color: Annotated[str, f"Color for UI: {COLORS}"] = "gray",
    ) -> dict[str, Any]:
        """Create a new lead status for the pipeline.

        Returns the created status.
        """
        client = get_client()
        return await client.create_doc(
            "CRM Lead Status",
            {
                "lead_status": status,
                "position": position,
                "color": color,
            },
        )

    @mcp.tool(annotations={"readOnlyHint": False})
    async def lead_statuses_update(
        name: Annotated[str, "The status name to update"],
        position: Annotated[int | None, "Position in pipeline"] = None,
        color: Annotated[str | None, f"Color: {COLORS}"] = None,
    ) -> dict[str, Any]:
        """Update a lead status.

        Only provided fields will be updated.
        """
        client = get_client()
        data = {
            k: v
            for k, v in {
                "position": position,
                "color": color,
            }.items()
            if v is not None
        }

        if not data:
            return await client.get_doc("CRM Lead Status", name)

        return await client.update_doc("CRM Lead Status", name, data)
