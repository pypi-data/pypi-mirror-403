from typing import Literal, cast

TsTableRetrieveFunction = Literal["mean"]

TS_TABLE_RETRIEVE_FUNCTION_VALUES: set[TsTableRetrieveFunction] = {
    "mean",
}


def check_ts_table_retrieve_function(value: str) -> TsTableRetrieveFunction:
    if value in TS_TABLE_RETRIEVE_FUNCTION_VALUES:
        return cast(TsTableRetrieveFunction, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_TABLE_RETRIEVE_FUNCTION_VALUES!r}")
