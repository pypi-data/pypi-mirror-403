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


T = TypeVar("T", bound="PatchedDevice")


@_attrs_define
class PatchedDevice:
    """
    Attributes:
        id (int | Unset):
        ref (str | Unset):
        name (str | Unset):
        title (str | Unset):
        name_ref (str | Unset):
        latitude (float | Unset):
        longitude (float | Unset):
        owner_full_name (str | Unset):  Default: ''.
        site_status (str | Unset):
        solar (str | Unset):  Default: 'Unknown'.
        latest (datetime.datetime | None | Unset):
        latest_ago (int | None | Unset): Return seconds since last data
            -666 if no latest data (to distinguish from 0 and allow nice formatting in grafana)
        images (list[str] | Unset): Get the relative URLs of the images.
            Relative since we can't easily determine the
            the hostname the callee used (e.g. maybe proxied, via grafana, etc).
            eg. /media/2021-03-19_11.13.01_Large.jpg
            Images are publicly available if you know the url
            By convention, priorities <=50 are 'public' and returned
            Those with priorities >50 not returned
            Caching N+1 queries so cache. Use just device.ref as the key (args_rewrite)
        rates (Rates | Unset):
        metrics (list[MetricLabel] | Unset):
        videos (list[DeviceVideo] | Unset):
        users (list[int] | Unset): Each device may have many users
        timezone (str | Unset):
        goodwe_site_id (str | Unset):
        battery (bool | Unset):
    """

    id: int | Unset = UNSET
    ref: str | Unset = UNSET
    name: str | Unset = UNSET
    title: str | Unset = UNSET
    name_ref: str | Unset = UNSET
    latitude: float | Unset = UNSET
    longitude: float | Unset = UNSET
    owner_full_name: str | Unset = ""
    site_status: str | Unset = UNSET
    solar: str | Unset = "Unknown"
    latest: datetime.datetime | None | Unset = UNSET
    latest_ago: int | None | Unset = UNSET
    images: list[str] | Unset = UNSET
    rates: Rates | Unset = UNSET
    metrics: list[MetricLabel] | Unset = UNSET
    videos: list[DeviceVideo] | Unset = UNSET
    users: list[int] | Unset = UNSET
    timezone: str | Unset = UNSET
    goodwe_site_id: str | Unset = UNSET
    battery: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        ref = self.ref

        name = self.name

        title = self.title

        name_ref = self.name_ref

        latitude = self.latitude

        longitude = self.longitude

        owner_full_name = self.owner_full_name

        site_status = self.site_status

        solar = self.solar

        latest: None | str | Unset
        if isinstance(self.latest, Unset):
            latest = UNSET
        elif isinstance(self.latest, datetime.datetime):
            latest = self.latest.isoformat()
        else:
            latest = self.latest

        latest_ago: int | None | Unset
        if isinstance(self.latest_ago, Unset):
            latest_ago = UNSET
        else:
            latest_ago = self.latest_ago

        images: list[str] | Unset = UNSET
        if not isinstance(self.images, Unset):
            images = self.images

        rates: dict[str, Any] | Unset = UNSET
        if not isinstance(self.rates, Unset):
            rates = self.rates.to_dict()

        metrics: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.metrics, Unset):
            metrics = []
            for metrics_item_data in self.metrics:
                metrics_item = metrics_item_data.to_dict()
                metrics.append(metrics_item)

        videos: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.videos, Unset):
            videos = []
            for videos_item_data in self.videos:
                videos_item = videos_item_data.to_dict()
                videos.append(videos_item)

        users: list[int] | Unset = UNSET
        if not isinstance(self.users, Unset):
            users = self.users

        timezone = self.timezone

        goodwe_site_id = self.goodwe_site_id

        battery = self.battery

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if ref is not UNSET:
            field_dict["ref"] = ref
        if name is not UNSET:
            field_dict["name"] = name
        if title is not UNSET:
            field_dict["title"] = title
        if name_ref is not UNSET:
            field_dict["name_ref"] = name_ref
        if latitude is not UNSET:
            field_dict["latitude"] = latitude
        if longitude is not UNSET:
            field_dict["longitude"] = longitude
        if owner_full_name is not UNSET:
            field_dict["owner_full_name"] = owner_full_name
        if site_status is not UNSET:
            field_dict["site_status"] = site_status
        if solar is not UNSET:
            field_dict["solar"] = solar
        if latest is not UNSET:
            field_dict["latest"] = latest
        if latest_ago is not UNSET:
            field_dict["latest_ago"] = latest_ago
        if images is not UNSET:
            field_dict["images"] = images
        if rates is not UNSET:
            field_dict["rates"] = rates
        if metrics is not UNSET:
            field_dict["metrics"] = metrics
        if videos is not UNSET:
            field_dict["videos"] = videos
        if users is not UNSET:
            field_dict["users"] = users
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if goodwe_site_id is not UNSET:
            field_dict["goodwe_site_id"] = goodwe_site_id
        if battery is not UNSET:
            field_dict["battery"] = battery

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        if not isinstance(self.id, Unset):
            files.append(("id", (None, str(self.id).encode(), "text/plain")))

        if not isinstance(self.ref, Unset):
            files.append(("ref", (None, str(self.ref).encode(), "text/plain")))

        if not isinstance(self.name, Unset):
            files.append(("name", (None, str(self.name).encode(), "text/plain")))

        if not isinstance(self.title, Unset):
            files.append(("title", (None, str(self.title).encode(), "text/plain")))

        if not isinstance(self.name_ref, Unset):
            files.append(("name_ref", (None, str(self.name_ref).encode(), "text/plain")))

        if not isinstance(self.latitude, Unset):
            files.append(("latitude", (None, str(self.latitude).encode(), "text/plain")))

        if not isinstance(self.longitude, Unset):
            files.append(("longitude", (None, str(self.longitude).encode(), "text/plain")))

        if not isinstance(self.owner_full_name, Unset):
            files.append(("owner_full_name", (None, str(self.owner_full_name).encode(), "text/plain")))

        if not isinstance(self.site_status, Unset):
            files.append(("site_status", (None, str(self.site_status).encode(), "text/plain")))

        if not isinstance(self.solar, Unset):
            files.append(("solar", (None, str(self.solar).encode(), "text/plain")))

        if not isinstance(self.latest, Unset):
            if isinstance(self.latest, datetime.datetime):
                files.append(("latest", (None, self.latest.isoformat().encode(), "text/plain")))
            else:
                files.append(("latest", (None, str(self.latest).encode(), "text/plain")))

        if not isinstance(self.latest_ago, Unset):
            if isinstance(self.latest_ago, int):
                files.append(("latest_ago", (None, str(self.latest_ago).encode(), "text/plain")))
            else:
                files.append(("latest_ago", (None, str(self.latest_ago).encode(), "text/plain")))

        if not isinstance(self.images, Unset):
            for images_item_element in self.images:
                files.append(("images", (None, str(images_item_element).encode(), "text/plain")))

        if not isinstance(self.rates, Unset):
            files.append(("rates", (None, json.dumps(self.rates.to_dict()).encode(), "application/json")))

        if not isinstance(self.metrics, Unset):
            for metrics_item_element in self.metrics:
                files.append(
                    ("metrics", (None, json.dumps(metrics_item_element.to_dict()).encode(), "application/json"))
                )

        if not isinstance(self.videos, Unset):
            for videos_item_element in self.videos:
                files.append(("videos", (None, json.dumps(videos_item_element.to_dict()).encode(), "application/json")))

        if not isinstance(self.users, Unset):
            for users_item_element in self.users:
                files.append(("users", (None, str(users_item_element).encode(), "text/plain")))

        if not isinstance(self.timezone, Unset):
            files.append(("timezone", (None, str(self.timezone).encode(), "text/plain")))

        if not isinstance(self.goodwe_site_id, Unset):
            files.append(("goodwe_site_id", (None, str(self.goodwe_site_id).encode(), "text/plain")))

        if not isinstance(self.battery, Unset):
            files.append(("battery", (None, str(self.battery).encode(), "text/plain")))

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.device_video import DeviceVideo
        from ..models.metric_label import MetricLabel
        from ..models.rates import Rates

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        ref = d.pop("ref", UNSET)

        name = d.pop("name", UNSET)

        title = d.pop("title", UNSET)

        name_ref = d.pop("name_ref", UNSET)

        latitude = d.pop("latitude", UNSET)

        longitude = d.pop("longitude", UNSET)

        owner_full_name = d.pop("owner_full_name", UNSET)

        site_status = d.pop("site_status", UNSET)

        solar = d.pop("solar", UNSET)

        def _parse_latest(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                latest_type_0 = isoparse(data)

                return latest_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        latest = _parse_latest(d.pop("latest", UNSET))

        def _parse_latest_ago(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        latest_ago = _parse_latest_ago(d.pop("latest_ago", UNSET))

        images = cast(list[str], d.pop("images", UNSET))

        _rates = d.pop("rates", UNSET)
        rates: Rates | Unset
        if isinstance(_rates, Unset):
            rates = UNSET
        else:
            rates = Rates.from_dict(_rates)

        _metrics = d.pop("metrics", UNSET)
        metrics: list[MetricLabel] | Unset = UNSET
        if _metrics is not UNSET:
            metrics = []
            for metrics_item_data in _metrics:
                metrics_item = MetricLabel.from_dict(metrics_item_data)

                metrics.append(metrics_item)

        _videos = d.pop("videos", UNSET)
        videos: list[DeviceVideo] | Unset = UNSET
        if _videos is not UNSET:
            videos = []
            for videos_item_data in _videos:
                videos_item = DeviceVideo.from_dict(videos_item_data)

                videos.append(videos_item)

        users = cast(list[int], d.pop("users", UNSET))

        timezone = d.pop("timezone", UNSET)

        goodwe_site_id = d.pop("goodwe_site_id", UNSET)

        battery = d.pop("battery", UNSET)

        patched_device = cls(
            id=id,
            ref=ref,
            name=name,
            title=title,
            name_ref=name_ref,
            latitude=latitude,
            longitude=longitude,
            owner_full_name=owner_full_name,
            site_status=site_status,
            solar=solar,
            latest=latest,
            latest_ago=latest_ago,
            images=images,
            rates=rates,
            metrics=metrics,
            videos=videos,
            users=users,
            timezone=timezone,
            goodwe_site_id=goodwe_site_id,
            battery=battery,
        )

        patched_device.additional_properties = d
        return patched_device

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
