from __future__ import annotations

import ctypes
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Literal, Optional

import iceoryx2 as iox2
import numpy as np

from mviz.ice_tools.msgs.odometry import Odometry
from mviz.ice_tools.msgs.pointcloud2 import PointCloud2, PointFieldDataType
from mviz.viser_tools.base_visualizer import VisualizerModule
from mviz.viser_tools.plugin_registry import register_plugin

logger = logging.getLogger(__name__)


DEFAULT_TOPIC = "/livox/lidar"
DEFAULT_ODOM_TOPIC = "/livox/odometry"
DEFAULT_COLOR = (245, 0, 245)
MIN_RETENTION = 0.05

FIELD_DTYPES: Dict[int, np.dtype] = {
    PointFieldDataType.INT8: np.int8,
    PointFieldDataType.UINT8: np.uint8,
    PointFieldDataType.INT16: np.int16,
    PointFieldDataType.UINT16: np.uint16,
    PointFieldDataType.INT32: np.int32,
    PointFieldDataType.UINT32: np.uint32,
    PointFieldDataType.FLOAT32: np.float32,
    PointFieldDataType.FLOAT64: np.float64,
}


CUBE_VERTICES = np.array(
    [
        [-0.5, -0.5, -0.5],
        [0.5, -0.5, -0.5],
        [0.5, 0.5, -0.5],
        [-0.5, 0.5, -0.5],
        [-0.5, -0.5, 0.5],
        [0.5, -0.5, 0.5],
        [0.5, 0.5, 0.5],
        [-0.5, 0.5, 0.5],
    ],
    dtype=np.float32,
)

CUBE_FACES = np.array(
    [
        [0, 1, 2],
        [0, 2, 3],
        [4, 5, 6],
        [4, 6, 7],
        [0, 1, 5],
        [0, 5, 4],
        [2, 3, 7],
        [2, 7, 6],
        [1, 2, 6],
        [1, 6, 5],
        [0, 3, 7],
        [0, 7, 4],
    ],
    dtype=np.int32,
)

OCTAHEDRON_VERTICES = np.array(
    [
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [-1.0, 0.0, 0.0],
        [0.0, -1.0, 0.0],
        [0.0, 0.0, -1.0],
    ],
    dtype=np.float32,
) * 0.5

OCTAHEDRON_FACES = np.array(
    [
        [0, 1, 2],
        [0, 2, 3],
        [0, 3, 4],
        [0, 4, 1],
        [5, 2, 1],
        [5, 3, 2],
        [5, 4, 3],
        [5, 1, 4],
    ],
    dtype=np.int32,
)

ColorMode = Literal["single", "x-gradient", "y-gradient", "z-gradient"]
GlyphMode = Literal["point", "voxel", "sphere"]


def _decode_field_name(field) -> str:
    raw = bytes(field.name)
    end = raw.find(b"\x00")
    if end >= 0:
        raw = raw[:end]
    return raw.decode("utf-8", errors="ignore")


def _axis_gradient(points: np.ndarray, axis: int) -> np.ndarray:
    if points.size == 0:
        return np.zeros((0, 3), dtype=np.float32)
    axis_values = points[:, axis]
    span = axis_values.max() - axis_values.min()
    if span <= 1e-6:
        normalized = np.zeros_like(axis_values)
    else:
        normalized = (axis_values - axis_values.min()) / max(span, 1e-6)
    red = normalized
    green = 1.0 - normalized
    blue = 0.5 + 0.5 * (0.5 - np.abs(normalized - 0.5))
    colors = np.stack([red, green, np.clip(blue, 0.0, 1.0)], axis=1).astype(np.float32)
    return colors


@dataclass
class PointFieldInfo:
    offset: int
    dtype: np.dtype


