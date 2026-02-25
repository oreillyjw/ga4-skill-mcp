---
name: google-analytics
description: Query Google Analytics 4 data. Use when the user asks about website traffic, page views, sessions, user counts, conversions, top pages, traffic sources, or any analytics/metrics questions. Trigger on keywords like "analytics", "traffic", "visitors", "page views", "sessions", "GA4", "bounce rate", "conversions", "top pages", "referrals".
---

# Google Analytics 4 Skill

Query GA4 property data using the Google Analytics Data API v1.

## Setup

### 1. Environment Variables

Set these before using the skill:

| Variable | Required | Description |
|----------|----------|-------------|
| `GA4_CREDENTIALS_PATH` | Yes | Absolute path to your Google service account JSON key file |
| `GA4_PROPERTY_ID` | No | Default GA4 property ID (can be overridden per-query with `--property-id`) |

### 2. Python Virtual Environment

These skills require a Python venv with their dependencies installed. Set `SKILLS_PYTHON` to the venv's Python binary:

```bash
# Create a venv (or use an existing one)
python3 -m venv ~/.claude/venv

# Install dependencies
~/.claude/venv/bin/pip install -r PATH_TO_SKILL/requirements.txt
```

Then add to your Claude Code settings:

```json
{
  "env": {
    "SKILLS_PYTHON": "/path/to/your/venv/bin/python3"
  }
}
```

### 3. Service Account Permissions

The service account must have **Viewer** (or higher) access to each GA4 property you want to query. Add it via GA4 Admin > Property Access Management using the service account email.

### 4. Multi-Property Usage

To query different properties, either:
- Set `GA4_PROPERTY_ID` to your most-used property and override with `--property-id` as needed
- Use `--report properties` to list all properties the service account has access to

## How to Use

Run the query script using the venv Python:

```bash
$SKILLS_PYTHON PATH_TO_SKILL/ga_query.py --report <report_type> [options]
```

## Available Reports

### 1. `properties` — List all GA4 properties

```bash
python ga_query.py --report properties
```

Returns: account names, account IDs, property names, property IDs. Useful for discovering available properties and their IDs.

### 2. `overview` — High-level summary

```bash
python ga_query.py --report overview --days 30
```

Returns: total users, sessions, page views, avg session duration, bounce rate, new vs returning users.

### 3. `pages` — Top pages by views

```bash
python ga_query.py --report pages --days 30 --limit 20
```

Returns: page path, title, views, users, avg engagement time.

### 4. `sources` — Traffic sources

```bash
python ga_query.py --report sources --days 30 --limit 20
```

Returns: source, medium, sessions, users, conversions.

### 5. `countries` — Geographic breakdown

```bash
python ga_query.py --report countries --days 30 --limit 20
```

Returns: country, sessions, users, engagement rate.

### 6. `devices` — Device category breakdown

```bash
python ga_query.py --report devices --days 30
```

Returns: device category (desktop/mobile/tablet), sessions, users.

### 7. `daily` — Day-by-day trend

```bash
python ga_query.py --report daily --days 30
```

Returns: date, users, sessions, page views per day.

### 8. `realtime` — Active users right now

```bash
python ga_query.py --report realtime
```

Returns: active users in last 30 minutes by source.

### 9. `custom` — Custom query (advanced)

```bash
python ga_query.py --report custom --metrics "sessions,totalUsers" --dimensions "city" --days 7 --limit 10
```

Pass any valid GA4 API metric/dimension names as comma-separated values.

## Common Options

| Option | Default | Description |
|--------|---------|-------------|
| `--property-id` | `$GA4_PROPERTY_ID` | GA4 property ID (overrides env var) |
| `--days` | `30` | Lookback period in days |
| `--limit` | `10` | Max rows returned |
| `--start` | — | Explicit start date (YYYY-MM-DD), overrides --days |
| `--end` | — | Explicit end date (YYYY-MM-DD), defaults to today |
| `--output` | `table` | Output format: `table`, `json`, or `csv` |

## GA4 Metric and Dimension Reference (for custom queries)

**Common Metrics**: totalUsers, newUsers, sessions, screenPageViews, averageSessionDuration, bounceRate, engagementRate, conversions, eventCount, activeUsers

**Common Dimensions**: date, pagePath, pageTitle, sessionSource, sessionMedium, country, city, deviceCategory, browser, operatingSystem, landingPage, sessionDefaultChannelGroup
