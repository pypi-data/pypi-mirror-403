# Frappe CRM MCP Server

[![PyPI Version](https://img.shields.io/pypi/v/frappe-crm-mcp.svg)](https://pypi.org/project/frappe-crm-mcp/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/frappe-crm-mcp?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/frappe-crm-mcp)
[![License](https://img.shields.io/pypi/l/frappe-crm-mcp.svg)](https://github.com/joehaddad2000/frappe-crm-mcp/blob/main/LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/frappe-crm-mcp.svg)](https://pypi.org/project/frappe-crm-mcp/)

Connect your AI tools to [Frappe CRM](https://frappe.io/crm) using the [Model Context Protocol](https://modelcontextprotocol.io/).

Once connected, your AI assistants can interact with your CRM data:

- "Show me all open deals"
- "Create a lead for John at Acme Corp"
- "What's happening with the Tesla deal?"
- "Add a note to the Stripe deal about our call today"

## Prerequisites

1. A Frappe CRM instance (cloud or self-hosted)
2. API credentials (see [Generate API Keys](#generate-api-keys))
3. Python 3.11+ and [uv](https://docs.astral.sh/uv/) (for local installation)

## Installation

### Claude Code

```bash
claude mcp add frappe-crm \
  -e FRAPPE_URL=https://your-site.frappe.cloud \
  -e FRAPPE_API_KEY=your_api_key \
  -e FRAPPE_API_SECRET=your_api_secret \
  -- uvx frappe-crm-mcp
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "frappe-crm": {
      "command": "uvx",
      "args": ["frappe-crm-mcp"],
      "env": {
        "FRAPPE_URL": "https://your-site.frappe.cloud",
        "FRAPPE_API_KEY": "your_api_key",
        "FRAPPE_API_SECRET": "your_api_secret"
      }
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "frappe-crm": {
      "command": "uvx",
      "args": ["frappe-crm-mcp"],
      "env": {
        "FRAPPE_URL": "https://your-site.frappe.cloud",
        "FRAPPE_API_KEY": "your_api_key",
        "FRAPPE_API_SECRET": "your_api_secret"
      }
    }
  }
}
```

### Windsurf

Add to your Windsurf MCP config:

```json
{
  "mcpServers": {
    "frappe-crm": {
      "command": "uvx",
      "args": ["frappe-crm-mcp"],
      "env": {
        "FRAPPE_URL": "https://your-site.frappe.cloud",
        "FRAPPE_API_KEY": "your_api_key",
        "FRAPPE_API_SECRET": "your_api_secret"
      }
    }
  }
}
```

## Generate API Keys

1. Log into your Frappe CRM instance
2. Go to **User** → your user → **API Access**
3. Click **Generate Keys**
4. Copy the **API Key** and **API Secret** (secret is only shown once)

## Available Tools

| Tool | Description |
|------|-------------|
| `deals_list` | List deals with optional filters |
| `deals_get` | Get a single deal by ID |
| `deals_create` | Create a new deal |
| `deals_update` | Update deal fields |
| `deals_get_contacts` | Get contacts linked to a deal |
| `deals_add_contact` | Link a contact to a deal |
| `deals_remove_contact` | Unlink a contact from a deal |
| `deals_set_primary_contact` | Set a deal's primary contact |
| `leads_list` | List leads with optional filters |
| `leads_get` | Get a single lead by ID |
| `leads_create` | Create a new lead |
| `leads_update` | Update lead fields |
| `leads_convert` | Convert a lead to a deal |
| `contacts_search` | Search contacts by name or email |
| `contacts_get` | Get a single contact by ID |
| `contacts_create` | Create a new contact |
| `contacts_update` | Update contact fields |
| `contacts_get_deals` | Get deals linked to a contact |
| `organizations_list` | List organizations |
| `organizations_get` | Get a single organization by ID |
| `organizations_create` | Create a new organization |
| `organizations_update` | Update organization fields |
| `notes_list` | List notes on a deal or lead |
| `notes_add` | Add a note to a deal or lead |
| `tasks_list` | List tasks with optional filters |
| `tasks_get` | Get a single task by ID |
| `tasks_add` | Create a new task |
| `tasks_update` | Update task fields |
| `activities_get` | Get activity timeline for a deal or lead |
| `deal_statuses_list` | List all deal pipeline statuses |
| `deal_statuses_create` | Create a new deal status |
| `deal_statuses_update` | Update a deal status |
| `lead_statuses_list` | List all lead pipeline statuses |
| `lead_statuses_create` | Create a new lead status |
| `lead_statuses_update` | Update a lead status |

## Development

```bash
git clone https://github.com/joehaddad2000/frappe-crm-mcp.git
cd frappe-crm-mcp
uv sync

# Run with environment variables
FRAPPE_URL=... FRAPPE_API_KEY=... FRAPPE_API_SECRET=... uv run frappe-crm-mcp
```

## License

MIT
