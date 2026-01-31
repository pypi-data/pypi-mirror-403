from typing import Literal, cast

TsMetricsRetrieveSource = Literal["calc", "inverter", "iotawatt", "nem"]

TS_METRICS_RETRIEVE_SOURCE_VALUES: set[TsMetricsRetrieveSource] = {
    "calc",
    "inverter",
    "iotawatt",
    "nem",
}


def check_ts_metrics_retrieve_source(value: str) -> TsMetricsRetrieveSource:
    if value in TS_METRICS_RETRIEVE_SOURCE_VALUES:
        return cast(TsMetricsRetrieveSource, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_METRICS_RETRIEVE_SOURCE_VALUES!r}")
