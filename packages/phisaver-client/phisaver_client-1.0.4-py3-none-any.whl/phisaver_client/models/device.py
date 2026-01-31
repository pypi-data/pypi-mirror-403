from __future__ import annotations

import datetime
import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from .. import types
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.device_video import DeviceVideo
    from ..models.metric_label import MetricLabel
    from ..models.rates import Rates


T = TypeVar("T", bound="Device")


@_attrs_define
class Device:
    """
    Attributes:
        id (int):
        ref (str):
        name (str):
        name_ref (str):
        owner_full_name (str):  Default: ''.
        solar (str):  Default: 'Unknown'.
        latest (datetime.datetime | None):
        latest_ago (int | None): Return seconds since last data
            -666 if no latest data (to distinguish from 0 and allow nice formatting in grafana)
        images (list[str]): Get the relative URLs of the images.
            Relative since we can't easily determine the
            the hostname the callee used (e.g. maybe proxied, via grafana, etc).
            eg. /media/2021-03-19_11.13.01_Large.jpg
            Images are publicly available if you know the url
            By convention, priorities <=50 are 'public' and returned
            Those with priorities >50 not returned
            Caching N+1 queries so cache. Use just device.ref as the key (args_rewrite)
        metrics (list[MetricLabel]):
        videos (list[DeviceVideo]):
        timezone (str):
        battery (bool):
        title (str | Unset):
        latitude (float | Unset):
        longitude (float | Unset):
        site_status (str | Unset):
        rates (Rates | Unset):
        users (list[int] | Unset): Each device may have many users
        goodwe_site_id (str | Unset):
    """

    id: int
    ref: str
    name: str
    name_ref: str
    latest: datetime.datetime | None
    latest_ago: int | None
    images: list[str]
    metrics: list[MetricLabel]
    videos: list[DeviceVideo]
    timezone: str
    battery: bool
    owner_full_name: str = ""
    solar: str = "Unknown"
    title: str | Unset = UNSET
    latitude: float | Unset = UNSET
    longitude: float | Unset = UNSET
    site_status: str | Unset = UNSET
    rates: Rates | Unset = UNSET
    users: list[int] | Unset = UNSET
    goodwe_site_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        ref = self.ref

        name = self.name

        name_ref = self.name_ref

        owner_full_name = self.owner_full_name

        solar = self.solar

        latest: None | str
        if isinstance(self.latest, datetime.datetime):
            latest = self.latest.isoformat()
        else:
            latest = self.latest

        latest_ago: int | None
        latest_ago = self.latest_ago

        images = self.images

        metrics = []
        for metrics_item_data in self.metrics:
            metrics_item = metrics_item_data.to_dict()
            metrics.append(metrics_item)

        videos = []
        for videos_item_data in self.videos:
            videos_item = videos_item_data.to_dict()
            videos.append(videos_item)

        timezone = self.timezone

        battery = self.battery

        title = self.title

        latitude = self.latitude

        longitude = self.longitude

        site_status = self.site_status

        rates: dict[str, Any] | Unset = UNSET
        if not isinstance(self.rates, Unset):
            rates = self.rates.to_dict()

        users: list[int] | Unset = UNSET
        if not isinstance(self.users, Unset):
            users = self.users

        goodwe_site_id = self.goodwe_site_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "ref": ref,
                "name": name,
                "name_ref": name_ref,
                "owner_full_name": owner_full_name,
                "solar": solar,
                "latest": latest,
                "latest_ago": latest_ago,
                "images": images,
                "metrics": metrics,
                "videos": videos,
                "timezone": timezone,
                "battery": battery,
            }
        )
        if title is not UNSET:
            field_dict["title"] = title
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if longitude is not UNSET:
            field_dict["longitude"] = longitude
        if site_status is not UNSET:
            field_dict["site_status"] = site_status
        if rates is not UNSET:
            field_dict["rates"] = rates
        if users is not UNSET:
            field_dict["users"] = users
        if goodwe_site_id is not UNSET:
            field_dict["goodwe_site_id"] = goodwe_site_id

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("id", (None, str(self.id).encode(), "text/plain")))

        files.append(("ref", (None, str(self.ref).encode(), "text/plain")))

        files.append(("name", (None, str(self.name).encode(), "text/plain")))

        files.append(("name_ref", (None, str(self.name_ref).encode(), "text/plain")))

        files.append(("owner_full_name", (None, str(self.owner_full_name).encode(), "text/plain")))

        files.append(("solar", (None, str(self.solar).encode(), "text/plain")))

        if isinstance(self.latest, datetime.datetime):
            files.append(("latest", (None, self.latest.isoformat().encode(), "text/plain")))
        else:
            files.append(("latest", (None, str(self.latest).encode(), "text/plain")))

        if isinstance(self.latest_ago, int):
            files.append(("latest_ago", (None, str(self.latest_ago).encode(), "text/plain")))
        else:
            files.append(("latest_ago", (None, str(self.latest_ago).encode(), "text/plain")))

        for images_item_element in self.images:
            files.append(("images", (None, str(images_item_element).encode(), "text/plain")))

        for metrics_item_element in self.metrics:
            files.append(("metrics", (None, json.dumps(metrics_item_element.to_dict()).encode(), "application/json")))

        for videos_item_element in self.videos:
            files.append(("videos", (None, json.dumps(videos_item_element.to_dict()).encode(), "application/json")))

        files.append(("timezone", (None, str(self.timezone).encode(), "text/plain")))

        files.append(("battery", (None, str(self.battery).encode(), "text/plain")))

        if not isinstance(self.title, Unset):
            files.append(("title", (None, str(self.title).encode(), "text/plain")))

        if not isinstance(self.latitude, Unset):
            files.append(("latitude", (None, str(self.latitude).encode(), "text/plain")))

        if not isinstance(self.longitude, Unset):
            files.append(("longitude", (None, str(self.longitude).encode(), "text/plain")))

        if not isinstance(self.site_status, Unset):
            files.append(("site_status", (None, str(self.site_status).encode(), "text/plain")))

        if not isinstance(self.rates, Unset):
            files.append(("rates", (None, json.dumps(self.rates.to_dict()).encode(), "application/json")))

        if not isinstance(self.users, Unset):
            for users_item_element in self.users:
                files.append(("users", (None, str(users_item_element).encode(), "text/plain")))

        if not isinstance(self.goodwe_site_id, Unset):
            files.append(("goodwe_site_id", (None, str(self.goodwe_site_id).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.device_video import DeviceVideo
        from ..models.metric_label import MetricLabel
        from ..models.rates import Rates

        d = dict(src_dict)
        id = d.pop("id")

        ref = d.pop("ref")

        name = d.pop("name")

        name_ref = d.pop("name_ref")

        owner_full_name = d.pop("owner_full_name")

        solar = d.pop("solar")

        def _parse_latest(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                latest_type_0 = isoparse(data)

                return latest_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        latest = _parse_latest(d.pop("latest"))

        def _parse_latest_ago(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        latest_ago = _parse_latest_ago(d.pop("latest_ago"))

        images = cast(list[str], d.pop("images"))

        metrics = []
        _metrics = d.pop("metrics")
        for metrics_item_data in _metrics:
            metrics_item = MetricLabel.from_dict(metrics_item_data)

            metrics.append(metrics_item)

        videos = []
        _videos = d.pop("videos")
        for videos_item_data in _videos:
            videos_item = DeviceVideo.from_dict(videos_item_data)

            videos.append(videos_item)

        timezone = d.pop("timezone")

        battery = d.pop("battery")

        title = d.pop("title", UNSET)

        latitude = d.pop("latitude", UNSET)

        longitude = d.pop("longitude", UNSET)

        site_status = d.pop("site_status", UNSET)

        _rates = d.pop("rates", UNSET)
        rates: Rates | Unset
        if isinstance(_rates, Unset):
            rates = UNSET
        else:
            rates = Rates.from_dict(_rates)

        users = cast(list[int], d.pop("users", UNSET))

        goodwe_site_id = d.pop("goodwe_site_id", UNSET)

        device = cls(
            id=id,
            ref=ref,
            name=name,
            name_ref=name_ref,
            owner_full_name=owner_full_name,
            solar=solar,
            latest=latest,
            latest_ago=latest_ago,
            images=images,
            metrics=metrics,
            videos=videos,
            timezone=timezone,
            battery=battery,
            title=title,
            latitude=latitude,
            longitude=longitude,
            site_status=site_status,
            rates=rates,
            users=users,
            goodwe_site_id=goodwe_site_id,
        )

        device.additional_properties = d
        return device

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
