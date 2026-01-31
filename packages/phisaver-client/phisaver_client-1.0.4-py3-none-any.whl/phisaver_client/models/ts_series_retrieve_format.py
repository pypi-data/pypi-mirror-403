from typing import Literal, cast

TsSeriesRetrieveFormat = Literal["csv", "json"]

TS_SERIES_RETRIEVE_FORMAT_VALUES: set[TsSeriesRetrieveFormat] = {
    "csv",
    "json",
}


def check_ts_series_retrieve_format(value: str) -> TsSeriesRetrieveFormat:
    if value in TS_SERIES_RETRIEVE_FORMAT_VALUES:
        return cast(TsSeriesRetrieveFormat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_SERIES_RETRIEVE_FORMAT_VALUES!r}")
