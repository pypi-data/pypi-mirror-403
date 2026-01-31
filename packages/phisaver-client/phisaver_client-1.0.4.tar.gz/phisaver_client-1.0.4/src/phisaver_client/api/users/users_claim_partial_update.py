from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.patched_user import PatchedUser
from ...models.user import User
from ...types import UNSET, Response, Unset


def _get_kwargs(
    id: int,
    ref: str,
    *,
    body: PatchedUser | PatchedUser | PatchedUser | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/api/v1/users/{id}/claim/{ref}/".format(
            id=quote(str(id), safe=""),
            ref=quote(str(ref), safe=""),
        ),
    }

    if isinstance(body, PatchedUser):
        if not isinstance(body, Unset):
            _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"
    if isinstance(body, PatchedUser):
        if not isinstance(body, Unset):
            _kwargs["data"] = body.to_dict()

        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if isinstance(body, PatchedUser):
        if not isinstance(body, Unset):
            _kwargs["files"] = body.to_multipart()

        headers["Content-Type"] = "multipart/form-data"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> User | None:
    if response.status_code == 200:
        response_200 = User.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[User]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    id: int,
    ref: str,
    *,
    client: AuthenticatedClient,
    body: PatchedUser | PatchedUser | PatchedUser | Unset = UNSET,
) -> Response[User]:
    r"""/user/1/device/hfs01a/
    PATCH data { claim_token: \"xxxx\" }
    Device(hfs01a).claim_token must match
    Return 200 with user with additional device

    Args:
        id (int):
        ref (str):
        body (PatchedUser | Unset):
        body (PatchedUser | Unset):
        body (PatchedUser | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[User]
    """

    kwargs = _get_kwargs(
        id=id,
        ref=ref,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    id: int,
    ref: str,
    *,
    client: AuthenticatedClient,
    body: PatchedUser | PatchedUser | PatchedUser | Unset = UNSET,
) -> User | None:
    r"""/user/1/device/hfs01a/
    PATCH data { claim_token: \"xxxx\" }
    Device(hfs01a).claim_token must match
    Return 200 with user with additional device

    Args:
        id (int):
        ref (str):
        body (PatchedUser | Unset):
        body (PatchedUser | Unset):
        body (PatchedUser | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        User
    """

    return sync_detailed(
        id=id,
        ref=ref,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    id: int,
    ref: str,
    *,
    client: AuthenticatedClient,
    body: PatchedUser | PatchedUser | PatchedUser | Unset = UNSET,
) -> Response[User]:
    r"""/user/1/device/hfs01a/
    PATCH data { claim_token: \"xxxx\" }
    Device(hfs01a).claim_token must match
    Return 200 with user with additional device

    Args:
        id (int):
        ref (str):
        body (PatchedUser | Unset):
        body (PatchedUser | Unset):
        body (PatchedUser | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[User]
    """

    kwargs = _get_kwargs(
        id=id,
        ref=ref,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    id: int,
    ref: str,
    *,
    client: AuthenticatedClient,
    body: PatchedUser | PatchedUser | PatchedUser | Unset = UNSET,
) -> User | None:
    r"""/user/1/device/hfs01a/
    PATCH data { claim_token: \"xxxx\" }
    Device(hfs01a).claim_token must match
    Return 200 with user with additional device

    Args:
        id (int):
        ref (str):
        body (PatchedUser | Unset):
        body (PatchedUser | Unset):
        body (PatchedUser | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        User
    """

    return (
        await asyncio_detailed(
            id=id,
            ref=ref,
            client=client,
            body=body,
        )
    ).parsed
