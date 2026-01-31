from typing import Literal, cast

TsTableRetrieveFormat = Literal["csv", "json"]

TS_TABLE_RETRIEVE_FORMAT_VALUES: set[TsTableRetrieveFormat] = {
    "csv",
    "json",
}


def check_ts_table_retrieve_format(value: str) -> TsTableRetrieveFormat:
    if value in TS_TABLE_RETRIEVE_FORMAT_VALUES:
        return cast(TsTableRetrieveFormat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_TABLE_RETRIEVE_FORMAT_VALUES!r}")
