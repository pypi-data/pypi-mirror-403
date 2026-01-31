def get_dataset_summary():
    "This will be visible to the agent at all times, so keep it short, but let the agent know if the dataset can answer the question of the user."
    return """
    UK broadband ISP availability and infrastructure forecasting data 
    with attractiveness scores and predicted operator footprint expansion by postcode. 
    Semi-annual forecasts.
    Data from 2025
    """


def get_db_info():
    return f"""
    {DB_INFO}

    {DB_SCHEMA}

    {SQL_EXAMPLES}
    """


DB_SCHEMA = """
forecast_v7.reports.all_general_attractiveness (
	postcode varchar(16777216) comment 'the uk postcode',
	time_since_last_upgrade number(35,6) comment 'attractiveness factor (0-1 scale): time elapsed since the last network upgrade in the area',
	affordability float comment 'attractiveness factor (0-1 scale): measure of the local population''s ability to afford broadband services',
	population_density float comment 'attractiveness factor (0-1 scale): measure of population density in the postcode area',
	digital_deprivation float comment 'attractiveness factor (0-1 scale): measure of the area''s need for better digital services',
	general_attractiveness float comment 'the overall attractiveness score, which is the sum of all other factor columns',
	quarter varchar(16777216) comment 'the quarter the report is for, format: YYYYQ[1-4], e.g., 2022Q3',
	reported_at date comment 'the date representation of the quarter, always the first day of the last month of the quarter, e.g., 2022-09-01 for 2022Q3'
)

forecast_v7.intermediate.int_forecast_output (
	postcode varchar(16777216) comment 'the uk postcode',
	operator varchar(16777216) comment 'the name of the broadband operator',
	present number(2,0) comment 'binary flag (0 or 1) indicating if the operator is forecast to have a presence (footprint) in the postcode by the end of the forecast period',
	reported_at varchar(10) comment 'the end date of the forecast period. CRITICAL: ''yyyy-06-01'' means end of year yyyy; ''yyyy-12-01'' means end of H1 of yyyy+1'
)
"""

UPC_FORECAST_DISTINCT_OPERATOR_LIST = [
    "CityFibre",
    "Community Fibre",
    "Connexin FTTP",
    "FW Networks",
    "Fibrus",
    "Full Fibre Ltd",
    "GNetwork",
    "Gigaclear",
    "Hyperoptic",
    "ITS FTTP",
    "KCOM Lightstream",
    "MS3 FTTP",
    "Netomnia You Fibre",
    "Openreach",
    "Trooli",
    "Virgin",
    "Voneus FTTP",
    "Zzoomm",
    "brsk FTTP",
    "nexfibre Virgin Media"
]

DB_INFO = f"""
UK BROADBAND INFRASTRUCTURE FORECASTING DATA

TWO TABLES:

1. all_general_attractiveness: postcode-level attractiveness scores (quarterly, ~1.7M postcodes)
   - quarter: VARCHAR 'YYYYQ[1-4]' (e.g., '2023Q4')
   - reported_at: DATE first day of last month of quarter (e.g., '2023-12-01')
   - general_attractiveness: sum of factor columns (0-1 scale each)
   - factors: time_since_last_upgrade, affordability, population_density, digital_deprivation

2. int_forecast_output: semi-annual footprint forecasts to 2030 (data from 2025)
   - present: binary flag (1=presence forecast, 0=no presence)
   - cumulative: if present=1 at date X, also present=1 at all later dates
   - operators: {UPC_FORECAST_DISTINCT_OPERATOR_LIST}

CRITICAL: reported_at INTERPRETATION
reported_at does NOT mean "when forecast was made" but "point in time forecast is FOR":
- yyyy-06-01 = forecast as of END OF YEAR yyyy
- yyyy-12-01 = forecast as of END OF H1 (first 6 months) of year yyyy+1

Examples:
- 2025-12-01 = mid 2026
- 2026-06-01 = end of 2026
- 2027-06-01 = end of 2027
- 2030-06-01 = end of 2030 (latest forecast)

CALCULATING NEW BUILD:
To find postcodes built in H2 2027:
1. postcodes with present=1 at 2027-06-01 (end of 2027)
2. subtract postcodes with present=1 at 2026-12-01 (mid-2027)
3. difference = H2 2027 build (use LEFT JOIN with NULL check or EXCEPT)
"""


SQL_EXAMPLES = [
    {
        "request": "Show top 20 most attractive postcodes that Openreach is not forecasted to have presence in by mid-2029",
        "response": """
-- reported_at='2028-12-01' = mid-2029 forecast
with latest_attractiveness as (
    select postcode, general_attractiveness
    from forecast_v7.reports.all_general_attractiveness
    qualify row_number() over (partition by postcode order by reported_at desc) = 1
),
openreach_future_footprint as (
    select distinct postcode
    from forecast_v7.intermediate.int_forecast_output
    where operator = 'Openreach' and reported_at = '2028-12-01' and present = 1
)
select la.postcode, la.general_attractiveness
from latest_attractiveness la
left join openreach_future_footprint off on la.postcode = off.postcode
where off.postcode is null
order by la.general_attractiveness desc
limit 20
        """
    },
    {
        "request": "Calculate forecasted growth for Netomnia You Fibre from mid-2026 to end of 2028",
        "response": """
-- reported_at='2025-12-01' = mid-2026, reported_at='2028-06-01' = end of 2028
with counts_by_period as (
    select
        count(distinct case when reported_at = '2025-12-01' then postcode end) as count_2026_mid,
        count(distinct case when reported_at = '2028-06-01' then postcode end) as count_2028
    from forecast_v7.intermediate.int_forecast_output
    where operator = 'Netomnia You Fibre' 
        and reported_at in ('2025-12-01', '2028-06-01')
        and present = 1
)
select
    count_2026_mid,
    count_2028,
    count_2028 - count_2026_mid as absolute_growth,
    round(((count_2028 - count_2026_mid) / count_2026_mid) * 100, 2) as percentage_growth
from counts_by_period
        """
    }
]