class PointCloudHistory:
    def __init__(self, retention: float) -> None:
        self.frames: Deque[tuple[float, np.ndarray]] = deque()
        self.retention = max(retention, MIN_RETENTION)

    def clear(self) -> None:
        self.frames.clear()

    def update_retention(self, value: float) -> None:
        self.retention = max(value, MIN_RETENTION)

    def add_frame(self, timestamp: float, points: np.ndarray) -> None:
        if points.size == 0:
            return
        self.frames.append((timestamp, points))
        self._trim(timestamp)

    def gather(self, timestamp: float, max_points: int) -> np.ndarray:
        self._trim(timestamp)
        if not self.frames:
            return np.zeros((0, 3), dtype=np.float32)
        points = np.concatenate([pts for _, pts in self.frames], axis=0)
        if max_points > 0 and points.shape[0] > max_points:
            points = points[-max_points:]
        return points

    def _trim(self, reference_time: float) -> None:
        cutoff = reference_time - self.retention
        while self.frames and self.frames[0][0] < cutoff:
            self.frames.popleft()


@register_plugin
class PointCloudViewerModule(VisualizerModule):
    plugin_cfg = {
        "default_topic": DEFAULT_TOPIC,
        "default_odom_topic": DEFAULT_ODOM_TOPIC,
        "retention_seconds": 1.5,
        "max_points": 120000,
        "point_size": 0.03,
        "point_shape": "rounded",
        "single_color": DEFAULT_COLOR,
        "connection_timeout": 1.0,
    }

    def __init__(self, server) -> None:
        super().__init__("Point Cloud Viewer", server)

        self.topic_name = self.plugin_cfg["default_topic"]
        self.odom_topic_name = self.plugin_cfg["default_odom_topic"]
        self.color_mode: ColorMode = "z-gradient"
        self.glyph_mode: GlyphMode = "point"
        self.retention_seconds = float(self.plugin_cfg["retention_seconds"])
        self.max_points = int(self.plugin_cfg["max_points"])
        self.point_size = float(self.plugin_cfg["point_size"])
        self.single_color = np.array(self.plugin_cfg["single_color"], dtype=np.float32) / 255.0

        self.history = PointCloudHistory(self.retention_seconds)
        self.node: Optional[iox2.Node] = None
        self.subscriber = None
        self._active_service_name: Optional[str] = None
        self._last_message_time: Optional[float] = None
        self._connected_recently = False
        
        # Odometry related
        self.odom_node: Optional[iox2.Node] = None
        self.odom_subscriber = None
        self._active_odom_service_name: Optional[str] = None
        self._last_odom_message_time: Optional[float] = None
        self._odom_connected_recently = False
        self._odom_frame_handle = None

        self._point_handle = None
        self._voxel_handle = None
        self._sphere_handle = None
        self._visualizer = None

        self._has_new_data = False
        self._last_glyph_mode = None
        self._last_point_size = None
        self._last_color_mode = None
        self._last_single_color = None
        self._last_rendered_points: Optional[np.ndarray] = None
        self._last_rendered_colors: Optional[np.ndarray] = None

        self._pointcloud_visible = True
        self._odom_visible = True

        self.topic_input = None
        self.pointcloud_enable_checkbox = None
        self.point_stats_text = None
        self.retention_slider = None
        self.max_points_slider = None
        self.size_slider = None
        self.glyph_dropdown = None
        self.color_dropdown = None
        self.color_picker = None

        self.odom_topic_input = None
        self.odom_enable_checkbox = None

        self._setup_subscriber()
        self._setup_odom_subscriber()

    def set_visualizer(self, visualizer) -> None:
        self._visualizer = visualizer
        self._sync_robot_visibility()

    def set_enabled(self, enabled: bool) -> None:
        super().set_enabled(enabled)
        self._sync_robot_visibility()

    def _sync_robot_visibility(self) -> None:
        if self._visualizer is None:
            return
        self._visualizer.set_robot_visible(not self.enabled)
        if not self.enabled:
            self._clear_scene()
            self.history.clear()

    def build_ui(self, parent_folder: Optional[str] = None) -> None:
        folder_title = parent_folder or self.name
        self.ui_folder = self.server.gui.add_folder(folder_title)
        with self.ui_folder:
            self.server.gui.add_markdown("Point Cloud")
            self.pointcloud_enable_checkbox = self.server.gui.add_checkbox(
                "Enable", initial_value=self._pointcloud_visible
            )
            
            @self.pointcloud_enable_checkbox.on_update
            def _(event) -> None:
                self._pointcloud_visible = event.target.value
                self._update_pointcloud_visibility()
            
            self.topic_input = self.server.gui.add_text("Topic", self.topic_name)
            reconnect_btn = self.server.gui.add_button("Apply Topic")

            @reconnect_btn.on_click
            def _(_event) -> None:
                if self.topic_input is None:
                    return
                desired = (self.topic_input.value or "").strip() or DEFAULT_TOPIC
                if desired == self.topic_name:
                    return
                self.topic_name = desired
                self._setup_subscriber()

            self.server.gui.add_markdown("---")
            self.retention_slider = self.server.gui.add_slider(
                "Retention (s)", min=0.1, max=10.0, step=0.1, initial_value=self.retention_seconds
            )

            @self.retention_slider.on_update
            def _(event) -> None:
                self.retention_seconds = float(event.target.value)
                self.history.update_retention(self.retention_seconds)

            self.max_points_slider = self.server.gui.add_slider(
                "Max Points", min=1000, max=1000000, step=1000, initial_value=self.max_points
            )

            @self.max_points_slider.on_update
            def _(event) -> None:
                self.max_points = int(event.target.value)

            self.size_slider = self.server.gui.add_slider(
                "Glyph Size (m)", min=0.005, max=0.2, step=0.005, initial_value=self.point_size
            )

            @self.size_slider.on_update
            def _(event) -> None:
                self.point_size = float(event.target.value)

            self.glyph_dropdown = self.server.gui.add_dropdown(
                "Point Shape",
                options=["point", "voxel", "sphere"],
                initial_value=self.glyph_mode,
            )

            @self.glyph_dropdown.on_update
            def _(event) -> None:
                self.glyph_mode = event.target.value  # type: ignore[assignment]

            self.color_dropdown = self.server.gui.add_dropdown(
                "Color Mode",
                options=["single", "z-gradient", "x-gradient", "y-gradient"],
                initial_value=self.color_mode,
            )

            @self.color_dropdown.on_update
            def _(event) -> None:
                self.color_mode = event.target.value  # type: ignore[assignment]

            self.color_picker = self.server.gui.add_rgb(
                "Single Color",
                initial_value=tuple(int(c * 255) for c in self.single_color),
            )

            @self.color_picker.on_update
            def _(event) -> None:
                rgb = np.array(event.target.value, dtype=np.float32) / 255.0
                self.single_color = np.clip(rgb, 0.0, 1.0)

            self.point_stats_text = self.server.gui.add_text("Buffered Points", "0")

            self.server.gui.add_markdown("---")
            self.server.gui.add_markdown("Odometry")
            self.odom_enable_checkbox = self.server.gui.add_checkbox(
                "Enable", initial_value=self._odom_visible
            )
            
            @self.odom_enable_checkbox.on_update
            def _(event) -> None:
                self._odom_visible = event.target.value
                self._update_odom_visibility()
            
            self.odom_topic_input = self.server.gui.add_text("Topic", self.odom_topic_name)
            odom_reconnect_btn = self.server.gui.add_button("Apply Odometry Topic")

            @odom_reconnect_btn.on_click
            def _(_event) -> None:
                if self.odom_topic_input is None:
                    return
                desired = (self.odom_topic_input.value or "").strip() or DEFAULT_ODOM_TOPIC
                if desired == self.odom_topic_name:
                    return
                self.odom_topic_name = desired
                self._setup_odom_subscriber()

    def _setup_subscriber(self) -> None:
        self._close_connections()
        try:
            iox2.set_log_level_from_env_or(iox2.LogLevel.Warn)
            self.node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)
            service_name = (self.topic_name or "").strip() or DEFAULT_TOPIC
            service = (
                self.node.service_builder(iox2.ServiceName.new(service_name))
                .publish_subscribe(PointCloud2)
                .open_or_create()
            )
            self.subscriber = service.subscriber_builder().create()
            self._active_service_name = service_name
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to create pointcloud subscriber: %s", exc)
            self.subscriber = None
            self.node = None
            self._active_service_name = None

    def _close_connections(self) -> None:
        if self.subscriber is not None:
            close = getattr(self.subscriber, "close", None)
            if callable(close):
                close()
        if self.node is not None:
            close = getattr(self.node, "close", None)
            if callable(close):
                close()
        self.subscriber = None
        self.node = None
        self._active_service_name = None
    
    def _setup_odom_subscriber(self) -> None:
        self._close_odom_connections()
        try:
            iox2.set_log_level_from_env_or(iox2.LogLevel.Warn)
            self.odom_node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)
            service_name = (self.odom_topic_name or "").strip() or DEFAULT_ODOM_TOPIC
            service = (
                self.odom_node.service_builder(iox2.ServiceName.new(service_name))
                .publish_subscribe(Odometry)
                .open_or_create()
            )
            self.odom_subscriber = service.subscriber_builder().create()
            self._active_odom_service_name = service_name
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to create odometry subscriber: %s", exc)
            self.odom_subscriber = None
            self.odom_node = None
            self._active_odom_service_name = None

    def _close_odom_connections(self) -> None:
        if self.odom_subscriber is not None:
            close = getattr(self.odom_subscriber, "close", None)
            if callable(close):
                close()
        if self.odom_node is not None:
            close = getattr(self.odom_node, "close", None)
            if callable(close):
                close()
        self.odom_subscriber = None
        self.odom_node = None
        self._active_odom_service_name = None

    def _ensure_point_handle(self):
        if self._point_handle is None:
            points = np.zeros((1, 3), dtype=np.float32)
            colors = np.ones((1, 3), dtype=np.float32)
            self._point_handle = self.server.scene.add_point_cloud(
                "/plugins/pointcloud/raw",
                points=points,
                colors=colors,
                point_size=self.point_size,
                point_shape=self.plugin_cfg["point_shape"],
            )
            self._point_handle.visible = False
        return self._point_handle

    def _ensure_voxel_handle(self):
        if self._voxel_handle is None:
            self._voxel_handle = self.server.scene.add_batched_meshes_simple(
                "/plugins/pointcloud/voxels",
                vertices=CUBE_VERTICES,
                faces=CUBE_FACES,
                batched_positions=np.zeros((1, 3), dtype=np.float32),
                batched_wxyzs=np.tile([1.0, 0.0, 0.0, 0.0], (1, 1)),
                batched_scales=np.ones((1,), dtype=np.float32),
                batched_colors=np.ones((1, 3), dtype=np.float32),
            )
            self._voxel_handle.visible = False
        return self._voxel_handle

    def _ensure_sphere_handle(self):
        if self._sphere_handle is None:
            self._sphere_handle = self.server.scene.add_batched_meshes_simple(
                "/plugins/pointcloud/spheres",
                vertices=OCTAHEDRON_VERTICES,
                faces=OCTAHEDRON_FACES,
                batched_positions=np.zeros((1, 3), dtype=np.float32),
                batched_wxyzs=np.tile([1.0, 0.0, 0.0, 0.0], (1, 1)),
                batched_scales=np.ones((1,), dtype=np.float32),
                batched_colors=np.ones((1, 3), dtype=np.float32),
            )
            self._sphere_handle.visible = False
        return self._sphere_handle

    def _deactivate_mesh_handles(self) -> None:
        if self._voxel_handle is not None:
            self._voxel_handle.visible = False
        if self._sphere_handle is not None:
            self._sphere_handle.visible = False

    def _deactivate_point_handle(self) -> None:
        if self._point_handle is not None:
            self._point_handle.visible = False

    def _ensure_odom_frame(self):
        if self._odom_frame_handle is None:
            self._odom_frame_handle = self.server.scene.add_frame(
                "/plugins/pointcloud/odom",
                position=(0.0, 0.0, 0.0),
                wxyz=(1.0, 0.0, 0.0, 0.0),
                show_axes=True,
                visible=True,
                axes_length=0.3,
                axes_radius=0.02,
            )
        return self._odom_frame_handle

    def _clear_scene(self) -> None:
        self._clear_pointcloud_scene()
        if self._odom_frame_handle is not None:
            self._odom_frame_handle.visible = False

        self._has_new_data = False
        self._last_glyph_mode = None
        self._last_point_size = None
        self._last_color_mode = None
        self._last_single_color = None
        self._last_rendered_points = None
        self._last_rendered_colors = None

    def _poll_messages(self) -> None:
        if self.subscriber is None:
            return
        while True:
            sample = self.subscriber.receive()
            if sample is None:
                break
            pointcloud = self._copy_message(sample)
            points = self._message_to_points(pointcloud)
            now = time.perf_counter()
            if points.size:
                self.history.add_frame(now, points)
                self._has_new_data = True
            self._last_message_time = now
    
    def _poll_odom_messages(self) -> None:
        if self.odom_subscriber is None:
            return
        while True:
            sample = self.odom_subscriber.receive()
            if sample is None:
                break
            odom = self._copy_odom_message(sample)
            self._update_odom_frame(odom)
            self._last_odom_message_time = time.perf_counter()
    
    def _copy_odom_message(self, sample) -> Odometry:
        payload_ptr = sample.payload()
        src = payload_ptr.contents
        dst = Odometry()
        ctypes.memmove(ctypes.addressof(dst), ctypes.addressof(src), ctypes.sizeof(Odometry))
        return dst
    
    def _update_odom_frame(self, odom: Odometry) -> None:
        if not self.enabled or not self._odom_visible:
            if self._odom_frame_handle is not None:
                self._odom_frame_handle.visible = False
            return
        frame = self._ensure_odom_frame()

        position = np.array([
            odom.pose.pose.position.x,
            odom.pose.pose.position.y,
            odom.pose.pose.position.z
        ], dtype=np.float32)

        quat_xyzw = np.array([
            odom.pose.pose.orientation.x,
            odom.pose.pose.orientation.y,
            odom.pose.pose.orientation.z,
            odom.pose.pose.orientation.w
        ], dtype=np.float32)

        quat_wxyz = np.array([
            quat_xyzw[3],  # w
            quat_xyzw[0],  # x
            quat_xyzw[1],  # y
            quat_xyzw[2]   # z
        ], dtype=np.float32)
        
        frame.position = position
        frame.wxyz = quat_wxyz
        frame.visible = True
    
    def _update_pointcloud_visibility(self) -> None:
        if not self._pointcloud_visible:
            self._clear_pointcloud_scene()
    
    def _update_odom_visibility(self) -> None:
        if not self._odom_visible:
            if self._odom_frame_handle is not None:
                self._odom_frame_handle.visible = False
    
    def _clear_pointcloud_scene(self) -> None:
        if self._point_handle is not None:
            self._point_handle.visible = False
            self._point_handle.points = np.zeros((0, 3), dtype=np.float32)
        if self._voxel_handle is not None:
            self._voxel_handle.visible = False
            self._voxel_handle.batched_positions = np.zeros((0, 3), dtype=np.float32)
        if self._sphere_handle is not None:
            self._sphere_handle.visible = False
            self._sphere_handle.batched_positions = np.zeros((0, 3), dtype=np.float32)

    def _copy_message(self, sample) -> PointCloud2:
        payload_ptr = sample.payload()
        src = payload_ptr.contents
        dst = PointCloud2()
        ctypes.memmove(ctypes.addressof(dst), ctypes.addressof(src), ctypes.sizeof(PointCloud2))
        return dst

    def _message_to_points(self, message: PointCloud2) -> np.ndarray:
        point_step = int(message.point_step)
        if point_step <= 0:
            return np.zeros((0, 3), dtype=np.float32)
        total_points = int(message.width * message.height)
        available = int(message.data_length // point_step)
        count = min(total_points, available)
        if count <= 0:
            return np.zeros((0, 3), dtype=np.float32)

        field_map: Dict[str, PointFieldInfo] = {}
        for idx in range(int(message.fields_count)):
            if idx >= len(message.fields):
                break
            field = message.fields[idx]
            name = _decode_field_name(field)
            if not name:
                continue
            dtype = FIELD_DTYPES.get(int(field.datatype))
            if dtype is None:
                continue
            field_map[name] = PointFieldInfo(offset=int(field.offset), dtype=dtype)

        if not {"x", "y", "z"}.issubset(field_map.keys()):
            return np.zeros((0, 3), dtype=np.float32)

        raw_buffer = np.ctypeslib.as_array(message.data)[: message.data_length]
        mv = memoryview(raw_buffer)
        axes = []
        for axis_name in ("x", "y", "z"):
            field = field_map[axis_name]
            dtype = field.dtype
            try:
                axis_values = np.ndarray(
                    shape=(count,),
                    dtype=dtype,
                    buffer=mv,
                    offset=field.offset,
                    strides=(point_step,),
                )
            except ValueError:
                return np.zeros((0, 3), dtype=np.float32)
            if axis_values.dtype != np.float32:
                axis_values = axis_values.astype(np.float32)
            axes.append(axis_values)
        stacked = np.stack(axes, axis=1)
        return stacked.astype(np.float32, copy=False)

    def _build_colors(self, points: np.ndarray) -> np.ndarray:
        if points.size == 0:
            return np.zeros((0, 3), dtype=np.float32)
        if self.color_mode == "single":
            return np.tile(self.single_color, (points.shape[0], 1)).astype(np.float32)
        axis_map = {"x-gradient": 0, "y-gradient": 1, "z-gradient": 2}
        axis = axis_map.get(self.color_mode, 2)
        return _axis_gradient(points, axis)

    def _update_connection_ui(self, now: float) -> None:
        # Connection status tracking (no UI display needed)
        timeout = float(self.plugin_cfg["connection_timeout"])
        connected = (
            self._last_message_time is not None and (now - self._last_message_time) < timeout
        )
        self._connected_recently = connected
        odom_connected = (
            self._last_odom_message_time is not None and (now - self._last_odom_message_time) < timeout
        )
        self._odom_connected_recently = odom_connected

    def _render_points(self, points: np.ndarray, colors: np.ndarray) -> None:
        if not self._pointcloud_visible:
            self._clear_pointcloud_scene()
            return
        
        settings_changed = (
            self.glyph_mode != self._last_glyph_mode
            or self.point_size != self._last_point_size
            or self.color_mode != self._last_color_mode
            or (self.color_mode == "single" and self._last_single_color is not None and not np.array_equal(self.single_color, self._last_single_color))
        )
        
        if not self._has_new_data and not settings_changed:
            return
        
        data_changed = (
            self._last_rendered_points is None
            or self._last_rendered_colors is None
            or points.shape[0] != self._last_rendered_points.shape[0]
        )
        
        if not data_changed and self._has_new_data:
            data_changed = (
                not np.array_equal(points, self._last_rendered_points)
                or not np.array_equal(colors, self._last_rendered_colors)
            )
        
        if not data_changed and not settings_changed:
            return
        
        self._has_new_data = False
        old_glyph_mode = self._last_glyph_mode
        self._last_glyph_mode = self.glyph_mode
        self._last_point_size = self.point_size
        self._last_color_mode = self.color_mode
        if self.color_mode == "single":
            self._last_single_color = self.single_color.copy()
        
        self._last_rendered_points = points.copy() if points.size > 0 else points
        self._last_rendered_colors = colors.copy() if colors.size > 0 else colors
        
        with self.server.atomic():
            if self.glyph_mode == "point":
                handle = self._ensure_point_handle()
                self._deactivate_mesh_handles()
                if points.size == 0:
                    handle.visible = False
                    return
                handle.visible = True
                handle.points = points
                handle.colors = colors
                handle.point_size = self.point_size
                handle.point_shape = self.plugin_cfg["point_shape"]
                return

            if old_glyph_mode is not None and self.glyph_mode != old_glyph_mode:
                if self._voxel_handle is not None:
                    self._voxel_handle.visible = False
                    self._voxel_handle = None
                if self._sphere_handle is not None:
                    self._sphere_handle.visible = False
                    self._sphere_handle = None

            if self.glyph_mode == "voxel":
                handle = self._ensure_voxel_handle()
            else:
                handle = self._ensure_sphere_handle()
            self._deactivate_point_handle()

            if points.size == 0:
                handle.visible = False
                return

            handle.visible = True
            handle.batched_positions = points
            handle.batched_wxyzs = np.tile([1.0, 0.0, 0.0, 0.0], (points.shape[0], 1))
            handle.batched_scales = np.full((points.shape[0],), self.point_size, dtype=np.float32)
            handle.batched_colors = colors

    def update(self):
        self._poll_messages()
        self._poll_odom_messages()
        now = time.perf_counter()
        points = self.history.gather(now, self.max_points)
        colors = self._build_colors(points)
        self._render_points(points, colors)
        self._update_connection_ui(now)
        if self.point_stats_text is not None:
            self.point_stats_text.value = f"{points.shape[0]:,d}"

    def shutdown(self) -> None:
        self._close_connections()
        self._close_odom_connections()
        self._clear_scene()
        self.history.clear()


