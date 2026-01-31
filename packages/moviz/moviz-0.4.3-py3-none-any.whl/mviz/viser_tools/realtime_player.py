from termcolor import cprint
import ctypes
import viser
import numpy as np
import time
from typing import Optional, Dict
import iceoryx2 as iox2

from mviz.ice_tools.msgs import G1State, G1Quat, Kpose, Quaternion
from mviz.utils.fk_standalone import FKStandalone
from mviz.utils.mlib_standalone import MotionLibrary, FrameBuffer
from mviz.viser_tools.base_visualizer import VisualizerModule
from mviz.viser_tools.plugin_registry import register_plugin
from mviz import TMP_DIR


@register_plugin
class RealtimePlayerModule(VisualizerModule):
    plugin_cfg = {
        'topic_name': '/mviz/msg',
        'max_frame_samples': 30,
        'fps_update_interval': 0.25,
    }
    
    def __init__(self, server: viser.ViserServer) -> None:
        super().__init__("Message Subscriber", server)
        
        self.topic_name = self.plugin_cfg['topic_name']
        self.max_frame_samples = self.plugin_cfg['max_frame_samples']
        self.fps_update_interval = self.plugin_cfg['fps_update_interval']
        
        # iceoryx
        self.node = None
        self.subscriber = None
        self.latest_state: Optional[G1State] = None
        # quat publishing
        self.quat_publisher = None
        self.quat_message_count = 0
        self.sending = False
        self._fk_helper: Optional[FKStandalone] = None
        
        # fstate publishing
        self.fstate_publisher = None
        
        # flags
        self._has_new_state = False
        self.last_message_time: Optional[float] = None
        self._connected_recently: bool = False

        # FPS tracking
        self.fps = 0.0
        self.frame_times = []
        self._last_frame_end = time.perf_counter()
        self._last_fps_text_update = self._last_frame_end
        
        # Motion library matching
        self.motion_lib: Optional[MotionLibrary] = None
        self.use_motion_lib: bool = False
        self.lib_window_size: int = 30
        self.lib_playback_buffer: Optional[list] = None
        self.lib_buffer_index: int = 0
        self.lib_match_score: float = 0.0
        self.lib_frame_buffer: Optional[FrameBuffer] = None
        
        # UI elements
        self.fps_text = None
        self.status_btn_connected = None
        self.status_btn_disconnected = None
        self.topic_display = None
        
        # init
        self.setup_subscriber()
        self.setup_quat_publisher()
        self.setup_fstate_publisher()
        self.setup_motion_library()

    def setup_motion_library(self) -> None:
        import os

        path_file = os.path.join(TMP_DIR, 'motion_lib_path.txt')
        
        if os.path.exists(path_file):
            try:
                with open(path_file, 'r') as f:
                    lib_path = f.read().strip()
                if os.path.exists(lib_path):
                    self.motion_lib = MotionLibrary(lib_path)
                    self.lib_frame_buffer = FrameBuffer(self.motion_lib.window_size)
                    cprint(f"Auto-loaded motion library from {lib_path}", 'green')
                else:
                    cprint(f"Saved motion library path not found: {lib_path}", 'yellow')
            except Exception as e:
                cprint(f"Error loading motion library: {e}", 'red')

    def _ensure_fk(self) -> None:
        if self._fk_helper is None:
            self._fk_helper = FKStandalone()

    def setup_quat_publisher(self) -> None:
        try:
            if self.node is None:
                iox2.set_log_level_from_env_or(iox2.LogLevel.Warn)
                self.node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)
            quat_service = (
                self.node.service_builder(iox2.ServiceName.new("/mviz/fquat"))
                .publish_subscribe(G1Quat)
                .open_or_create()
            )
            self.quat_publisher = quat_service.publisher_builder().create()
        except Exception as e:
            # Silently handle initialization errors - no user-facing output needed
            self.quat_publisher = None

    def setup_fstate_publisher(self) -> None:
        try:
            if self.node is None:
                iox2.set_log_level_from_env_or(iox2.LogLevel.Warn)
                self.node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)
            fstate_service = (
                self.node.service_builder(iox2.ServiceName.new("/mviz/fstate"))
                .publish_subscribe(G1State)
                .open_or_create()
            )
            self.fstate_publisher = fstate_service.publisher_builder().create()
        except Exception as e:
            # Silently handle initialization errors - no user-facing output needed
            self.fstate_publisher = None

    def setup_subscriber(self) -> None:
        try:
            iox2.set_log_level_from_env_or(iox2.LogLevel.Warn)
            self.node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)
            
            service = (
                self.node.service_builder(iox2.ServiceName.new(self.topic_name))
                .publish_subscribe(G1State)
                .open_or_create()
            )
            
            self.subscriber = service.subscriber_builder().create()
        except Exception as e:
            # Silently handle initialization errors - no user-facing output needed
            self.subscriber = None
    
    def receive_messages(self) -> None:
        if self.subscriber is None:
            return
        while True:
            sample = self.subscriber.receive()
            if sample is None:
                break

            payload_ptr = sample.payload()
            src = payload_ptr.contents
            state_copy = G1State()
            ctypes.memmove(
                ctypes.addressof(state_copy),
                ctypes.addressof(src),
                ctypes.sizeof(G1State),
            )
            self.latest_state = state_copy
            self._has_new_state = True
            self.last_message_time = time.perf_counter()
    
    def update(self) -> Optional[Dict[str, np.ndarray]]:
        # Receive new messages
        self.receive_messages()
        
        # Update FPS tracking
        frame_end = time.perf_counter()
        frame_time = frame_end - self._last_frame_end
        self._last_frame_end = frame_end
        if frame_time > 0:
            self.frame_times.append(frame_time)
            if len(self.frame_times) > self.max_frame_samples:
                self.frame_times.pop(0)

        # Throttle GUI text updates
        if (frame_end - self._last_fps_text_update) >= self.fps_update_interval and self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            self.fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
            if self.fps_text is not None:
                self.fps_text.value = f"{self.fps:.2f}"
            self._last_fps_text_update = frame_end

            # Update connection status
            now_ts = frame_end
            connected = (
                self.last_message_time is not None
                and (now_ts - self.last_message_time) < 1.0
            )
            if connected != self._connected_recently:
                self._connected_recently = connected
                if self.status_btn_connected is not None and self.status_btn_disconnected is not None:
                    self.status_btn_connected.visible = connected
                    self.status_btn_disconnected.visible = not connected
        
        if not self._has_new_state or self.latest_state is None:
            return None
            
        self._has_new_state = False
        state = self.latest_state
        
        root_pos = np.array([state.root_joint.x, state.root_joint.y, state.root_joint.z], dtype=np.float32)
        root_quat_xyzw = np.array([state.root_joint.qx, state.root_joint.qy, 
                                    state.root_joint.qz, state.root_joint.qw], dtype=np.float32)
        root_quat_wxyz = np.array([root_quat_xyzw[3], root_quat_xyzw[0], 
                                    root_quat_xyzw[1], root_quat_xyzw[2]], dtype=np.float32)
        
        joint_angles = np.array([
            state.left_hip_pitch_joint,
            state.left_hip_roll_joint,
            state.left_hip_yaw_joint,
            state.left_knee_joint,
            state.left_ankle_pitch_joint,
            state.left_ankle_roll_joint,
            state.right_hip_pitch_joint,
            state.right_hip_roll_joint,
            state.right_hip_yaw_joint,
            state.right_knee_joint,
            state.right_ankle_pitch_joint,
            state.right_ankle_roll_joint,
            state.waist_yaw_joint,
            state.waist_roll_joint,
            state.waist_pitch_joint,
            state.left_shoulder_pitch_joint,
            state.left_shoulder_roll_joint,
            state.left_shoulder_yaw_joint,
            state.left_elbow_joint,
            state.left_wrist_roll_joint,
            state.left_wrist_pitch_joint,
            state.left_wrist_yaw_joint,
            state.right_shoulder_pitch_joint,
            state.right_shoulder_roll_joint,
            state.right_shoulder_yaw_joint,
            state.right_elbow_joint,
            state.right_wrist_roll_joint,
            state.right_wrist_pitch_joint,
            state.right_wrist_yaw_joint,
        ], dtype=np.float32)

        if self.sending and self.quat_publisher is not None:
            try:
                self._ensure_fk()
                gq = self._fk_helper.compute_g1_quat(root_pos, root_quat_xyzw, joint_angles)
                sample = self.quat_publisher.loan_uninit()
                sample = sample.write_payload(gq)
                sample.send()
                self.quat_message_count += 1
                if getattr(self, 'status_text', None) is not None:
                    self.status_text.value = f"Topic: /mviz/quat ({self.quat_message_count})"
            except Exception as e:
                cprint(f"Failed to publish /mviz/quat: {e}", 'red')
        else:
            if getattr(self, 'status_text', None) is not None and not self.sending:
                self.status_text.value = "Topic: /mviz/quat (idle)"

        # Motion library matching
        if self.use_motion_lib and self.motion_lib is not None:
            try:
                # Add current frame to buffer
                if self.lib_frame_buffer is not None:
                    self.lib_frame_buffer.add_frame(joint_angles)
                
                # Check if buffer is empty or exhausted
                if self.lib_playback_buffer is None or self.lib_buffer_index >= len(self.lib_playback_buffer):
                    # Re-match and refill buffer using frame history
                    if self.lib_frame_buffer is not None and len(self.lib_frame_buffer) > 0:
                        window = self.lib_frame_buffer.get_window()
                        clip_idx, frame_idx, score = self.motion_lib.find_best_match(window)
                        self.lib_playback_buffer = self.motion_lib.get_frames_from(
                            clip_idx, frame_idx, self.lib_window_size
                        )
                        self.lib_buffer_index = 0
                        self.lib_match_score = score
                        
                        # Update match score display
                        if hasattr(self, 'match_score_text') and self.match_score_text is not None:
                            self.match_score_text.value = f"Match Score: {score:.4f}"
                
                if self.lib_playback_buffer and self.lib_buffer_index < len(self.lib_playback_buffer):
                    buffered_frame = self.lib_playback_buffer[self.lib_buffer_index]
                    root_pos = buffered_frame['root_pos']
                    root_quat_wxyz = buffered_frame['root_rot']
                    joint_angles = buffered_frame['joint_pos']
                    self.lib_buffer_index += 1
                    
            except Exception as e:
                cprint(f"Motion library matching error: {e}", 'red')
                if self.lib_frame_buffer is not None:
                    self.lib_frame_buffer.clear()
                pass

        if self.fstate_publisher is not None:
            try:
                fstate = G1State()
                fstate.root_joint.x = root_pos[0]
                fstate.root_joint.y = root_pos[1]
                fstate.root_joint.z = root_pos[2]
                fstate.root_joint.qw = root_quat_wxyz[0]
                fstate.root_joint.qx = root_quat_wxyz[1]
                fstate.root_joint.qy = root_quat_wxyz[2]
                fstate.root_joint.qz = root_quat_wxyz[3]
                # Set joint angles
                fstate.left_hip_pitch_joint = joint_angles[0]
                fstate.left_hip_roll_joint = joint_angles[1]
                fstate.left_hip_yaw_joint = joint_angles[2]
                fstate.left_knee_joint = joint_angles[3]
                fstate.left_ankle_pitch_joint = joint_angles[4]
                fstate.left_ankle_roll_joint = joint_angles[5]
                fstate.right_hip_pitch_joint = joint_angles[6]
                fstate.right_hip_roll_joint = joint_angles[7]
                fstate.right_hip_yaw_joint = joint_angles[8]
                fstate.right_knee_joint = joint_angles[9]
                fstate.right_ankle_pitch_joint = joint_angles[10]
                fstate.right_ankle_roll_joint = joint_angles[11]
                fstate.waist_yaw_joint = joint_angles[12]
                fstate.waist_roll_joint = joint_angles[13]
                fstate.waist_pitch_joint = joint_angles[14]
                fstate.left_shoulder_pitch_joint = joint_angles[15]
                fstate.left_shoulder_roll_joint = joint_angles[16]
                fstate.left_shoulder_yaw_joint = joint_angles[17]
                fstate.left_elbow_joint = joint_angles[18]
                fstate.left_wrist_roll_joint = joint_angles[19]
                fstate.left_wrist_pitch_joint = joint_angles[20]
                fstate.left_wrist_yaw_joint = joint_angles[21]
                fstate.right_shoulder_pitch_joint = joint_angles[22]
                fstate.right_shoulder_roll_joint = joint_angles[23]
                fstate.right_shoulder_yaw_joint = joint_angles[24]
                fstate.right_elbow_joint = joint_angles[25]
                fstate.right_wrist_roll_joint = joint_angles[26]
                fstate.right_wrist_pitch_joint = joint_angles[27]
                fstate.right_wrist_yaw_joint = joint_angles[28]
                
                # Publish
                sample = self.fstate_publisher.loan_uninit()
                sample = sample.write_payload(fstate)
                sample.send()
            except Exception as e:
                cprint(f"Failed to publish /mviz/fstate: {e}", 'red')

        return {
            'position': root_pos,
            'quaternion': root_quat_wxyz,
            'joint_angles': joint_angles
        }
    
    def build_ui(self, parent_folder: Optional[str] = None) -> None:
        self.ui_folder = self.server.gui.add_folder(self.name)
        
        with self.ui_folder:
            # Status buttons
            self.status_btn_disconnected = self.server.gui.add_button(
                "Disconnected",
                color=(255, 59, 48),  # red
            )
            self.status_btn_connected = self.server.gui.add_button(
                "Connected",
                color=(52, 199, 89),  # green
            )
            self.status_btn_disconnected.visible = True
            self.status_btn_connected.visible = False
            
            # Topic info
            self.topic_display = self.server.gui.add_text(
                "Topic", 
                f"{self.topic_name}"
            )

            # FPS display
            self.fps_text = self.server.gui.add_text(
                "FPS",
                "0.00"
            )

            # Send/Stop controls and status
            self.send_button = self.server.gui.add_button("Send")
            self.stop_button = self.server.gui.add_button("Stop")
            self.stop_button.visible = False

            @self.send_button.on_click
            def _(_event) -> None:
                self.sending = True
                self.quat_message_count = 0
                self.send_button.visible = False
                self.stop_button.visible = True

            @self.stop_button.on_click
            def _(_event) -> None:
                self.sending = False
                self.send_button.visible = True
                self.stop_button.visible = False

            self.status_text = self.server.gui.add_text(
                "Status",
                "Topic: /mviz/quat (idle)",
            )
            
            # Motion Library Matching UI
            self.server.gui.add_text("Motion Library", "Motion Library Matching")
            
            # Enable/disable motion library matching
            self.motion_lib_checkbox = self.server.gui.add_checkbox(
                "Enable Motion Library Match",
                initial_value=False
            )
            
            @self.motion_lib_checkbox.on_update
            def _on_motion_lib_toggle(event) -> None:
                self.use_motion_lib = event.target.value
                if not self.use_motion_lib:
                    # Reset buffer when disabling
                    self.lib_playback_buffer = None
                    self.lib_buffer_index = 0
            
            # Select motion library folder button
            self.select_folder_button = self.server.gui.add_button(
                "Select Motion Library Folder"
            )
            
            @self.select_folder_button.on_click
            def _on_select_folder(_event) -> None:
                import tkinter as tk
                from tkinter import filedialog
                
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                
                folder_path = filedialog.askdirectory(
                    title="Select Motion Library Folder"
                )
                root.destroy()
                
                if folder_path:
                    try:
                        self.motion_lib = MotionLibrary(folder_path)
                        self.lib_frame_buffer = FrameBuffer(self.motion_lib.window_size)
                        cprint(f"Loaded motion library from {folder_path}", 'green')

                        import os
                        os.makedirs(TMP_DIR, exist_ok=True)
                        path_file = os.path.join(TMP_DIR, 'motion_lib_path.txt')
                        with open(path_file, 'w') as f:
                            f.write(folder_path)
                        
                        # Update library status display
                        if hasattr(self, 'lib_status_text') and self.lib_status_text is not None:
                            info = self.motion_lib.get_library_info()
                            self.lib_status_text.value = f"Loaded: {info['num_clips']} clips, {info['total_frames']} frames"
                        
                    except Exception as e:
                        cprint(f"Error loading motion library: {e}", 'red')
            
            # Library status display
            self.lib_status_text = self.server.gui.add_text(
                "Library Status",
                "No library loaded"
            )
            
            # Window size slider
            self.window_size_slider = self.server.gui.add_slider(
                "Playback Window Size",
                min=10,
                max=120,
                step=1,
                initial_value=30
            )
            
            @self.window_size_slider.on_update
            def _on_window_size_change(event) -> None:
                self.lib_window_size = int(event.target.value)
                # Reset buffer when window size changes
                self.lib_playback_buffer = None
                self.lib_buffer_index = 0
            
            # Match score display
            self.match_score_text = self.server.gui.add_text(
                "Match Score",
                "Match Score: N/A"
            )
            
            # Initialize library status if already loaded
            if self.motion_lib is not None:
                info = self.motion_lib.get_library_info()
                self.lib_status_text.value = f"Loaded: {info['num_clips']} clips, {info['total_frames']} frames"
    
    def shutdown(self) -> None:
        if getattr(self, "quat_publisher", None) is not None:
            close = getattr(self.quat_publisher, "close", None)
            if callable(close):
                close()
            self.quat_publisher = None
        if getattr(self, "fstate_publisher", None) is not None:
            close = getattr(self.fstate_publisher, "close", None)
            if callable(close):
                close()
            self.fstate_publisher = None
        if getattr(self, "subscriber", None) is not None:
            close = getattr(self.subscriber, "close", None)
            if callable(close):
                close()
            self.subscriber = None

        if getattr(self, "node", None) is not None:
            close = getattr(self.node, "close", None)
            if callable(close):
                close()
            self.node = None


if __name__ == "__main__":
    import argparse
    from mviz.viser_tools.base_visualizer import BaseVisualizer
    
    parser = argparse.ArgumentParser(description='Realtime robot motion player')
    parser.add_argument('--topic', type=str, default='/mviz/msg',
                        help='Topic name to subscribe to (default: /mviz/msg)')
    parser.add_argument('--urdf', type=str, default=None,
                        help='Path to URDF file (default: from config)')
    parser.add_argument('--fps', type=float, default=200.0,
                        help='Target FPS for visualization (default: 200.0)')
    
    args = parser.parse_args()
    
    cprint("="*60, 'cyan')
    cprint("Realtime Player Module - Message Subscriber (Standalone)", 'cyan', attrs=['bold'])
    cprint("="*60, 'cyan')

    visualizer = BaseVisualizer(urdf_path=args.urdf, target_fps=args.fps)
    player_module = RealtimePlayerModule(visualizer.server, topic_name=args.topic)
    visualizer.register_module(player_module)
    visualizer.set_active_module("Message Subscriber")
    visualizer.main_loop()