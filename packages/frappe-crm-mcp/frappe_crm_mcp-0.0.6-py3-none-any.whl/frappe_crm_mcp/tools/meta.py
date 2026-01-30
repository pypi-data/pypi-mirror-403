"""Metadata and field options for Frappe CRM."""

from typing import Annotated, Any, Callable

from fastmcp import FastMCP

from frappe_crm_mcp.client import FrappeClient


def register(mcp: FastMCP, get_client: Callable[[], FrappeClient]) -> None:
    """Register metadata tools with the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    async def get_field_options(
        doctype: Annotated[
            str,
            "The CRM doctype name. Examples: 'CRM Lead', 'CRM Deal', 'Contact', 'CRM Organization'",
        ],
        fieldname: Annotated[
            str,
            "The field name to get options for. Examples: 'source', 'status', 'territory', 'industry', 'no_of_employees'",
        ],
    ) -> dict[str, Any]:
        """Get available options for a constrained field (Link or Select type).

        Use this tool when you need to know what values are allowed for a field
        before creating or updating a record. This is essential for fields like:

        **Common Link fields** (reference another doctype):
        - source: Lead/deal source (e.g., "Website", "Referral", "Cold Call")
        - status: Pipeline status (use deal_statuses_list or lead_statuses_list for more details)
        - territory: Sales territory
        - industry: Industry/sector
        - salutation: Title (Mr, Ms, Dr, etc.)
        - gender: Gender options
        - currency: Currency codes
        - communication_status: Communication tracking status
        - lost_reason: Reasons for lost deals

        **Common Select fields** (predefined options):
        - no_of_employees: Company size ranges ("1-10", "11-50", "51-200", etc.)
        - sla_status: SLA status values

        Returns a dict with:
        - fieldtype: "Link" or "Select"
        - linked_doctype: (for Link fields) the doctype being referenced
        - options: list of available values with 'name' (and additional fields for Link types)

        Example usage:
        - get_field_options("CRM Lead", "source") -> returns all lead sources
        - get_field_options("CRM Deal", "territory") -> returns all territories
        - get_field_options("CRM Lead", "no_of_employees") -> returns size ranges
        """
        client = get_client()
        doctype_meta = await client.call_method(
            "frappe.client.get",
            doctype="DocType",
            name=doctype,
        )

        if not doctype_meta:
            return {"error": f"Doctype '{doctype}' not found"}

        # Find the field in the doctype definition
        fields = doctype_meta.get("fields", [])
        field = next(
            (f for f in fields if f.get("fieldname") == fieldname),
            None,
        )

        if not field:
            # List available fields to help the user
            available = [f.get("fieldname") for f in fields if f.get("fieldname")]
            return {
                "error": f"Field '{fieldname}' not found in {doctype}",
                "available_fields": sorted(available),
            }

        fieldtype = field.get("fieldtype")
        options = field.get("options")

        if fieldtype == "Link" and options:
            try:
                docs = await client.get_list(
                    options,
                    fields=["name"],
                    order_by="name asc",
                    limit=200,
                )
                return {
                    "fieldtype": "Link",
                    "linked_doctype": options,
                    "options": docs,
                }
            except Exception as e:
                return {
                    "error": f"Failed to fetch options from {options}: {str(e)}",
                    "fieldtype": "Link",
                    "linked_doctype": options,
                }

        if fieldtype == "Select" and options:
            option_list = [opt.strip() for opt in options.split("\n") if opt.strip()]
            return {
                "fieldtype": "Select",
                "options": [{"name": opt} for opt in option_list],
            }

        return {
            "error": f"Field '{fieldname}' is type '{fieldtype}' which doesn't have constrained options",
            "fieldtype": fieldtype,
            "hint": "This field accepts free-form text input",
        }
