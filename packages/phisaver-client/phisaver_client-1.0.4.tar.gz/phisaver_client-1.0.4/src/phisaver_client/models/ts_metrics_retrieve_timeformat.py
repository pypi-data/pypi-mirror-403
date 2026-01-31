from typing import Literal, cast

TsMetricsRetrieveTimeformat = Literal["epoch", "epochms", "iso"]

TS_METRICS_RETRIEVE_TIMEFORMAT_VALUES: set[TsMetricsRetrieveTimeformat] = {
    "epoch",
    "epochms",
    "iso",
}


def check_ts_metrics_retrieve_timeformat(value: str) -> TsMetricsRetrieveTimeformat:
    if value in TS_METRICS_RETRIEVE_TIMEFORMAT_VALUES:
        return cast(TsMetricsRetrieveTimeformat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_METRICS_RETRIEVE_TIMEFORMAT_VALUES!r}")
