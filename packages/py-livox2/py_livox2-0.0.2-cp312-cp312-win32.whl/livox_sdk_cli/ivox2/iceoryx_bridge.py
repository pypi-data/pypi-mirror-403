"""Utilities for publishing Livox data via iceoryx2."""

from __future__ import annotations

import ctypes
import logging
from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np

from .iceoryx_msgs import (
    Header,
    IceoryxMessageOverflow,
    Imu,
    PointCloud2,
    PointFieldDataType,
    POINTCLOUD_POINT_STEP,
    set_covariance,
    write_c_string,
)

LOGGER = logging.getLogger(__name__)


class IceoryxBridgeUnavailable(RuntimeError):
    """Raised when iceoryx2 is not installed or fails to initialize."""


@dataclass(slots=True)
class IceoryxBridgeConfig:
    """Runtime knobs for the IceoryxBridge."""

    frame_id: str = "livox_frame"
    pointcloud_service: str = "livox/pointcloud2/main"
    imu_service: str = "livox/imu/main"


class _PointCloudBuilder:
    def __init__(self, frame_id: str) -> None:
        self.frame_id = frame_id
        self._dtype = np.dtype(
            [
                ("x", np.float32),
                ("y", np.float32),
                ("z", np.float32),
                ("intensity", np.float32),
                ("tag", np.uint8),
                ("line", np.uint8),
                ("padding", np.uint16),
            ],
            align=True,
        )
        self._field_specs: Tuple[Tuple[str, int, int, int], ...] = (
            ("x", 0, PointFieldDataType.FLOAT32, 1),
            ("y", 4, PointFieldDataType.FLOAT32, 1),
            ("z", 8, PointFieldDataType.FLOAT32, 1),
            ("intensity", 12, PointFieldDataType.FLOAT32, 1),
            ("tag", 16, PointFieldDataType.UINT8, 1),
            ("line", 17, PointFieldDataType.UINT8, 1),
        )
        self._capacity_bytes = len(PointCloud2().data)
        if self._dtype.itemsize != POINTCLOUD_POINT_STEP:
            LOGGER.warning(
                "Point dtype (%s bytes) does not match configured POINT_STEP (%s bytes).",
                self._dtype.itemsize,
                POINTCLOUD_POINT_STEP,
            )

    def build(
        self,
        xyz_m: np.ndarray,
        intensity: np.ndarray,
        tags: np.ndarray,
        stamp_ns: int,
    ) -> PointCloud2:
        msg = PointCloud2()
        _populate_header(msg.header, self.frame_id, stamp_ns)
        width = int(xyz_m.shape[0])
        msg.height = 1
        msg.width = width
        msg.point_step = self._dtype.itemsize
        msg.row_step = msg.point_step * width
        msg.fields_count = len(self._field_specs)
        for idx, spec in enumerate(self._field_specs):
            field = msg.fields[idx]
            write_c_string(field, "name", spec[0])
            field.offset = spec[1]
            field.datatype = spec[2]
            field.count = spec[3]
        msg.is_bigendian = False
        if intensity.shape[0] != width or tags.shape[0] != width:
            raise ValueError(
                f"Mismatched point cloud buffers: xyz={width}, intensity={intensity.shape[0]}, tags={tags.shape[0]}"
            )
        valid_mask = np.isfinite(xyz_m)
        msg.is_dense = bool(width > 0 and valid_mask.all())

        if width == 0:
            msg.data_length = 0
            return msg

        structured = np.zeros(width, dtype=self._dtype)
        structured["x"] = xyz_m[:, 0].astype(np.float32, copy=False)
        structured["y"] = xyz_m[:, 1].astype(np.float32, copy=False)
        structured["z"] = xyz_m[:, 2].astype(np.float32, copy=False)
        structured["intensity"] = intensity.astype(np.float32, copy=False)
        structured["tag"] = tags.astype(np.uint8, copy=False)
        structured["line"] = 0

        raw = structured.tobytes()
        if len(raw) > self._capacity_bytes:
            raise IceoryxMessageOverflow(
                f"PointCloud2 payload requires {len(raw)} bytes but buffer is {self._capacity_bytes} bytes. "
                "Increase LIVOX_POINTCLOUD_MAX_POINTS to publish larger frames."
            )
        ctypes.memmove(msg.data, raw, len(raw))
        msg.data_length = len(raw)
        return msg


