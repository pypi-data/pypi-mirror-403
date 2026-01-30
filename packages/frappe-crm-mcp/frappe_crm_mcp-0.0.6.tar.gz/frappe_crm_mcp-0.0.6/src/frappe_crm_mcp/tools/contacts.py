"""Contact operations for Frappe CRM."""

from typing import Annotated, Any, Callable

from fastmcp import FastMCP

from frappe_crm_mcp.client import FrappeClient


def register(mcp: FastMCP, get_client: Callable[[], FrappeClient]) -> None:
    """Register contact tools with the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def contacts_search(
        query: Annotated[str | None, "Search by name or email"] = None,
        organization: Annotated[str | None, "Filter by organization/company"] = None,
        limit: Annotated[int, "Maximum number of contacts to return"] = 20,
    ) -> list[dict[str, Any]]:
        """Search for contacts.

        Search contacts by name, email, or filter by organization.
        """
        client = get_client()
        filters: dict[str, Any] = {}
        if query:
            filters["full_name"] = ["like", f"%{query}%"]
        if organization:
            filters["company_name"] = ["like", f"%{organization}%"]

        return await client.get_list(
            "Contact",
            filters=filters or None,
            fields=[
                "name",
                "full_name",
                "email_id",
                "mobile_no",
                "phone",
                "company_name",
                "modified",
            ],
            order_by="modified desc",
            limit=limit,
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    async def contacts_get(
        name: Annotated[str, "The contact ID"],
    ) -> dict[str, Any]:
        """Get a single contact by ID.

        Returns full contact details including all phone numbers and emails.
        """
        client = get_client()
        return await client.get_doc("Contact", name)

    @mcp.tool(annotations={"readOnlyHint": True})
    async def contacts_get_deals(
        contact: Annotated[str, "The contact ID"],
    ) -> Any:
        """Get all deals linked to a contact.

        Returns deals where this contact is involved.
        """
        client = get_client()
        return await client.call_method(
            "crm.api.contact.get_linked_deals",
            contact=contact,
        )

    @mcp.tool(annotations={"readOnlyHint": False})
    async def contacts_create(
        first_name: Annotated[str, "First name (required)"],
        last_name: Annotated[str | None, "Last name"] = None,
        email: Annotated[str | None, "Email address"] = None,
        phone: Annotated[str | None, "Phone number"] = None,
        mobile_no: Annotated[str | None, "Mobile number"] = None,
        company_name: Annotated[str | None, "Company/organization name"] = None,
        designation: Annotated[str | None, "Job title/designation"] = None,
        salutation: Annotated[str | None, "Salutation (Mr, Ms, Dr, etc.)"] = None,
    ) -> dict[str, Any]:
        """Create a new contact.

        Returns the created contact with its generated ID.
        """
        client = get_client()
        data: dict[str, Any] = {"first_name": first_name}

        optional = {
            "last_name": last_name,
            "company_name": company_name,
            "designation": designation,
            "salutation": salutation,
        }
        data.update({k: v for k, v in optional.items() if v is not None})

        # Email and phone are stored in child tables
        if email:
            data["email_ids"] = [{"email_id": email, "is_primary": 1}]
        if phone:
            data["phone_nos"] = [{"phone": phone, "is_primary_phone": 1}]
        if mobile_no:
            if "phone_nos" in data:
                data["phone_nos"].append(
                    {"phone": mobile_no, "is_primary_mobile_no": 1}
                )
            else:
                data["phone_nos"] = [{"phone": mobile_no, "is_primary_mobile_no": 1}]

        return await client.create_doc("Contact", data)

    @mcp.tool(annotations={"readOnlyHint": False})
    async def contacts_update(
        name: Annotated[str, "The contact ID to update"],
        first_name: Annotated[str | None, "First name"] = None,
        last_name: Annotated[str | None, "Last name"] = None,
        company_name: Annotated[str | None, "Company/organization name"] = None,
        designation: Annotated[str | None, "Job title/designation"] = None,
        salutation: Annotated[str | None, "Salutation (Mr, Ms, Dr, etc.)"] = None,
    ) -> dict[str, Any]:
        """Update a contact's fields.

        Only provided fields will be updated. Returns the updated contact.
        Note: To update email/phone, use the Frappe UI as they are stored in child tables.
        """
        client = get_client()
        data = {
            k: v
            for k, v in {
                "first_name": first_name,
                "last_name": last_name,
                "company_name": company_name,
                "designation": designation,
                "salutation": salutation,
            }.items()
            if v is not None
        }

        if not data:
            return await client.get_doc("Contact", name)

        return await client.update_doc("Contact", name, data)
