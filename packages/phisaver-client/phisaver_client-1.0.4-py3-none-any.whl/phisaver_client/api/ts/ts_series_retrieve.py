import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ts_series_retrieve_attribute import TsSeriesRetrieveAttribute
from ...models.ts_series_retrieve_engine import TsSeriesRetrieveEngine
from ...models.ts_series_retrieve_format import TsSeriesRetrieveFormat
from ...models.ts_series_retrieve_function import TsSeriesRetrieveFunction
from ...models.ts_series_retrieve_metcat import TsSeriesRetrieveMetcat
from ...models.ts_series_retrieve_response_200 import TsSeriesRetrieveResponse200
from ...models.ts_series_retrieve_source import TsSeriesRetrieveSource
from ...models.ts_series_retrieve_timeformat import TsSeriesRetrieveTimeformat
from ...models.ts_series_retrieve_units import TsSeriesRetrieveUnits
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    attribute: TsSeriesRetrieveAttribute | Unset = "power",
    bin_: str,
    duration: str | Unset = UNSET,
    engine: TsSeriesRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsSeriesRetrieveFormat | Unset = UNSET,
    function: TsSeriesRetrieveFunction | Unset = "mean",
    metcat: TsSeriesRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsSeriesRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsSeriesRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsSeriesRetrieveUnits | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_attribute: str | Unset = UNSET
    if not isinstance(attribute, Unset):
        json_attribute = attribute

    params["attribute"] = json_attribute

    params["bin"] = bin_

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

    json_function: str | Unset = UNSET
    if not isinstance(function, Unset):
        json_function = function

    params["function"] = json_function

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
        "url": "/api/v1/ts/series/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> TsSeriesRetrieveResponse200 | None:
    if response.status_code == 200:
        response_200 = TsSeriesRetrieveResponse200.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[TsSeriesRetrieveResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    attribute: TsSeriesRetrieveAttribute | Unset = "power",
    bin_: str,
    duration: str | Unset = UNSET,
    engine: TsSeriesRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsSeriesRetrieveFormat | Unset = UNSET,
    function: TsSeriesRetrieveFunction | Unset = "mean",
    metcat: TsSeriesRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsSeriesRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsSeriesRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsSeriesRetrieveUnits | Unset = UNSET,
) -> Response[TsSeriesRetrieveResponse200]:
    """
    Args:
        attribute (TsSeriesRetrieveAttribute | Unset):  Default: 'power'.
        bin_ (str):
        duration (str | Unset):
        engine (TsSeriesRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsSeriesRetrieveFormat | Unset):
        function (TsSeriesRetrieveFunction | Unset):  Default: 'mean'.
        metcat (TsSeriesRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsSeriesRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsSeriesRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsSeriesRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TsSeriesRetrieveResponse200]
    """

    kwargs = _get_kwargs(
        attribute=attribute,
        bin_=bin_,
        duration=duration,
        engine=engine,
        fleet=fleet,
        format_=format_,
        function=function,
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
    attribute: TsSeriesRetrieveAttribute | Unset = "power",
    bin_: str,
    duration: str | Unset = UNSET,
    engine: TsSeriesRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsSeriesRetrieveFormat | Unset = UNSET,
    function: TsSeriesRetrieveFunction | Unset = "mean",
    metcat: TsSeriesRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsSeriesRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsSeriesRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsSeriesRetrieveUnits | Unset = UNSET,
) -> TsSeriesRetrieveResponse200 | None:
    """
    Args:
        attribute (TsSeriesRetrieveAttribute | Unset):  Default: 'power'.
        bin_ (str):
        duration (str | Unset):
        engine (TsSeriesRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsSeriesRetrieveFormat | Unset):
        function (TsSeriesRetrieveFunction | Unset):  Default: 'mean'.
        metcat (TsSeriesRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsSeriesRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsSeriesRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsSeriesRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TsSeriesRetrieveResponse200
    """

    return sync_detailed(
        client=client,
        attribute=attribute,
        bin_=bin_,
        duration=duration,
        engine=engine,
        fleet=fleet,
        format_=format_,
        function=function,
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
    attribute: TsSeriesRetrieveAttribute | Unset = "power",
    bin_: str,
    duration: str | Unset = UNSET,
    engine: TsSeriesRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsSeriesRetrieveFormat | Unset = UNSET,
    function: TsSeriesRetrieveFunction | Unset = "mean",
    metcat: TsSeriesRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsSeriesRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsSeriesRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsSeriesRetrieveUnits | Unset = UNSET,
) -> Response[TsSeriesRetrieveResponse200]:
    """
    Args:
        attribute (TsSeriesRetrieveAttribute | Unset):  Default: 'power'.
        bin_ (str):
        duration (str | Unset):
        engine (TsSeriesRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsSeriesRetrieveFormat | Unset):
        function (TsSeriesRetrieveFunction | Unset):  Default: 'mean'.
        metcat (TsSeriesRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsSeriesRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsSeriesRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsSeriesRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TsSeriesRetrieveResponse200]
    """

    kwargs = _get_kwargs(
        attribute=attribute,
        bin_=bin_,
        duration=duration,
        engine=engine,
        fleet=fleet,
        format_=format_,
        function=function,
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
    attribute: TsSeriesRetrieveAttribute | Unset = "power",
    bin_: str,
    duration: str | Unset = UNSET,
    engine: TsSeriesRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsSeriesRetrieveFormat | Unset = UNSET,
    function: TsSeriesRetrieveFunction | Unset = "mean",
    metcat: TsSeriesRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsSeriesRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsSeriesRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsSeriesRetrieveUnits | Unset = UNSET,
) -> TsSeriesRetrieveResponse200 | None:
    """
    Args:
        attribute (TsSeriesRetrieveAttribute | Unset):  Default: 'power'.
        bin_ (str):
        duration (str | Unset):
        engine (TsSeriesRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsSeriesRetrieveFormat | Unset):
        function (TsSeriesRetrieveFunction | Unset):  Default: 'mean'.
        metcat (TsSeriesRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsSeriesRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsSeriesRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsSeriesRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TsSeriesRetrieveResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            attribute=attribute,
            bin_=bin_,
            duration=duration,
            engine=engine,
            fleet=fleet,
            format_=format_,
            function=function,
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
