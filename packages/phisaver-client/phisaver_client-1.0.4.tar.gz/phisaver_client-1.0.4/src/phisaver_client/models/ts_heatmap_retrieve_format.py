from typing import Literal, cast

TsHeatmapRetrieveFormat = Literal["csv", "json"]

TS_HEATMAP_RETRIEVE_FORMAT_VALUES: set[TsHeatmapRetrieveFormat] = {
    "csv",
    "json",
}


def check_ts_heatmap_retrieve_format(value: str) -> TsHeatmapRetrieveFormat:
    if value in TS_HEATMAP_RETRIEVE_FORMAT_VALUES:
        return cast(TsHeatmapRetrieveFormat, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_HEATMAP_RETRIEVE_FORMAT_VALUES!r}")
