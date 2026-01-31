from typing import Any

from phisaver_client.client import AuthenticatedClient, Client
from phisaver_client.models.auth_token import AuthToken


def get_client_from_env(verify_ssl: bool | str = True) -> AuthenticatedClient:
    """
    Get an AuthenticatedClient using environment variables PHISAVER_URL, PHISAVER_USERNAME, and PHISAVER_PASSWORD.
    """
    import os

    url = os.getenv("PHISAVER_URL")
    username = os.getenv("PHISAVER_USERNAME")
    password = os.getenv("PHISAVER_PASSWORD")

    if not url or not username or not password:
        raise ValueError("Environment variables PHISAVER_URL, PHISAVER_USERNAME, and PHISAVER_PASSWORD must be set")

    return get_client(url, username, password, verify_ssl)


def get_client(base_url: str, username: str, password: str, verify_ssl: bool | str = True) -> AuthenticatedClient:
    """
    1. Send a form-encoded POST /api/v1/token/ with username/password.
    2. Parse back the JSON { "token": "<jwt-here>", … }.
    3. Return an AuthenticatedClient preconfigured with "Bearer <token>".
    """
    # Step 1: plain HTTP client
    plain = Client(base_url=base_url, verify_ssl=verify_ssl)  # noqa: F821

    # Build an AuthToken model (server will ignore its `token` field)
    # login_payload = AuthToken(username=username, password=password, token="")

    # Manually issue a form-encoded request (instead of using token_create.sync)
    
    response = plain.get_httpx_client().request(
        method="post",
        url="/api/v1/token/",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    resp_json = response.json()

    # Step 2: map JSON back onto AuthToken (so you get .token, plus any extra fields)
    token_model = AuthToken.from_dict(  # noqa: F821
        {
            "username": resp_json.get("username", username),
            "password": "",  # the returned password is usually omitted or blank
            "token": resp_json["token"],
        }
    )

    return AuthenticatedClient(base_url=base_url, prefix="Token", token=token_model.token, verify_ssl=verify_ssl)  # noqa: F821


# Type aliases for time series data structures
TimeSeriesPoint = tuple[float | int, float]  # [timestamp, value]
MetricSeries = list[TimeSeriesPoint]  # List of [timestamp, value] pairs
DeviceMetrics = dict[str, MetricSeries]  # metric_name -> series
TimeSeriesData = dict[str, DeviceMetrics]  # device_id -> metrics


def as_dict(response_model: Any) -> dict[str, Any]:
    """
    Convert an OpenAPI response model to a plain dict.
    
    For models with additionalProperties (like TsSeriesRetrieveResponse200),
    this provides direct dict access without needing .additional_properties
    
    Example:
        >>> from phisaver_client.api.ts import ts_series_retrieve
        >>> result = ts_series_retrieve.sync(client=client, bin_="1h", sites="demo1")
        >>> data = as_dict(result)  # Plain dict
        >>> production = data["demo1"]["Production"]  # Direct access
    
    Note: The model already supports dict-like access via __getitem__,
    so you can also use: result["demo1"]["Production"]
    """
    if hasattr(response_model, 'additional_properties'):
        return response_model.additional_properties
    elif hasattr(response_model, 'to_dict'):
        return response_model.to_dict()
    else:
        return dict(response_model)
