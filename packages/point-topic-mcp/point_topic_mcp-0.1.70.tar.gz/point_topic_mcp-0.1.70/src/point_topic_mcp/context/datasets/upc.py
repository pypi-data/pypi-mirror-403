
def get_dataset_summary():
    """This will be visible to the agent at all times, so keep it short, but let the agent know if the dataset can answer the question of the user."""
    return """
    UK broadband infrastructure availability data at postcode level. 
    Monthly snapshots showing operator footprint and premises coverage (not subscriber numbers). 
    Also contains the whole UK at postcode granularity, with geographic and demographic data.
    """


def get_db_info():
    return f"""
    {DB_INFO}

    {DB_SCHEMA}

    {SQL_EXAMPLES}
    """

DB_INFO = """
UPC = unit post code. All UPC tables at postcode granularity, monthly snapshots.
reported_at field: first day of each month.

CRITICAL DISTINCTIONS:
- Footprint/premises passed ≠ market share (footprint = availability, market share = paying subscribers)
- This is AVAILABILITY data, not subscriber counts

SANITY CHECK VALUES:
- UK premises: ~33M | households: ~30M | population: ~67M
- Always verify totals against these values

OPERATOR DEFINITIONS:
- Virgin Media ISPs: 'Virgin Media RFOG', 'Virgin Cable' (NOT altnet)
- 'nexfibre Virgin Media': considered altnet in our systems
- CityFibre variants: 'CityFibre Vodafone', 'CityFibre TalkTalk', etc. (wholesale relationships)
- Use get_distinct_value_list('upc','operator') to see full operator list

ALTNET FILTERING:
Exclude: BT, Sky, TalkTalk, Vodafone, Virgin Cable, Virgin Media RFOG, KCOM Lightstream
Example: where operator not in ('BT','Sky','TalkTalk','Vodafone','Virgin Cable','Virgin Media RFOG') and operator not like '%nexfibre%'

CRITICAL: CITYFIBRE CANONICALIZATION
CityFibre appears as multiple variants due to wholesale relationships.
MUST canonicalize before counting distinct operators or calculating overbuild:
  case when operator like '%CityFibre%' then 'CityFibre' else operator end

WRONG: count(distinct operator) where operator not in (...)
RIGHT: use canonicalized operator_canonical THEN count distinct

CRITICAL: MARKET SHARE CALCULATIONS
fact_operator is unique per (postcode, operator, tech, reported_at).
Joining to upc_output creates duplicates when operators have multiple techs in same postcode.

RULES:
1. Individual operator footprint: distinct postcodes from fact_operator joined to upc_output
2. Total UK premises: SUM(premises) FROM upc_output directly (NEVER derive from fact_operator joins)
3. For homes passed by operator: use households metric from upc_output

CRITICAL: TIME SERIES VS NON-TIME-SERIES
Check latest dates with get_dataset_status() tool.

- Current/latest/specific date = latest snapshot: use upc_output, fact_operator (simpler, no date filter)
- Historical trends/comparisons/dates before latest: use upc_output_time_series, fact_operator_time_series

PREFER fact_altnet/fact_altnet_time_series FOR ALTNET QUERIES:
- CityFibre canonicalization already applied
- Openreach/VM exclusions already applied
- Still filter nexfibre if using strict altnet definition: where operator != 'nexfibre Virgin Media'

TIPS:
1. FTTP queries: tech like '%fttp%' (value is 'fttponly')
2. Current data only: use non-time-series tables directly
"""

