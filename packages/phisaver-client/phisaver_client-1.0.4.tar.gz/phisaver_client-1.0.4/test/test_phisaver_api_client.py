import os
from datetime import datetime as dt
from zoneinfo import ZoneInfo

import pytest
import requests

from phisaver_client.api.devices.devices_list import sync as get_devices
from phisaver_client.api.devices.devices_list import sync_detailed as get_devices_detailed  # noqa: F401
from phisaver_client.api.devices.devices_retrieve import sync as get_device
from phisaver_client.api.ts.ts_series_retrieve import sync_detailed as get_ts_series_detailed  # noqa: F401
from phisaver_client.api.ts.ts_table_retrieve import sync_detailed as get_ts_table_detailed  # noqa: F401
from phisaver_client.client import AuthenticatedClient
from phisaver_client.helpers import get_client, get_client_from_env

BNE = ZoneInfo("Australia/Brisbane")

url = os.getenv("PHISAVER_URL")
password = os.getenv("PHISAVER_PASSWORD")
username = os.getenv("PHISAVER_USERNAME")
token = os.getenv("PHISAVER_TOKEN")

assert url, "Environment variable PHISAVER_URL must be set"
assert password, "Environment variable PHISAVER_PASSWORD must be set"
assert username, "Environment variable PHISAVER_USERNAME must be set"


@pytest.fixture(scope="module")
def phisaver_api():
    assert url and password and username, (
        "Environment variables PHISAVER_URL, PHISAVER_PASSWORD, and PHISAVER_USERNAME must be set"
    )
    # Check if the server is running
    if requests.get(url).status_code != 200:
        print(
            "Run the following:\ncd ~/phisaver\ndirenv allow\n~/phisaver/.venv/bin/python ~/phisaver/manage.py runserver"
        )
        raise RuntimeError(f"Cannot connect to PHISAVER server at {url}. Please check the URL and server status.")

    return get_client_from_env(verify_ssl=False)  # or True if you want to enable SSL verification


def test_device(phisaver_api):
    client = phisaver_api

    device = get_device("hfs01a", client=client)
    print(f"Retrieved device: {device}")
    assert device.id == 686

    devices = get_devices(client=client)
    assert len(devices) > 0, "No devices found"
    print(f"Retrieved devices: {devices}")


def test_ts_series(phisaver_api):
    series = get_ts_series_detailed(
        sites=["hfs01a"],
        client=phisaver_api,
        start=dt(2023, 1, 1, tzinfo=BNE),
        stop=dt(2024, 1, 1, tzinfo=BNE),
        bin_="1d",
        mets=["Production"],
        units="W",
    )

    print(f"Retrieved series: {series.parsed}")
    assert series.parsed["hfs01a"]["Production"] is not None, "No data found for the specified series"


def test_ts_table(phisaver_api):
    table = get_ts_table_detailed(
        sites=["hfs01a"],
        client=phisaver_api,
        start=dt(2023, 1, 1, tzinfo=BNE),
        stop=dt(2024, 1, 1, tzinfo=BNE),
        units="W",
    )
    print(f"Retrieved table: {table.parsed}")
    assert table.parsed["hfs01a"] is not None, "No data found for the specified table"


def test_connect_with_password():
    client = get_client(url, username, password)
    device = get_device("hfs01a", client=client)
    print(f"Retrieved device: {device}")
    assert device.id == 686


def test_connect_with_token():
    assert url and token, "Environment variables PHISAVER_URL and PHISAVER_TOKEN must be set"

    authclient = AuthenticatedClient(
        base_url=url,
        prefix="Token",
        token=token,
        verify_ssl=False,  # or False if you want to disable SSL verification
    )
    device = get_device("hfs01a", client=authclient)
    assert device.id == 686
