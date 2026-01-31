import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ts_metrics_retrieve_attribute import TsMetricsRetrieveAttribute
from ...models.ts_metrics_retrieve_engine import TsMetricsRetrieveEngine
from ...models.ts_metrics_retrieve_format import TsMetricsRetrieveFormat
from ...models.ts_metrics_retrieve_metcat import TsMetricsRetrieveMetcat
from ...models.ts_metrics_retrieve_response_200 import TsMetricsRetrieveResponse200
from ...models.ts_metrics_retrieve_source import TsMetricsRetrieveSource
from ...models.ts_metrics_retrieve_timeformat import TsMetricsRetrieveTimeformat
from ...models.ts_metrics_retrieve_units import TsMetricsRetrieveUnits
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    attribute: TsMetricsRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsMetricsRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsMetricsRetrieveFormat | Unset = UNSET,
    metcat: TsMetricsRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsMetricsRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsMetricsRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsMetricsRetrieveUnits | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_attribute: str | Unset = UNSET
    if not isinstance(attribute, Unset):
        json_attribute = attribute

    params["attribute"] = json_attribute

    params["duration"] = duration

    json_engine: str | Unset = UNSET
    if not isinstance(engine, Unset):
        json_engine = engine

    params["engine"] = json_engine

    params["fleet"] = fleet

    json_format_: str | Unset = UNSET
    if not isinstance(format_, Unset):
        json_format_ = format_

    params["format"] = json_format_

    json_metcat: str | Unset = UNSET
    if not isinstance(metcat, Unset):
        json_metcat = metcat

    params["metcat"] = json_metcat

    params["mets"] = mets

    params["named"] = named

    params["sites"] = sites

    json_source: str | Unset = UNSET
    if not isinstance(source, Unset):
        json_source = source

    params["source"] = json_source

    json_start: str | Unset = UNSET
    if not isinstance(start, Unset):
        json_start = start.isoformat()
    params["start"] = json_start

    json_stop: str | Unset = UNSET
    if not isinstance(stop, Unset):
        json_stop = stop.isoformat()
    params["stop"] = json_stop

    json_timeformat: str | Unset = UNSET
    if not isinstance(timeformat, Unset):
        json_timeformat = timeformat

    params["timeformat"] = json_timeformat

    params["timezone"] = timezone

    json_units: str | Unset = UNSET
    if not isinstance(units, Unset):
        json_units = units

    params["units"] = json_units

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/ts/metrics/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> TsMetricsRetrieveResponse200 | None:
    if response.status_code == 200:
        response_200 = TsMetricsRetrieveResponse200.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[TsMetricsRetrieveResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    attribute: TsMetricsRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsMetricsRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsMetricsRetrieveFormat | Unset = UNSET,
    metcat: TsMetricsRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsMetricsRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsMetricsRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsMetricsRetrieveUnits | Unset = UNSET,
) -> Response[TsMetricsRetrieveResponse200]:
    """Return metadata about metrics

    Args:
        attribute (TsMetricsRetrieveAttribute | Unset):  Default: 'power'.
        duration (str | Unset):
        engine (TsMetricsRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsMetricsRetrieveFormat | Unset):
        metcat (TsMetricsRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsMetricsRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsMetricsRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsMetricsRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TsMetricsRetrieveResponse200]
    """

    kwargs = _get_kwargs(
        attribute=attribute,
        duration=duration,
        engine=engine,
        fleet=fleet,
        format_=format_,
        metcat=metcat,
        mets=mets,
        named=named,
        sites=sites,
        source=source,
        start=start,
        stop=stop,
        timeformat=timeformat,
        timezone=timezone,
        units=units,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    attribute: TsMetricsRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsMetricsRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsMetricsRetrieveFormat | Unset = UNSET,
    metcat: TsMetricsRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsMetricsRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsMetricsRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsMetricsRetrieveUnits | Unset = UNSET,
) -> TsMetricsRetrieveResponse200 | None:
    """Return metadata about metrics

    Args:
        attribute (TsMetricsRetrieveAttribute | Unset):  Default: 'power'.
        duration (str | Unset):
        engine (TsMetricsRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsMetricsRetrieveFormat | Unset):
        metcat (TsMetricsRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsMetricsRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsMetricsRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsMetricsRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TsMetricsRetrieveResponse200
    """

    return sync_detailed(
        client=client,
        attribute=attribute,
        duration=duration,
        engine=engine,
        fleet=fleet,
        format_=format_,
        metcat=metcat,
        mets=mets,
        named=named,
        sites=sites,
        source=source,
        start=start,
        stop=stop,
        timeformat=timeformat,
        timezone=timezone,
        units=units,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    attribute: TsMetricsRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsMetricsRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsMetricsRetrieveFormat | Unset = UNSET,
    metcat: TsMetricsRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsMetricsRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsMetricsRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsMetricsRetrieveUnits | Unset = UNSET,
) -> Response[TsMetricsRetrieveResponse200]:
    """Return metadata about metrics

    Args:
        attribute (TsMetricsRetrieveAttribute | Unset):  Default: 'power'.
        duration (str | Unset):
        engine (TsMetricsRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsMetricsRetrieveFormat | Unset):
        metcat (TsMetricsRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsMetricsRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsMetricsRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsMetricsRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TsMetricsRetrieveResponse200]
    """

    kwargs = _get_kwargs(
        attribute=attribute,
        duration=duration,
        engine=engine,
        fleet=fleet,
        format_=format_,
        metcat=metcat,
        mets=mets,
        named=named,
        sites=sites,
        source=source,
        start=start,
        stop=stop,
        timeformat=timeformat,
        timezone=timezone,
        units=units,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    attribute: TsMetricsRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsMetricsRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsMetricsRetrieveFormat | Unset = UNSET,
    metcat: TsMetricsRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsMetricsRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsMetricsRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsMetricsRetrieveUnits | Unset = UNSET,
) -> TsMetricsRetrieveResponse200 | None:
    """Return metadata about metrics

    Args:
        attribute (TsMetricsRetrieveAttribute | Unset):  Default: 'power'.
        duration (str | Unset):
        engine (TsMetricsRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsMetricsRetrieveFormat | Unset):
        metcat (TsMetricsRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsMetricsRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsMetricsRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsMetricsRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TsMetricsRetrieveResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            attribute=attribute,
            duration=duration,
            engine=engine,
            fleet=fleet,
            format_=format_,
            metcat=metcat,
            mets=mets,
            named=named,
            sites=sites,
            source=source,
            start=start,
            stop=stop,
            timeformat=timeformat,
            timezone=timezone,
            units=units,
        )
    ).parsed
