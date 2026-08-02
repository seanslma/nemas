# Reference tables (DUDETAIL, STATIONS, PARTICIPANT, etc.)
# change occasionally (new units register, ratings update)
# — even with no partition column, consider keeping an effective_date or
# ingestion-date column so you can track changes over time rather than just overwriting,
# since these aren't truly static.

__all__ = [
    'TABLE_CONFIG',
    'get_tables',
    'to_duckdb_schema',
    'to_polars_dtypes',
]

TABLE_CONFIG = {
    # --- Dispatch (5-min) ---
    'DISPATCHPRICE': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
        'schema': {
            'SETTLEMENTDATE': 'TIMESTAMP',
            'RUNNO': 'INTEGER',
            'REGIONID': 'VARCHAR',
            'INTERVENTION': 'INTEGER',
            'RRP': 'DOUBLE',
            'RAISE6SECRRP': 'DOUBLE',
            'RAISE60SECRRP': 'DOUBLE',
            'RAISE5MINRRP': 'DOUBLE',
            'RAISEREGRRP': 'DOUBLE',
            'LOWER6SECRRP': 'DOUBLE',
            'LOWER60SECRRP': 'DOUBLE',
            'LOWER5MINRRP': 'DOUBLE',
            'LOWERREGRRP': 'DOUBLE',
        },
        'primary_key': ['SETTLEMENTDATE', 'REGIONID', 'INTERVENTION'],
    },
    'DISPATCHLOAD': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
    },
    'DISPATCH_UNIT_SCADA': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
        'schema': {
            'SETTLEMENTDATE': 'TIMESTAMP',
            'DUID': 'VARCHAR',
            'SCADAVALUE': 'DOUBLE',
        },
        'primary_key': ['SETTLEMENTDATE', 'DUID'],
    },
    'DISPATCHREGIONSUM': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    'DISPATCHINTERCONNECTORRES': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
    },
    'DISPATCHCONSTRAINT': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
    },
    'DISPATCHCASESOLUTION': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    'DISPATCH_MNSPBIDTRK': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    'DISPATCH_FCAS_REQ': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
    },
    # --- Trading (30-min settlement) ---
    'TRADINGPRICE': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    'TRADINGLOAD': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    'TRADINGREGIONSUM': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    'TRADINGINTERCONNECT': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    # --- P5MIN (5-min forecast) ---
    'P5MIN_REGIONSOLUTION': {
        'partition_column': 'RUN_DATETIME',
        'partition_granularity': 'day',
    },
    'P5MIN_UNITSOLUTION': {
        'partition_column': 'RUN_DATETIME',
        'partition_granularity': 'day',
    },
    'P5MIN_INTERCONNECTORSOLN': {
        'partition_column': 'RUN_DATETIME',
        'partition_granularity': 'day',
    },
    'P5MIN_CONSTRAINTSOLUTION': {
        'partition_column': 'RUN_DATETIME',
        'partition_granularity': 'day',
    },
    'P5MIN_CASESOLUTION': {
        'partition_column': 'RUN_DATETIME',
        'partition_granularity': 'month',
    },
    # --- PREDISPATCH (30-min forecast, ~1-2 days ahead) ---
    'PREDISPATCHPRICE': {
        'partition_column': 'PREDISPATCH_RUN_DATETIME',
        'partition_granularity': 'month',
    },
    'PREDISPATCHLOAD': {
        'partition_column': 'PREDISPATCH_RUN_DATETIME',
        'partition_granularity': 'month',
    },
    'PREDISPATCHREGIONSUM': {
        'partition_column': 'PREDISPATCH_RUN_DATETIME',
        'partition_granularity': 'month',
    },
    'PREDISPATCHINTERCONNECTORRES': {
        'partition_column': 'PREDISPATCH_RUN_DATETIME',
        'partition_granularity': 'month',
    },
    'PREDISPATCHCASESOLUTION': {
        'partition_column': 'PREDISPATCH_RUN_DATETIME',
        'partition_granularity': 'month',
    },
    # --- PASA (ST PASA / MT PASA) ---
    'STPASA_REGIONSOLUTION': {
        'partition_column': 'RUN_DATETIME',
        'partition_granularity': 'month',
    },
    'STPASA_INTERCONNECTORSOLN': {
        'partition_column': 'RUN_DATETIME',
        'partition_granularity': 'month',
    },
    'MTPASA_REGIONSOLUTION': {
        'partition_column': 'RUN_DATETIME',
        'partition_granularity': 'month',
    },
    'MTPASA_DUIDAVAILABILITY': {
        'partition_column': 'RUN_DATETIME',
        'partition_granularity': 'month',
    },
    # --- Bidding ---
    'BIDPEROFFER': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
    },
    'BIDDAYOFFER': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    'BIDPEROFFER_D': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
    },
    'BIDDAYOFFER_D': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    # --- FCAS / Ancillary Services ---
    'DISPATCH_LOCAL_PRICE': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
    },
    'FCAS_4S': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'day',
    },
    # --- Settlements ---
    'DAILY_REGION_SUMMARY': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    'BILLING_NMAS_TML_RECOVERY': {
        'partition_column': 'SETTLEMENTDATE',
        'partition_granularity': 'month',
    },
    # --- Reference / registration data (near-static, no time partition) ---
    'DUDETAIL': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'DUDETAILSUMMARY': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'STATIONS': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'GENUNITS': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'PARTICIPANT': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'PARTICIPANTCLASSIFICATION': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'MARKETFEE': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'INTERCONNECTOR': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'INTERCONNECTORCONSTRAINT': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'LOSSFACTORMODEL': {
        'partition_column': None,
        'partition_granularity': None,
    },
    'LOSSMODEL': {
        'partition_column': None,
        'partition_granularity': None,
    },
}


# ---------------------------------------------------------------------------
# Canonical type -> engine-specific type adapters
# ---------------------------------------------------------------------------

_DUCKDB_TYPE_MAP = {
    'TIMESTAMP': 'TIMESTAMP',
    'DATE': 'DATE',
    'VARCHAR': 'VARCHAR',
    'INTEGER': 'INTEGER',
    'BIGINT': 'BIGINT',
    'DOUBLE': 'DOUBLE',
    'BOOLEAN': 'BOOLEAN',
}


def get_tables() -> list[str]:
    """Return the list of table names in TABLE_CONFIG."""
    return list(TABLE_CONFIG.keys())


def to_duckdb_schema(schema: dict) -> dict:
    """Canonical schema dict -> DuckDB column-type dict for read_csv(dtype=...)."""
    return {col: _DUCKDB_TYPE_MAP[t] for col, t in schema.items()}


def to_polars_dtypes(schema: dict) -> dict:
    """
    Canonical schema dict -> Polars dtype dict, e.g. for
    pl.read_csv(path, dtypes=to_polars_dtypes(schema)) or a `pl.Schema`.

    Imports polars lazily so this module doesn't require it unless called.
    """
    import polars as pl

    canonical_to_polars = {
        'TIMESTAMP': pl.Datetime,
        'DATE': pl.Date,
        'VARCHAR': pl.Utf8,
        'INTEGER': pl.Int32,
        'BIGINT': pl.Int64,
        'DOUBLE': pl.Float64,
        'BOOLEAN': pl.Boolean,
    }
    return {col: canonical_to_polars[t] for col, t in schema.items()}
