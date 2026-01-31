from typing import Literal, cast

TsMetricsRetrieveFormat = Literal["csv", "json"]

TS_METRICS_RETRIEVE_FORMAT_VALUES: set[TsMetricsRetrieveFormat] = {
    "csv",
    "json",
}


def check_ts_metrics_retrieve_format(value: str) -> TsMetricsRetrieveFormat:
    if value in TS_METRICS_RETRIEVE_FORMAT_VALUES:
        return cast(TsMetricsRetrieveFormat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_METRICS_RETRIEVE_FORMAT_VALUES!r}")
