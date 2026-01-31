from typing import Literal, cast

TsTableRetrieveMetcat = Literal["battery", "calc", "load", "net", "other", "production"]

TS_TABLE_RETRIEVE_METCAT_VALUES: set[TsTableRetrieveMetcat] = {
    "battery",
    "calc",
    "load",
    "net",
    "other",
    "production",
}


def check_ts_table_retrieve_metcat(value: str) -> TsTableRetrieveMetcat:
    if value in TS_TABLE_RETRIEVE_METCAT_VALUES:
        return cast(TsTableRetrieveMetcat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_TABLE_RETRIEVE_METCAT_VALUES!r}")
