from typing import Literal, cast

TsSeriesRetrieveMetcat = Literal["battery", "calc", "load", "net", "other", "production"]

TS_SERIES_RETRIEVE_METCAT_VALUES: set[TsSeriesRetrieveMetcat] = {
    "battery",
    "calc",
    "load",
    "net",
    "other",
    "production",
}


def check_ts_series_retrieve_metcat(value: str) -> TsSeriesRetrieveMetcat:
    if value in TS_SERIES_RETRIEVE_METCAT_VALUES:
        return cast(TsSeriesRetrieveMetcat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_SERIES_RETRIEVE_METCAT_VALUES!r}")
