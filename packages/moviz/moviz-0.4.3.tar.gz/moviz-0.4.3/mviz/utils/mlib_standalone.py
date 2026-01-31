import os
import glob
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from mviz.configs.robot import ISAAC_SIM_TO_G1_JOINT_MAPPING




class MotionLibrary:
    def __init__(self, motion_folder: str, target_fps: int = 30, max_frames: int = 400, window_size: int = 10):
        self.motion_folder = motion_folder
        self.target_fps = target_fps
        self.max_frames = max_frames
        self.window_size = window_size
        
        self.motion_clips: List[Dict[str, np.ndarray]] = []
        self.clip_names: List[str] = []
        self.clip_lengths: List[int] = []
        
        self.joint_data: Optional[np.ndarray] = None
        self.clip_start_indices: Optional[np.ndarray] = None
        
        self.window_data: Optional[np.ndarray] = None
        self.window_start_indices: Optional[np.ndarray] = None
        self.window_clip_indices: Optional[np.ndarray] = None
        
        self._urdf_to_g1_mapping = ISAAC_SIM_TO_G1_JOINT_MAPPING
        
        self._load_motion_library()
        self._preprocess_for_matching()
    
    
    def _load_motion_library(self) -> None:
        if not os.path.exists(self.motion_folder):
            raise FileNotFoundError(f"Motion folder not found: {self.motion_folder}")
        
        npz_files = glob.glob(os.path.join(self.motion_folder, "*.npz"))
        if not npz_files:
            raise ValueError(f"No npz files found in {self.motion_folder}")
        
        
        for npz_file in sorted(npz_files):
            try:
                data = np.load(npz_file, allow_pickle=True)
                clip_name = os.path.basename(npz_file).split('.')[0]
                
                if 'fps' in data:
                    file_fps = int(data['fps'][0]) if isinstance(data['fps'], np.ndarray) else int(data['fps'])
                else:
                    file_fps = 50
                
                skip = max(1, file_fps // self.target_fps)
                
                joint_pos = data['joint_pos'][::skip].astype(np.float32)
                
                if self._urdf_to_g1_mapping is not None:
                    joint_pos = joint_pos[:, self._urdf_to_g1_mapping]
                
                if 'root_pos' in data:
                    root_pos = data['root_pos'][::skip].astype(np.float32)
                elif 'body_pos_w' in data:
                    root_pos = data['body_pos_w'][::skip, 0].astype(np.float32)
                else:
                    root_pos = np.zeros((joint_pos.shape[0], 3), dtype=np.float32)
                
                if 'root_rot' in data:
                    root_rot = data['root_rot'][::skip].astype(np.float32)
                elif 'body_quat_w' in data:
                    root_rot = data['body_quat_w'][::skip, 0].astype(np.float32)
                else:
                    root_rot = np.zeros((joint_pos.shape[0], 4), dtype=np.float32)
                
                if joint_pos.shape[1] != 29:
                    if joint_pos.shape[1] < 29:
                        padded_joints = np.zeros((joint_pos.shape[0], 29), dtype=np.float32)
                        padded_joints[:, :joint_pos.shape[1]] = joint_pos
                        joint_pos = padded_joints
                    else:
                        joint_pos = joint_pos[:, :29]
                
                if joint_pos.shape[0] > self.max_frames:
                    joint_pos = joint_pos[:self.max_frames]
                    root_pos = root_pos[:self.max_frames]
                    root_rot = root_rot[:self.max_frames]
                elif joint_pos.shape[0] < self.max_frames:
                    pad_frames = self.max_frames - joint_pos.shape[0]
                    joint_pos = np.concatenate([joint_pos, np.tile(joint_pos[-1:], (pad_frames, 1))], axis=0)
                    root_pos = np.concatenate([root_pos, np.tile(root_pos[-1:], (pad_frames, 1))], axis=0)
                    root_rot = np.concatenate([root_rot, np.tile(root_rot[-1:], (pad_frames, 1))], axis=0)
                
                
                clip_data = {
                    'joint_pos': joint_pos,
                    'root_pos': root_pos,
                    'root_rot': root_rot,
                    'original_length': data['joint_pos'].shape[0]
                }
                
                self.motion_clips.append(clip_data)
                self.clip_names.append(clip_name)
                self.clip_lengths.append(joint_pos.shape[0])
            except Exception as e:
                continue
        
        if not self.motion_clips:
            raise ValueError("No valid motion clips loaded")
        
    
    def _preprocess_for_matching(self) -> None:
        all_joint_data = []
        clip_start_indices = []
        current_start = 0
        
        for clip in self.motion_clips:
            clip_start_indices.append(current_start)
            all_joint_data.append(clip['joint_pos'])
            current_start += clip['joint_pos'].shape[0]
        
        self.joint_data = np.concatenate(all_joint_data, axis=0)
        self.clip_start_indices = np.array(clip_start_indices, dtype=np.int64)
        
        all_windows = []
        window_start_indices = []
        window_clip_indices = []
        
        for clip_idx, clip in enumerate(self.motion_clips):
            clip_length = clip['joint_pos'].shape[0]
            
            if clip_length < self.window_size:
                continue
            
            for start in range(clip_length - self.window_size + 1):
                window = clip['joint_pos'][start:start + self.window_size]
                all_windows.append(window)
                window_start_indices.append(self.clip_start_indices[clip_idx] + start)
                window_clip_indices.append(clip_idx)
        
        if not all_windows:
            raise ValueError("No valid windows found - all clips too short for window size")
        
        self.window_data = np.array(all_windows, dtype=np.float32)
        self.window_start_indices = np.array(window_start_indices, dtype=np.int64)
        self.window_clip_indices = np.array(window_clip_indices, dtype=np.int64)
        
        
        
    
    def find_best_match(self, input_frames: np.ndarray) -> Tuple[int, int, float]:
        if self.window_data is None:
            raise ValueError("Motion library not loaded")
        
        input_frames = np.array(input_frames, dtype=np.float32)
        
        if input_frames.ndim == 1:
            raise ValueError(f"Single frame input (29,) is not supported for motion matching")
        
        if input_frames.ndim != 2 or input_frames.shape[1] != 29:
            raise ValueError(f"Expected input shape (N, 29), got {input_frames.shape}")
        
        if input_frames.shape[0] > self.window_size:
            raise ValueError(f"Input frames ({input_frames.shape[0]}) exceeds window size ({self.window_size})")
        
        if input_frames.shape[0] < self.window_size:
            padded_input = np.zeros((self.window_size, 29), dtype=np.float32)
            padded_input[:input_frames.shape[0]] = input_frames
            padded_input[input_frames.shape[0]:] = input_frames[-1]
            input_frames = padded_input
        
        return self._find_best_match_numpy(input_frames)
    
    
    
    def _find_best_match_numpy(self, input_frames: np.ndarray) -> Tuple[int, int, float]:
        distances = np.linalg.norm(self.window_data - input_frames, axis=(1, 2))
        
        best_window_idx = np.argmin(distances)
        min_distance = distances[best_window_idx]
        
        clip_idx = self.window_clip_indices[best_window_idx]
        frame_idx = self.window_start_indices[best_window_idx] - self.clip_start_indices[clip_idx]
        
        return clip_idx, frame_idx, min_distance
    
    def get_frames_from(self, clip_idx: int, frame_idx: int, n_frames: int) -> List[Dict[str, np.ndarray]]:
        if clip_idx >= len(self.motion_clips):
            raise ValueError(f"Clip index {clip_idx} out of range (max: {len(self.motion_clips)-1})")
        
        clip = self.motion_clips[clip_idx]
        clip_length = clip['joint_pos'].shape[0]
        
        if frame_idx >= clip_length:
            frame_idx = clip_length - 1
        elif frame_idx < 0:
            frame_idx = 0
        
        end_frame = min(frame_idx + n_frames, clip_length)
        actual_frames = end_frame - frame_idx
        
        frames = []
        for i in range(actual_frames):
            frame_data = {
                'root_pos': clip['root_pos'][frame_idx + i],
                'root_rot': clip['root_rot'][frame_idx + i],
                'joint_pos': clip['joint_pos'][frame_idx + i]
            }
            frames.append(frame_data)
        
        while len(frames) < n_frames:
            frames.append(frames[-1].copy())
        
        return frames
    
    def get_library_info(self) -> Dict[str, Union[int, List[str]]]:
        return {
            'num_clips': len(self.motion_clips),
            'total_frames': self.joint_data.shape[0] if self.joint_data is not None else 0,
            'num_windows': self.window_data.shape[0] if self.window_data is not None else 0,
            'window_size': self.window_size,
            'clip_names': self.clip_names,
            'clip_lengths': self.clip_lengths,
            'torch_available': False
        }


def load_motion_library(folder_path: str, target_fps: int = 30, max_frames: int = 400, window_size: int = 10) -> MotionLibrary:
    return MotionLibrary(folder_path, target_fps, max_frames, window_size)


class FrameBuffer:
    def __init__(self, window_size: int):
        self.window_size = window_size
        self.buffer = []
    
    def add_frame(self, frame: np.ndarray) -> None:
        if frame.shape != (29,):
            raise ValueError(f"Expected frame shape (29,), got {frame.shape}")
        
        self.buffer.append(frame.copy())
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
    
    def get_window(self) -> np.ndarray:
        if len(self.buffer) == 0:
            raise ValueError("Buffer is empty")
        return np.array(self.buffer, dtype=np.float32)
    
    def is_ready(self) -> bool:
        return len(self.buffer) >= self.window_size
    
    def clear(self) -> None:
        self.buffer.clear()
    
    def __len__(self) -> int:
        return len(self.buffer)


