from typing import Literal, cast

TsMetricsRetrieveAttribute = Literal["current", "pf", "power", "soc", "status", "voltage"]

TS_METRICS_RETRIEVE_ATTRIBUTE_VALUES: set[TsMetricsRetrieveAttribute] = {
    "current",
    "pf",
    "power",
    "soc",
    "status",
    "voltage",
}


def check_ts_metrics_retrieve_attribute(value: str) -> TsMetricsRetrieveAttribute:
    if value in TS_METRICS_RETRIEVE_ATTRIBUTE_VALUES:
        return cast(TsMetricsRetrieveAttribute, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_METRICS_RETRIEVE_ATTRIBUTE_VALUES!r}")
