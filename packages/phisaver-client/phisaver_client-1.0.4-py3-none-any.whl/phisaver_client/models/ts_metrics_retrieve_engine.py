from typing import Literal, cast

TsMetricsRetrieveEngine = Literal["influx", "timescale"]

TS_METRICS_RETRIEVE_ENGINE_VALUES: set[TsMetricsRetrieveEngine] = {
    "influx",
    "timescale",
}


def check_ts_metrics_retrieve_engine(value: str) -> TsMetricsRetrieveEngine:
    if value in TS_METRICS_RETRIEVE_ENGINE_VALUES:
        return cast(TsMetricsRetrieveEngine, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_METRICS_RETRIEVE_ENGINE_VALUES!r}")
