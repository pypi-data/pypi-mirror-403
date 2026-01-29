"""Reusable runner that mirrors the original `samples/livox_python/start.py`."""

from __future__ import annotations

import atexit
import sys
import time
from typing import Optional

import numpy as np
import livox_sdk

from ..cfg import LivoxNetworkConfig, build_sdk_cfg
from ..ivox2.iceoryx_bridge import (
    IceoryxBridge,
    IceoryxBridgeConfig,
)
from ..ivox2.iceoryx_msgs import IceoryxMessageOverflow
from .config_store import load_cfg

atexit.register(livox_sdk.LivoxLidarSdkUninit)


class LivoxRunner:
    """High-level convenience wrapper around the pybind11 bindings."""

    _livox_dtype = np.dtype(
        [
            ("x", "i4"),
            ("y", "i4"),
            ("z", "i4"),
            ("reflectivity", "u1"),
            ("tag", "u1"),
        ],
    )

    def __init__(self, net_cfg: Optional[LivoxNetworkConfig] = None) -> None:
        self.net_cfg = net_cfg or load_cfg()
        self.cfg = build_sdk_cfg(self.net_cfg)
        self.pcd_buffer: list[np.ndarray] = []
        self.start_ts: Optional[int] = None
        self.frame_id = 0
        self.publish_interval_ns = int(
            1_000_000_000 / max(self.net_cfg.pub_rate_hz, 1)
        )
        self.iceoryx = IceoryxBridge(
            IceoryxBridgeConfig(
                frame_id=self.net_cfg.frame_id,
                pointcloud_service=self.net_cfg.pointcloud_service,
                imu_service=self.net_cfg.imu_service,
            )
        )

    def init_sdk(self) -> bool:
        from pathlib import Path

        # Use configured log path or default to user home
        if self.net_cfg.log_path:
            log_file = Path(self.net_cfg.log_path).absolute()
            log_dir = log_file.parent
        else:
            log_dir = Path.home() / ".livox" / "logs"
            log_file = log_dir / "livox_log.txt"

        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            livox_sdk.SetLogFilePath(str(log_file))
            livox_sdk.SaveLivoxLidarSdkLoggerFile()
            livox_sdk.DisableLivoxSdkConsoleLogger()
        except Exception as e:
            print(f"Warning: Could not setup logging at {log_dir}: {e}")

        success = livox_sdk.LivoxLidarSdkInitFromCfg(self.cfg)
        if success:
            print("Livox SDK initialized successfully.")
        else:
            print("Livox SDK failed to initialize.")
        return success

    def pointcloud_callback(self, packet) -> None:
        raw = packet.get_pts_data()
        points = np.frombuffer(raw, dtype=self._livox_dtype).copy()
        if len(points) == 0:
            return

        ts = packet.ts

        if self.start_ts is None:
            self.start_ts = ts

        self.pcd_buffer.append(points)

        if ts - self.start_ts >= self.publish_interval_ns:
            all_points = np.concatenate(self.pcd_buffer, axis=0)
            self._handle_full_frame(all_points, ts)
            self.frame_id += 1
            self.start_ts = None
            self.pcd_buffer = []

    def imu_callback(self, imu_packet) -> None:
        self.iceoryx.publish_imu(
            imu_packet.ts,
            imu_packet.gyr,
            imu_packet.acc,
        )

    def _handle_full_frame(self, points: np.ndarray, stamp_ns: int) -> None:
        print(f"[{self.frame_id}] Received {len(points)} points")
        if len(points) == 0:
            return
        xyz_mm = np.stack(
            [points["x"], points["y"], points["z"]],
            axis=-1,
        ).astype(np.float32)
        xyz_m = xyz_mm / 1000.0
        intensity = points["reflectivity"].astype(np.float32)
        tags = points["tag"].astype(np.uint8)
        try:
            self.iceoryx.publish_pointcloud(xyz_m, intensity, tags, stamp_ns)
        except IceoryxMessageOverflow as exc:
            print(f"Iceoryx pointcloud buffer overflow: {exc}")

    def run(self) -> None:
        if not self.init_sdk():
            sys.exit(1)

        livox_sdk.SetLivoxLidarPointCloudCallBack(self.pointcloud_callback)
        livox_sdk.SetLivoxLidarImuDataCallback(self.imu_callback)

        print("Publishing continuously; press Ctrl+C to stop ...")
        while True:
            time.sleep(1.0)

