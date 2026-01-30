"""Deal operations for Frappe CRM."""

from typing import Annotated, Any, Callable

from fastmcp import FastMCP

from frappe_crm_mcp.client import FrappeClient


def register(mcp: FastMCP, get_client: Callable[[], FrappeClient]) -> None:
    """Register deal tools with the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def deals_list(
        status: Annotated[
            str | None, "Filter by status (e.g., Open, Won, Lost)"
        ] = None,
        organization: Annotated[str | None, "Filter by organization name"] = None,
        limit: Annotated[int, "Maximum number of deals to return"] = 20,
    ) -> list[dict[str, Any]]:
        """List CRM deals with optional filtering.

        Returns a list of deals from the CRM. Use filters to narrow down results.
        """
        client = get_client()
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = status
        if organization:
            filters["organization"] = ["like", f"%{organization}%"]

        return await client.get_list(
            "CRM Deal",
            filters=filters or None,
            fields=[
                "name",
                "organization",
                "status",
                "deal_value",
                "currency",
                "expected_closure_date",
                "closed_date",
                "probability",
                "modified",
            ],
            order_by="modified desc",
            limit=limit,
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    async def deals_get(
        name: Annotated[str, "The deal ID (e.g., CRM-DEAL-2024-00001)"],
    ) -> dict[str, Any]:
        """Get a single deal by its ID.

        Returns all fields for the specified deal including contacts,
        organization details, and deal value information.
        """
        client = get_client()
        return await client.get_doc("CRM Deal", name)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def deals_update(
        name: Annotated[str, "The deal ID to update"],
        status: Annotated[str | None, "New status (e.g., Open, Won, Lost)"] = None,
        deal_value: Annotated[float | None, "Deal value amount"] = None,
        expected_deal_value: Annotated[
            float | None, "Expected deal value for forecasting"
        ] = None,
        probability: Annotated[int | None, "Win probability percentage (0-100)"] = None,
        expected_closure_date: Annotated[
            str | None, "Expected closure date (YYYY-MM-DD)"
        ] = None,
        closed_date: Annotated[str | None, "Actual closure date (YYYY-MM-DD)"] = None,
    ) -> dict[str, Any]:
        """Update a deal's fields.

        Only provided fields will be updated. Returns the updated deal.
        """
        client = get_client()
        data = {
            k: v
            for k, v in {
                "status": status,
                "deal_value": deal_value,
                "expected_deal_value": expected_deal_value,
                "probability": probability,
                "expected_closure_date": expected_closure_date,
                "closed_date": closed_date,
            }.items()
            if v is not None
        }

        if not data:
            return await client.get_doc("CRM Deal", name)

        return await client.update_doc("CRM Deal", name, data)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def deals_create(
        organization: Annotated[str, "Organization name for the deal"],
        deal_value: Annotated[float | None, "Deal value amount"] = None,
        status: Annotated[str, "Deal status"] = "Open",
        probability: Annotated[int, "Win probability percentage (0-100)"] = 50,
        currency: Annotated[str, "Currency code (e.g., USD, EUR)"] = "USD",
    ) -> dict[str, Any]:
        """Create a new deal.

        Returns the created deal with its generated ID.
        """
        client = get_client()
        data: dict[str, Any] = {
            "organization": organization,
            "status": status,
            "probability": probability,
            "currency": currency,
        }

        if deal_value is not None:
            data["deal_value"] = deal_value

        return await client.create_doc("CRM Deal", data)

    @mcp.tool(annotations={"readOnlyHint": True})
    async def deals_get_contacts(
        name: Annotated[str, "The deal ID"],
    ) -> Any:
        """Get all contacts linked to a deal.

        Returns contacts with their details and primary status.
        """
        client = get_client()
        return await client.call_method(
            "crm.fcrm.doctype.crm_deal.api.get_deal_contacts",
            name=name,
        )

    @mcp.tool(annotations={"readOnlyHint": False})
    async def deals_add_contact(
        deal: Annotated[str, "The deal ID"],
        contact: Annotated[str, "The contact ID to link"],
    ) -> bool:
        """Link a contact to a deal.

        Adds a contact to the deal's contacts list. Returns True on success.
        """
        client = get_client()
        return await client.call_method(
            "crm.fcrm.doctype.crm_deal.crm_deal.add_contact",
            deal=deal,
            contact=contact,
        )

    @mcp.tool(annotations={"readOnlyHint": False})
    async def deals_remove_contact(
        deal: Annotated[str, "The deal ID"],
        contact: Annotated[str, "The contact ID to unlink"],
    ) -> bool:
        """Unlink a contact from a deal.

        Removes a contact from the deal's contacts list. Returns True on success.
        """
        client = get_client()
        return await client.call_method(
            "crm.fcrm.doctype.crm_deal.crm_deal.remove_contact",
            deal=deal,
            contact=contact,
        )

    @mcp.tool(annotations={"readOnlyHint": False})
    async def deals_set_primary_contact(
        deal: Annotated[str, "The deal ID"],
        contact: Annotated[str, "The contact ID to set as primary"],
    ) -> bool:
        """Set a contact as the primary contact for a deal.

        The contact must already be linked to the deal. Returns True on success.
        """
        client = get_client()
        return await client.call_method(
            "crm.fcrm.doctype.crm_deal.crm_deal.set_primary_contact",
            deal=deal,
            contact=contact,
        )