DB_SCHEMA = """
upc_core.reports.fact_operator_time_series (
	postcode varchar(16777216) comment 'name of postcode',
	operator varchar(16777216) comment 'name of operator',
	tech varchar(16777216) comment 'technology',
	fastest_up number(38,2) comment 'fastest upload speed',
	fastest_down number(38,0) comment 'fastest download speed',
	activated_date date comment 'date when this footprint happenws',
	reported_at date comment 'represent for version of postcode (vtable-tbb)'
)

upc_core.reports.fact_operator (
    # this is the same as upc_core.reports.fact_operator_time_series but with only the most recent snapshot of data
)

upc_core.reports.fact_altnet_time_series (
	postcode varchar(16777216) comment 'name of postcode',
	operator varchar(16777216) comment 'canonicalized altnet operator name (CityFibre variants collapsed)',
	tech varchar(16777216) comment 'technology',
	reported_at date comment 'represent for version of postcode (vtable-tbb)'
)

upc_core.reports.fact_altnet (
    # this is the same as upc_core.reports.fact_altnet_time_series but with only the most recent snapshot of data
    # CRITICAL: Use this table for altnet queries - it has CityFibre canonicalization and openreach/VM exclusions already applied
    # Excluded operators: BT, Sky, TalkTalk, Vodafone, Virgin Cable, Virgin Media RFOG, KCOM Lightstream
    # NOTE: Currently includes 'nexfibre Virgin Media' which may need filtering depending on your definition of altnet
)

upc_core.reports.upc_output_time_series (
	postcode varchar(16777216) comment 'key for upc_output, unique per reporting month',
	mapinfo_id number(18,0) comment 'map information identification code',
	post_sector varchar(16777216) comment 'higher level postcode grouping',
	northings number(38,0) comment 'distance in metres north of national grid origin',
	eastings number(38,0) comment 'distance in metres east of national grid origin',
	coa_code varchar(16777216) comment 'ons-defined code for the census output area in which the upc is located',
	lsoa varchar(16777216) comment 'ons-defined code for the lower super output area in which the upc is located',
	msoa_and_im varchar(16777216) comment 'ons-defined code for the middle super output area or intermediate zone in scotland in which the upc is located',
	la_code varchar(16777216) comment 'local authority area code',
	la_name varchar(16777216) comment 'local authority area name',
	government_region varchar(16777216) comment 'government region',
	country varchar(16777216) comment 'name of the nation in which the upc is located',
	population number(38,2) comment 'estimated population of the upc',
	premises number(38,2) comment 'total number of households and business premises (sites or workplaces) in the upc',
	households number(38,0) comment 'estimated number of households in the upc',
	bus_sites_total number(38,2) comment 'estimated number of business premises (sites or workplaces) in the upc',
	mdfcode varchar(16777216) comment 'identifier for bt/openreach exchange serving the upc',
	exchange_name varchar(16777216) comment 'name of exchange serving the upc',
	cityfibre_postcode_passed varchar(1) comment 'whether the upc is within cityfibre halo (200m-500m)',
)

upc_core.reports.upc_output (
    # this is the same as upc_core.reports.upc_output_time_series but with only the most recent snapshot of data
)

"""

SQL_EXAMPLES = [
    {
        'request': 'What is the current FTTP footprint of the top 10 operators?',
        'response': """
-- Essential pattern: distinct postcodes from fact_operator joined to upc_output for premise counts
select
  case when f.operator like '%CityFibre%' then 'CityFibre' else f.operator end as operator_group,
  round(sum(u.premises)) as total_premises_passed
from (
  select distinct operator, postcode
  from upc_core.reports.fact_operator
  where tech like '%fttp%'
) as f
join upc_core.reports.upc_output as u on f.postcode = u.postcode
group by operator_group
order by total_premises_passed desc
limit 10"""
    },
    {
        'request': 'Show me altnet FTTP network overbuild: how many premises were passed by 1, 2, 3, 4, 5+ altnet FTTP networks',
        'response': """
-- PREFERRED: Use fact_altnet (CityFibre canonicalization and exclusions already applied)
with operator_count_per_postcode as (
  select postcode, count(distinct operator) as altnet_count
  from upc_core.reports.fact_altnet
  where tech like '%fttp%' and operator != 'nexfibre Virgin Media'
  group by postcode
)
select 
  altnet_count as number_of_altnet_fttp_networks,
  round(sum(u.premises), 0) as premises_passed
from operator_count_per_postcode o
join upc_core.reports.upc_output u using (postcode)
group by altnet_count
order by altnet_count asc"""
    }
]
