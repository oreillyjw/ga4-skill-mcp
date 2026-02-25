#!/usr/bin/env python3
"""
MCP server wrapping the GA4 query tool for Claude Desktop.
Imports ga_query directly instead of shelling out.
"""

import os
import sys

# Ensure the skill directory is on the Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from mcp.server.fastmcp import FastMCP
import argparse

# Import the query module directly
import ga_query

mcp = FastMCP("ga4-skill-mcp")


def make_args(**kwargs):
    """Build a namespace object mimicking argparse output."""
    defaults = {
        "days": 30, "start": None, "end": None, "limit": 10,
        "output": "table", "metrics": None, "dimensions": None,
        "property_id": None, "report": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@mcp.tool()
def ga_properties() -> str:
    """List all GA4 accounts and properties the service account can access."""
    try:
        client = ga_query.get_client()
        return ga_query.report_properties(client, make_args(output="table"))
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def ga_overview(days: int = 30, property_id: str = "") -> str:
    """High-level GA4 summary: users, sessions, page views, bounce rate."""
    try:
        client = ga_query.get_client()
        args = make_args(days=days, property_id=property_id or None)
        return ga_query.report_overview(client, args)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def ga_pages(days: int = 30, limit: int = 20, property_id: str = "") -> str:
    """Top pages by views with page path, title, views, users."""
    try:
        client = ga_query.get_client()
        args = make_args(days=days, limit=limit, property_id=property_id or None)
        return ga_query.report_pages(client, args)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def ga_sources(days: int = 30, limit: int = 20, property_id: str = "") -> str:
    """Traffic sources breakdown by source/medium."""
    try:
        client = ga_query.get_client()
        args = make_args(days=days, limit=limit, property_id=property_id or None)
        return ga_query.report_sources(client, args)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def ga_countries(days: int = 30, limit: int = 20, property_id: str = "") -> str:
    """Geographic breakdown of sessions and users by country."""
    try:
        client = ga_query.get_client()
        args = make_args(days=days, limit=limit, property_id=property_id or None)
        return ga_query.report_countries(client, args)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def ga_devices(days: int = 30, property_id: str = "") -> str:
    """Device category breakdown (desktop, mobile, tablet)."""
    try:
        client = ga_query.get_client()
        args = make_args(days=days, property_id=property_id or None)
        return ga_query.report_devices(client, args)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def ga_daily(days: int = 30, property_id: str = "") -> str:
    """Day-by-day trend of users, sessions, and page views."""
    try:
        client = ga_query.get_client()
        args = make_args(days=days, property_id=property_id or None)
        return ga_query.report_daily(client, args)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def ga_realtime(limit: int = 10, property_id: str = "") -> str:
    """Active users right now (last 30 minutes)."""
    try:
        client = ga_query.get_client()
        args = make_args(limit=limit, property_id=property_id or None)
        return ga_query.report_realtime(client, args)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def ga_custom(metrics: str, dimensions: str = "", days: int = 30, limit: int = 10, property_id: str = "") -> str:
    """Custom GA4 query with any metrics and dimensions (comma-separated)."""
    try:
        client = ga_query.get_client()
        args = make_args(
            metrics=metrics, dimensions=dimensions or None,
            days=days, limit=limit, property_id=property_id or None,
        )
        return ga_query.report_custom(client, args)
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
