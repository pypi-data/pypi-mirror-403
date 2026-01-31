from __future__ import annotations

import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import viser
import viser.transforms as tf
from termcolor import cprint

from mviz.viser_tools.base_visualizer import VisualizerModule, BaseVisualizer
from mviz.viser_tools.plugin_registry import register_plugin
from mviz import ROOT_DIR, TMP_DIR


@dataclass(frozen=True)
class SmplOutputs:
    vertices: np.ndarray
    faces: np.ndarray
    T_world_joint: np.ndarray
    T_parent_joint: np.ndarray


class SmplHelper:

    def __init__(self, model_path: Path) -> None:
        assert model_path.suffix.lower() == ".npz", "Model should be an .npz file!"
        body_dict = dict(**np.load(model_path, allow_pickle=True))

        self.J_regressor = body_dict["J_regressor"]
        self.weights = body_dict["weights"]
        self.v_template = body_dict["v_template"]
        self.posedirs = body_dict["posedirs"]
        self.shapedirs = body_dict["shapedirs"]
        self.faces = body_dict["f"]

        self.num_joints: int = self.weights.shape[-1]
        self.num_betas: int = self.shapedirs.shape[-1]
        self.parent_idx: np.ndarray = body_dict["kintree_table"][0]

    def get_outputs(self, betas: np.ndarray, joint_rotmats: np.ndarray) -> SmplOutputs:
        v_tpose = self.v_template + np.einsum("vxb,b->vx", self.shapedirs, betas)
        j_tpose = np.einsum("jv,vx->jx", self.J_regressor, v_tpose)

        T_parent_joint = np.zeros((self.num_joints, 4, 4)) + np.eye(4)
        T_parent_joint[:, :3, :3] = joint_rotmats
        T_parent_joint[0, :3, 3] = j_tpose[0]
        T_parent_joint[1:, :3, 3] = j_tpose[1:] - j_tpose[self.parent_idx[1:]]

        T_world_joint = T_parent_joint.copy()
        for i in range(1, self.num_joints):
            T_world_joint[i] = T_world_joint[self.parent_idx[i]] @ T_parent_joint[i]

        pose_delta = (joint_rotmats[1:, ...] - np.eye(3)).flatten()
        v_blend = v_tpose + np.einsum("byn,n->by", self.posedirs, pose_delta)
        v_delta = np.ones((v_blend.shape[0], self.num_joints, 4))
        v_delta[:, :, :3] = v_blend[:, None, :] - j_tpose[None, :, :]
        v_posed = np.einsum(
            "jxy,vj,vjy->vx", T_world_joint[:, :3, :], self.weights, v_delta
        )
        return SmplOutputs(v_posed, self.faces, T_world_joint, T_parent_joint)


