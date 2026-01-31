from typing import Literal, cast

TsMetricsRetrieveMetcat = Literal["battery", "calc", "load", "net", "other", "production"]

TS_METRICS_RETRIEVE_METCAT_VALUES: set[TsMetricsRetrieveMetcat] = {
    "battery",
    "calc",
    "load",
    "net",
    "other",
    "production",
}


def check_ts_metrics_retrieve_metcat(value: str) -> TsMetricsRetrieveMetcat:
    if value in TS_METRICS_RETRIEVE_METCAT_VALUES:
        return cast(TsMetricsRetrieveMetcat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_METRICS_RETRIEVE_METCAT_VALUES!r}")
