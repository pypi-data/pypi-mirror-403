import os
import time
from pathlib import Path
from typing import List, Optional, Dict

import numpy as np
import viser
import viser.transforms as tf
from termcolor import cprint

from mviz import TMP_DIR, ROOT_DIR
from mviz.viser_tools.motion_player import MotionPlayerModule
from mviz.viser_tools.plugin_registry import register_plugin
from mviz.viser_tools.amass_player import SmplHelper
from mviz.viser_tools.base_visualizer import BaseVisualizer


@register_plugin
class MotionSearchModule(MotionPlayerModule):
    plugin_cfg = {
        'target_fps': 30,
        'default_playback_speed': 1.0,
        'loop_by_default': True,
        # amass
        'default_model_path': str((Path(__file__).parent / "../robots/smplh/male/model.npz").resolve()),
        'mesh_color': (180, 142, 245),
        'default_loop': True,
        'default_speed': 1.0,
    }

    def __init__(self, server: viser.ViserServer):
        super().__init__(server)
        self.name = "Motion Search"
        self.keyword: str = self._load_keyword()
        self.keyword_input = None
        self.max_search_results = 200
        
        # amass
        self._is_amass_mode: bool = False
        self._visualizer: Optional[BaseVisualizer] = None
        self._model_path: str = self._load_model_path() or self.plugin_cfg['default_model_path']
        self._smpl: Optional[SmplHelper] = None
        self._mesh_handle: Optional[viser.MeshHandle] = None
        self._amass_data: Optional[Dict[str, np.ndarray]] = None
        self._amass_num_frames: int = 0
        self._amass_current_frame_f: float = 0.0
        self._amass_playing: bool = False
        self._amass_loop: bool = self.plugin_cfg['default_loop']
        self._amass_speed: float = self.plugin_cfg['default_speed']
        self._amass_target_fps: int = int(self.plugin_cfg['target_fps'])
        self._amass_last_time: float = time.time()
        self._updating_amass_slider: bool = False

        self._model_input = None
        self._wireframe_checkbox = None
        self._color_input = None

    def _path_cache_file(self) -> str:
        return os.path.join(TMP_DIR, "motion_search_amass_path.txt")

    def _keyword_cache_file(self) -> str:
        return os.path.join(TMP_DIR, "motion_search_keyword.txt")

    def _load_folder_path(self) -> str:
        os.makedirs(TMP_DIR, exist_ok=True)
        path_file = self._path_cache_file()
        if os.path.exists(path_file):
            with open(path_file, "r") as f:
                return f.read().strip()
        return ""

    def _save_folder_path(self, folder_path: str) -> None:
        os.makedirs(TMP_DIR, exist_ok=True)
        with open(self._path_cache_file(), "w") as f:
            f.write(folder_path)

    def _load_keyword(self) -> str:
        os.makedirs(TMP_DIR, exist_ok=True)
        keyword_file = self._keyword_cache_file()
        if os.path.exists(keyword_file):
            with open(keyword_file, "r") as f:
                return f.read().strip()
        return ""

    def _save_keyword(self, keyword: str) -> None:
        os.makedirs(TMP_DIR, exist_ok=True)
        with open(self._keyword_cache_file(), "w") as f:
            f.write(keyword)

    def _detect_file_type(self, file_path: str) -> str:
        if file_path.endswith('.csv'):
            return 'motion_player'
        
        if not file_path.endswith('.npz'):
            return 'motion_player'
        
        try:
            data = np.load(file_path, allow_pickle=True)
            keys = set(data.keys())
            
            if 'poses' in keys and 'trans' in keys:
                return 'amass'
            
            if 'body_pos_w' in keys and 'body_quat_w' in keys:
                return 'motion_player'
            
            return 'motion_player'
        except Exception as e:
            cprint(f"Error detecting file type for {file_path}: {e}", 'yellow')
            return 'motion_player'

    def _load_model_path(self) -> str:
        os.makedirs(TMP_DIR, exist_ok=True)
        path_file = os.path.join(TMP_DIR, 'amass_model_path.txt')
        if os.path.exists(path_file):
            with open(path_file, 'r') as f:
                return f.read().strip()
        return ""

    def _save_model_path(self, model_path: str) -> None:
        os.makedirs(TMP_DIR, exist_ok=True)
        path_file = os.path.join(TMP_DIR, 'amass_model_path.txt')
        with open(path_file, 'w') as f:
            f.write(model_path)

    def _load_smpl(self) -> bool:
        try:
            path = Path(self._model_path)
            if not path.exists():
                cprint(f"SMPL model not found: {path}", 'red')
                return False
            self._smpl = SmplHelper(path)
            return True
        except Exception as e:
            cprint(f"Failed to load SMPL model: {e}", 'red')
            self._smpl = None
            return False

    def _ensure_mesh(self) -> None:
        if self._mesh_handle is None:
            verts = np.zeros((3, 3), dtype=np.float32)
            faces = np.array([[0, 1, 2]], dtype=np.int32)
            self._mesh_handle = self.server.scene.add_mesh_simple(
                "/motion_search_human",
                vertices=verts,
                faces=faces,
                color=self.plugin_cfg['mesh_color'],
                wireframe=False,
            )

    def _axisangle_to_rotmats(self, axisangle_packed: np.ndarray, expected_joints: int) -> np.ndarray:
        Jp = axisangle_packed.shape[0] // 3
        axisangles = axisangle_packed.reshape(Jp, 3)
        mats = tf.SO3.exp(axisangles).as_matrix()
        if Jp == expected_joints:
            return mats
        out = np.tile(np.eye(3), (expected_joints, 1, 1))
        count = min(Jp, expected_joints)
        out[:count] = mats[:count]
        return out

    def _update_amass_frame(self, idx: int) -> None:
        if self._amass_data is None or self._smpl is None or self._mesh_handle is None:
            return
        betas = self._amass_data['betas']
        poses = self._amass_data['poses'][idx]
        trans = self._amass_data['trans'][idx]

        joint_rotmats = self._axisangle_to_rotmats(poses, self._smpl.num_joints)
        smpl_out = self._smpl.get_outputs(betas=betas, joint_rotmats=joint_rotmats)

        verts = smpl_out.vertices + trans[None, :]
        self._mesh_handle.vertices = verts

    def _build_source_controls(self) -> None:
        self.folder_input = self.server.gui.add_text(
            "Motion Folder Path",
            initial_value=self.folder_path,
        )

        def _refresh_dropdown(load_first: bool = True) -> None:
            if self.file_dropdown is None:
                return
            if self.motion_files:
                self.file_dropdown.options = self.motion_files
                self.file_dropdown.value = self.motion_files[0]
                if load_first:
                    self._load_motion_file(self.motion_files[0])
            else:
                self.motion_loader = None
                self._update_clip_controls()
                self.file_dropdown.options = ["No motion files found"]
                self.file_dropdown.value = "No motion files found"

        @self.folder_input.on_update
        def _(event) -> None:
            self.folder_path = event.target.value
            self._save_folder_path(self.folder_path)
            self.motion_files = self._scan_motion_files(self.folder_path)
            _refresh_dropdown(load_first=True)

        self.keyword_input = self.server.gui.add_text(
            "Keyword",
            initial_value=self.keyword,
        )

        @self.keyword_input.on_update
        def _(event) -> None:
            self.keyword = event.target.value or ""
            self._save_keyword(self.keyword)
            self.motion_files = self._scan_motion_files(self.folder_path)
            _refresh_dropdown(load_first=True)

    def _scan_motion_files(self, folder_path: str) -> List[str]:
        if not folder_path or not os.path.isdir(folder_path):
            return []

        keyword = (self.keyword or "").strip().lower()
        matches: List[str] = []

        try:
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    if not (filename.endswith(".npz") or filename.endswith(".csv")):
                        continue
                    rel_dir = os.path.relpath(root, folder_path)
                    rel_path = (
                        filename if rel_dir == "." else os.path.join(rel_dir, filename)
                    )
                    rel_path_norm = rel_path.replace(os.sep, "/")
                    target = rel_path_norm.lower()
                    if keyword and keyword not in target:
                        continue
                    matches.append(rel_path_norm)
                    if len(matches) >= self.max_search_results:
                        break
                if len(matches) >= self.max_search_results:
                    break
        except Exception as exc:
            cprint(f"Error searching motions in {folder_path}: {exc}", "red")
            return []

        return sorted(matches)

    def _load_motion_file(self, filename: str) -> None:
        if not self.folder_path or not filename:
            return
        
        file_path = os.path.join(self.folder_path, filename)
        if not os.path.exists(file_path):
            cprint(f"File not found: {file_path}", 'red')
            return

        file_type = self._detect_file_type(file_path)
        
        if file_type == 'amass':
            self._is_amass_mode = True
            self._load_amass_file(file_path)
        else:
            self._is_amass_mode = False
            if self._mesh_handle is not None:
                self._mesh_handle.visible = False
            if self._visualizer is not None:
                self._visualizer.set_robot_visible(True)
            super()._load_motion_file(filename)
            if self.motion_loader is not None and self.motion_loader.num_clips > 0:
                self.playing = True
                if self.play_button is not None:
                    self.play_button.visible = False
                if self.pause_button is not None:
                    self.pause_button.visible = True

    def _load_amass_file(self, path: str) -> None:
        if not os.path.exists(path):
            cprint(f"File not found: {path}", 'red')
            return
        
        self.current_file = os.path.basename(path)
        
        if self._visualizer is not None:
            self._visualizer.set_robot_visible(False)
        
        if self._smpl is None and not self._load_smpl():
            return
        
        try:
            data = dict(**np.load(path, allow_pickle=True))
        except Exception as e:
            cprint(f"Failed to load AMASS file: {e}", 'red')
            return

        poses = data.get('poses', None)
        trans = data.get('trans', None)
        betas = data.get('betas', None)

        if poses is None or trans is None:
            cprint("AMASS file missing 'poses' or 'trans'", 'red')
            return

        poses = np.asarray(poses, dtype=np.float32)
        trans = np.asarray(trans, dtype=np.float32)
        if betas is None:
            betas = np.zeros((self._smpl.num_betas,), dtype=np.float32)
        else:
            betas = np.asarray(betas, dtype=np.float32).reshape(-1)
            if betas.shape[0] > self._smpl.num_betas:
                betas = betas[: self._smpl.num_betas]
            elif betas.shape[0] < self._smpl.num_betas:
                tmp = np.zeros((self._smpl.num_betas,), dtype=np.float32)
                tmp[: betas.shape[0]] = betas
                betas = tmp

        T = int(poses.shape[0]) if poses is not None else 0
        if not np.isfinite(T) or T <= 0:
            self._amass_data = None
            self._amass_num_frames = 0
            return

        self._amass_data = {
            'poses': poses,
            'trans': trans,
            'betas': betas,
        }
        self._amass_num_frames = T
        self._amass_current_frame_f = 0.0
        self._amass_playing = False

        assert self._smpl is not None
        smpl_out = self._smpl.get_outputs(betas, np.repeat(np.eye(3)[None, ...], self._smpl.num_joints, axis=0))
        self._ensure_mesh()
        if self._mesh_handle is not None:
            self._mesh_handle.vertices = smpl_out.vertices
            self._mesh_handle.faces = smpl_out.faces
            self._mesh_handle.color = self._color_input.value if self._color_input is not None else self.plugin_cfg['mesh_color']
            self._mesh_handle.wireframe = self._wireframe_checkbox.value if self._wireframe_checkbox is not None else False
            self._mesh_handle.visible = True

        if self.frame_slider is not None:
            self.frame_slider.visible = True
            self.frame_slider.min = 0
            self.frame_slider.max = max(1, T - 1)
            self.frame_slider.value = 0.0
            self.frame_slider.disabled = (T <= 1)
        if self.frame_info_text is not None:
            self.frame_info_text.visible = True
            self.frame_info_text.value = f"Frame 0/{max(0, T - 1)}"
        if self.play_button is not None:
            self.play_button.visible = (T > 1)
            self.play_button.disabled = (T <= 1)
        if self.pause_button is not None:
            self.pause_button.visible = False
        if self.speed_slider is not None:
            self.speed_slider.visible = (T > 1)
        if self.loop_checkbox is not None:
            self.loop_checkbox.visible = (T > 1)
        
        self._amass_current_frame_f = 0.0
        self._update_amass_frame(0)
        
        self._amass_playing = True
        if self.play_button is not None:
            self.play_button.visible = False
        if self.pause_button is not None:
            self.pause_button.visible = True

    def set_visualizer(self, visualizer: BaseVisualizer) -> None:
        self._visualizer = visualizer

    def build_ui(self, parent_folder: Optional[str] = None) -> None:
        self.ui_folder = self.server.gui.add_folder(self.name)
        
        with self.ui_folder:
            self._build_source_controls()
            self._model_input = self.server.gui.add_text("SMPL Model .npz", initial_value=self._model_path)
            
            @self._model_input.on_update
            def _(event) -> None:
                self._model_path = event.target.value
                self._save_model_path(self._model_path)
                self._smpl = None
                if self._is_amass_mode and self.current_file:
                    file_path = os.path.join(self.folder_path, self.current_file)
                    if os.path.exists(file_path):
                        self._load_amass_file(file_path)
            
            self._wireframe_checkbox = self.server.gui.add_checkbox("Wireframe", initial_value=False)
            
            @self._wireframe_checkbox.on_update
            def _(_):
                if self._mesh_handle is not None:
                    self._mesh_handle.wireframe = self._wireframe_checkbox.value
            
            self._color_input = self.server.gui.add_rgb("Color", initial_value=self.plugin_cfg['mesh_color'])
            
            @self._color_input.on_update
            def _(_):
                if self._mesh_handle is not None:
                    self._mesh_handle.color = self._color_input.value
            self.fps_input = self.server.gui.add_number(
                "FPS",
                initial_value=self.target_fps,
                min=1,
                max=240,
                step=1,
            )
            
            @self.fps_input.on_update
            def _(event) -> None:
                new_fps = int(event.target.value)
                if new_fps > 0:
                    self.target_fps = new_fps
                    if not self._is_amass_mode and self.motion_loader is not None and self.current_file:
                        cprint(f"Reloading with new FPS: {new_fps}", 'cyan')
                        self._load_motion_file(self.current_file)
            
            self.motion_files = self._scan_motion_files(self.folder_path)
            
            if self.motion_files:
                self.file_dropdown = self.server.gui.add_dropdown(
                    "Motion File",
                    options=self.motion_files,
                    initial_value=self.motion_files[0],
                )
                
                @self.file_dropdown.on_update
                def _(event) -> None:
                    filename = event.target.value
                    if filename and (filename.endswith('.npz') or filename.endswith('.csv')):
                        self._load_motion_file(filename)
                
                if self.motion_loader is None and not self._is_amass_mode:
                    self._load_motion_file(self.motion_files[0])
            else:
                self.file_dropdown = self.server.gui.add_dropdown(
                    "Motion File",
                    options=["No motion files found"],
                    initial_value="No motion files found",
                )
                
                @self.file_dropdown.on_update
                def _(event) -> None:
                    filename = event.target.value
                    if filename and (filename.endswith('.npz') or filename.endswith('.csv')):
                        self._load_motion_file(filename)
            
            has_motion = (self.motion_loader is not None and self.motion_loader.num_clips > 0) or (self._is_amass_mode and self._amass_num_frames > 0)
            initial_max_frame = 1
            if has_motion:
                if self._is_amass_mode:
                    initial_max_frame = max(1, self._amass_num_frames - 1)
                else:
                    try:
                        clip_data = self.motion_loader.get_clip(0)
                        if clip_data and len(clip_data) > 0:
                            first_key = next(iter(clip_data.keys()))
                            initial_max_frame = max(1, clip_data[first_key].shape[0] - 1)
                    except Exception as e:
                        cprint(f"Warning: Error getting initial frame count: {e}", 'yellow')
                        initial_max_frame = 1
            
            self.frame_slider = self.server.gui.add_slider(
                "Frame",
                min=0,
                max=int(initial_max_frame),
                step=1,
                initial_value=0,
                visible=has_motion,
            )
            
            @self.frame_slider.on_update
            def _(event) -> None:
                if self._is_amass_mode:
                    if not self._updating_amass_slider:
                        self._amass_current_frame_f = float(event.target.value)
                        self._amass_playing = False
                else:
                    if not self._updating_from_playback:
                        self.current_frame = event.target.value
                        self.playing = False
            
            self.frame_info_text = self.server.gui.add_text(
                "Frame Info",
                f"Frame 0/{int(initial_max_frame)}" if has_motion else "No frame loaded",
                visible=has_motion,
            )

            self.play_button = self.server.gui.add_button("Play", visible=has_motion)
            self.pause_button = self.server.gui.add_button("Pause", visible=False)
            
            @self.play_button.on_click
            def _(_) -> None:
                if self._is_amass_mode:
                    self._amass_playing = True
                else:
                    self.playing = True
                if self.play_button is not None:
                    self.play_button.visible = False
                if self.pause_button is not None:
                    self.pause_button.visible = True
            
            @self.pause_button.on_click
            def _(_) -> None:
                if self._is_amass_mode:
                    self._amass_playing = False
                else:
                    self.playing = False
                if self.play_button is not None:
                    self.play_button.visible = True
                if self.pause_button is not None:
                    self.pause_button.visible = False
            
            self.speed_slider = self.server.gui.add_slider(
                "Speed",
                min=0.1,
                max=3.0,
                step=0.1,
                initial_value=1.0,
                visible=has_motion,
            )
            
            @self.speed_slider.on_update
            def _(event) -> None:
                if self._is_amass_mode:
                    self._amass_speed = event.target.value
                else:
                    self.playback_speed = event.target.value
            
            self.loop_checkbox = self.server.gui.add_checkbox(
                "Loop",
                initial_value=True,
                visible=has_motion,
            )
            
            @self.loop_checkbox.on_update
            def _(event) -> None:
                if self._is_amass_mode:
                    self._amass_loop = event.target.value
                else:
                    self.loop = event.target.value
            
            if self.publisher is not None:
                self.send_button = self.server.gui.add_button("Send", visible=has_motion and not self._is_amass_mode)
                self.stop_button = self.server.gui.add_button("Stop", visible=False)
                
                @self.send_button.on_click
                def _(_) -> None:
                    self.sending = True
                    self.message_count = 0
                    self.send_button.visible = False
                    self.stop_button.visible = True
                
                @self.stop_button.on_click
                def _(_) -> None:
                    self.sending = False
                    self.send_button.visible = True
                    self.stop_button.visible = False
                
                self.status_text = self.server.gui.add_text(
                    "Status",
                    "Topic: /mviz/msg (idle)",
                    visible=has_motion and not self._is_amass_mode
                )
            else:
                self.send_button = self.server.gui.add_button("Send (unavailable)", visible=has_motion and not self._is_amass_mode)
                self.send_button.disabled = True
                self.stop_button = None
                self.status_text = self.server.gui.add_text(
                    "Status",
                    "iceoryx2 not available",
                    visible=has_motion and not self._is_amass_mode
                )
        
        self._ensure_mesh()

    def update(self) -> Optional[Dict[str, np.ndarray]]:
        """Update method that handles both AMASS and motion player modes."""
        if not self.enabled:
            if self._mesh_handle is not None:
                self._mesh_handle.visible = False
            return None
        
        if self._is_amass_mode:
            if self._visualizer is not None:
                self._visualizer.set_robot_visible(False)
            
            if self._amass_data is None or self._smpl is None or self._amass_num_frames <= 0:
                if self._mesh_handle is not None:
                    self._mesh_handle.visible = False
                return None
            
            now = time.time()
            dt = now - self._amass_last_time
            self._amass_last_time = now
            
            if self._amass_num_frames <= 1:
                self._amass_playing = False
                self._amass_current_frame_f = 0.0
            elif self._amass_playing:
                self._amass_current_frame_f += dt * self._amass_target_fps * self._amass_speed
                if self._amass_current_frame_f >= float(self._amass_num_frames - 1):
                    if self._amass_loop:
                        self._amass_current_frame_f = 0.0
                    else:
                        self._amass_current_frame_f = float(self._amass_num_frames - 1)
                        self._amass_playing = False
                        if self.play_button is not None:
                            self.play_button.visible = True
                        if self.pause_button is not None:
                            self.pause_button.visible = False
            
            if not np.isfinite(self._amass_current_frame_f):
                self._amass_current_frame_f = 0.0
            
            max_idx_val = max(0, int(self._amass_num_frames - 1))
            frame_idx_f = float(np.clip(self._amass_current_frame_f, 0.0, float(max_idx_val)))
            frame_idx = 0 if not np.isfinite(frame_idx_f) else int(np.round(frame_idx_f))
            frame_idx = max(0, min(frame_idx, max_idx_val))
            
            self._update_amass_frame(frame_idx)
            
            if self._mesh_handle is not None:
                self._mesh_handle.visible = True
            
            if self.frame_slider is not None:
                self.frame_slider.min = 0
                safe_max = max(1, int(self._amass_num_frames - 1))
                self.frame_slider.max = safe_max
                safe_val = max(0, min(frame_idx, safe_max))
                
                self._updating_amass_slider = True
                self.frame_slider.value = 0.0 if not np.isfinite(safe_val) else float(safe_val)
                self._updating_amass_slider = False
                
                self.frame_slider.visible = True
                self.frame_slider.disabled = (self._amass_num_frames <= 1)
            if self.frame_info_text is not None:
                self.frame_info_text.visible = True
                self.frame_info_text.value = f"Frame {frame_idx}/{max(0, self._amass_num_frames - 1)}"
            if self.play_button is not None:
                self.play_button.visible = (self._amass_num_frames > 1) and not self._amass_playing
                self.play_button.disabled = (self._amass_num_frames <= 1)
            if self.pause_button is not None:
                self.pause_button.visible = (self._amass_num_frames > 1) and self._amass_playing
            if self.speed_slider is not None:
                self.speed_slider.visible = (self._amass_num_frames > 1)
            if self.loop_checkbox is not None:
                self.loop_checkbox.visible = (self._amass_num_frames > 1)
            
            return None
        
        else:
            if self._visualizer is not None:
                self._visualizer.set_robot_visible(True)
            if self._mesh_handle is not None:
                self._mesh_handle.visible = False
            return super().update()

    def set_enabled(self, enabled: bool) -> None:
        super().set_enabled(enabled)
        if self._mesh_handle is not None:
            self._mesh_handle.visible = enabled and self._is_amass_mode
        if self._visualizer is not None:
            if enabled and self._is_amass_mode:
                self._visualizer.set_robot_visible(False)
            elif enabled and not self._is_amass_mode:
                self._visualizer.set_robot_visible(True)


