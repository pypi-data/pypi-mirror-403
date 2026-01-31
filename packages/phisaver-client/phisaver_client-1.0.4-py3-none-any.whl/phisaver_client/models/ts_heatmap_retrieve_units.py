from typing import Literal, cast

TsHeatmapRetrieveUnits = Literal["W"]

TS_HEATMAP_RETRIEVE_UNITS_VALUES: set[TsHeatmapRetrieveUnits] = {
    "W",
}


def check_ts_heatmap_retrieve_units(value: str) -> TsHeatmapRetrieveUnits:
    if value in TS_HEATMAP_RETRIEVE_UNITS_VALUES:
        return cast(TsHeatmapRetrieveUnits, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_HEATMAP_RETRIEVE_UNITS_VALUES!r}")
