from typing import Literal, cast

TsHeatmapRetrieveEngine = Literal["influx", "timescale"]

TS_HEATMAP_RETRIEVE_ENGINE_VALUES: set[TsHeatmapRetrieveEngine] = {
    "influx",
    "timescale",
}


def check_ts_heatmap_retrieve_engine(value: str) -> TsHeatmapRetrieveEngine:
    if value in TS_HEATMAP_RETRIEVE_ENGINE_VALUES:
        return cast(TsHeatmapRetrieveEngine, value)
    raise TypeError(f"Unexpected value {value!r}. Expected one of {TS_HEATMAP_RETRIEVE_ENGINE_VALUES!r}")
