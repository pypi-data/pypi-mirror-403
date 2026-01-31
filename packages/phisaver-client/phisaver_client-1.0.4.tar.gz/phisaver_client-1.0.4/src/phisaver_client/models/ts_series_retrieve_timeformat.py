from typing import Literal, cast

TsSeriesRetrieveTimeformat = Literal["epoch", "epochms", "iso"]

TS_SERIES_RETRIEVE_TIMEFORMAT_VALUES: set[TsSeriesRetrieveTimeformat] = {
    "epoch",
    "epochms",
    "iso",
}


def check_ts_series_retrieve_timeformat(value: str) -> TsSeriesRetrieveTimeformat:
    if value in TS_SERIES_RETRIEVE_TIMEFORMAT_VALUES:
        return cast(TsSeriesRetrieveTimeformat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_SERIES_RETRIEVE_TIMEFORMAT_VALUES!r}")
