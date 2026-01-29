"""Iceoryx message definitions for Livox data publishing."""

from __future__ import annotations

import ctypes
import os
from typing import Iterable

FRAME_ID_MAX_LEN = int(os.getenv("LIVOX_FRAME_ID_MAX_LEN", "64"))
POINT_FIELD_NAME_MAX_LEN = int(os.getenv("LIVOX_POINT_FIELD_NAME_MAX_LEN", "32"))
POINT_FIELD_CAPACITY = int(os.getenv("LIVOX_POINT_FIELD_CAPACITY", "6"))
POINTCLOUD_MAX_POINTS = int(os.getenv("LIVOX_POINTCLOUD_MAX_POINTS", "200000"))
POINTCLOUD_POINT_STEP = int(os.getenv("LIVOX_POINTCLOUD_POINT_STEP", "20"))
POINTCLOUD_MAX_DATA_BYTES = POINTCLOUD_MAX_POINTS * POINTCLOUD_POINT_STEP


def _validate_positive(name: str, value: int) -> int:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


POINT_FIELD_CAPACITY = _validate_positive("POINT_FIELD_CAPACITY", POINT_FIELD_CAPACITY)
FRAME_ID_MAX_LEN = _validate_positive("FRAME_ID_MAX_LEN", FRAME_ID_MAX_LEN)
POINTCLOUD_POINT_STEP = _validate_positive("POINTCLOUD_POINT_STEP", POINTCLOUD_POINT_STEP)
POINTCLOUD_MAX_DATA_BYTES = _validate_positive(
    "POINTCLOUD_MAX_DATA_BYTES", POINTCLOUD_MAX_DATA_BYTES
)


class PointFieldDataType:
    """Enum values copied from sensor_msgs/msg/PointField."""

    INT8 = 1
    UINT8 = 2
    INT16 = 3
    UINT16 = 4
    INT32 = 5
    UINT32 = 6
    FLOAT32 = 7
    FLOAT64 = 8


class Time(ctypes.Structure):
    """ROS-style builtin_interfaces/msg/Time."""

    _fields_ = [
        ("sec", ctypes.c_uint32),
        ("nanosec", ctypes.c_uint32),
    ]

    @staticmethod
    def type_name() -> str:
        return "Time"


class Header(ctypes.Structure):
    """std_msgs/msg/Header with fixed-size frame_id."""

    _fields_ = [
        ("stamp", Time),
        ("frame_id", ctypes.c_char * FRAME_ID_MAX_LEN),
    ]

    @staticmethod
    def type_name() -> str:
        return "Header"


class PointField(ctypes.Structure):
    """sensor_msgs/msg/PointField with bounded name storage."""

    _fields_ = [
        ("name", ctypes.c_char * POINT_FIELD_NAME_MAX_LEN),
        ("offset", ctypes.c_uint32),
        ("datatype", ctypes.c_uint8),
        ("count", ctypes.c_uint32),
        ("_padding", ctypes.c_uint8 * 3),
    ]

    @staticmethod
    def type_name() -> str:
        return "PointField"


class PointCloud2(ctypes.Structure):
    """Bounded variant of sensor_msgs/msg/PointCloud2."""

    _fields_ = [
        ("header", Header),
        ("height", ctypes.c_uint32),
        ("width", ctypes.c_uint32),
        ("fields_count", ctypes.c_uint32),
        ("fields", PointField * POINT_FIELD_CAPACITY),
        ("is_bigendian", ctypes.c_bool),
        ("point_step", ctypes.c_uint32),
        ("row_step", ctypes.c_uint32),
        ("data_length", ctypes.c_uint32),
        ("data", ctypes.c_uint8 * POINTCLOUD_MAX_DATA_BYTES),
        ("is_dense", ctypes.c_bool),
        ("_padding", ctypes.c_uint8 * 3),
    ]

    @staticmethod
    def type_name() -> str:
        return "PointCloud2"


class Quaternion(ctypes.Structure):
    """geometry_msgs/msg/Quaternion."""

    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
        ("w", ctypes.c_double),
    ]

    @staticmethod
    def type_name() -> str:
        return "Quaternion"


class Vector3(ctypes.Structure):
    """geometry_msgs/msg/Vector3."""

    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
    ]

    @staticmethod
    def type_name() -> str:
        return "Vector3"


CovarianceArray = ctypes.c_double * 9


class Imu(ctypes.Structure):
    """sensor_msgs/msg/Imu."""

    _fields_ = [
        ("header", Header),
        ("orientation", Quaternion),
        ("orientation_covariance", CovarianceArray),
        ("angular_velocity", Vector3),
        ("angular_velocity_covariance", CovarianceArray),
        ("linear_acceleration", Vector3),
        ("linear_acceleration_covariance", CovarianceArray),
    ]

    @staticmethod
    def type_name() -> str:
        return "Imu"


class Point(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
    ]

    @staticmethod
    def type_name() -> str:
        return "Point"


class Pose(ctypes.Structure):
    _fields_ = [
        ("position", Point),
        ("orientation", Quaternion),
    ]

    @staticmethod
    def type_name() -> str:
        return "Pose"


PoseCovarianceArray = ctypes.c_double * 36


class PoseWithCovariance(ctypes.Structure):
    _fields_ = [
        ("pose", Pose),
        ("covariance", PoseCovarianceArray),
    ]

    @staticmethod
    def type_name() -> str:
        return "PoseWithCovariance"


class Twist(ctypes.Structure):
    _fields_ = [
        ("linear", Vector3),
        ("angular", Vector3),
    ]

    @staticmethod
    def type_name() -> str:
        return "Twist"


TwistCovarianceArray = ctypes.c_double * 36


class TwistWithCovariance(ctypes.Structure):
    _fields_ = [
        ("twist", Twist),
        ("covariance", TwistCovarianceArray),
    ]

    @staticmethod
    def type_name() -> str:
        return "TwistWithCovariance"


class Odometry(ctypes.Structure):
    _fields_ = [
        ("header", Header),
        ("pose", PoseWithCovariance),
        ("twist", TwistWithCovariance),
    ]

    @staticmethod
    def type_name() -> str:
        return "Odometry"


class IceoryxMessageOverflow(RuntimeError):
    """Raised when data exceeds the statically allocated message capacity."""


def write_c_string(owner: ctypes.Structure, field_name: str, value: str) -> None:
    field = getattr(type(owner), field_name)
    capacity = getattr(field, "size", 0)
    if capacity <= 0:
        return
    encoded = value.encode("utf-8")
    if len(encoded) >= capacity:
        encoded = encoded[: capacity - 1]
    setattr(owner, field_name, encoded)


def set_covariance(target: CovarianceArray, values: Iterable[float]) -> None:
    """Copy covariance iterable (length 9) into the ctypes array."""
    for idx, value in enumerate(values):
        if idx >= 9:
            break
        target[idx] = value


def set_pose_covariance(target: PoseCovarianceArray, values: Iterable[float]) -> None:
    for idx, value in enumerate(values):
        if idx >= 36:
            break
        target[idx] = value


def set_twist_covariance(target: TwistCovarianceArray, values: Iterable[float]) -> None:
    for idx, value in enumerate(values):
        if idx >= 36:
            break
        target[idx] = value

