from typing import Literal, cast

TsHeatmapRetrieveAttribute = Literal["current", "pf", "power", "soc", "status", "voltage"]

TS_HEATMAP_RETRIEVE_ATTRIBUTE_VALUES: set[TsHeatmapRetrieveAttribute] = {
    "current",
    "pf",
    "power",
    "soc",
    "status",
    "voltage",
}


def check_ts_heatmap_retrieve_attribute(value: str) -> TsHeatmapRetrieveAttribute:
    if value in TS_HEATMAP_RETRIEVE_ATTRIBUTE_VALUES:
        return cast(TsHeatmapRetrieveAttribute, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_HEATMAP_RETRIEVE_ATTRIBUTE_VALUES!r}")