class _ImuBuilder:
    def __init__(self, frame_id: str) -> None:
        self.frame_id = frame_id
        self._gyro_cov = (1e-4, 0.0, 0.0, 0.0, 1e-4, 0.0, 0.0, 0.0, 1e-4)
        self._acc_cov = (1e-2, 0.0, 0.0, 0.0, 1e-2, 0.0, 0.0, 0.0, 1e-2)

    def build(self, stamp_ns: int, gyr: Iterable[float], acc: Iterable[float]) -> Imu:
        msg = Imu()
        _populate_header(msg.header, self.frame_id, stamp_ns)
        msg.orientation.w = 1.0
        msg.orientation.x = 0.0
        msg.orientation.y = 0.0
        msg.orientation.z = 0.0
        set_covariance(msg.orientation_covariance, (-1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

        gyr_vals = list(gyr)
        acc_vals = list(acc)
        msg.angular_velocity.x = float(gyr_vals[0])
        msg.angular_velocity.y = float(gyr_vals[1])
        msg.angular_velocity.z = float(gyr_vals[2])
        set_covariance(msg.angular_velocity_covariance, self._gyro_cov)

        msg.linear_acceleration.x = float(acc_vals[0])
        msg.linear_acceleration.y = float(acc_vals[1])
        msg.linear_acceleration.z = float(acc_vals[2])
        set_covariance(msg.linear_acceleration_covariance, self._acc_cov)
        return msg


def _populate_header(header: Header, frame_id: str, stamp_ns: int) -> None:
    sec, nanosec = divmod(int(max(stamp_ns, 0)), 1_000_000_000)
    header.stamp.sec = sec & 0xFFFFFFFF
    header.stamp.nanosec = nanosec
    write_c_string(header, "frame_id", frame_id)


class IceoryxBridge:
    """Wraps the iceoryx2 IPC primitives and Livox-specific message builders."""

    def __init__(self, config: IceoryxBridgeConfig) -> None:
        self.config = config
        self._iox2 = self._import_iceoryx()
        self._node = self._iox2.NodeBuilder.new().create(self._iox2.ServiceType.Ipc)
        self._pointcloud_pub = (
            self._node.service_builder(self._iox2.ServiceName.new(config.pointcloud_service))
            .publish_subscribe(PointCloud2)
            .open_or_create()
            .publisher_builder()
            .create()
        )
        self._imu_pub = (
            self._node.service_builder(self._iox2.ServiceName.new(config.imu_service))
            .publish_subscribe(Imu)
            .open_or_create()
            .publisher_builder()
            .create()
        )
        self._point_builder = _PointCloudBuilder(config.frame_id)
        self._imu_builder = _ImuBuilder(config.frame_id)
        LOGGER.info(
            "Initialized iceoryx2 publishers: pointcloud=%s, imu=%s",
            config.pointcloud_service,
            config.imu_service,
        )

    @staticmethod
    def _import_iceoryx():
        try:
            import iceoryx2 as iox2  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover - import guard
            raise IceoryxBridgeUnavailable(
                "iceoryx2 is not installed. Install it via `pip install iceoryx2` or "
                "`pip install .[ipc]` to enable shared-memory publishing."
            ) from exc
        return iox2

    def publish_pointcloud(
        self,
        xyz_m: np.ndarray,
        intensity: np.ndarray,
        tags: np.ndarray,
        stamp_ns: int,
    ) -> None:
        msg = self._point_builder.build(xyz_m, intensity, tags, stamp_ns)
        sample = self._pointcloud_pub.loan_uninit()
        sample = sample.write_payload(msg)
        sample.send()

    def publish_imu(self, stamp_ns: int, gyr: Iterable[float], acc: Iterable[float]) -> None:
        msg = self._imu_builder.build(stamp_ns, gyr, acc)
        sample = self._imu_pub.loan_uninit()
        sample = sample.write_payload(msg)
        sample.send()

