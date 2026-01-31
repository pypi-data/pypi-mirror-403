"""BI Reports dataset context - dynamically generated from GitHub DBT models."""

import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# Cache for GitHub metadata (fetched once per session)
_github_cache: Dict[str, List[Dict[str, str]]] = {}


def _get_static_fallback() -> Dict[str, List[Dict[str, str]]]:
    """Return static fallback table list when GitHub API unavailable."""
    return {
        "operator": [
            {"name": "op_diff_uk", "description": "Operator month-over-month premises growth and decline for UK market analysis"},
            {"name": "op_gor", "description": "Operator premises coverage by government region for geographic market share analysis"},
            {"name": "op_la", "description": "Operator premises coverage by local authority for LA-level market analysis"},
            {"name": "op_no_growth_uk", "description": "Operators with zero or negative postcode growth over 6 months for market decline analysis"},
            {"name": "op_prem_more_than_1", "description": "Premises with multiple FTTP operators for overbuild and competition analysis"},
            {"name": "op_uk", "description": "UK operator footprint summary with postcode and premises counts for market overview"},
            {"name": "ts_2_altnets_la", "description": "Postcodes with exactly 2 altnet FTTP operators by LA for competitive overlap analysis"},
            {"name": "ts_3_altnets_la", "description": "Postcodes with exactly 3 altnet FTTP operators by LA for competitive overlap analysis"},
            {"name": "ts_altnet_overbuild_uk", "description": "Altnet FTTP overbuild counts by postcode for UK-wide competition analysis"},
            {"name": "ts_op_overlap_la", "description": "Aggregated operator lists by LA for quick market presence overview queries"},
            {"name": "ts_op_overlap_pc", "description": "Aggregated operator lists by postcode for detailed overlap analysis queries"},
            {"name": "ts_overbuild_uk", "description": "FTTP overbuild counts per postcode with canonicalized operators for market share queries"},
            {"name": "ts_upc_progress_uk", "description": "UK-wide UPC progress metrics tracking total postcodes and premises over time"},
            {"name": "tsq_pvt_op_hh_uk", "description": "Quarterly operator household coverage pivot table for UK time series analysis"},
            {"name": "tsq_pvt_op_uk", "description": "Quarterly operator premises coverage pivot table for UK time series analysis"},
        ],
        "tech": [
            {"name": "fttp_la", "description": "FTTP premises coverage by LA with percentage calculations for geographic analysis"},
            {"name": "premises_not_passed_by_gigabit_country", "description": "Latest snapshot of premises not passed by gigabit-capable networks by country"},
            {"name": "premises_not_passed_by_gigabit_la", "description": "Latest snapshot of premises not passed by gigabit-capable networks by LA"},
            {"name": "rfog_or_gig1_fttp_overlap_lsoa", "description": "Virgin RFOG/Gig1 and FTTP overlap analysis by LSOA for technology competition queries"},
            {"name": "ts_altnet_tech_uk", "description": "Altnet technology coverage time series with canonicalized operators for UK analysis"},
            {"name": "ts_bt_fttp_la", "description": "BT FTTP premises coverage by LA with percentage calculations for geographic analysis"},
            {"name": "ts_bt_tech_uk", "description": "BT technology coverage time series for UK-wide premises tracking by tech type"},
            {"name": "ts_fttp_la", "description": "FTTP coverage time series by LA with quarterly growth metrics for trend analysis"},
            {"name": "ts_fttp_uk", "description": "UK-wide FTTP premises time series for national coverage tracking queries"},
            {"name": "ts_gig1_la", "description": "Virgin Gig1 coverage by LA with percentage calculations for geographic analysis"},
            {"name": "ts_gig1_uk", "description": "UK-wide Virgin Gig1 premises time series for national coverage tracking"},
            {"name": "ts_op_tech_uk", "description": "Operator technology coverage time series for UK-wide premises tracking by operator and tech"},
            {"name": "ts_openreach_ops_nga_tech_uk", "description": "Openreach operator NGA technology coverage time series for BT/Sky/TalkTalk analysis"},
            {"name": "ts_premises_not_passed_by_gigabit_country", "description": "Time series of premises not passed by gigabit-capable networks by country for coverage gap analysis"},
            {"name": "ts_premises_not_passed_by_gigabit_la", "description": "Time series of premises not passed by gigabit-capable networks by LA for coverage gap analysis"},
            {"name": "ts_rfog_uk", "description": "UK-wide Virgin RFOG premises time series for national coverage tracking"},
            {"name": "tsq_bt_fttp_la", "description": "Quarterly BT FTTP coverage by LA with growth metrics for trend analysis"},
            {"name": "tsq_bt_tech_uk", "description": "Quarterly BT technology coverage time series with growth metrics for UK-wide analysis"},
            {"name": "tsq_gig1_uk", "description": "Quarterly Virgin Gig1 UK coverage time series with growth metrics for trend analysis"},
            {"name": "tsq_op_tech_uk", "description": "Quarterly operator technology coverage time series with growth metrics for UK-wide analysis"},
            {"name": "tsq_pvt_tech_uk", "description": "Quarterly technology premises coverage pivot table for UK time series analysis"},
            {"name": "tsq_rfog_uk", "description": "Quarterly Virgin RFOG UK coverage time series with growth metrics for trend analysis"},
        ]
    }


