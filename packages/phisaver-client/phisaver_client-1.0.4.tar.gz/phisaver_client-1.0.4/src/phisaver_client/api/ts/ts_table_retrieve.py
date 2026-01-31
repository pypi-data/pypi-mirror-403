import datetime
from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ts_table_retrieve_attribute import TsTableRetrieveAttribute
from ...models.ts_table_retrieve_engine import TsTableRetrieveEngine
from ...models.ts_table_retrieve_format import TsTableRetrieveFormat
from ...models.ts_table_retrieve_function import TsTableRetrieveFunction
from ...models.ts_table_retrieve_metcat import TsTableRetrieveMetcat
from ...models.ts_table_retrieve_response_200 import TsTableRetrieveResponse200
from ...models.ts_table_retrieve_source import TsTableRetrieveSource
from ...models.ts_table_retrieve_timeformat import TsTableRetrieveTimeformat
from ...models.ts_table_retrieve_units import TsTableRetrieveUnits
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    attribute: TsTableRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsTableRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsTableRetrieveFormat | Unset = UNSET,
    function: TsTableRetrieveFunction | Unset = "mean",
    metcat: TsTableRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsTableRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsTableRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsTableRetrieveUnits | Unset = UNSET,
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
        "url": "/api/v1/ts/table/",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> TsTableRetrieveResponse200 | None:
    if response.status_code == 200:
        response_200 = TsTableRetrieveResponse200.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[TsTableRetrieveResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    attribute: TsTableRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsTableRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsTableRetrieveFormat | Unset = UNSET,
    function: TsTableRetrieveFunction | Unset = "mean",
    metcat: TsTableRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsTableRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsTableRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsTableRetrieveUnits | Unset = UNSET,
) -> Response[TsTableRetrieveResponse200]:
    """Return data as table (i.e. without timestamps)

    Args:
        attribute (TsTableRetrieveAttribute | Unset):  Default: 'power'.
        duration (str | Unset):
        engine (TsTableRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsTableRetrieveFormat | Unset):
        function (TsTableRetrieveFunction | Unset):  Default: 'mean'.
        metcat (TsTableRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsTableRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsTableRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsTableRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TsTableRetrieveResponse200]
    """

    kwargs = _get_kwargs(
        attribute=attribute,
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
    attribute: TsTableRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsTableRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsTableRetrieveFormat | Unset = UNSET,
    function: TsTableRetrieveFunction | Unset = "mean",
    metcat: TsTableRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsTableRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsTableRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsTableRetrieveUnits | Unset = UNSET,
) -> TsTableRetrieveResponse200 | None:
    """Return data as table (i.e. without timestamps)

    Args:
        attribute (TsTableRetrieveAttribute | Unset):  Default: 'power'.
        duration (str | Unset):
        engine (TsTableRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsTableRetrieveFormat | Unset):
        function (TsTableRetrieveFunction | Unset):  Default: 'mean'.
        metcat (TsTableRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsTableRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsTableRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsTableRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TsTableRetrieveResponse200
    """

    return sync_detailed(
        client=client,
        attribute=attribute,
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
    attribute: TsTableRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsTableRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsTableRetrieveFormat | Unset = UNSET,
    function: TsTableRetrieveFunction | Unset = "mean",
    metcat: TsTableRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsTableRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsTableRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsTableRetrieveUnits | Unset = UNSET,
) -> Response[TsTableRetrieveResponse200]:
    """Return data as table (i.e. without timestamps)

    Args:
        attribute (TsTableRetrieveAttribute | Unset):  Default: 'power'.
        duration (str | Unset):
        engine (TsTableRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsTableRetrieveFormat | Unset):
        function (TsTableRetrieveFunction | Unset):  Default: 'mean'.
        metcat (TsTableRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsTableRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsTableRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsTableRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[TsTableRetrieveResponse200]
    """

    kwargs = _get_kwargs(
        attribute=attribute,
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
    attribute: TsTableRetrieveAttribute | Unset = "power",
    duration: str | Unset = UNSET,
    engine: TsTableRetrieveEngine | Unset = "influx",
    fleet: str | Unset = UNSET,
    format_: TsTableRetrieveFormat | Unset = UNSET,
    function: TsTableRetrieveFunction | Unset = "mean",
    metcat: TsTableRetrieveMetcat | Unset = UNSET,
    mets: str | Unset = UNSET,
    named: bool | Unset = False,
    sites: str | Unset = UNSET,
    source: TsTableRetrieveSource | Unset = "iotawatt",
    start: datetime.datetime | Unset = UNSET,
    stop: datetime.datetime | Unset = UNSET,
    timeformat: TsTableRetrieveTimeformat | Unset = UNSET,
    timezone: str | Unset = UNSET,
    units: TsTableRetrieveUnits | Unset = UNSET,
) -> TsTableRetrieveResponse200 | None:
    """Return data as table (i.e. without timestamps)

    Args:
        attribute (TsTableRetrieveAttribute | Unset):  Default: 'power'.
        duration (str | Unset):
        engine (TsTableRetrieveEngine | Unset):  Default: 'influx'.
        fleet (str | Unset):
        format_ (TsTableRetrieveFormat | Unset):
        function (TsTableRetrieveFunction | Unset):  Default: 'mean'.
        metcat (TsTableRetrieveMetcat | Unset):
        mets (str | Unset):
        named (bool | Unset):  Default: False.
        sites (str | Unset):
        source (TsTableRetrieveSource | Unset):  Default: 'iotawatt'.
        start (datetime.datetime | Unset):
        stop (datetime.datetime | Unset):
        timeformat (TsTableRetrieveTimeformat | Unset):
        timezone (str | Unset):
        units (TsTableRetrieveUnits | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        TsTableRetrieveResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            attribute=attribute,
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
