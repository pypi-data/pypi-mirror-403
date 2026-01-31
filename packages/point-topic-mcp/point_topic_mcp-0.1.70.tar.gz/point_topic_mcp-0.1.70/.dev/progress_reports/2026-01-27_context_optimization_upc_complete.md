# context optimization - upc dataset complete

## summary
reduced upc.py from 378 to 168 lines (55.6% reduction)

## what changed

### removed (210 lines)
- 4 complex sql examples:
  - fttp growth by LA (time series comparison with pivoting)
  - fttp market share (multi-step with separate numerator/denominator)
  - cityfibre vs altnet overbuild (intersect pattern)
  - manual canonicalization overbuild (alternative method)
- verbose explanations in DB_INFO
- duplicate information

### kept (168 lines)
- complete schema (all fields intact)
- critical gotchas:
  - cityfibre canonicalization requirement
  - market share calculation rules (distinct postcodes, total from upc_output)
  - time series vs non-time-series guidance
  - fact_altnet preference for altnet queries
- 2 essential examples:
  - operator footprint (basic pattern)
  - altnet overbuild (using fact_altnet)
- sanity check values (33M premises, 30M households, 67M population)

## validation
tested remaining query - works correctly:
```
OPERATOR_GROUP         TOTAL_PREMISES_PASSED
BT                     20,839,577
TalkTalk               20,101,322
Sky                    19,957,055
CityFibre              16,866,455
```

## next steps
1. strip ontology.py (255 → ~100 lines target)
2. strip tariffs.py (225 → ~80 lines target)
3. strip take_up.py (238 → ~80 lines target)
4. strip forecast.py (289 → ~100 lines target)
5. create bi_reports.py (dynamic context from dbt model comments)
6. test 10 queries from pt_agent_sync.core.results

## key insight
complex sql examples (overbuild, market share) are already pre-computed in bi_reports tables:
- ts_altnet_overbuild_uk
- ts_overbuild_uk
- op_uk, op_la, op_gor (market share)
- ts_fttp_uk, ts_fttp_la (tech coverage)

agent should query these instead of building 50+ line CTEs
