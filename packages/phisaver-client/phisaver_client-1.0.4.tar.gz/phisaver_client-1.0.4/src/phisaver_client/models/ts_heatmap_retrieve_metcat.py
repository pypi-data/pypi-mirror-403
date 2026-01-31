from typing import Literal, cast

TsHeatmapRetrieveMetcat = Literal["battery", "calc", "load", "net", "other", "production"]

TS_HEATMAP_RETRIEVE_METCAT_VALUES: set[TsHeatmapRetrieveMetcat] = {
    "battery",
    "calc",
    "load",
    "net",
    "other",
    "production",
}


def check_ts_heatmap_retrieve_metcat(value: str) -> TsHeatmapRetrieveMetcat:
    if value in TS_HEATMAP_RETRIEVE_METCAT_VALUES:
        return cast(TsHeatmapRetrieveMetcat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_HEATMAP_RETRIEVE_METCAT_VALUES!r}")
