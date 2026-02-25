#!/usr/bin/env python3
"""
Google Analytics 4 Data API query tool.
Queries GA4 property data using a service account.
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta

# ============================================================
# CONFIGURATION — Set via environment variables:
#   GA4_CREDENTIALS_PATH  - path to service account JSON key
#   GA4_PROPERTY_ID       - GA4 property ID
# ============================================================
CREDENTIALS_PATH = os.environ.get("GA4_CREDENTIALS_PATH", "")
PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "")


def get_property_id(args):
    """Get property ID from args or env var."""
    pid = getattr(args, "property_id", None) or PROPERTY_ID
    if not pid:
        print(
            "Error: No property ID provided. Use --property-id or set GA4_PROPERTY_ID env var.",
            file=sys.stderr,
        )
        sys.exit(1)
    return pid


def get_client():
    """Create and return a GA4 BetaAnalyticsDataClient."""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    return BetaAnalyticsDataClient()


def build_request(property_id, metrics, dimensions, days=30, start=None, end=None, limit=10, order_by_metric=None, desc=True):
    """Build a RunReportRequest."""
    from google.analytics.data_v1beta.types import (
        RunReportRequest, Metric, Dimension, DateRange, OrderBy
    )

    end_date = end or datetime.now().strftime("%Y-%m-%d")
    if start:
        start_date = start
    else:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    request = RunReportRequest(
        property=f"properties/{property_id}",
        metrics=[Metric(name=m.strip()) for m in metrics],
        dimensions=[Dimension(name=d.strip()) for d in dimensions] if dimensions else [],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        limit=limit,
    )

    if order_by_metric:
        request.order_bys = [
            OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name=order_by_metric),
                desc=desc,
            )
        ]

    return request


def format_response(response, output="table"):
    """Format the API response into the desired output format."""
    headers = [h.name for h in response.dimension_headers] + [h.name for h in response.metric_headers]
    rows = []
    for row in response.rows:
        values = [dv.value for dv in row.dimension_values] + [mv.value for mv in row.metric_values]
        rows.append(values)

    if output == "json":
        result = []
        for row in rows:
            result.append(dict(zip(headers, row)))
        return json.dumps(result, indent=2)

    elif output == "csv":
        lines = [",".join(headers)]
        for row in rows:
            lines.append(",".join(row))
        return "\n".join(lines)

    else:  # table
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_row = "|" + "|".join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + "|"

        lines = [separator, header_row, separator]
        for row in rows:
            line = "|" + "|".join(f" {str(v):<{col_widths[i]}} " for i, v in enumerate(row)) + "|"
            lines.append(line)
        lines.append(separator)

        if response.row_count:
            lines.append(f"\nTotal rows: {response.row_count}")

        return "\n".join(lines)


def report_properties(client, args):
    """List all GA4 properties the service account can access."""
    from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    admin_client = AnalyticsAdminServiceClient()

    accounts = list(admin_client.list_account_summaries())
    if not accounts:
        return "No GA4 accounts found for this service account."

    headers = ["Account", "Account ID", "Property", "Property ID"]
    rows = []
    for account in accounts:
        for prop in account.property_summaries:
            # property name is "properties/123456789"
            prop_id = prop.property.split("/")[-1] if prop.property else ""
            rows.append([
                account.display_name or account.name,
                account.account.split("/")[-1] if account.account else "",
                prop.display_name or prop.property,
                prop_id,
            ])

    if not rows:
        return "No properties found."

    if args.output == "json":
        result = [dict(zip(headers, row)) for row in rows]
        return json.dumps(result, indent=2)
    elif args.output == "csv":
        lines = [",".join(headers)]
        for row in rows:
            lines.append(",".join(row))
        return "\n".join(lines)
    else:
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_row = "|" + "|".join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + "|"
        lines = [separator, header_row, separator]
        for row in rows:
            line = "|" + "|".join(f" {str(v):<{col_widths[i]}} " for i, v in enumerate(row)) + "|"
            lines.append(line)
        lines.append(separator)
        return "\n".join(lines)


def report_overview(client, args):
    """High-level site overview."""
    property_id = get_property_id(args)
    request = build_request(
        property_id,
        metrics=["totalUsers", "newUsers", "sessions", "screenPageViews",
                 "averageSessionDuration", "engagementRate", "bounceRate"],
        dimensions=[],
        days=args.days, start=args.start, end=args.end, limit=1,
    )
    response = client.run_report(request)
    return format_response(response, args.output)


def report_pages(client, args):
    """Top pages by views."""
    property_id = get_property_id(args)
    request = build_request(
        property_id,
        metrics=["screenPageViews", "totalUsers", "averageSessionDuration"],
        dimensions=["pagePath", "pageTitle"],
        days=args.days, start=args.start, end=args.end, limit=args.limit,
        order_by_metric="screenPageViews",
    )
    response = client.run_report(request)
    return format_response(response, args.output)


def report_sources(client, args):
    """Traffic sources."""
    property_id = get_property_id(args)
    request = build_request(
        property_id,
        metrics=["sessions", "totalUsers", "engagementRate", "conversions"],
        dimensions=["sessionSource", "sessionMedium"],
        days=args.days, start=args.start, end=args.end, limit=args.limit,
        order_by_metric="sessions",
    )
    response = client.run_report(request)
    return format_response(response, args.output)


def report_countries(client, args):
    """Geographic breakdown."""
    property_id = get_property_id(args)
    request = build_request(
        property_id,
        metrics=["sessions", "totalUsers", "engagementRate"],
        dimensions=["country"],
        days=args.days, start=args.start, end=args.end, limit=args.limit,
        order_by_metric="sessions",
    )
    response = client.run_report(request)
    return format_response(response, args.output)


def report_devices(client, args):
    """Device category breakdown."""
    property_id = get_property_id(args)
    request = build_request(
        property_id,
        metrics=["sessions", "totalUsers", "engagementRate"],
        dimensions=["deviceCategory"],
        days=args.days, start=args.start, end=args.end, limit=args.limit,
        order_by_metric="sessions",
    )
    response = client.run_report(request)
    return format_response(response, args.output)


def report_daily(client, args):
    """Day-by-day trend."""
    property_id = get_property_id(args)
    request = build_request(
        property_id,
        metrics=["totalUsers", "sessions", "screenPageViews"],
        dimensions=["date"],
        days=args.days, start=args.start, end=args.end, limit=args.days or 30,
    )
    from google.analytics.data_v1beta.types import OrderBy
    request.order_bys = [
        OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"), desc=False)
    ]
    response = client.run_report(request)
    return format_response(response, args.output)


def report_realtime(client, args):
    """Realtime active users."""
    property_id = get_property_id(args)
    from google.analytics.data_v1beta.types import (
        RunRealtimeReportRequest, Metric, Dimension
    )
    request = RunRealtimeReportRequest(
        property=f"properties/{property_id}",
        metrics=[Metric(name="activeUsers")],
        dimensions=[Dimension(name="unifiedScreenName")],
        limit=args.limit,
    )
    response = client.run_realtime_report(request)

    headers = [h.name for h in response.dimension_headers] + [h.name for h in response.metric_headers]
    rows = []
    for row in response.rows:
        values = [dv.value for dv in row.dimension_values] + [mv.value for mv in row.metric_values]
        rows.append(values)

    if not rows:
        return "No active users right now."

    if args.output == "json":
        result = [dict(zip(headers, row)) for row in rows]
        return json.dumps(result, indent=2)
    elif args.output == "csv":
        lines = [",".join(headers)]
        for row in rows:
            lines.append(",".join(row))
        return "\n".join(lines)
    else:
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_row = "|" + "|".join(f" {h:<{col_widths[i]}} " for i, h in enumerate(headers)) + "|"
        lines = [separator, header_row, separator]
        for row in rows:
            line = "|" + "|".join(f" {str(v):<{col_widths[i]}} " for i, v in enumerate(row)) + "|"
            lines.append(line)
        lines.append(separator)
        return "\n".join(lines)


def report_custom(client, args):
    """Custom query with user-specified metrics and dimensions."""
    if not args.metrics:
        return "Error: --metrics required for custom report (comma-separated)"

    property_id = get_property_id(args)
    metrics = [m.strip() for m in args.metrics.split(",")]
    dimensions = [d.strip() for d in args.dimensions.split(",")] if args.dimensions else []

    request = build_request(
        property_id,
        metrics=metrics,
        dimensions=dimensions,
        days=args.days, start=args.start, end=args.end, limit=args.limit,
        order_by_metric=metrics[0],
    )
    response = client.run_report(request)
    return format_response(response, args.output)


REPORTS = {
    "properties": report_properties,
    "overview": report_overview,
    "pages": report_pages,
    "sources": report_sources,
    "countries": report_countries,
    "devices": report_devices,
    "daily": report_daily,
    "realtime": report_realtime,
    "custom": report_custom,
}


def main():
    parser = argparse.ArgumentParser(description="Query Google Analytics 4 data")
    parser.add_argument("--report", required=True, choices=REPORTS.keys(), help="Report type")
    parser.add_argument("--property-id", help="GA4 property ID (overrides GA4_PROPERTY_ID env var)")
    parser.add_argument("--days", type=int, default=30, help="Lookback period in days (default: 30)")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD), overrides --days")
    parser.add_argument("--end", help="End date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--limit", type=int, default=10, help="Max rows (default: 10)")
    parser.add_argument("--output", choices=["table", "json", "csv"], default="table", help="Output format")
    parser.add_argument("--metrics", help="Comma-separated metrics (for custom report)")
    parser.add_argument("--dimensions", help="Comma-separated dimensions (for custom report)")

    args = parser.parse_args()

    try:
        client = get_client()
        result = REPORTS[args.report](client, args)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 