from typing import Literal, cast

TsTableRetrieveEngine = Literal["influx", "timescale"]

TS_TABLE_RETRIEVE_ENGINE_VALUES: set[TsTableRetrieveEngine] = {
    "influx",
    "timescale",
}


def check_ts_table_retrieve_engine(value: str) -> TsTableRetrieveEngine:
    if value in TS_TABLE_RETRIEVE_ENGINE_VALUES:
        return cast(TsTableRetrieveEngine, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_TABLE_RETRIEVE_ENGINE_VALUES!r}")
