from typing import Literal, cast

TsSeriesRetrieveEngine = Literal["influx", "timescale"]

TS_SERIES_RETRIEVE_ENGINE_VALUES: set[TsSeriesRetrieveEngine] = {
    "influx",
    "timescale",
}


def check_ts_series_retrieve_engine(value: str) -> TsSeriesRetrieveEngine:
    if value in TS_SERIES_RETRIEVE_ENGINE_VALUES:
        return cast(TsSeriesRetrieveEngine, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_SERIES_RETRIEVE_ENGINE_VALUES!r}")
