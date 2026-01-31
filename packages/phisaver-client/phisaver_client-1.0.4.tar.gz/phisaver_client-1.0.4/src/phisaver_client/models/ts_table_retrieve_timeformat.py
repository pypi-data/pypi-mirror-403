from typing import Literal, cast

TsTableRetrieveTimeformat = Literal["epoch", "epochms", "iso"]

TS_TABLE_RETRIEVE_TIMEFORMAT_VALUES: set[TsTableRetrieveTimeformat] = {
    "epoch",
    "epochms",
    "iso",
}


def check_ts_table_retrieve_timeformat(value: str) -> TsTableRetrieveTimeformat:
    if value in TS_TABLE_RETRIEVE_TIMEFORMAT_VALUES:
        return cast(TsTableRetrieveTimeformat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_TABLE_RETRIEVE_TIMEFORMAT_VALUES!r}")
