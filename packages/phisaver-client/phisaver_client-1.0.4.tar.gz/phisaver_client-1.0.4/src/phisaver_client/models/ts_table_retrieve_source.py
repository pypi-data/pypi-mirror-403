from typing import Literal, cast

TsTableRetrieveSource = Literal["calc", "inverter", "iotawatt", "nem"]

TS_TABLE_RETRIEVE_SOURCE_VALUES: set[TsTableRetrieveSource] = {
    "calc",
    "inverter",
    "iotawatt",
    "nem",
}


def check_ts_table_retrieve_source(value: str) -> TsTableRetrieveSource:
    if value in TS_TABLE_RETRIEVE_SOURCE_VALUES:
        return cast(TsTableRetrieveSource, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_TABLE_RETRIEVE_SOURCE_VALUES!r}")
