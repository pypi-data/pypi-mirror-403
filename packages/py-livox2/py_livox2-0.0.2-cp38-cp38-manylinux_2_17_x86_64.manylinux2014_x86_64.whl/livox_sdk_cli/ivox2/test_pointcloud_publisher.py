"""CLI helper that publishes synthetic point clouds via iceoryx2."""

from __future__ import annotations

import argparse
import math
import sys
import time
from typing import Tuple

import numpy as np

from ..cli.config_store import load_cfg
from .iceoryx_bridge import (
    IceoryxBridge,
    IceoryxBridgeConfig,
    IceoryxBridgeUnavailable,
)
from .iceoryx_msgs import POINTCLOUD_MAX_POINTS


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish synthetic point clouds over iceoryx2."
    )
    parser.add_argument(
        "--points",
        type=int,
        default=20_000,
        help="Number of points per frame (default: 20000).",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=100000,
        help="Number of frames to send (default: 10). Pass 0 to keep running.",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=50.0,
        help="Frame publish rate in Hz (default: 2.0).",
    )
    parser.add_argument(
        "--pattern",
        choices=("random", "plane", "sphere", "spiral"),
        default="random",
        help="Spatial distribution for generated points.",
    )
    parser.add_argument(
        "--radius",
        type=float,
        default=2.0,
        help="Logical radius used by the pattern generators.",
    )
    parser.add_argument(
        "--height",
        type=float,
        default=1.0,
        help="Vertical span for plane/spiral patterns (meters).",
    )
    parser.add_argument(
        "--noise-std",
        type=float,
        default=0.01,
        help="Optional Gaussian noise (meters) added to xyz.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible frames.",
    )
    parser.add_argument(
        "--frame-id",
        type=str,
        default=None,
        help="Override the frame_id used in the published PointCloud2.",
    )
    parser.add_argument(
        "--pointcloud-service",
        type=str,
        default=None,
        help="Override the iceoryx service for pointcloud messages.",
    )
    return parser


def _build_bridge(args: argparse.Namespace) -> IceoryxBridge:
    net_cfg = load_cfg()
    frame_id = args.frame_id or net_cfg.frame_id
    service = args.pointcloud_service or net_cfg.pointcloud_service
    config = IceoryxBridgeConfig(
        frame_id=frame_id,
        pointcloud_service=service,
        imu_service=net_cfg.imu_service,
    )
    return IceoryxBridge(config)


def _make_pattern(
    pattern: str,
    points: int,
    radius: float,
    height: float,
    rng: np.random.Generator,
) -> np.ndarray:
    if pattern == "random":
        xyz = rng.uniform(-radius, radius, size=(points, 3))
    elif pattern == "plane":
        side = math.ceil(math.sqrt(points))
        grid = np.linspace(-radius, radius, side, dtype=np.float32)
        xv, yv = np.meshgrid(grid, grid, indexing="xy")
        base = np.stack([xv, yv, np.zeros_like(xv)], axis=-1).reshape(-1, 3)
        xyz = base[:points]
    elif pattern == "sphere":
        u = rng.random(points)
        v = rng.random(points)
        theta = 2.0 * math.pi * u
        phi = np.arccos(2.0 * v - 1.0)
        r = radius
        xyz = np.column_stack(
            [
                r * np.sin(phi) * np.cos(theta),
                r * np.sin(phi) * np.sin(theta),
                r * np.cos(phi),
            ]
        )
    elif pattern == "spiral":
        theta = np.linspace(0.0, 6.0 * math.pi, points, dtype=np.float32)
        z = np.linspace(-height / 2.0, height / 2.0, points, dtype=np.float32)
        radial = np.linspace(0.2, radius, points, dtype=np.float32)
        xyz = np.column_stack(
            [
                radial * np.cos(theta),
                radial * np.sin(theta),
                z,
            ]
        )
    else:  # pragma: no cover - parser prevents this
        raise ValueError(f"Unsupported pattern: {pattern}")
    return xyz.astype(np.float32, copy=False)


def _generate_frame(
    frame_idx: int,
    args: argparse.Namespace,
    rng: np.random.Generator,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    xyz = _make_pattern(args.pattern, args.points, args.radius, args.height, rng)
    if args.noise_std > 0.0:
        xyz += rng.normal(scale=args.noise_std, size=xyz.shape).astype(np.float32)

    intensity = np.linspace(0.0, 255.0, args.points, dtype=np.float32)
    tags = np.full(args.points, frame_idx % 256, dtype=np.uint8)
    return xyz, intensity, tags


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.points <= 0:
        parser.error("--points must be positive.")
    if args.points > POINTCLOUD_MAX_POINTS:
        parser.error(
            f"--points exceeds configured LIVOX_POINTCLOUD_MAX_POINTS ({POINTCLOUD_MAX_POINTS})."
        )
    if args.rate < 0:
        parser.error("--rate must be non-negative.")

    rng = np.random.default_rng(args.seed)

    try:
        bridge = _build_bridge(args)
    except IceoryxBridgeUnavailable as exc:
        parser.error(str(exc))

    interval = 1.0 / args.rate if args.rate > 0 else 0.0
    total_frames = args.frames if args.frames > 0 else None
    frame_idx = 0

    print(
        f"Publishing synthetic point clouds to '{bridge.config.pointcloud_service}' "
        f"(frame_id='{bridge.config.frame_id}')"
    )

    try:
        while True:
            xyz, intensity, tags = _generate_frame(frame_idx, args, rng)
            stamp_ns = time.time_ns()
            bridge.publish_pointcloud(xyz, intensity, tags, stamp_ns)
            gyr = (0.0, 0.0, 0.0)
            acc = (0.0, 0.0, 9.81)
            bridge.publish_imu(stamp_ns, gyr, acc)
            print(
                f"Sent frame {frame_idx} with {args.points} points at {time.strftime('%H:%M:%S')} "
                f"(pointcloud='{bridge.config.pointcloud_service}', imu='{bridge.config.imu_service}')"
            )
            frame_idx += 1
            if total_frames is not None and frame_idx >= total_frames:
                break
            if interval > 0:
                time.sleep(interval)
    except KeyboardInterrupt:
        print("\nInterrupted by user, stopping publisher.")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main(sys.argv[1:])