@register_plugin
class AmassPlayerModule(VisualizerModule):
    plugin_cfg = {
        'default_model_path': str((Path(__file__).parent / "../robots/smplh/male/model.npz").resolve()),
        'mesh_color': (180, 142, 245),
        'default_loop': True,
        'default_speed': 1.0,
        'target_fps': 30,
    }

    def __init__(self, server: viser.ViserServer):
        super().__init__("AMASS Player", server)

        self._visualizer: Optional[BaseVisualizer] = None
        self._model_path: str = self._load_model_path() or self.plugin_cfg['default_model_path']
        self._smpl: Optional[SmplHelper] = None
        self._mesh_handle: Optional[viser.MeshHandle] = None
        self._amass_data: Optional[Dict[str, np.ndarray]] = None
        self._num_frames: int = 0
        self._current_frame_f: float = 0.0
        self._playing: bool = False
        self._loop: bool = self.plugin_cfg['default_loop']
        self._speed: float = self.plugin_cfg['default_speed']
        self._target_fps: int = int(self.plugin_cfg['target_fps'])
        self._last_time: float = time.time()
        self._updating_slider: bool = False

        self._ui_folder: Optional[viser.GuiHandle] = None
        self._folder_input = None
        self._model_input = None
        self._file_dropdown = None
        self._frame_slider = None
        self._frame_info = None
        self._play_btn = None
        self._pause_btn = None
        self._next_btn = None
        self._delete_btn = None
        self._speed_slider = None
        self._loop_checkbox = None
        self._wireframe_checkbox = None
        self._color_input = None

        self._folder_path: str = self._load_folder_path()
        self._files: list[str] = []
        self._current_file: Optional[str] = None

    def set_visualizer(self, visualizer: BaseVisualizer) -> None:
        self._visualizer = visualizer
        if self.enabled and self._visualizer is not None:
            self._visualizer.set_robot_visible(False)

    def build_ui(self, parent_folder: Optional[str] = None) -> None:
        self.ui_folder = self.server.gui.add_folder(self.name)
        self._ui_folder = self.ui_folder
        with self.ui_folder:
            self._folder_input = self.server.gui.add_text("AMASS Path", initial_value=self._folder_path)

            @self._folder_input.on_update
            def _(event) -> None:
                input_val = event.target.value
                if input_val.lower().endswith('.npz') and os.path.isfile(input_val):
                    folder_path = os.path.dirname(input_val)
                    target_file = os.path.basename(input_val)

                    self._folder_path = folder_path
                    self._folder_input.value = folder_path

                    self._save_folder_path(self._folder_path)
                    self._refresh_file_list()

                    if target_file in self._files and self._file_dropdown is not None:
                        self._file_dropdown.value = target_file
                else:
                    self._folder_path = input_val
                    self._save_folder_path(self._folder_path)
                    self._refresh_file_list()

            self._model_input = self.server.gui.add_text("SMPL Model .npz", initial_value=self._model_path)

            @self._model_input.on_update
            def _(event) -> None:
                self._model_path = event.target.value
                self._save_model_path(self._model_path)
                self._smpl = None

            self._file_dropdown = self.server.gui.add_dropdown(
                "Sequence", options=["<none>"], initial_value="<none>"
            )

            @self._file_dropdown.on_update
            def _(event) -> None:
                filename = event.target.value
                if filename and filename != "<none>":
                    self._load_amass_file(os.path.join(self._folder_path, filename))

            self._frame_slider = self.server.gui.add_slider("Frame", min=0, max=1, step=1, initial_value=0.0, visible=False)

            @self._frame_slider.on_update
            def _(event) -> None:
                if self._updating_slider:
                    return

                self._playing = False
                if self._play_btn is not None:
                    self._play_btn.visible = True
                if self._pause_btn is not None:
                    self._pause_btn.visible = False
                
                val = event.target.value
                if val is None or not np.isfinite(val):
                    val = 0.0
                else:
                    val = float(val)
                
                max_frame = max(0, self._num_frames - 1)
                if self._num_frames <= 1 or val < 0:
                    val = 0.0
                elif val > max_frame:
                    val = float(max_frame)
                
                self._current_frame_f = val
                frame_idx = int(np.clip(val, 0, max_frame))
                self._update_frame(frame_idx)

            self._frame_info = self.server.gui.add_text("Info", "No sequence loaded", visible=False)

            self._play_btn = self.server.gui.add_button("Play", visible=False)
            self._pause_btn = self.server.gui.add_button("Pause", visible=False)

            @self._play_btn.on_click
            def _(_):
                self._playing = True
                self._play_btn.visible = False
                self._pause_btn.visible = True

            @self._pause_btn.on_click
            def _(_):
                self._playing = False
                self._play_btn.visible = True
                self._pause_btn.visible = False

            self._next_btn = self.server.gui.add_button("Next", visible=False, color=(0, 200, 0))

            @self._next_btn.on_click
            def _(_):
                self._next_file()

            self._delete_btn = self.server.gui.add_button("Delete", visible=False, color=(200, 0, 0))

            @self._delete_btn.on_click
            def _(_):
                self._delete_current_file()

            self._speed_slider = self.server.gui.add_slider("Speed", min=0.1, max=10.0, step=0.1, initial_value=self._speed, visible=False)

            @self._speed_slider.on_update
            def _(event) -> None:
                self._speed = float(event.target.value)

            self._loop_checkbox = self.server.gui.add_checkbox("Loop", initial_value=self._loop, visible=False)

            @self._loop_checkbox.on_update
            def _(event) -> None:
                self._loop = bool(event.target.value)

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

        self._ensure_mesh()
        
        if self._folder_path:
            self._refresh_file_list()

    def update(self) -> Optional[Dict[str, np.ndarray]]:
        if not self.enabled:
            return None

        if self._visualizer is not None:
            self._visualizer.set_robot_visible(False)

        if self._amass_data is None or self._smpl is None or self._num_frames <= 0:
            if self._frame_slider is not None:
                self._frame_slider.visible = False
            if self._frame_info is not None:
                self._frame_info.visible = False
            if self._play_btn is not None:
                self._play_btn.visible = False
            if self._pause_btn is not None:
                self._pause_btn.visible = False
            if self._next_btn is not None:
                self._next_btn.visible = False
            if self._delete_btn is not None:
                self._delete_btn.visible = False
            if self._speed_slider is not None:
                self._speed_slider.visible = False
            if self._loop_checkbox is not None:
                self._loop_checkbox.visible = False
            return None

        now = time.time()
        dt = now - self._last_time
        self._last_time = now

        if self._num_frames <= 1:
            self._playing = False
            self._current_frame_f = 0.0
        elif self._playing:
            self._current_frame_f += dt * self._target_fps * self._speed
            if self._current_frame_f >= float(self._num_frames - 1):
                if self._loop:
                    self._current_frame_f = 0.0
                else:
                    self._current_frame_f = float(self._num_frames - 1)
                    self._playing = False
                    if self._play_btn is not None:
                        self._play_btn.visible = True
                    if self._pause_btn is not None:
                        self._pause_btn.visible = False

        if not np.isfinite(self._current_frame_f):
            self._current_frame_f = 0.0
        
        max_idx_val = max(0, int(self._num_frames - 1))
        frame_idx_f = float(np.clip(self._current_frame_f, 0.0, float(max_idx_val)))
        frame_idx = 0 if not np.isfinite(frame_idx_f) else int(np.round(frame_idx_f))
        frame_idx = max(0, min(frame_idx, max_idx_val))
        
        self._update_frame(frame_idx)

        if self._frame_slider is not None:
            self._frame_slider.min = 0
            safe_max = max(1, int(self._num_frames - 1))
            self._frame_slider.max = safe_max
            safe_val = max(0, min(frame_idx, safe_max))
            
            self._updating_slider = True
            self._frame_slider.value = 0.0 if not np.isfinite(safe_val) else float(safe_val)
            self._updating_slider = False
            
            self._frame_slider.visible = True
            self._frame_slider.disabled = (self._num_frames <= 1)
        if self._frame_info is not None:
            self._frame_info.visible = True
            self._frame_info.value = f"Frame {frame_idx}/{max(0, self._num_frames - 1)}"
        if self._play_btn is not None:
            self._play_btn.visible = (self._num_frames > 1) and not self._playing
            self._play_btn.disabled = (self._num_frames <= 1)
        if self._pause_btn is not None:
            self._pause_btn.visible = (self._num_frames > 1) and self._playing
        if self._next_btn is not None:
            self._next_btn.visible = (self._num_frames > 0)
            self._next_btn.disabled = (len(self._files) <= 1)
        if self._delete_btn is not None:
            self._delete_btn.visible = (self._num_frames > 0)
            self._delete_btn.disabled = False
        if self._speed_slider is not None:
            self._speed_slider.visible = (self._num_frames > 1)
        if self._loop_checkbox is not None:
            self._loop_checkbox.visible = (self._num_frames > 1)

        return None

    def set_enabled(self, enabled: bool) -> None:
        super().set_enabled(enabled)
        if self._mesh_handle is not None:
            self._mesh_handle.visible = enabled
        if self._visualizer is not None:
            self._visualizer.set_robot_visible(not enabled)

    def _ensure_mesh(self) -> None:
        if self._mesh_handle is None:
            verts = np.zeros((3, 3), dtype=np.float32)
            faces = np.array([[0, 1, 2]], dtype=np.int32)
            self._mesh_handle = self.server.scene.add_mesh_simple(
                "/amass_human",
                vertices=verts,
                faces=faces,
                color=self.plugin_cfg['mesh_color'],
                wireframe=False,
            )

    def _load_folder_path(self) -> str:
        os.makedirs(TMP_DIR, exist_ok=True)
        path_file = os.path.join(TMP_DIR, 'amass_folder_path.txt')
        if os.path.exists(path_file):
            with open(path_file, 'r') as f:
                return f.read().strip()
        return ""

    def _save_folder_path(self, folder_path: str) -> None:
        os.makedirs(TMP_DIR, exist_ok=True)
        path_file = os.path.join(TMP_DIR, 'amass_folder_path.txt')
        with open(path_file, 'w') as f:
            f.write(folder_path)

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

    def _refresh_file_list(self) -> None:
        if not self._folder_path or not os.path.isdir(self._folder_path):
            self._files = []
        else:
            self._files = sorted([f for f in os.listdir(self._folder_path) if f.lower().endswith('.npz')])
        if self._file_dropdown is not None:
            opts = self._files if self._files else ["<none>"]
            self._file_dropdown.options = opts
            self._file_dropdown.value = opts[0]

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

    def _load_amass_file(self, path: str) -> None:
        if not os.path.exists(path):
            cprint(f"File not found: {path}", 'red')
            return
        self._current_file = os.path.basename(path)
        
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
            self._num_frames = 0
            if self._frame_slider is not None:
                self._frame_slider.visible = False
                self._frame_slider.value = 0.0
            if self._frame_info is not None:
                self._frame_info.visible = False
            if self._play_btn is not None:
                self._play_btn.visible = False
            if self._pause_btn is not None:
                self._pause_btn.visible = False
            if self._speed_slider is not None:
                self._speed_slider.visible = False
            if self._loop_checkbox is not None:
                self._loop_checkbox.visible = False
            return

        self._amass_data = {
            'poses': poses,
            'trans': trans,
            'betas': betas,
        }
        self._num_frames = T
        self._current_frame_f = 0.0
        self._playing = False

        assert self._smpl is not None
        smpl_out = self._smpl.get_outputs(betas, np.repeat(np.eye(3)[None, ...], self._smpl.num_joints, axis=0))
        self._ensure_mesh()
        if self._mesh_handle is not None:
            self._mesh_handle.vertices = smpl_out.vertices
            self._mesh_handle.faces = smpl_out.faces
            self._mesh_handle.color = self._color_input.value if self._color_input is not None else self.plugin_cfg['mesh_color']
            self._mesh_handle.wireframe = self._wireframe_checkbox.value if self._wireframe_checkbox is not None else False

        if self._frame_slider is not None:
            self._frame_slider.visible = False
            self._frame_slider.min = 0
            self._frame_slider.max = max(1, T - 1)
            self._frame_slider.value = 0.0
            self._frame_slider.disabled = (T <= 1)
            self._frame_slider.visible = True
        if self._frame_info is not None:
            self._frame_info.visible = True
            self._frame_info.value = f"Frame 0/{max(0, T - 1)}"
        if self._play_btn is not None:
            self._play_btn.visible = (T > 1)
            self._play_btn.disabled = (T <= 1)
        if self._pause_btn is not None:
            self._pause_btn.visible = False
        if self._speed_slider is not None:
            self._speed_slider.visible = (T > 1)
        if self._loop_checkbox is not None:
            self._loop_checkbox.visible = (T > 1)
        
        self._current_frame_f = 0.0
        self._update_frame(0)

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

    def _update_frame(self, idx: int) -> None:
        if self._amass_data is None or self._smpl is None or self._mesh_handle is None:
            return
        betas = self._amass_data['betas']
        poses = self._amass_data['poses'][idx]
        trans = self._amass_data['trans'][idx]

        joint_rotmats = self._axisangle_to_rotmats(poses, self._smpl.num_joints)
        smpl_out = self._smpl.get_outputs(betas=betas, joint_rotmats=joint_rotmats)

        verts = smpl_out.vertices + trans[None, :]
        self._mesh_handle.vertices = verts

    def _next_file(self) -> None:
        if not self._files or self._current_file is None:
            return

        current_idx = self._files.index(self._current_file)
        next_idx = (current_idx + 1) % len(self._files)
        next_file = self._files[next_idx]

        if self._file_dropdown is not None:
            self._file_dropdown.value = next_file
        
        self._load_amass_file(os.path.join(self._folder_path, next_file))
        self._current_file = next_file

        self._playing = True
        if self._play_btn is not None:
            self._play_btn.visible = False
        if self._pause_btn is not None:
            self._pause_btn.visible = True
    def _delete_current_file(self) -> None:
        if not self._files or self._current_file is None or not self._folder_path:
            return
        
        # remove folder
        remove_folder = os.path.join(self._folder_path, 'remove')
        os.makedirs(remove_folder, exist_ok=True)
        
        current_file_path = os.path.join(self._folder_path, self._current_file)
        if not os.path.exists(current_file_path):
            cprint(f"File not found: {current_file_path}", 'red')
            return

        dest_path = os.path.join(remove_folder, self._current_file)
        shutil.move(current_file_path, dest_path)
        cprint(f"Moved {self._current_file} to remove folder", 'green')

        current_idx = self._files.index(self._current_file)
        self._refresh_file_list()
        
        if self._files:
            next_idx = min(current_idx, len(self._files) - 1)
            next_file = self._files[next_idx]

            if self._file_dropdown is not None:
                self._file_dropdown.value = next_file
            
            self._load_amass_file(os.path.join(self._folder_path, next_file))
            self._current_file = next_file

            self._playing = True
            if self._play_btn is not None:
                self._play_btn.visible = False
            if self._pause_btn is not None:
                self._pause_btn.visible = True
        else:
            # No more files
            self._current_file = None
            self._amass_data = None
            self._num_frames = 0
            cprint("No more files in folder", 'yellow')

if __name__ == "__main__":
    vis = BaseVisualizer(target_fps=30.0)
    amass = AmassPlayerModule(vis.server)
    vis.register_module(amass)
    vis.set_active_module("AMASS Player")
    vis.main_loop()