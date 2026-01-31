from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.password_reset_confirm import PasswordResetConfirm
from ...models.rest_auth_detail import RestAuthDetail
from ...types import UNSET, Response


def _get_kwargs(
    *,
    body: PasswordResetConfirm | PasswordResetConfirm | PasswordResetConfirm | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/password/reset/confirm/",
    }

    if isinstance(body, PasswordResetConfirm):
        _kwargs["json"] = body.to_dict()

        headers["Content-Type"] = "application/json"
    if isinstance(body, PasswordResetConfirm):
        _kwargs["data"] = body.to_dict()

        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if isinstance(body, PasswordResetConfirm):
        _kwargs["files"] = body.to_multipart()

        headers["Content-Type"] = "multipart/form-data"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> RestAuthDetail | None:
    if response.status_code == 200:
        response_200 = RestAuthDetail.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[RestAuthDetail]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: PasswordResetConfirm | PasswordResetConfirm | PasswordResetConfirm | Unset = UNSET,
) -> Response[RestAuthDetail]:
    """Password reset e-mail link is confirmed, therefore
    this resets the user's password.

    Accepts the following POST parameters: token, uid,
        new_password1, new_password2
    Returns the success/fail message.

    Args:
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RestAuthDetail]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: PasswordResetConfirm | PasswordResetConfirm | PasswordResetConfirm | Unset = UNSET,
) -> RestAuthDetail | None:
    """Password reset e-mail link is confirmed, therefore
    this resets the user's password.

    Accepts the following POST parameters: token, uid,
        new_password1, new_password2
    Returns the success/fail message.

    Args:
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RestAuthDetail
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: PasswordResetConfirm | PasswordResetConfirm | PasswordResetConfirm | Unset = UNSET,
) -> Response[RestAuthDetail]:
    """Password reset e-mail link is confirmed, therefore
    this resets the user's password.

    Accepts the following POST parameters: token, uid,
        new_password1, new_password2
    Returns the success/fail message.

    Args:
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RestAuthDetail]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: PasswordResetConfirm | PasswordResetConfirm | PasswordResetConfirm | Unset = UNSET,
) -> RestAuthDetail | None:
    """Password reset e-mail link is confirmed, therefore
    this resets the user's password.

    Accepts the following POST parameters: token, uid,
        new_password1, new_password2
    Returns the success/fail message.

    Args:
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.
        body (PasswordResetConfirm): Serializer for confirming a password reset attempt.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RestAuthDetail
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
