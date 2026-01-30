.PHONY: dev run lint format clean build publish

# Load .env file if it exists
ifneq (,$(wildcard .env))
    include .env
    export
endif

# Development server with FastMCP dev tools
dev:
	uv run fastmcp dev src/frappe_crm_mcp/server.py

# Run the server
run:
	uv run frappe-crm-mcp

# Lint with ruff
lint:
	uv run ruff check .

# Format with ruff
format:
	uv run ruff format .
	uv run ruff check --fix .

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info/

# Build package
build: clean
	uv build

# Publish to PyPI (requires UV_PUBLISH_TOKEN in .env)
publish: build
	uv publish --token $(UV_PUBLISH_TOKEN)