"""Organization operations for Frappe CRM."""

from typing import Annotated, Any, Callable

from fastmcp import FastMCP

from frappe_crm_mcp.client import FrappeClient


def register(mcp: FastMCP, get_client: Callable[[], FrappeClient]) -> None:
    """Register organization tools with the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def organizations_list(
        query: Annotated[str | None, "Search by organization name"] = None,
        industry: Annotated[str | None, "Filter by industry"] = None,
        limit: Annotated[int, "Maximum number of organizations to return"] = 20,
    ) -> list[dict[str, Any]]:
        """List organizations/companies in the CRM.

        Search by name or filter by industry.
        """
        client = get_client()
        filters: dict[str, Any] = {}
        if query:
            filters["organization_name"] = ["like", f"%{query}%"]
        if industry:
            filters["industry"] = industry

        return await client.get_list(
            "CRM Organization",
            filters=filters or None,
            fields=[
                "name",
                "organization_name",
                "industry",
                "website",
                "territory",
                "modified",
            ],
            order_by="modified desc",
            limit=limit,
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    async def organizations_get(
        name: Annotated[str, "The organization ID"],
    ) -> dict[str, Any]:
        """Get a single organization by ID.

        Returns full organization details including address and contacts.
        """
        client = get_client()
        return await client.get_doc("CRM Organization", name)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def organizations_create(
        organization_name: Annotated[str, "Organization/company name (required)"],
        website: Annotated[str | None, "Company website URL"] = None,
        industry: Annotated[str | None, "Industry type"] = None,
        territory: Annotated[str | None, "Territory/region"] = None,
        annual_revenue: Annotated[float | None, "Annual revenue amount"] = None,
        no_of_employees: Annotated[
            str | None,
            "Number of employees (1-10, 11-50, 51-200, 201-500, 501-1000, 1000+)",
        ] = None,
    ) -> dict[str, Any]:
        """Create a new organization/company.

        Returns the created organization with its generated ID.
        """
        client = get_client()
        data: dict[str, Any] = {"organization_name": organization_name}

        optional = {
            "website": website,
            "industry": industry,
            "territory": territory,
            "annual_revenue": annual_revenue,
            "no_of_employees": no_of_employees,
        }
        data.update({k: v for k, v in optional.items() if v is not None})

        return await client.create_doc("CRM Organization", data)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def organizations_update(
        name: Annotated[str, "The organization ID to update"],
        organization_name: Annotated[str | None, "New organization name"] = None,
        website: Annotated[str | None, "Company website URL"] = None,
        industry: Annotated[str | None, "Industry type"] = None,
        territory: Annotated[str | None, "Territory/region"] = None,
        annual_revenue: Annotated[float | None, "Annual revenue amount"] = None,
        no_of_employees: Annotated[
            str | None,
            "Number of employees (1-10, 11-50, 51-200, 201-500, 501-1000, 1000+)",
        ] = None,
    ) -> dict[str, Any]:
        """Update an organization's fields.

        Only provided fields will be updated. Returns the updated organization.
        """
        client = get_client()
        data = {
            k: v
            for k, v in {
                "organization_name": organization_name,
                "website": website,
                "industry": industry,
                "territory": territory,
                "annual_revenue": annual_revenue,
                "no_of_employees": no_of_employees,
            }.items()
            if v is not None
        }

        if not data:
            return await client.get_doc("CRM Organization", name)

        return await client.update_doc("CRM Organization", name, data)
