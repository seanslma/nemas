# layout

```
nemas/
│
├── api/
│
├── data/
│
├── market/
│   ├── price.py
│   ├── generation.py
│   ├── demand.py
│   ├── fcas.py
│   └── constraints.py
│
├── analytics/
│   ├── revenue.py
│   ├── curtailment.py
│   ├── capacity.py
│   ├── emissions.py
│   ├── arbitrage.py
│   └── profitability.py
│
├── reports/
│
├── plotting/
│
└── engine/
```

## parts
- data: data fetching and caching
- market: provides descriptive information and statistics about market entities (prices, demand, generation, FCAS, etc.).
- analytics: provides higher-level derived metrics and business logic (revenue, curtailment, price capture, profitability, emissions, arbitrage).
- reports: combines multiple analytics into ready-to-use summaries.

## flowchart
```
            ┌────────────────────────┐
            │      Public API        │
            └──────────┬─────────────┘
                        │
    ┌──────────────────┼───────────────────┐
    │                  │                   │
    ▼                  ▼                   ▼
Data Management    Analytics          Visualisation
    │                  │                   │
    └──────────────┬───┴───────────────────┘
                    ▼
            Query / Compute Engine
                    │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
Downloader      Cache         Metadata
```

## compute layer
I would also introduce a central compute layer. Many analytics—revenue, price statistics, capacity factors, curtailment, FCAS, emissions—share the same sequence:

Read cached data.
Join with generator metadata (DUID, station, region, technology).
Aggregate by time or asset.
Compute metrics.

Rather than duplicating this in every analytics module, have an internal engine that provides reusable primitives such as:
```py
engine.load("DISPATCHPRICE")
engine.join_generators(df)
engine.aggregate(df, by=["REGIONID", "TECHNOLOGY"])
engine.calculate_revenue(df)
```
Then the analytics modules become thin wrappers over a common engine. This keeps the codebase consistent, easier to test, and much simpler to extend as NEMAS grows into a comprehensive analytics platform.

## more details
```
nemas/
│
├── __init__.py
├── config.py
├── constants.py
├── exceptions.py
│
├── api/
│   ├── download.py
│   ├── cache.py
│   ├── data.py
│   ├── analytics.py
│   └── stats.py
│
├── data/
│   ├── downloader.py
│   ├── parser.py
│   ├── parquet.py
│   ├── cache.py
│   ├── metadata.py
│   └── registry.py
│
├── engine/
│   ├── query.py
│   ├── joins.py
│   ├── aggregation.py
│   ├── lazy.py
│   └── backend.py
│
├── analytics/
│   │
│   ├── price/
│   │   ├── region.py
│   │   ├── duid.py
│   │   ├── technology.py
│   │   ├── volatility.py
│   │   ├── duration.py
│   │   └── negative.py
│   │
│   ├── revenue/
│   │   ├── generator.py
│   │   ├── battery.py
│   │   ├── solar.py
│   │   ├── wind.py
│   │   ├── storage.py
│   │   └── regional.py
│   │
│   ├── curtailment/
│   │   ├── rooftop.py
│   │   ├── wind.py
│   │   ├── solar.py
│   │   └── battery.py
│   │
│   ├── generation/
│   │   ├── dispatch.py
│   │   ├── capacity_factor.py
│   │   ├── availability.py
│   │   └── utilisation.py
│   │
│   ├── bids/
│   ├── fcas/
│   ├── transmission/
│   ├── constraints/
│   ├── emissions/
│   └── reports/
│
├── models/
│   ├── generators.py
│   ├── regions.py
│   ├── technology.py
│   └── market.py
│
├── metadata/
│   ├── generators.parquet
│   ├── stations.parquet
│   ├── technology.parquet
│   ├── regions.parquet
│   ├── tables.yaml
│   └── schemas.yaml
│
├── plotting/
│   ├── prices.py
│   ├── revenue.py
│   ├── duration.py
│   ├── generation.py
│   └── curtailment.py
│
└── utils/
```
