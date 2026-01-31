"""
Motion Viewer - Multi-robot motion visualization plugin for mviz.

Features:
- Upload NPZ files via button click or drag-to-button
- Support multiple robots with automatic color assignment
- Synchronized playback controls for all robots
- Robot management UI with remove functionality
"""

import numpy as np
import os
import time
import tempfile
import viser
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from termcolor import cprint

from mviz.viser_tools.plugin_registry import register_plugin
from mviz.utils.models import ViserUrdf
from mviz import G1_URDF_PATH, TMP_DIR


COLOR_PALETTE: List[Tuple[int, int, int]] = [

    (231, 76, 60),    # Red
    (46, 204, 113),   # Green
    (52, 152, 219),   # Blue
    (155, 89, 182),   # Purple
    (241, 196, 15),   # Yellow
    (230, 126, 34),   # Orange
    (26, 188, 156),   # Teal
    (149, 165, 166),  # Gray
]


class SimpleNpzMotion:
    
    def __init__(self, data: np.lib.npyio.NpzFile, target_fps: int = 30):
        self.fps = target_fps
        self.motion_dict: Dict[str, np.ndarray] = {}
        
        if 'fps' in data:
            file_fps = int(data['fps'][0]) if isinstance(data['fps'], np.ndarray) else int(data['fps'])
        else:
            file_fps = 50
        skip = max(1, file_fps // self.fps)

        
        body_pos_w = data['body_pos_w'][::skip].astype(np.float32)
        body_quat_w = data['body_quat_w'][::skip].astype(np.float32)
        
        joint_pos = data['joint_pos'][::skip].astype(np.float32)
        try:


            from mviz.configs.robot import ISAAC_SIM_TO_G1_JOINT_MAPPING
            if ISAAC_SIM_TO_G1_JOINT_MAPPING is not None:
                joint_pos = joint_pos[:, ISAAC_SIM_TO_G1_JOINT_MAPPING]
        except Exception:
            pass
        
        # wxyz -> xyzw
        body_rot_xyzw = body_quat_w[:, :, [1, 2, 3, 0]]
        root_rot_xyzw = body_quat_w[:, 0, [1, 2, 3, 0]]
        root_pos = body_pos_w[:, 0, :]
        
        self.motion_dict['root_pos'] = root_pos
        self.motion_dict['root_rot'] = root_rot_xyzw

        self.motion_dict['joint_pos'] = joint_pos
        self.length = root_pos.shape[0]
    
    def get_frame(self, frame_idx: int) -> Dict[str, np.ndarray]:
        frame_idx = int(np.clip(frame_idx, 0, self.length - 1))
        return {
            'root_pos': self.motion_dict['root_pos'][frame_idx],
            'root_rot': self.motion_dict['root_rot'][frame_idx],
            'joint_pos': self.motion_dict['joint_pos'][frame_idx],
        }


@dataclass
class RobotInstance:
    id: str
    name: str
    color: Tuple[int, int, int]
    motion: SimpleNpzMotion
    robot_vis: ViserUrdf
    offset_x: float = 0.0
    visible: bool = True


@register_plugin

class MotionViewerModule:
    
    plugin_cfg = {
        'target_fps': 30,
        'default_playback_speed': 1.0,
        'loop_by_default': True,
    }
    
    def __init__(self, server: viser.ViserServer):
        self.name = "Motion Viewer"
        self.server = server
        self.enabled = True
        self.ui_folder: Optional[viser.GuiHandle] = None

        self.target_fps = self.plugin_cfg['target_fps']
        self.playback_speed = self.plugin_cfg['default_playback_speed']
        self.loop = self.plugin_cfg['loop_by_default']

        self.robot_instances: List[RobotInstance] = []

        self._next_robot_id = 0
        self._color_index = 0
        self._urdf_path = G1_URDF_PATH

        
        self.current_frame: float = 0.0
        self.playing = False
        self.last_update_time = time.time()

        self._upload_button = None
        self._robots_folder = None
        self._robot_ui_elements: Dict[str, List] = {}
        self._frame_slider = None
        self._frame_info = None
        self._play_button = None
        self._pause_button = None
        self._speed_slider = None
        self._loop_checkbox = None

    def _get_next_color(self) -> Tuple[int, int, int]:
        color = COLOR_PALETTE[self._color_index % len(COLOR_PALETTE)]
        self._color_index += 1
        return color

    def _calculate_offset(self, robot_index: int) -> float:
        return robot_index * 2.0

    def _add_robot_from_bytes(self, filename: str, content: bytes) -> Optional[RobotInstance]:
        try:
            with tempfile.NamedTemporaryFile(suffix='.npz', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            data = np.load(temp_path, allow_pickle=True)
            motion = SimpleNpzMotion(data, target_fps=self.target_fps)
            
            os.unlink(temp_path)
            
            if motion.length == 0:
                cprint(f"No motion data found in {filename}", 'yellow')

                return None
            
            # Get color and create robot visualization
            color = self._get_next_color()
            robot_id = f"robot_{self._next_robot_id}"
            self._next_robot_id += 1
            
            offset_x = self._calculate_offset(len(self.robot_instances))
            
            robot_node_name = f"/{robot_id}"
            robot_vis = ViserUrdf(
                self.server,
                self._urdf_path,
                robot_node_name=robot_node_name,
                mesh_color=color,
            )
            
            robot_vis.update_base(
                np.array([offset_x, 0.0, 0.82], dtype=np.float32),
                np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
            )
            
            display_name = os.path.basename(filename).replace('.npz', '')
            robot_instance = RobotInstance(
                id=robot_id,
                name=display_name,
                color=color,
                motion=motion,
                robot_vis=robot_vis,
                offset_x=offset_x,
            )
            
            self.robot_instances.append(robot_instance)
            
            self._add_robot_ui(robot_instance)
            self._update_playback_controls()
            
            cprint(f"Added robot: {display_name} (color: RGB{color})", 'green')
            return robot_instance
            
        except Exception as e:
            cprint(f"Error loading {filename}: {e}", 'red')
            import traceback
            traceback.print_exc()
            return None
    
    def _remove_robot(self, robot_id: str) -> None:
        robot_to_remove = None
        for robot in self.robot_instances:
            if robot.id == robot_id:
                robot_to_remove = robot
                break
        
        if robot_to_remove is None:
            return
        
        if robot_to_remove.robot_vis is not None:
            robot_to_remove.robot_vis.remove()
        
        if robot_id in self._robot_ui_elements:
            for elem in self._robot_ui_elements[robot_id]:
                try:
                    elem.remove()
                except Exception:
                    pass
            del self._robot_ui_elements[robot_id]
        
        self.robot_instances.remove(robot_to_remove)
        
        for i, robot in enumerate(self.robot_instances):
            new_offset = self._calculate_offset(i)
            robot.offset_x = new_offset
        
        self._update_playback_controls()
        
        cprint(f"Removed robot: {robot_to_remove.name}", 'yellow')

    
    def _get_max_frame(self) -> int:
        if not self.robot_instances:
            return 1
        return max(robot.motion.length - 1 for robot in self.robot_instances)
    
    def _add_robot_ui(self, robot: RobotInstance) -> None:
        if self._robots_folder is None:
            return
        
        elements = []
        with self._robots_folder:
            r, g, b = robot.color
            color_icon = self._get_color_name(robot.color)
            
            display_name = robot.name
            if len(display_name) > 22:
                display_name = display_name[:20] + "..."
            
            robot_folder = self.server.gui.add_folder(f"{color_icon} {display_name}")
            elements.append(robot_folder)
            
            with robot_folder:
                self.server.gui.add_markdown(
                    f"**Frames:** {robot.motion.length} | **FPS:** {robot.motion.fps}"
                )
                
                visibility_cb = self.server.gui.add_checkbox(
                    "Visible",
                    initial_value=True,
                )
                
                robot_id = robot.id
                @visibility_cb.on_update
                def _(event, rid=robot_id):
                    self._toggle_robot_visibility(rid, event.target.value)

                remove_btn = self.server.gui.add_button(
                    "Remove Robot",
                    icon="trash",
                    color="red",
                )
                
                @remove_btn.on_click
                def _(event, rid=robot_id):
                    self._remove_robot(rid)
        
        self._robot_ui_elements[robot.id] = elements
    
    def _get_color_name(self, color: Tuple[int, int, int]) -> str:
        color_names = {
            (231, 76, 60): "🔴",
            (46, 204, 113): "🟢",
            (52, 152, 219): "🔵",
            (155, 89, 182): "🟣",
            (241, 196, 15): "🟡",
            (230, 126, 34): "🟠",
            (26, 188, 156): "🩵",
            (149, 165, 166): "⚪",
        }
        return color_names.get(color, "⚫")
    
    def _toggle_robot_visibility(self, robot_id: str, visible: bool) -> None:
        for robot in self.robot_instances:
            if robot.id == robot_id:
                robot.visible = visible
                if robot.robot_vis is not None:
                    robot.robot_vis.set_frame_visible(visible)
                    for mesh in robot.robot_vis._meshes:
                        mesh.visible = visible
                break
    
    def _update_playback_controls(self) -> None:
        has_robots = len(self.robot_instances) > 0
        max_frame = self._get_max_frame()
        
        if self._frame_slider is not None:
            self._frame_slider.visible = has_robots
            if has_robots:
                self._frame_slider.max = int(max_frame)
        
        if self._frame_info is not None:
            self._frame_info.visible = has_robots
            if has_robots:
                self._frame_info.content = f"Frame: 0 / {max_frame}"
        
        if self._play_button is not None:
            self._play_button.visible = has_robots and not self.playing
        if self._pause_button is not None:
            self._pause_button.visible = has_robots and self.playing
        if self._speed_slider is not None:
            self._speed_slider.visible = has_robots
        if self._loop_checkbox is not None:
            self._loop_checkbox.visible = has_robots
    
    def _inject_drag_drop_overlay(self) -> None:
        drop_zone_html = '''

<div id="mviz-drop-zone" style="
    border: 3px dashed #3498db;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1) 0%, rgba(155, 89, 182, 0.1) 100%);
    margin: 10px 0;
    cursor: pointer;
    transition: all 0.3s ease;
" ondragover="this.style.background='rgba(52, 152, 219, 0.3)'; this.style.borderColor='#2ecc71'; event.preventDefault();"
   ondragleave="this.style.background='linear-gradient(135deg, rgba(52, 152, 219, 0.1) 0%, rgba(155, 89, 182, 0.1) 100%)'; this.style.borderColor='#3498db';"
   ondrop="
        event.preventDefault();
        this.style.background='linear-gradient(135deg, rgba(52, 152, 219, 0.1) 0%, rgba(155, 89, 182, 0.1) 100%)';
        this.style.borderColor='#3498db';
        var files = event.dataTransfer.files;
        for (var i = 0; i < files.length; i++) {
            if (files[i].name.endsWith('.npz')) {
                var input = document.querySelector('input[type=file][accept*=npz]') || document.querySelector('input[type=file]');
                if (input) {
                    var dt = new DataTransfer();
                    dt.items.add(files[i]);
                    input.files = dt.files;
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }
        }
   ">
    <div style="font-size: 48px; margin-bottom: 10px;">📁</div>
    <div style="font-size: 16px; color: #3498db; font-weight: bold;">Drop NPZ files here</div>
    <div style="font-size: 12px; color: #7f8c8d; margin-top: 5px;">or click the button above</div>
</div>

<!-- Hidden iframe for global drag-drop initialization -->
<iframe id="mviz-init-frame" style="display:none;" srcdoc="
<html><body><script>
(function() {
    if (parent._mvizDragDropInit) return;
    parent._mvizDragDropInit = true;
    
    // Create overlay in parent document
    var overlay = parent.document.createElement('div');
    overlay.id = 'mviz-drop-overlay';
    overlay.innerHTML = '<div style=&quot;color:white;font-size:32px;font-weight:bold;text-align:center;padding:40px;border:4px dashed white;border-radius:20px;background:rgba(0,0,0,0.2);&quot;><span style=&quot;font-size:64px;display:block;margin-bottom:20px;&quot;>📁</span>Drop NPZ files here</div>';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(52,152,219,0.9);display:none;justify-content:center;align-items:center;z-index:99999;pointer-events:none;';
    parent.document.body.appendChild(overlay);
    
    var dragCounter = 0;
    
    parent.document.addEventListener('dragenter', function(e) {
        e.preventDefault();
        dragCounter++;
        if (e.dataTransfer.types.indexOf('Files') !== -1) {
            overlay.style.display = 'flex';
        }
    });
    
    parent.document.addEventListener('dragleave', function(e) {
        e.preventDefault();
        dragCounter--;
        if (dragCounter <= 0) {
            overlay.style.display = 'none';
            dragCounter = 0;
        }
    });
    
    parent.document.addEventListener('dragover', function(e) {
        e.preventDefault();
    });
    
    parent.document.addEventListener('drop', function(e) {
        e.preventDefault();
        overlay.style.display = 'none';
        dragCounter = 0;
        
        var files = e.dataTransfer.files;
        for (var i = 0; i < files.length; i++) {
            if (files[i].name.endsWith('.npz')) {
                var input = parent.document.querySelector('input[type=file][accept*=npz]') || parent.document.querySelector('input[type=file]');
                if (input) {
                    var dt = new DataTransfer();
                    dt.items.add(files[i]);
                    input.files = dt.files;
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                    parent.console.log('[Motion Viewer] File dropped:', files[i].name);
                }
            }
        }
    });
    
    parent.console.log('[Motion Viewer] Global drag-drop initialized');
})();
</script></body></html>
"></iframe>
'''
        self._drag_drop_html = self.server.gui.add_html(drop_zone_html)
    
    def build_ui(self, parent_folder: Optional[str] = None) -> None:
        self.ui_folder = self.server.gui.add_folder(self.name)
        
        with self.ui_folder:
            self._upload_button = self.server.gui.add_upload_button(
                "Select NPZ File",
                mime_type=".npz",
                icon="file-upload",
            )
            
            self._inject_drag_drop_overlay()
            
            @self._upload_button.on_upload

            def _(event):
                uploaded_file = event.target.value
                if uploaded_file is not None:
                    filename = uploaded_file.name
                    content = uploaded_file.content
                    if filename.endswith('.npz'):
                        self._add_robot_from_bytes(filename, content)
                    else:
                        cprint(f"Unsupported file type: {filename}. Only .npz files are supported.", 'yellow')
            
            self.server.gui.add_markdown("---")
            self._robots_folder = self.server.gui.add_folder("Loaded Robots")

            self.server.gui.add_markdown("---")
            self.server.gui.add_markdown("### Playback")
            
            self._frame_slider = self.server.gui.add_slider(
                "Frame",
                min=0,
                max=1,
                step=1,
                initial_value=0,
                visible=False,
            )
            
            @self._frame_slider.on_update
            def _(event):
                if not self.playing:
                    self.current_frame = event.target.value
            
            self._frame_info = self.server.gui.add_markdown("Frame: 0 / 0", visible=False)

            
            self._play_button = self.server.gui.add_button("▶ Play", icon="player-play", visible=False)
            self._pause_button = self.server.gui.add_button("⏸ Pause", icon="player-pause", visible=False)
            
            @self._play_button.on_click
            def _(_):
                self.playing = True
                self._play_button.visible = False
                self._pause_button.visible = True
            
            @self._pause_button.on_click
            def _(_):
                self.playing = False
                self._play_button.visible = True
                self._pause_button.visible = False
            
            self._speed_slider = self.server.gui.add_slider(
                "Speed",
                min=0.1,
                max=3.0,
                step=0.1,
                initial_value=1.0,
                visible=False,
            )
            
            @self._speed_slider.on_update
            def _(event):
                self.playback_speed = event.target.value
            
            self._loop_checkbox = self.server.gui.add_checkbox(
                "Loop",
                initial_value=True,
                visible=False,
            )
            
            @self._loop_checkbox.on_update
            def _(event):
                self.loop = event.target.value
    
    def update(self) -> Optional[Dict[str, np.ndarray]]:
        if not self.robot_instances:
            return None
        

        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        max_frame = self._get_max_frame()

        if self.playing:
            fps = self.robot_instances[0].motion.fps if self.robot_instances else self.target_fps
            frame_advance = dt * fps * self.playback_speed
            self.current_frame += frame_advance
            
            if self.current_frame >= max_frame:
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = max_frame
                    self.playing = False
                    if self._play_button is not None:
                        self._play_button.visible = True
                    if self._pause_button is not None:
                        self._pause_button.visible = False
            
            current_frame_int = int(self.current_frame)
            if self._frame_slider is not None:
                self._frame_slider.value = current_frame_int
            if self._frame_info is not None:
                self._frame_info.content = f"Frame: {current_frame_int} / {max_frame}"
        
        for robot in self.robot_instances:
            self._update_robot_visualization(robot)
        
        return None

    
    def _update_robot_visualization(self, robot: RobotInstance) -> None:
        if not robot.visible:
            return
        
        try:
            frame_data = robot.motion.get_frame(int(self.current_frame))
            
            root_pos = frame_data['root_pos'].copy()
            root_rot = frame_data['root_rot']
            joint_pos = frame_data['joint_pos']
            
            root_pos[0] += robot.offset_x
            
            root_quat_wxyz = np.array([root_rot[3], root_rot[0], root_rot[1], root_rot[2]], dtype=np.float32)
            
            robot.robot_vis.update_base(root_pos, root_quat_wxyz)
            robot.robot_vis.update_cfg(joint_pos)
            
        except Exception:
            pass
    
    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if self.ui_folder is not None:
            self.ui_folder.visible = enabled
        
        if hasattr(self, 'visualizer') and self.visualizer is not None:
            self.visualizer.set_robot_visible(not enabled)

    def set_visualizer(self, visualizer: Any) -> None:
        self.visualizer = visualizer



if __name__ == "__main__":
    from mviz.viser_tools.base_visualizer import BaseVisualizer
    
    visualizer = BaseVisualizer(target_fps=30.0)
    motion_viewer = MotionViewerModule(visualizer.server)
    visualizer.register_module(motion_viewer)
    visualizer.set_active_module("Motion Viewer")

    visualizer.set_robot_visible(False)

    visualizer.main_loop()

