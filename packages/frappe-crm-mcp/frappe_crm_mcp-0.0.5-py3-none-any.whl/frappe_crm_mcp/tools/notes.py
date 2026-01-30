"""Note operations for Frappe CRM."""

from typing import Annotated, Any, Callable

from fastmcp import FastMCP

from frappe_crm_mcp.client import FrappeClient


def register(mcp: FastMCP, get_client: Callable[[], FrappeClient]) -> None:
    """Register note tools with the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def notes_list(
        reference_doctype: Annotated[
            str, "Parent document type (CRM Deal or CRM Lead)"
        ],
        reference_name: Annotated[str, "Parent document ID"],
        limit: Annotated[int, "Maximum number of notes to return"] = 20,
    ) -> list[dict[str, Any]]:
        """List notes attached to a deal or lead.

        Get all notes for a specific deal or lead.
        """
        client = get_client()
        filters = {
            "reference_doctype": reference_doctype,
            "reference_docname": reference_name,
        }

        return await client.get_list(
            "FCRM Note",
            filters=filters,
            fields=["name", "title", "content", "owner", "creation", "modified"],
            order_by="creation desc",
            limit=limit,
        )

    @mcp.tool(annotations={"readOnlyHint": False})
    async def notes_add(
        reference_doctype: Annotated[
            str, "Parent document type (CRM Deal or CRM Lead)"
        ],
        reference_name: Annotated[str, "Parent document ID"],
        title: Annotated[str, "Note title"],
        content: Annotated[str, "Note content (supports HTML)"],
    ) -> dict[str, Any]:
        """Add a note to a deal or lead.

        Creates a new note attached to the specified deal or lead.
        Returns the created note.
        """
        client = get_client()
        data = {
            "reference_doctype": reference_doctype,
            "reference_docname": reference_name,
            "title": title,
            "content": content,
        }

        return await client.create_doc("FCRM Note", data)
