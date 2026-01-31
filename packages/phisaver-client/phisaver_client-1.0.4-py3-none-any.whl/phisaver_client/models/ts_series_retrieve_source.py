from typing import Literal, cast

TsSeriesRetrieveSource = Literal["calc", "inverter", "iotawatt", "nem"]

TS_SERIES_RETRIEVE_SOURCE_VALUES: set[TsSeriesRetrieveSource] = {
    "calc",
    "inverter",
    "iotawatt",
    "nem",
}


def check_ts_series_retrieve_source(value: str) -> TsSeriesRetrieveSource:
    if value in TS_SERIES_RETRIEVE_SOURCE_VALUES:
        return cast(TsSeriesRetrieveSource, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_SERIES_RETRIEVE_SOURCE_VALUES!r}")
