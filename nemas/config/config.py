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

URL_BASE = 'https://www.nemweb.com.au/'

TABLE_CONFIG = {
    # --- dispatch (5-min) ---
    'dispatch_price': {
        'file_mask': 'DISPATCHPRICE',
        'primary_key': ['settlementdate', 'regionid', 'intervention'],
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    'dispatch_load': {
        'file_mask': 'DISPATCHLOAD',
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    'dispatch_unit_scada': {
        'file_mask': 'public_archive#dispatch_unit_scada#file01#*.zip',
        'primary_key': ['settlementdate', 'duid'],
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    'dispatch_regionsum': {
        'file_mask': 'public_archive#dispatchregionsum#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    'dispatch_interconnection': {
        'file_mask': 'public_archive#dispatchinterconnectorres#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    'dispatch_interconnectorres': {
        'file_mask': 'public_archive#dispatchinterconnectorres#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    'dispatch_constraint': {
        'file_mask': 'public_archive#dispatchconstraint#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    'dispatch_local_price': {
        'file_mask': 'public_archive#dispatch_local_price#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    'dispatch_casesolution': {
        'file_mask': 'public_archive#dispatchcasesolution#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    'dispatch_mnspbidtrk': {
        'file_mask': 'public_archive#dispatch_mnspbidtrk#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    'dispatch_fcas_req': {
        'file_mask': 'public_archive#dispatch_fcas_req#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    # --- trading (30-min settlement) ---
    'tradingprice': {
        'file_mask': 'public_archive#tradingprice#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    'tradingload': {
        'file_mask': 'public_archive#tradingload#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    'tradingregionsum': {
        'file_mask': 'public_archive#tradingregionsum#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    'tradinginterconnect': {
        'file_mask': 'public_archive#tradinginterconnect#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    # --- p5min (5-min forecast) ---
    'p5min_regionsolution': {
        'file_mask': 'public_archive#p5min_regionsolution#file01#*.zip',
        'partition_column': 'run_datetime',
        'partition_granularity': 'day',
    },
    'p5min_unitsolution': {
        'file_mask': 'public_archive#p5min_unitsolution#file01#*.zip',
        'partition_column': 'run_datetime',
        'partition_granularity': 'day',
    },
    'p5min_interconnectorsoln': {
        'file_mask': 'public_archive#p5min_interconnectorsoln#file01#*.zip',
        'partition_column': 'run_datetime',
        'partition_granularity': 'day',
    },
    'p5min_constraintsolution': {
        'file_mask': 'public_archive#p5min_constraintsolution#file01#*.zip',
        'partition_column': 'run_datetime',
        'partition_granularity': 'day',
    },
    'p5min_casesolution': {
        'file_mask': 'public_archive#p5min_casesolution#file01#*.zip',
        'partition_column': 'run_datetime',
        'partition_granularity': 'month',
    },
    # --- predispatch (30-min forecast, ~1-2 days ahead) ---
    'predispatchprice': {
        'file_mask': 'public_archive#predispatchprice#file01#*.zip',
        'partition_column': 'predispatch_run_datetime',
        'partition_granularity': 'month',
    },
    'predispatchload': {
        'file_mask': 'public_archive#predispatchload#file01#*.zip',
        'partition_column': 'predispatch_run_datetime',
        'partition_granularity': 'month',
    },
    'predispatchregionsum': {
        'file_mask': 'public_archive#predispatchregionsum#file01#*.zip',
        'partition_column': 'predispatch_run_datetime',
        'partition_granularity': 'month',
    },
    'predispatchinterconnectorres': {
        'file_mask': 'public_archive#predispatchinterconnectorres#file01#*.zip',
        'partition_column': 'predispatch_run_datetime',
        'partition_granularity': 'month',
    },
    'predispatchcasesolution': {
        'file_mask': 'public_archive#predispatchcasesolution#file01#*.zip',
        'partition_column': 'predispatch_run_datetime',
        'partition_granularity': 'month',
    },
    # --- pasa (st pasa / mt pasa) ---
    'stpasa_regionsolution': {
        'file_mask': 'public_archive#stpasa_regionsolution#file01#*.zip',
        'partition_column': 'run_datetime',
        'partition_granularity': 'month',
    },
    'stpasa_interconnectorsoln': {
        'file_mask': 'public_archive#stpasa_interconnectorsoln#file01#*.zip',
        'partition_column': 'run_datetime',
        'partition_granularity': 'month',
    },
    'mtpasa_regionsolution': {
        'file_mask': 'public_archive#mtpasa_regionsolution#file01#*.zip',
        'partition_column': 'run_datetime',
        'partition_granularity': 'month',
    },
    'mtpasa_duidavailability': {
        'file_mask': 'public_archive#mtpasa_duidavailability#file01#*.zip',
        'partition_column': 'run_datetime',
        'partition_granularity': 'month',
    },
    # --- bidding ---
    'bidperoffer': {
        'file_mask': 'public_archive#bidperoffer#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    'biddayoffer': {
        'file_mask': 'public_archive#biddayoffer#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    'bidperoffer_d': {
        'file_mask': 'public_archive#bidperoffer_d#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    'biddayoffer_d': {
        'file_mask': 'public_archive#biddayoffer_d#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    # --- fcas / ancillary services ---
    'fcas_4s': {
        'file_mask': 'public_archive#fcas_4s#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'day',
    },
    # --- settlements ---
    'daily_region_summary': {
        'file_mask': 'public_archive#daily_region_summary#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    'billing_nmas_tml_recovery': {
        'file_mask': 'public_archive#billing_nmas_tml_recovery#file01#*.zip',
        'partition_column': 'settlementdate',
        'partition_granularity': 'month',
    },
    # --- reference / registration data (near-static, no time partition) ---
    'dudetail': {
        'file_mask': 'public_archive#dudetail#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'dudetailsummary': {
        'file_mask': 'public_archive#dudetailsummary#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'stations': {
        'file_mask': 'public_archive#stations#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'genunits': {
        'file_mask': 'public_archive#genunits#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'participant': {
        'file_mask': 'public_archive#participant#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'participantclassification': {
        'file_mask': 'public_archive#participantclassification#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'marketfee': {
        'file_mask': 'public_archive#marketfee#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'interconnector': {
        'file_mask': 'public_archive#interconnector#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'interconnectorconstraint': {
        'file_mask': 'public_archive#interconnectorconstraint#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'lossfactormodel': {
        'file_mask': 'public_archive#lossfactormodel#file01#*.zip',
        'partition_column': None,
        'partition_granularity': None,
    },
    'lossmodel': {
        'file_mask': 'public_archive#lossmodel#file01#*.zip',
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


def get_tables() -> set[str]:
    """
    Return the set of table names in TABLE_CONFIG.
    """
    return set(TABLE_CONFIG.keys())


def get_table_config(table_name: str) -> dict | None:
    """
    Return the config dict for a given table name.
    """
    return TABLE_CONFIG.get(table_name)


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
