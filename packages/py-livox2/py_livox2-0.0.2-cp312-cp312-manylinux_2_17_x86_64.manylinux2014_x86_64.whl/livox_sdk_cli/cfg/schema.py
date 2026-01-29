"""Dataclasses and helpers for Livox runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LivoxNetworkConfig:
    """Network and runtime knobs loaded from YAML."""

    lidar_name: str = "MID360"
    lidar_ipaddr: str = "192.168.1.201"
    lidar_subnet_mask: str = "255.255.255.0"
    lidar_gateway: str = "192.168.1.1"
    host_ip: str = "192.168.1.50"
    multicast_ip: str = "224.1.1.5"
    lidar_cmd_data_port: int = 56100
    lidar_push_msg_port: int = 56200
    lidar_point_data_port: int = 56300
    lidar_imu_data_port: int = 56400
    lidar_log_data_port: int = 56500
    host_cmd_data_port: int = 56101
    host_push_msg_port: int = 56201
    host_point_data_port: int = 56301
    host_imu_data_port: int = 56401
    host_log_data_port: int = 56501
    pub_rate_hz: float = 10.0
    frame_id: str = "livox_frame"
    pointcloud_service: str = "livox/lidar"
    imu_service: str = "livox/imu"
    log_path: str = ""


def build_sdk_cfg(net_cfg: LivoxNetworkConfig):
    """Translate the dataclass into the pybind11 cfg object."""
    import livox_sdk  # pylint: disable=import-outside-toplevel

    cfg = livox_sdk.PyLivoxLidarCfg()
    cfg.lidar_name = net_cfg.lidar_name
    cfg.lidar_ipaddr = net_cfg.lidar_ipaddr
    cfg.lidar_subnet_mask = net_cfg.lidar_subnet_mask
    cfg.lidar_gateway = net_cfg.lidar_gateway
    cfg.host_ip = net_cfg.host_ip
    cfg.multicast_ip = net_cfg.multicast_ip
    cfg.lidar_cmd_data_port = net_cfg.lidar_cmd_data_port
    cfg.lidar_push_msg_port = net_cfg.lidar_push_msg_port
    cfg.lidar_point_data_port = net_cfg.lidar_point_data_port
    cfg.lidar_imu_data_port = net_cfg.lidar_imu_data_port
    cfg.lidar_log_data_port = net_cfg.lidar_log_data_port
    cfg.host_cmd_data_port = net_cfg.host_cmd_data_port
    cfg.host_push_msg_port = net_cfg.host_push_msg_port
    cfg.host_point_data_port = net_cfg.host_point_data_port
    cfg.host_imu_data_port = net_cfg.host_imu_data_port
    cfg.host_log_data_port = net_cfg.host_log_data_port
    return cfg

