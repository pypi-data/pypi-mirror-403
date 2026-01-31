def get_dataset_summary():
    """This will be visible to the agent at all times, so keep it short."""
    return """
    uk broadband service pricing and plan details by isp and period. 
    includes monthly costs, speeds, contract terms, and postcode mappings for geographic analysis.
    quarterly snapshots with change tracking via group_id.
    """

def get_db_info():
    return f"""
    {DB_INFO}

    {DB_SCHEMA}

    {SQL_EXAMPLES}
    """

DB_INFO = """
UK broadband tariff pricing with postcode mapping. Quarterly snapshots 2021Q2-2025Q3.

TABLES:
- research.reports.rpt_tariff: global raw data (267k records, 99 countries)
- upc_client._src_research_app.upc_tariffs_time_series: uk-filtered with operator mapping (7.5k records, 78 operators)
- upc_client._src_research_app.upc_tariff_postcode_time_series: postcode mapping (978M records - ALWAYS filter by period!)

CRITICAL FILTERING:
- period = '2025Q2' for current data (or specify period)
- type = 'Standalone' for broadband-only, 'Bundle' for bundles
- monthly_subscription is not null (excludes plans without pricing)
- country = 'United Kingdom' (research.reports table only)

OPERATOR NAME MAPPING:
- tariff operators ("Sky UK") ≠ upc operators ("Sky", "Sky FTTP")
- use upc_isp field in processed tables for standardized names
- 78 operators in UK processed data vs 186 in raw

PERFORMANCE:
Postcode table has 978M records - always filter by period and limit geographic scope.

GEOGRAPHIC PATTERN:
tariffs → upc_tariff_postcode_time_series → upc_output (for demographics)

GOTCHAS:
- tech field: comma-separated values possible ('FTTP, FWA')
- contract_length: varchar (can be null or empty string)
- change tracking: group_id persists, tariff_id changes each period
"""

DB_SCHEMA = """
research.reports.rpt_tariff (
    tariff_id varchar comment 'unique identifier for tariff snapshot',
    group_id varchar comment 'persistent identifier across periods for change tracking',
    operator varchar comment 'isp name (global data, varies from upc naming)',
    date timestamp_ntz comment 'report date',
    period varchar comment 'quarterly period (e.g. 2024Q1)', 
    country varchar comment 'country (filter: United Kingdom for uk data)',
    domain varchar comment 'residential/business',
    name varchar comment 'tariff/plan name',
    tech varchar comment 'technology (can be comma-separated)',
    type varchar comment 'standalone/bundle',
    monthly_subscription float comment 'monthly price in local currency',
    downstream_mbs float comment 'download speed mbps',
    upstream_mbs float comment 'upload speed mbps',
    contract_length varchar comment 'contract months (varchar field)',
    broadband_included boolean comment 'true for broadband plans',
    tv varchar comment 'tv service details',
    monthly_tv_addon float comment 'tv addon monthly cost',
    notes varchar comment 'special offers and conditions'
)

upc_client._src_research_app.upc_tariffs_time_series (
    tariff_id varchar comment 'unique identifier linking to raw tariff data',
    operator varchar comment 'original operator name from research data',
    upc_isp varchar comment 'standardized operator name matching upc footprint data',
    upc_tech varchar comment 'standardized technology name', 
    date timestamp_ntz comment 'report date',
    period varchar comment 'quarterly period (e.g. 2025Q2)',
    country varchar comment 'always United Kingdom for this table',
    domain varchar comment 'residential/business',
    name varchar comment 'tariff/plan name',
    tech varchar comment 'original technology string',
    type varchar comment 'standalone/bundle',
    monthly_subscription float comment 'monthly price gbp',
    downstream_mbs float comment 'download speed mbps',
    upstream_mbs float comment 'upload speed mbps',
    contract_length varchar comment 'contract months (varchar)',
    broadband_included boolean comment 'always true for this filtered table',
    tv varchar comment 'tv service included',
    monthly_tv_addon float comment 'tv addon cost',
    fixed_telephony varchar comment 'phone service included',
    mobile_telephony varchar comment 'mobile service included',
    notes varchar comment 'plan details and offers'
)

upc_client._src_research_app.upc_tariff_postcode_time_series (
    postcode varchar comment 'uk postcode',
    tariff_id varchar comment 'links to tariff tables',
    upc_isp varchar comment 'standardized operator name',
    upc_tech varchar comment 'standardized technology',
    period varchar comment 'quarterly period'
)
"""

SQL_EXAMPLES = [
    {
        'request': 'What are the cheapest standalone broadband plans available in London?',
        'response': """
select 
    t.upc_isp as operator,
    t.name as plan_name,
    t.monthly_subscription as monthly_price,
    t.downstream_mbs as download_speed,
    count(distinct tp.postcode) as london_postcodes_covered
from upc_client._src_research_app.upc_tariffs_time_series t
join upc_client._src_research_app.upc_tariff_postcode_time_series tp using (tariff_id, period)
join upc_core.reports.upc_output u using (postcode)
where t.period = '2025Q2'
    and t.type = 'Standalone'
    and t.monthly_subscription is not null
    and u.government_region = 'London'
group by t.tariff_id, t.upc_isp, t.name, t.monthly_subscription, t.downstream_mbs
order by t.monthly_subscription asc
limit 10
        """
    },
    {
        'request': 'Compare average broadband pricing across UK regions',
        'response': """
select 
    u.government_region,
    count(distinct t.tariff_id) as available_plans,
    round(avg(t.monthly_subscription), 2) as avg_monthly_price,
    round(min(t.monthly_subscription), 2) as cheapest_plan
from upc_client._src_research_app.upc_tariffs_time_series t
join upc_client._src_research_app.upc_tariff_postcode_time_series tp using (tariff_id, period)
join upc_core.reports.upc_output u using (postcode)
where t.period = '2025Q2'
    and t.type = 'Standalone'
    and t.monthly_subscription is not null
group by u.government_region
order by avg_monthly_price desc
        """
    }
]
