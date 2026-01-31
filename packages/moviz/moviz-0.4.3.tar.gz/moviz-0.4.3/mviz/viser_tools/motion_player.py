import numpy as np
from tqdm import tqdm
import os
import time
import viser
from typing import List, Dict, Union, Any, Optional, TYPE_CHECKING
from termcolor import cprint
from mviz.utils.math_utils_np import get_vel, quat_inv, quat_mul, quat_to_rpy, quat_apply, quat_to_tan_norm, slerp
from abc import ABC
import iceoryx2 as iox2
from mviz.ice_tools.msgs import G1State, Kpose, G1Quat, Quaternion

if TYPE_CHECKING:
    from mviz.viser_tools.base_visualizer import VisualizerModule

from mviz.viser_tools.plugin_registry import register_plugin
from mviz.utils.fk_standalone import FKStandalone
from mviz import TMP_DIR
from mviz.configs.robot import ISAAC_SIM_TO_G1_JOINT_MAPPING

class MotionLoader(ABC):
    def __init__(self, device = 'cpu', target_fps = 30) -> None:
        self.device = device
        self.fps = target_fps
        self.vel_dict = {}
        self.motion_dict: Dict[str, np.ndarray] = {}
        self.motion_cfg: List[Dict[str, Any]] = []
        # All quaternions are in xyzw order
        
    def _load_motion(self, motion_path: List[str]) -> None:
        if isinstance(motion_path, str):
            motion_path = [motion_path]
        assert isinstance(motion_path, list) and len(motion_path) > 0, "motion_path should be a non-empty list of file paths"
        self.motion_names = [os.path.basename(path).split('.')[0] for path in motion_path]
        self.motion_paths = motion_path

    def __getitem__(self, name: str) -> np.ndarray:
        return self.motion_dict[name]

    @property
    def length(self) -> int:
        return next(iter(self.motion_dict.values())).shape[0] if self.motion_dict else 0
    
    @property
    def num_clips(self) -> int:
        return len(self.motion_cfg)
    
    def _post_init(self) -> None:
        self.all_clip_start_frames = np.array([cfg['idx'][0] for cfg in self.motion_cfg], dtype=np.int64)
        self.all_clip_end_frames = np.array([cfg['idx'][1] for cfg in self.motion_cfg], dtype=np.int64)
        self.all_clip_lengths_frames = self.all_clip_end_frames - self.all_clip_start_frames
        # set all vel variables at start frame to zero
        for key, value in self.motion_dict.items():
            if 'vel' in key and value.shape[0] > 0:
                self.motion_dict[key][self.all_clip_start_frames] = 0.0
        self.motion_lengths = np.array([cfg['idx'][1] - cfg['idx'][0] for cfg in self.motion_cfg], dtype=np.int64)
        
    def get_clip(self, idx: int) -> Dict[str, np.ndarray]:
        # get motion clip by index
        if idx < 0 or idx >= self.num_clips:
            raise IndexError(f"Index {idx} out of range for motion clips.")
        start, end = self.motion_cfg[idx]['idx']
        return {key: value[start:end] for key, value in self.motion_dict.items()}
    

    def resample(self, new_fps: int) -> None:
        # resample all motion clips to a new fps using interpolation
        if new_fps == self.fps:
            print(f"New FPS ({new_fps}) is the same as the current FPS. No action taken.")
            return

        print(f"Resampling motion data from {self.fps} FPS to {new_fps} FPS...")
        
        old_motion_dict = self.motion_dict
        old_fps = self.fps

        # identify primary keys to interpolate (velocities will be recalculated)
        primary_keys = [
            'link_pos', 'link_rot', 'joint_angles', 'obj_pos', 'obj_rot', 
            'target_keypoints', 'target_root_transform', 'target_rotation',
            'time_to_hit', 'hit_index', 'time_to_recovery', 'recovery_index',
            'feet_contact', 'hit', 'opponent_hit'
        ]
        keys_to_interpolate = [k for k in primary_keys if k in old_motion_dict]

        interpolated_motion_dict = {k: np.empty((0, *old_motion_dict[k].shape[1:]), dtype=old_motion_dict[k].dtype) 
                                    for k in keys_to_interpolate}

        new_motion_cfg = []
        total_new_frames = 0
        
        # interpolate primary data for each clip
        for i, clip_cfg in enumerate(tqdm(self.motion_cfg, desc="Resampling clips")):
            start_frame, end_frame = clip_cfg['idx']
            original_length = end_frame - start_frame
            if original_length <= 1: continue

            duration_s = (original_length - 1) / old_fps
            new_length = int(duration_s * new_fps) + 1
            time_steps = np.linspace(0, duration_s, new_length)

            query_frame_float = time_steps * old_fps
            f0 = np.floor(query_frame_float).astype(np.int64)
            f1 = np.ceil(query_frame_float).astype(np.int64)
            f0 = np.clip(f0, 0, original_length - 1)
            f1 = np.clip(f1, 0, original_length - 1)
            
            global_f0 = start_frame + f0
            global_f1 = start_frame + f1

            blend = (query_frame_float - f0.astype(np.float32))

            for key in keys_to_interpolate:
                slice0 = old_motion_dict[key][global_f0]
                slice1 = old_motion_dict[key][global_f1]
                
                current_blend = blend.reshape([-1] + [1] * (slice0.ndim - 1))

                if 'rot' in key and '6d' not in key:
                    interp_data = slerp(slice0, slice1, current_blend)
                
                interp_data = (1.0 - current_blend) * slice0 + current_blend * slice1
                
                if 'index' in key: # should resample 
                    interp_data = interp_data * new_fps / old_fps
                
                interpolated_motion_dict[key] = np.concatenate((interpolated_motion_dict[key], interp_data.astype(interpolated_motion_dict[key].dtype)), axis=0)

            new_start_frame = total_new_frames
            new_end_frame = total_new_frames + new_length
            new_motion_cfg.append({'idx': (new_start_frame, new_end_frame), 'object': clip_cfg['object']})
            total_new_frames = new_end_frame

        # Update state and recalculate derived data
        self.motion_dict = interpolated_motion_dict
        self.fps = new_fps
        self.motion_cfg = new_motion_cfg

        print("Re-calculating derived motion data (velocities, body frames, etc.)...")
        
        # Recalculate velocities
        vel_dict = {
            'link_vel': {'source': 'link_pos', 'type': 'linear'},
            'link_ang_vel': {'source': 'link_rot', 'type': 'angular'},
            'joint_vel': {'source': 'joint_angles', 'type': 'linear'},  
        }
        if getattr(self, 'has_object', False):
            vel_dict.update({
                'obj_vel': {'source': 'obj_pos', 'type': 'linear'},
                'obj_ang_vel': {'source': 'obj_rot', 'type': 'angular'},
            })

        for key, info in vel_dict.items():
            self.motion_dict[key] = get_vel(self.motion_dict[info['source']], info['type'], self.fps)

        # --- Recalculate RPY, 6D, and body-frame representations ---
        items = ['link'] 
        if getattr(self, 'has_object', False): items.append('obj')
        base_rot_w_quat_inv = quat_inv(self.motion_dict['link_rot'][:, 0:1, :])
        root_pos_w = self.motion_dict['link_pos'][:, 0:1, :]
        for item in items:
            base_rot_inv = base_rot_w_quat_inv if item == 'link' else base_rot_w_quat_inv.squeeze(-2)
            root_pos = root_pos_w if item == 'link' else root_pos_w.squeeze(-2)
            self.motion_dict[f'{item}_rpy'] = quat_to_rpy(self.motion_dict[f'{item}_rot'])
            self.motion_dict[f'{item}_6d_rot'] = quat_to_tan_norm(self.motion_dict[f'{item}_rot'])
            self.motion_dict[f'{item}_pos_b'] = quat_apply(base_rot_inv, self.motion_dict[f'{item}_pos'] - root_pos)
            self.motion_dict[f'{item}_rot_b'] = quat_mul(base_rot_inv, self.motion_dict[f'{item}_rot'])
            self.motion_dict[f'{item}_rpy_b'] = quat_to_rpy(self.motion_dict[f'{item}_rot_b'])
            self.motion_dict[f'{item}_6d_rot_b'] = quat_to_tan_norm(self.motion_dict[f'{item}_rot_b'])
            self.motion_dict[f'{item}_vel_b'] = quat_apply(base_rot_inv, self.motion_dict[f'{item}_vel'])
            self.motion_dict[f'{item}_ang_vel_b'] = quat_apply(base_rot_inv, self.motion_dict[f'{item}_ang_vel'])

        self._post_init()
        print(f"Resampling complete. New total frames: {self.length}, New FPS: {self.fps}")