def _fetch_github_metadata() -> Dict[str, List[Dict[str, str]]]:
    """Fetch table descriptions from GitHub UPC_Client repo (optional: requires GITHUB_TOKEN for private repo)."""
    if _github_cache:
        return _github_cache
    
    # Try GitHub API if token available (for private repo access)
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        try:
            from github import Github
            g = Github(github_token)
            repo = g.get_repo("Point-Topic/UPC_Client")
            
            tables_by_subdir: Dict[str, List[Dict[str, str]]] = {}
            
            def _traverse_directory(path: str):
                """Recursively traverse directory and extract SQL file metadata."""
                try:
                    contents = repo.get_contents(path, ref="main")
                    if not isinstance(contents, list):
                        contents = [contents]
                    
                    for item in contents:
                        if item.type == "file" and item.name.endswith(".sql"):
                            subdir = path.replace("models/bi_reports/", "").strip("/")
                            if not subdir:
                                subdir = "root"
                            
                            try:
                                file_content = item.decoded_content.decode("utf-8")
                                lines = file_content.split("\n")
                                description = None
                                for line in lines[:10]:
                                    stripped = line.strip()
                                    if stripped.startswith("--"):
                                        comment_text = stripped[2:].strip()
                                        if comment_text and "depends_on" not in comment_text.lower():
                                            description = comment_text
                                            break
                                if not description:
                                    description = "No description available"
                            except Exception:
                                description = "No description available"
                            
                            table_name = item.name[:-4]
                            if subdir not in tables_by_subdir:
                                tables_by_subdir[subdir] = []
                            tables_by_subdir[subdir].append({
                                "name": table_name,
                                "description": description
                            })
                        elif item.type == "dir":
                            _traverse_directory(item.path)
                except Exception:
                    pass
            
            _traverse_directory("models/bi_reports")
            if tables_by_subdir:
                _github_cache.update(tables_by_subdir)
                return tables_by_subdir
        except Exception:
            # Fall through to static fallback
            pass
    
    # Use static fallback (works without token, always available)
    fallback = _get_static_fallback()
    _github_cache.update(fallback)
    return fallback


def get_dataset_summary():
    """This will be visible to the agent at all times, so keep it short."""
    return """
    Pre-computed BI reports: overbuild analysis, market share, tech coverage, operator footprints.
    Use these tables instead of building complex CTEs - they're already optimized and pre-aggregated.
    """


def get_db_info():
    return f"""
{DB_INFO}

{DB_SCHEMA}

{SQL_EXAMPLES}
"""


def _build_table_list() -> str:
    """Build formatted table list from GitHub metadata, organized by subdirectory."""
    tables_by_subdir = _fetch_github_metadata()
    
    if not tables_by_subdir:
        # Fallback if GitHub fetch fails - return empty string (will be handled gracefully)
        return "BI_REPORTS tables (metadata unavailable - GitHub token may be missing)"
    
    sections = []
    
    # Sort subdirectories for consistent output (root first, then alphabetical)
    sorted_subdirs = sorted(tables_by_subdir.keys(), key=lambda x: (x != "root", x.lower()))
    
    for subdir in sorted_subdirs:
        tables = tables_by_subdir[subdir]
        if not tables:
            continue
        
        # Format subdirectory header
        if subdir == "root":
            header = "BI_REPORTS (root):"
        else:
            header = f"BI_REPORTS/{subdir}:"
        
        sections.append(header)
        
        # Sort tables within subdirectory by name
        for table in sorted(tables, key=lambda x: x["name"]):
            sections.append(f"  - {table['name']}: {table['description']}")
        
        sections.append("")  # Empty line between subdirectories
    
    return "\n".join(sections).rstrip()


