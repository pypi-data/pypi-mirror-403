from typing import Literal, cast

TsHeatmapRetrieveSource = Literal["calc", "inverter", "iotawatt", "nem"]

TS_HEATMAP_RETRIEVE_SOURCE_VALUES: set[TsHeatmapRetrieveSource] = {
    "calc",
    "inverter",
    "iotawatt",
    "nem",
}


def check_ts_heatmap_retrieve_source(value: str) -> TsHeatmapRetrieveSource:
    if value in TS_HEATMAP_RETRIEVE_SOURCE_VALUES:
        return cast(TsHeatmapRetrieveSource, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_HEATMAP_RETRIEVE_SOURCE_VALUES!r}")
