"""Lead operations for Frappe CRM."""

from typing import Annotated, Any, Callable

from fastmcp import FastMCP

from frappe_crm_mcp.client import FrappeClient


def register(mcp: FastMCP, get_client: Callable[[], FrappeClient]) -> None:
    """Register lead tools with the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def leads_list(
        status: Annotated[
            str | None, "Filter by status (e.g., Open, Qualified, Junk)"
        ] = None,
        source: Annotated[str | None, "Filter by lead source"] = None,
        limit: Annotated[int, "Maximum number of leads to return"] = 20,
    ) -> list[dict[str, Any]]:
        """List CRM leads with optional filtering.

        Returns a list of leads. Use status filter to find leads at specific stages.
        """
        client = get_client()
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if source:
            filters["source"] = source

        return await client.get_list(
            "CRM Lead",
            filters=filters or None,
            fields=[
                "name",
                "first_name",
                "last_name",
                "email",
                "mobile_no",
                "organization",
                "status",
                "source",
                "modified",
            ],
            order_by="modified desc",
            limit=limit,
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    async def leads_get(
        name: Annotated[str, "The lead ID (e.g., CRM-LEAD-2024-00001)"],
    ) -> dict[str, Any]:
        """Get a single lead by its ID.

        Returns all fields for the specified lead including contact
        information, organization, and status.
        """
        client = get_client()
        return await client.get_doc("CRM Lead", name)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def leads_update(
        name: Annotated[str, "The lead ID to update"],
        status: Annotated[
            str | None, "New status (e.g., Open, Qualified, Junk)"
        ] = None,
        first_name: Annotated[str | None, "First name"] = None,
        last_name: Annotated[str | None, "Last name"] = None,
        email: Annotated[str | None, "Email address"] = None,
        mobile_no: Annotated[str | None, "Mobile phone number"] = None,
        organization: Annotated[str | None, "Organization name"] = None,
    ) -> dict[str, Any]:
        """Update a lead's fields.

        Only provided fields will be updated. Returns the updated lead.
        """
        client = get_client()
        data = {
            k: v
            for k, v in {
                "status": status,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "mobile_no": mobile_no,
                "organization": organization,
            }.items()
            if v is not None
        }

        if not data:
            return await client.get_doc("CRM Lead", name)

        return await client.update_doc("CRM Lead", name, data)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def leads_create(
        first_name: Annotated[str, "First name (required)"],
        last_name: Annotated[str | None, "Last name"] = None,
        email: Annotated[str | None, "Email address"] = None,
        mobile_no: Annotated[str | None, "Mobile phone number"] = None,
        organization: Annotated[str | None, "Organization/company name"] = None,
        status: Annotated[str, "Lead status"] = "New",
        source: Annotated[str | None, "Lead source (e.g., Website, Referral)"] = None,
        job_title: Annotated[str | None, "Job title/designation"] = None,
    ) -> dict[str, Any]:
        """Create a new lead.

        Returns the created lead with its generated ID.
        """
        client = get_client()
        data: dict[str, Any] = {
            "first_name": first_name,
            "status": status,
        }

        optional = {
            "last_name": last_name,
            "email": email,
            "mobile_no": mobile_no,
            "organization": organization,
            "source": source,
            "job_title": job_title,
        }
        data.update({k: v for k, v in optional.items() if v is not None})

        return await client.create_doc("CRM Lead", data)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def leads_convert(
        name: Annotated[str, "The lead ID to convert to a deal"],
    ) -> Any:
        """Convert a qualified lead to a deal.

        This is a key workflow operation that:
        1. Marks the lead as converted
        2. Creates a new deal linked to the lead
        3. Creates/links contact and organization

        Returns the created deal information.
        """
        client = get_client()
        return await client.call_method(
            "crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal",
            lead=name,
        )
