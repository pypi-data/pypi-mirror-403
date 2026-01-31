from typing import Literal, cast

TsSeriesRetrieveFunction = Literal["mean"]

TS_SERIES_RETRIEVE_FUNCTION_VALUES: set[TsSeriesRetrieveFunction] = {
    "mean",
}


def check_ts_series_retrieve_function(value: str) -> TsSeriesRetrieveFunction:
    if value in TS_SERIES_RETRIEVE_FUNCTION_VALUES:
        return cast(TsSeriesRetrieveFunction, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_SERIES_RETRIEVE_FUNCTION_VALUES!r}")
