from typing import Literal, cast

TsHeatmapRetrieveTimeformat = Literal["epoch", "epochms", "iso"]

TS_HEATMAP_RETRIEVE_TIMEFORMAT_VALUES: set[TsHeatmapRetrieveTimeformat] = {
    "epoch",
    "epochms",
    "iso",
}


def check_ts_heatmap_retrieve_timeformat(value: str) -> TsHeatmapRetrieveTimeformat:
    if value in TS_HEATMAP_RETRIEVE_TIMEFORMAT_VALUES:
        return cast(TsHeatmapRetrieveTimeformat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_HEATMAP_RETRIEVE_TIMEFORMAT_VALUES!r}")
