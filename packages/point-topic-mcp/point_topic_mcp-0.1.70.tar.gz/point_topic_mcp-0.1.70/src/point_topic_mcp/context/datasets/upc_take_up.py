def get_dataset_summary():
    """This will be visible to the agent at all times, so keep it short, but let the agent know if the dataset can answer the question of the user."""
    return """
    UK broadband service take-up analytics with modeled subscriber estimates by ISP and technology at postcode level. 
    Algorithmic distribution of reported ISP totals using probability models. 
    Quarterly data with market share calculations.
    """


def get_db_info():
    return f"""
    {DB_INFO}

    {DB_SCHEMA}

    {SQL_EXAMPLES}
    """

TAKE_UP_DISTINCT_ISP_LIST = ['BT', 'Sky', 'TalkTalk', 'CityFibre TalkTalk', 'KCOM Lightstream', 'Virgin Cable', 'Gigaclear', 'Hyperoptic', 'Other']

DB_SCHEMA = """
-- Category 1: Latest quarterly distribution results (Wide Format)
-- These tables contain only the most recent quarter's data.

take_up_v3.report.rpt_postcode_lines_distribution_residential (
	postcode varchar(16777216) comment 'a single uk postcode.',
	lines float comment 'total number of residential lines in the postcode. sum of all isp_tech columns.',
	bt_fttc float comment 'number of lines for bt fttc.',
	bt_fttp float comment 'number of lines for bt fttp.',
	bt_adsl float comment 'number of lines for bt adsl.',
	sky_fttc float comment 'number of lines for sky fttc.',
	sky_fttp float comment 'number of lines for sky fttp.',
	sky_adsl float comment 'number of lines for sky adsl.',
	talktalk_opr_fttc float comment 'number of lines for talktalk (openreach) fttc.',
	talktalk_opr_fttp float comment 'number of lines for talktalk (openreach) fttp.',
	talktalk_opr_adsl float comment 'number of lines for talktalk (openreach) adsl.',
	talktalk_cf_fttp float comment 'number of lines for talktalk (cityfibre) fttp.',
	kcom_lightstream_fttp float comment 'number of lines for kcom lightstream fttp.',
	virgin_cable float comment 'number of lines for virgin cable.',
	gigaclear_fttp float comment 'number of lines for gigaclear fttp.',
	hyperoptic_fttp float comment 'number of lines for hyperoptic fttp.',
	other float comment 'number of lines for all other isps.',
	bt_market_share float comment 'market share for bt (all techs combined).',
	sky_market_share float comment 'market share for sky (all techs combined).',
	talktalk_market_share float comment 'market share for talktalk (all variants combined).',
	kcom_lightstream_market_share float comment 'market share for kcom lightstream.',
	virgin_market_share float comment 'market share for virgin cable.',
	gigaclear_market_share float comment 'market share for gigaclear.',
	hyperoptic_market_share float comment 'market share for hyperoptic.',
	other_market_share float comment 'market share for other isps.',
	quarter varchar(6) comment 'the reporting quarter, e.g., ''2025Q2''. contains only one value.',
	reported_at varchar(10) comment 'the reporting date, e.g., ''2025-06-01''. contains only one value.'
)

take_up_v3.report.rpt_postcode_lines_distribution_business (
	# this table has the exact same schema as the residential table above, but contains data for business lines.
)


-- Category 2: Full historical quarterly results (Long/Tidy Format)
-- These tables contain data for all available quarters, including the latest one.

take_up_v3.report.rpt_all_quarterly_results_residential (
	postcode varchar(16777216) comment 'a single uk postcode.',
	reported_at date comment 'the reporting date, e.g., ''2025-06-01''.',
	quarter varchar(6) comment 'the reporting quarter, e.g., ''2025Q2''.',
	operator_tech varchar(16777216) comment 'concatenated isp and technology, e.g., ''BT_FTTC''.',
	operator varchar(16777216) comment 'the name of the isp, e.g., ''BT'', ''Sky'', ''CityFibre TalkTalk''.',
	tech varchar(16777216) comment 'the technology type, e.g., ''fttp'', ''fttc''.',
	lines float comment 'number of residential lines for this specific operator_tech in this postcode and quarter. rows with lines=0 are not included.'
)

take_up_v3.report.rpt_all_quarterly_results_business (
	# this table has the exact same schema as the residential table above, but contains data for business lines.
)
"""



DB_INFO = f"""
QUARTERLY MODELED SUBSCRIBER ESTIMATES BY ISP/TECH AT POSTCODE LEVEL

TWO TABLE FORMATS:

1. WIDE FORMAT (latest quarter only):
   - rpt_postcode_lines_distribution_*: one row per postcode, columns per ISP/tech
   - shows 0 if ISP has no lines (includes all postcodes)
   - market_share columns pre-calculated

2. LONG FORMAT (all quarters):
   - rpt_all_quarterly_results_*: one row per postcode/operator/tech/quarter
   - OMITS rows where lines=0 (no presence = no row)
   - use for time-series, aggregations across periods

CRITICAL: ZERO-LINE HANDLING
- Wide tables: show 0 for no presence
- Long tables: omit row entirely if lines=0
- To find postcodes where ISP has zero lines in long format: use LEFT JOIN from complete postcode list

OPERATOR = ISP (critical convention)
Operators: {TAKE_UP_DISTINCT_ISP_LIST}
Tech: lowercase ('fttp', 'fttc', 'adsl')
'Other' operator has NULL tech

RESIDENTIAL VS BUSINESS:
Separate tables: _residential and _business

CALCULATIONS:
- Wide: lines = sum of all ISP/tech columns
- Wide: sum of market_share columns = 1.0
- Long: total lines = SUM(lines) GROUP BY postcode, quarter

DATE FIELDS:
- quarter: VARCHAR 'YYYYQN' (e.g., '2025Q2')
- reported_at: DATE 'YYYY-MM-01' (end of quarter)
"""



SQL_EXAMPLES = [
    {
        "request": "What is the national market share for each ISP for residential lines in the latest quarter?",
        "response": """
-- Use long format for efficient operator aggregation
with latest_quarter_data as (
    select operator, lines
    from take_up_v3.report.rpt_all_quarterly_results_residential
    where quarter = (select max(quarter) from take_up_v3.report.rpt_all_quarterly_results_residential)
),
operator_totals as (
    select operator, sum(lines) as total_lines
    from latest_quarter_data
    group by operator
)
select
    operator,
    total_lines,
    round(total_lines * 100.0 / sum(total_lines) over (), 2) as national_market_share_percentage
from operator_totals
order by national_market_share_percentage desc
        """
    },
    {
        "request": "Show FTTP growth for business lines over last 4 quarters",
        "response": """
-- Long format for time-series analysis
with fttp_business_lines as (
    select quarter, sum(lines) as total_fttp_lines
    from take_up_v3.report.rpt_all_quarterly_results_business
    where tech = 'fttp'
    group by quarter
)
select
    quarter,
    total_fttp_lines,
    lag(total_fttp_lines, 1, 0) over (order by quarter) as previous_quarter,
    total_fttp_lines - previous_quarter as quarterly_growth
from fttp_business_lines
qualify dense_rank() over (order by quarter desc) <= 4
order by quarter desc
        """
    }
]