class NpzMotion(MotionLoader):
    def __init__(self, motion_path: Union[str, List[str]] = None, device: str = 'cpu', target_fps: int = 30) -> None:
        super().__init__(device, target_fps)
        if motion_path is not None:
            self._load_motion(motion_path)
            self._post_init()
    def _load_motion(self, motion_path: Union[str, List[str]]) -> None:
        super()._load_motion(motion_path)
        
        self.motion_dict = {
            'root_pos': np.empty((0, 3), dtype=np.float32),
            'root_rot': np.empty((0, 4), dtype=np.float32),
            'joint_pos': np.empty((0, 0), dtype=np.float32),
            'joint_vel': np.empty((0, 0), dtype=np.float32),
            'body_pos': np.empty((0, 0, 3), dtype=np.float32),
            'body_rot': np.empty((0, 0, 4), dtype=np.float32),
            'body_vel': np.empty((0, 0, 3), dtype=np.float32),
            'body_ang_vel': np.empty((0, 0, 3), dtype=np.float32),
            'root_vel': np.empty((0, 3), dtype=np.float32),
            'root_ang_vel': np.empty((0, 3), dtype=np.float32),
        }
        
        start_idx = 0
        self._urdf_to_g1_mapping = ISAAC_SIM_TO_G1_JOINT_MAPPING

        for data_path in motion_path:
            data = np.load(data_path, allow_pickle=True)
            
            # get fps from the file
            if 'fps' in data:
                file_fps = int(data['fps'][0]) if isinstance(data['fps'], np.ndarray) else int(data['fps'])
            else:
                file_fps = 50  # default fps
                cprint(f"Warning: No FPS found in {data_path}, using default {file_fps}", 'yellow')
            
            # resample if needed
            skip = max(1, file_fps // self.fps)
            
            # load data - npz format has wxyz quaternions
            body_pos_w = data['body_pos_w'][::skip].astype(np.float32)
            body_quat_w = data['body_quat_w'][::skip].astype(np.float32)
            body_lin_vel_w = data['body_lin_vel_w'][::skip].astype(np.float32)
            body_ang_vel_w = data['body_ang_vel_w'][::skip].astype(np.float32)
            
            # load joint data
            joint_pos = data['joint_pos'][::skip].astype(np.float32)
            joint_vel = data['joint_vel'][::skip].astype(np.float32)
            
            # reorder joints from isaac sim order to g1 csv order
            if self._urdf_to_g1_mapping is not None:
                joint_pos = joint_pos[:, self._urdf_to_g1_mapping]
                joint_vel = joint_vel[:, self._urdf_to_g1_mapping]
            length = body_pos_w.shape[0]
            num_bodies = body_pos_w.shape[1]
            num_joints = joint_pos.shape[1]
            
            # initialize body and joint arrays if this is the first file
            if self.motion_dict['body_pos'].shape[1] == 0:
                self.motion_dict['body_pos'] = np.empty((0, num_bodies, 3), dtype=np.float32)
                self.motion_dict['body_rot'] = np.empty((0, num_bodies, 4), dtype=np.float32)
                self.motion_dict['body_vel'] = np.empty((0, num_bodies, 3), dtype=np.float32)
                self.motion_dict['body_ang_vel'] = np.empty((0, num_bodies, 3), dtype=np.float32)
            
            if self.motion_dict['joint_pos'].shape[1] == 0:
                self.motion_dict['joint_pos'] = np.empty((0, num_joints), dtype=np.float32)
                self.motion_dict['joint_vel'] = np.empty((0, num_joints), dtype=np.float32)
            
            # convert quaternions from wxyz to xyzw
            body_rot_xyzw = body_quat_w[:, :, [1, 2, 3, 0]]
            root_rot_xyzw = body_quat_w[:, 0, [1, 2, 3, 0]]
            
            # extract root
            root_pos = body_pos_w[:, 0, :]
            root_vel = body_lin_vel_w[:, 0, :]
            root_ang_vel = body_ang_vel_w[:, 0, :]
            
            end_idx = start_idx + length
            self.motion_cfg.append({'idx': (start_idx, end_idx), 'object': None})
            start_idx = end_idx
            
            # concatenate to motion_dict
            self.motion_dict['root_pos'] = np.concatenate((self.motion_dict['root_pos'], root_pos), axis=0)
            self.motion_dict['root_rot'] = np.concatenate((self.motion_dict['root_rot'], root_rot_xyzw), axis=0)
            self.motion_dict['root_vel'] = np.concatenate((self.motion_dict['root_vel'], root_vel), axis=0)
            self.motion_dict['root_ang_vel'] = np.concatenate((self.motion_dict['root_ang_vel'], root_ang_vel), axis=0)
            self.motion_dict['body_pos'] = np.concatenate((self.motion_dict['body_pos'], body_pos_w), axis=0)
            self.motion_dict['body_rot'] = np.concatenate((self.motion_dict['body_rot'], body_rot_xyzw), axis=0)
            self.motion_dict['body_vel'] = np.concatenate((self.motion_dict['body_vel'], body_lin_vel_w), axis=0)
            self.motion_dict['body_ang_vel'] = np.concatenate((self.motion_dict['body_ang_vel'], body_ang_vel_w), axis=0)
            self.motion_dict['joint_pos'] = np.concatenate((self.motion_dict['joint_pos'], joint_pos), axis=0)
            self.motion_dict['joint_vel'] = np.concatenate((self.motion_dict['joint_vel'], joint_vel), axis=0)


class CsvMotion(MotionLoader):
    def __init__(self, motion_path: Union[str, List[str]] = None, device: str = 'cpu', target_fps: int = 30) -> None:
        super().__init__(device, target_fps)
        if motion_path is not None:
            self._load_motion(motion_path)
            self._post_init()
        
    def _load_motion(self, motion_path: Union[str, List[str]]) -> None:
        super()._load_motion(motion_path)
        
        self.motion_dict = {
            'root_pos': np.empty((0, 3), dtype=np.float32),
            'root_rot': np.empty((0, 4), dtype=np.float32),
            'joint_pos': np.empty((0, 29), dtype=np.float32),
            'joint_vel': np.empty((0, 29), dtype=np.float32),
            'root_vel': np.empty((0, 3), dtype=np.float32),
            'root_ang_vel': np.empty((0, 3), dtype=np.float32),
        }
        
        start_idx = 0
        csv_fps = 30
        
        for data_path in motion_path:
            # csv format: xyz (3) + qxyzw (4) + 29 joints
            data = np.loadtxt(data_path, delimiter=',', dtype=np.float32)
            
            if data.shape[1] != 36:
                cprint(f"Warning: Expected 36 columns in CSV (3 pos + 4 quat + 29 joints), got {data.shape[1]} in {data_path}", 'yellow')
                if data.shape[1] < 7:
                    cprint(f"Error: CSV must have at least 7 columns (position + quaternion)", 'red')
                    continue
            
            skip = max(1, csv_fps // self.fps)
            data = data[::skip]
            
            root_pos = data[:, 0:3]
            root_rot_xyzw = data[:, 3:7]
            
            # extract joint angles
            num_joints = min(29, data.shape[1] - 7)
            if num_joints < 29:
                cprint(f"Warning: CSV has only {num_joints} joints, padding to 29 with zeros", 'yellow')
                joint_pos = np.zeros((data.shape[0], 29), dtype=np.float32)
                joint_pos[:, :num_joints] = data[:, 7:7+num_joints]
            else:
                joint_pos = data[:, 7:36]
            
            length = data.shape[0]
            
            # calculate velocities
            root_vel = get_vel(root_pos, 'linear', self.fps)
            root_ang_vel = get_vel(root_rot_xyzw, 'angular', self.fps)
            joint_vel = get_vel(joint_pos, 'linear', self.fps)
            
            end_idx = start_idx + length
            self.motion_cfg.append({'idx': (start_idx, end_idx), 'object': None})
            start_idx = end_idx
            
            # concatenate to motion_dict
            self.motion_dict['root_pos'] = np.concatenate((self.motion_dict['root_pos'], root_pos), axis=0)
            self.motion_dict['root_rot'] = np.concatenate((self.motion_dict['root_rot'], root_rot_xyzw), axis=0)
            self.motion_dict['joint_pos'] = np.concatenate((self.motion_dict['joint_pos'], joint_pos), axis=0)
            self.motion_dict['root_vel'] = np.concatenate((self.motion_dict['root_vel'], root_vel), axis=0)
            self.motion_dict['root_ang_vel'] = np.concatenate((self.motion_dict['root_ang_vel'], root_ang_vel), axis=0)
            self.motion_dict['joint_vel'] = np.concatenate((self.motion_dict['joint_vel'], joint_vel), axis=0)

@register_plugin  
class MotionPlayerModule:
    # plugin configuration (unified config dictionary)
    plugin_cfg = {
        'target_fps': 30,
        'default_playback_speed': 1.0,
        'loop_by_default': True,
    }
    
    def __init__(self, server: viser.ViserServer):
        from mviz.viser_tools.base_visualizer import VisualizerModule

        self.name = "Motion Loader"
        self.server = server
        self.enabled = True
        self.ui_folder: Optional[viser.GuiHandle] = None
        
        # unpack plugin configuration
        self.target_fps = self.plugin_cfg['target_fps']
        self.default_playback_speed = self.plugin_cfg['default_playback_speed']
        self.loop_by_default = self.plugin_cfg['loop_by_default']

        self.motion_loader = None
        self.current_clip_idx = 0
        self.current_frame = 0
        self.playing = False
        self.playback_speed = self.default_playback_speed
        self.loop = self.loop_by_default
        
        # timing
        self.last_update_time = time.time()
        
        # file/folder management
        self.folder_path = self._load_folder_path()
        self.motion_files = []
        self.current_file = None
        
        # playback state flag to prevent callback loops
        self._updating_from_playback = False
        
        # publishing state
        self.sending = False
        self.publisher = None
        self.quat_publisher = None
        self.node = None
        self.message_count = 0
        self.quat_message_count = 0
        self._fk_helper: Optional[FKStandalone] = None
        
        # initialize iceoryx2 publishers
        try:
            self.node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)
            service = (
                self.node.service_builder(iox2.ServiceName.new("/mviz/fstate"))
                .publish_subscribe(G1State)
                .open_or_create()
            )
            self.publisher = service.publisher_builder().create()

            quat_service = (
                self.node.service_builder(iox2.ServiceName.new("/mviz/fquat"))
                .publish_subscribe(G1Quat)
                .open_or_create()
            )
            self.quat_publisher = quat_service.publisher_builder().create()
            
        except Exception as e:
            # Silently handle initialization errors - no user-facing output needed
            self.publisher = None
            self.quat_publisher = None
            self.node = None
        
        # ui elements
        self.folder_input = None
        self.fps_input = None
        self.file_dropdown = None
        self.frame_slider = None
        self.play_button = None
        self.pause_button = None
        self.speed_slider = None
        self.loop_checkbox = None
        self.frame_info_text = None
        self.send_button = None
        self.stop_button = None
        self.status_text = None
    
    def _load_folder_path(self) -> str:
        # load saved folder path from temp file
        os.makedirs(TMP_DIR, exist_ok=True)
        path_file = os.path.join(TMP_DIR, 'motion_folder_path.txt')
        if os.path.exists(path_file):
            with open(path_file, 'r') as f:
                return f.read().strip()
        return ""
    
    def _save_folder_path(self, folder_path: str) -> None:
        # save folder path to temp file
        os.makedirs(TMP_DIR, exist_ok=True)
        path_file = os.path.join(TMP_DIR, 'motion_folder_path.txt')
        with open(path_file, 'w') as f:
            f.write(folder_path)
    
    def _scan_motion_files(self, folder_path: str) -> List[str]:
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return []
        files = [f for f in os.listdir(folder_path) if f.endswith('.npz') or f.endswith('.csv')]
        return sorted(files)

    def _build_source_controls(self) -> None:
        # folder path input
        self.folder_input = self.server.gui.add_text(
            "Folder Path",
            initial_value=self.folder_path,
        )
        
        @self.folder_input.on_update
        def _(event) -> None:
            input_val = event.target.value

            if (input_val.lower().endswith('.npz') or input_val.lower().endswith('.csv')) and os.path.isfile(input_val):
                folder_path = os.path.dirname(input_val)
                target_file = os.path.basename(input_val)
                
                self.folder_path = folder_path
                self.folder_input.value = folder_path
                self._save_folder_path(self.folder_path)

                self.motion_files = self._scan_motion_files(self.folder_path)
                
                if self.file_dropdown is not None:
                    if self.motion_files:
                        self.file_dropdown.options = self.motion_files
                        if target_file in self.motion_files:
                            self.file_dropdown.value = target_file
                        else:
                            self.file_dropdown.value = self.motion_files[0]
                    else:
                        self.motion_loader = None
                        self._update_clip_controls()
                        self.file_dropdown.options = ["No motion files found"]
                        self.file_dropdown.value = "No motion files found"
            else:
                self.folder_path = input_val
                self._save_folder_path(self.folder_path)
                
                # scan for motion files and update dropdown
                self.motion_files = self._scan_motion_files(self.folder_path)
                
                if self.file_dropdown is not None:
                    if self.motion_files:
                        # update dropdown options
                        self.file_dropdown.options = self.motion_files
                        self.file_dropdown.value = self.motion_files[0]
                    else:
                        # clear motion loader when no files found
                        self.motion_loader = None
                        self._update_clip_controls()
                        self.file_dropdown.options = ["No motion files found"]
                        self.file_dropdown.value = "No motion files found"
    
    def _load_motion_file(self, filename: str) -> None:
        if not self.folder_path or not filename:
            return
        
        file_path = os.path.join(self.folder_path, filename)
        if not os.path.exists(file_path):
            cprint(f"File not found: {file_path}", 'red')
            return
        
        try:
            # create new motion loader based on file extension
            if filename.endswith('.npz'):
                self.motion_loader = NpzMotion([file_path], device='cpu', target_fps=self.target_fps)
            elif filename.endswith('.csv'):
                self.motion_loader = CsvMotion([file_path], device='cpu', target_fps=self.target_fps)
            else:
                cprint(f"Unsupported file type: {filename}", 'red')
                return
            
            self.current_clip_idx = 0
            self.current_frame = 0
            self.playing = False
            self.current_file = filename  # track current file for reloading

            if self.motion_loader.num_clips > 0:
                self._update_clip_controls()
        except Exception as e:
            cprint(f"Error loading {filename}: {e}", 'red')
            self.current_file = None
        
    def _update_clip_controls(self) -> None:
        # update frame controls based on loaded motion
        if self.motion_loader is None or self.motion_loader.num_clips == 0:
            if self.frame_slider is not None:
                self.frame_slider.visible = False
            if self.frame_info_text is not None:
                self.frame_info_text.visible = False
            if self.play_button is not None:
                self.play_button.visible = False
            if self.pause_button is not None:
                self.pause_button.visible = False
            if self.speed_slider is not None:
                self.speed_slider.visible = False
            if self.loop_checkbox is not None:
                self.loop_checkbox.visible = False
            if self.send_button is not None:
                self.send_button.visible = False
            if self.stop_button is not None:
                self.stop_button.visible = False
            if self.status_text is not None:
                self.status_text.visible = False
            return
        
        # update frame slider
        try:
            clip_data = self.motion_loader.get_clip(0)
            if clip_data and len(clip_data) > 0:
                first_key = next(iter(clip_data.keys()))
                max_frame = max(1, clip_data[first_key].shape[0] - 1)  # at least 1
            else:
                max_frame = 1
        except Exception as e:
            cprint(f"Warning: Error getting frame count: {e}", 'yellow')
            max_frame = 1
        
        if self.frame_slider is not None:
            self.frame_slider.visible = True
            # update value before max to avoid nan
            self._updating_from_playback = True
            self.frame_slider.value = 0
            self._updating_from_playback = False
            self.frame_slider.max = int(max_frame)
        
        if self.frame_info_text is not None:
            self.frame_info_text.visible = True
            self.frame_info_text.value = f"Frame 0/{int(max_frame)}"
        
        if self.play_button is not None:
            self.play_button.visible = True
        if self.pause_button is not None:
            self.pause_button.visible = False
        if self.speed_slider is not None:
            self.speed_slider.visible = True
        if self.loop_checkbox is not None:
            self.loop_checkbox.visible = True
        if self.send_button is not None:
            self.send_button.visible = True
        if self.status_text is not None:
            self.status_text.visible = True
    
    def build_ui(self, parent_folder: Optional[str] = None) -> None:
        self.ui_folder = self.server.gui.add_folder(self.name)
        
        with self.ui_folder:
            self._build_source_controls()
            
            # fps input
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
                    # reload current file with new fps if one is loaded
                    if self.motion_loader is not None and self.current_file:
                        cprint(f"Reloading with new FPS: {new_fps}", 'cyan')
                        self._load_motion_file(self.current_file)
            
            # scan for initial motion files
            self.motion_files = self._scan_motion_files(self.folder_path)
            
            # file dropdown
            if self.motion_files:
                self.file_dropdown = self.server.gui.add_dropdown(
                    "Motion File",
                    options=self.motion_files,
                    initial_value=self.motion_files[0],
                )
                
                @self.file_dropdown.on_update
                def _(event) -> None:
                    filename = event.target.value
                    # only load if it's a valid motion file (not the "No motion files found" message)
                    if filename and (filename.endswith('.npz') or filename.endswith('.csv')):
                        self._load_motion_file(filename)
                
                # load the first file by default if no motion loader provided
                if self.motion_loader is None:
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
                    # only load if it's a valid motion file
                    if filename and (filename.endswith('.npz') or filename.endswith('.csv')):
                        self._load_motion_file(filename)
            
            # frame control
            has_motion = self.motion_loader is not None and self.motion_loader.num_clips > 0
            initial_max_frame = 1  # default to at least 1
            if has_motion:
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
                # only update and pause if this is a user interaction, not playback update
                if not self._updating_from_playback:
                    self.current_frame = event.target.value
                    self.playing = False  # pause when manually scrubbing
            
            self.frame_info_text = self.server.gui.add_text(
                "Frame Info",
                f"Frame 0/{int(initial_max_frame)}" if has_motion else "No frame loaded",
                visible=has_motion,
            )
            
            # playback controls
            self.play_button = self.server.gui.add_button("Play", visible=has_motion)
            self.pause_button = self.server.gui.add_button("Pause", visible=False)
            
            @self.play_button.on_click
            def _(_) -> None:
                self.playing = True
                if self.play_button is not None:
                    self.play_button.visible = False
                if self.pause_button is not None:
                    self.pause_button.visible = True
            
            @self.pause_button.on_click
            def _(_) -> None:
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
                self.playback_speed = event.target.value
            
            self.loop_checkbox = self.server.gui.add_checkbox(
                "Loop",
                initial_value=True,
                visible=has_motion,
            )
            
            @self.loop_checkbox.on_update
            def _(event) -> None:
                self.loop = event.target.value
            
            # send/stop buttons
            if self.publisher is not None:
                self.send_button = self.server.gui.add_button("Send", visible=has_motion)
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
                
                # status text
                self.status_text = self.server.gui.add_text(
                    "Status",
                    "Topic: /mviz/msg (idle)",
                    visible=has_motion
                )
            else:
                # show disabled button if iceoryx2 not available
                self.send_button = self.server.gui.add_button("Send (unavailable)", visible=has_motion)
                self.send_button.disabled = True
                self.stop_button = None
                self.status_text = self.server.gui.add_text(
                    "Status",
                    "iceoryx2 not available",
                    visible=has_motion
                )
    
    def update(self) -> Optional[Dict[str, np.ndarray]]:
        # update playback and return robot state
        if self.motion_loader is None or self.motion_loader.num_clips == 0:
            return None
        
        # update playback
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        if self.playing:
            # advance frame based on fps and playback speed
            frame_advance = dt * self.motion_loader.fps * self.playback_speed
            self.current_frame += frame_advance
            
            # get clip data with validation
            try:
                clip_data = self.motion_loader.get_clip(self.current_clip_idx)
                if clip_data and len(clip_data) > 0:
                    first_key = next(iter(clip_data.keys()))
                    max_frame = max(0, clip_data[first_key].shape[0] - 1)
                else:
                    max_frame = 0
            except Exception as e:
                cprint(f"Error getting clip data: {e}", 'yellow')
                max_frame = 0
                self.playing = False
            
            # handle looping/end of clip
            if self.current_frame >= max_frame:
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = max_frame
                    self.playing = False
                    if self.play_button is not None:
                        self.play_button.visible = True
                    if self.pause_button is not None:
                        self.pause_button.visible = False
            
            # update ui - ensure values are valid integers
            current_frame_int = int(np.clip(self.current_frame, 0, max_frame))
            if self.frame_slider is not None:
                # set flag to prevent callback loop
                self._updating_from_playback = True
                self.frame_slider.value = current_frame_int
                self._updating_from_playback = False
            if self.frame_info_text is not None:
                self.frame_info_text.value = f"Frame {current_frame_int}/{int(max_frame)}"
        
        # get current frame data with validation
        try:
            clip_data = self.motion_loader.get_clip(self.current_clip_idx)
            if clip_data and len(clip_data) > 0:
                first_key = next(iter(clip_data.keys()))
                max_idx = max(0, clip_data[first_key].shape[0] - 1)
                frame_idx = int(np.clip(self.current_frame, 0, max_idx))
            else:
                return None
        except Exception as e:
            cprint(f"Error getting frame data: {e}", 'yellow')
            return None
        
        # extract robot state from motion data
        if 'root_pos' in clip_data and 'root_rot' in clip_data:
            root_pos = clip_data['root_pos'][frame_idx]  # (3,)
            root_rot = clip_data['root_rot'][frame_idx]  # (4,) xyzw
            
            # convert xyzw to wxyz
            root_quat_wxyz = np.array([root_rot[3], root_rot[0], root_rot[1], root_rot[2]], dtype=np.float32)
            
            # use actual joint data from npz file
            if 'joint_pos' in clip_data:
                joint_angles = clip_data['joint_pos'][frame_idx]
            else:
                # fallback to zeros if joint data not available
                joint_angles = np.zeros(29, dtype=np.float32)
            
            # publish state and quaternion
            if self.sending:
                if self.publisher is not None:
                    self._publish_robot_state(root_pos, root_rot, joint_angles)
                if self.quat_publisher is not None:
                    self._publish_robot_quat(root_pos, root_rot, joint_angles)
            
            # update status text
            if self.status_text is not None:
                if self.sending:
                    self.status_text.value = f"Topics: /mviz/msg ({self.message_count}), /mviz/quat ({self.quat_message_count})"
                else:
                    self.status_text.value = "Topic: /mviz/msg (idle)"
            
            return {
                'position': root_pos,
                'quaternion': root_quat_wxyz,
                'joint_angles': joint_angles
            }
        
        return None
    
    def _publish_robot_state(self, root_pos: np.ndarray, root_rot: np.ndarray, joint_angles: np.ndarray) -> None:
        if self.publisher is None:
            return

        # convert xyzw to qx, qy, qz, qw for kpose
        root_pose = Kpose(
            x=float(root_pos[0]),
            y=float(root_pos[1]),
            z=float(root_pos[2]),
            qx=float(root_rot[0]),  # x component
            qy=float(root_rot[1]),  # y component
            qz=float(root_rot[2]),  # z component
            qw=float(root_rot[3]),  # w component
        )

        state = G1State(root_joint=root_pose)
        # left leg (6 joints)
        state.left_hip_pitch_joint = float(joint_angles[0])
        state.left_hip_roll_joint = float(joint_angles[1])
        state.left_hip_yaw_joint = float(joint_angles[2])
        state.left_knee_joint = float(joint_angles[3])
        state.left_ankle_pitch_joint = float(joint_angles[4])
        state.left_ankle_roll_joint = float(joint_angles[5])
        
        # right leg (6 joints)
        state.right_hip_pitch_joint = float(joint_angles[6])
        state.right_hip_roll_joint = float(joint_angles[7])
        state.right_hip_yaw_joint = float(joint_angles[8])
        state.right_knee_joint = float(joint_angles[9])
        state.right_ankle_pitch_joint = float(joint_angles[10])
        state.right_ankle_roll_joint = float(joint_angles[11])
        
        # waist (3 joints)
        state.waist_yaw_joint = float(joint_angles[12])
        state.waist_roll_joint = float(joint_angles[13])
        state.waist_pitch_joint = float(joint_angles[14])
        
        # left arm (7 joints)
        state.left_shoulder_pitch_joint = float(joint_angles[15])
        state.left_shoulder_roll_joint = float(joint_angles[16])
        state.left_shoulder_yaw_joint = float(joint_angles[17])
        state.left_elbow_joint = float(joint_angles[18])
        state.left_wrist_roll_joint = float(joint_angles[19])
        state.left_wrist_pitch_joint = float(joint_angles[20])
        state.left_wrist_yaw_joint = float(joint_angles[21])
        
        # right arm (7 joints)
        state.right_shoulder_pitch_joint = float(joint_angles[22])
        state.right_shoulder_roll_joint = float(joint_angles[23])
        state.right_shoulder_yaw_joint = float(joint_angles[24])
        state.right_elbow_joint = float(joint_angles[25])
        state.right_wrist_roll_joint = float(joint_angles[26])
        state.right_wrist_pitch_joint = float(joint_angles[27])
        state.right_wrist_yaw_joint = float(joint_angles[28])
        
        # publish the state
        sample = self.publisher.loan_uninit()
        sample = sample.write_payload(state)
        sample.send()

        self.message_count += 1

    def _ensure_fk(self) -> None:
        if self._fk_helper is None:
            self._fk_helper = FKStandalone()

    def _compute_g1_quat(self, root_pos: np.ndarray, root_rot_xyzw: np.ndarray, joint_angles: np.ndarray) -> G1Quat:
        self._ensure_fk()
        return self._fk_helper.compute_g1_quat(root_pos, root_rot_xyzw, joint_angles)

    def _publish_robot_quat(self, root_pos: np.ndarray, root_rot: np.ndarray, joint_angles: np.ndarray) -> None:
        if self.quat_publisher is None:
            return
        gq = self._compute_g1_quat(root_pos, root_rot, joint_angles)
        sample = self.quat_publisher.loan_uninit()
        sample = sample.write_payload(gq)
        sample.send()
        self.quat_message_count += 1
    
    def set_enabled(self, enabled: bool) -> None:
        # enable or disable this module
        self.enabled = enabled
        if self.ui_folder is not None:
            self.ui_folder.visible = enabled


if __name__ == "__main__":  
    import os
    from mviz.viser_tools.base_visualizer import BaseVisualizer
    from mviz import ROOT_DIR

    visualizer = BaseVisualizer(target_fps=30.0)
    motion_ui = MotionPlayerModule(visualizer.server)
    visualizer.register_module(motion_ui)
    visualizer.set_active_module("Motion Loader")
    visualizer.main_loop()