def _get_db_info_content():
    """Build DB_INFO content with dynamic table list."""
    table_list = _build_table_list()
    return f"""
PRE-COMPUTED BI_REPORTS TABLES

These tables contain pre-aggregated, optimized results for common analysis patterns.
Use them instead of building complex CTEs - they're faster and already handle edge cases.

{table_list}

CRITICAL NOTES:
- All tables are in upc_core.reports schema (not a separate bi_reports database)
- Quarterly tables prefixed with tsq_ (quarterly snapshots)
- Time series tables prefixed with ts_ (monthly snapshots)
- Non-time-series tables (op_*, fttp_la) contain latest snapshot only
- Overbuild tables already handle CityFibre canonicalization
- Market share tables already calculate correct denominators

WHEN TO USE BI_REPORTS:
- Overbuild analysis → ts_altnet_overbuild_uk, ts_overbuild_uk
- Market share queries → op_uk, op_la, op_gor
- Tech coverage trends → ts_fttp_uk, ts_fttp_la, ts_altnet_tech_uk
- Operator footprints → op_uk, op_la, op_gor
- Competition analysis → ts_op_overlap_la, ts_op_overlap_pc

If your query matches a BI report pattern, use the pre-computed table instead of building from scratch.
"""

DB_INFO = _get_db_info_content()

DB_SCHEMA = """
upc_core.reports.ts_altnet_overbuild_uk (
    altnet_fttp_count number comment 'number of distinct altnet fttp operators',
    reported_at date comment 'snapshot date (quarterly: mar/jun/sep/dec)',
    total_premises number comment 'total premises passed',
    total_bus_sites number comment 'total business sites',
    total_households number comment 'total households',
    total_postcodes number comment 'total postcodes',
    altnet_fttp_op_combinations array comment 'array of operator combinations (when count > 1)'
)

upc_core.reports.op_uk (
    operator varchar comment 'operator name',
    postcode_count number comment 'number of postcodes served',
    premises_passed number comment 'total premises passed',
    reported_at date comment 'snapshot date'
)

upc_core.reports.ts_fttp_uk (
    reported_at date comment 'snapshot date',
    fttp_premises number comment 'total uk premises with fttp availability'
)

upc_core.reports.ts_fttp_la (
    la_name varchar comment 'local authority name',
    la_code varchar comment 'local authority code',
    government_region varchar comment 'government region',
    total_prem number comment 'total premises in la',
    fttp_prem number comment 'premises with fttp availability',
    perc_total number comment 'percentage of premises with fttp',
    reported_at date comment 'snapshot date'
)

upc_core.reports.ts_overbuild_uk (
    altnet_count number comment 'number of distinct altnet fttp operators per postcode',
    reported_at date comment 'snapshot date',
    total_premises number comment 'total premises at this overbuild level',
    operator_combinations array comment 'array of operator combinations'
)
"""

SQL_EXAMPLES = [
    {
        'request': 'Show me altnet FTTP overbuild: how many premises passed by 1, 2, 3+ altnet networks',
        'response': """
-- Use pre-computed overbuild table instead of building complex CTE
select 
  altnet_fttp_count,
  round(total_premises) as premises_passed,
  reported_at
from upc_core.reports.ts_altnet_overbuild_uk
where reported_at = (select max(reported_at) from upc_core.reports.ts_altnet_overbuild_uk)
order by altnet_fttp_count asc"""
    },
    {
        'request': 'What is the current operator footprint for top 10 operators?',
        'response': """
-- Use pre-computed operator footprint table
select 
  operator,
  round(premises_passed) as total_premises,
  postcode_count
from upc_core.reports.op_uk
where reported_at = (select max(reported_at) from upc_core.reports.op_uk)
order by premises_passed desc
limit 10"""
    },
    {
        'request': 'Show FTTP coverage growth by local authority over last 6 months',
        'response': """
-- Use pre-computed tech coverage time series
with latest as (
  select max(reported_at) as max_date from upc_core.reports.ts_fttp_la
),
six_months_ago as (
  select dateadd(month, -6, max_date) as past_date from latest
)
select 
  t.la_name,
  max(case when t.reported_at = l.max_date then t.perc_total else 0 end) as current_pct,
  max(case when t.reported_at = s.past_date then t.perc_total else 0 end) as past_pct,
  current_pct - past_pct as growth_pct
from upc_core.reports.ts_fttp_la t
cross join latest l
cross join six_months_ago s
where t.reported_at in (l.max_date, s.past_date)
group by t.la_name
having growth_pct > 0
order by growth_pct desc
limit 10"""
    }
]
