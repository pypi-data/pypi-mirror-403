"""Task operations for Frappe CRM."""

from typing import Annotated, Any, Callable

from fastmcp import FastMCP

from frappe_crm_mcp.client import FrappeClient


def register(mcp: FastMCP, get_client: Callable[[], FrappeClient]) -> None:
    """Register task tools with the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def tasks_list(
        reference_doctype: Annotated[
            str | None, "Filter by parent type (CRM Deal or CRM Lead)"
        ] = None,
        reference_name: Annotated[str | None, "Filter by parent document ID"] = None,
        status: Annotated[str | None, "Filter by status (Open, Completed)"] = None,
        assigned_to: Annotated[str | None, "Filter by assignee email"] = None,
        limit: Annotated[int, "Maximum number of tasks to return"] = 20,
    ) -> list[dict[str, Any]]:
        """List CRM tasks with optional filtering.

        Get tasks for a specific deal/lead or filter by status/assignee.
        """
        client = get_client()
        filters: dict[str, Any] = {}
        if reference_doctype:
            filters["reference_doctype"] = reference_doctype
        if reference_name:
            filters["reference_docname"] = reference_name
        if status:
            filters["status"] = status
        if assigned_to:
            filters["assigned_to"] = assigned_to

        return await client.get_list(
            "CRM Task",
            filters=filters or None,
            fields=[
                "name",
                "title",
                "description",
                "status",
                "priority",
                "due_date",
                "assigned_to",
                "reference_doctype",
                "reference_docname",
                "modified",
            ],
            order_by="due_date asc",
            limit=limit,
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    async def tasks_get(
        name: Annotated[str, "The task ID"],
    ) -> dict[str, Any]:
        """Get a single task by ID.

        Returns full task details.
        """
        client = get_client()
        return await client.get_doc("CRM Task", name)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def tasks_add(
        title: Annotated[str, "Task title"],
        reference_doctype: Annotated[
            str | None, "Parent document type (CRM Deal or CRM Lead)"
        ] = None,
        reference_name: Annotated[str | None, "Parent document ID"] = None,
        description: Annotated[str | None, "Task description"] = None,
        due_date: Annotated[str | None, "Due date (YYYY-MM-DD)"] = None,
        assigned_to: Annotated[str | None, "Assignee email address"] = None,
        priority: Annotated[str, "Priority level (Low, Medium, High)"] = "Medium",
    ) -> dict[str, Any]:
        """Create a new task.

        Create a task optionally linked to a deal or lead.
        Returns the created task.
        """
        client = get_client()
        data: dict[str, Any] = {
            "title": title,
            "priority": priority,
            "status": "Open",
        }

        optional = {
            "reference_doctype": reference_doctype,
            "reference_docname": reference_name,
            "description": description,
            "due_date": due_date,
            "assigned_to": assigned_to,
        }
        data.update({k: v for k, v in optional.items() if v})

        return await client.create_doc("CRM Task", data)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def tasks_update(
        name: Annotated[str, "The task ID to update"],
        status: Annotated[str | None, "New status (Open, Completed)"] = None,
        title: Annotated[str | None, "New title"] = None,
        description: Annotated[str | None, "New description"] = None,
        due_date: Annotated[str | None, "New due date (YYYY-MM-DD)"] = None,
        priority: Annotated[str | None, "New priority (Low, Medium, High)"] = None,
    ) -> dict[str, Any]:
        """Update a task.

        Mark as completed, change due date, or update other fields.
        Returns the updated task.
        """
        client = get_client()
        data = {
            k: v
            for k, v in {
                "status": status,
                "title": title,
                "description": description,
                "due_date": due_date,
                "priority": priority,
            }.items()
            if v is not None
        }

        if not data:
            return await client.get_doc("CRM Task", name)

        return await client.update_doc("CRM Task", name, data)
