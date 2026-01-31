import viser
import termcolor
import numpy as np
from typing import Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from mviz.utils.models import ViserUrdf
from mviz.utils.video_recorder import VideoRecordingManager
from mviz.viser_tools.plugin_registry import discover_and_instantiate_plugins
from mviz import G1_URDF_PATH as URDF_PATH
from mviz.utils.table_output import print_startup_info


class VisualizerModule(ABC):
    def __init__(self, name: str, server: viser.ViserServer):
        self.name = name
        self.server = server
        self.enabled = True
        self.ui_folder: Optional[viser.GuiHandle] = None
        
    @abstractmethod
    def build_ui(self, parent_folder: Optional[str] = None) -> None:
        # build basic ui elements here
        pass
    
    @abstractmethod
    def update(self) -> Optional[Dict[str, np.ndarray]]:
        # update the module state and return robot state if this module should control it
        pass
    
    def set_enabled(self, enabled: bool) -> None:
        # enable or disable this module
        self.enabled = enabled
        if self.ui_folder is not None:
            self.ui_folder.visible = enabled


class BaseVisualizer:
    def __init__(self, urdf_path: Optional[str] = None, target_fps: float = 100.0, host: str = '0.0.0.0', port: int = 8081):
        import io
        import sys
        import re
        
        # Capture viser's verbose output to get actual port information
        old_stdout = sys.stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Create server with verbose=True to capture port info, but we'll suppress the output
            self.server = viser.ViserServer(host=host, port=port, verbose=True)
        finally:
            sys.stdout = old_stdout
        
        # Parse actual port from captured output
        output = captured_output.getvalue()
        actual_port = port
        actual_host = host
        port_patterns = [
            r'listening on \*:(\d+)',
            r'listening on port (\d+)',
            r'Server listening on port (\d+)',
            r'http://[^:]+:(\d+)',
            r'ws://[^:]+:(\d+)',
            r'wss://[^:]+:(\d+)',
            r':(\d+)\s+\(HTTP\)',
            r':(\d+)\s+\(WebSocket\)',
            r'port[:\s]+(\d+)',
            r'\*:(\d+)',
        ]
        
        for pattern in port_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                try:
                    parsed_port = int(match.group(1))
                    if 1 <= parsed_port <= 65535:  # Valid port range
                        actual_port = parsed_port
                        break
                except (ValueError, IndexError):
                    continue

        host_patterns = [
            r'http://([^:]+):\d+',
            r'ws://([^:]+):\d+',
            r'listening on ([^:]+):\d+',
        ]
        
        for pattern in host_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                extracted_host = match.group(1)
                if extracted_host != '*' and extracted_host != '0.0.0.0':
                    actual_host = extracted_host
                    break
        
        # Store server info for later unified printing
        self.host = actual_host
        self.port = actual_port
        self.startup_printed = False
        
        # model visualization
        self.urdf_path = urdf_path or URDF_PATH
        self.robot_vis = ViserUrdf(
            self.server,
            self.urdf_path
        )
        
        # visualization state
        self.target_fps = target_fps
        self.running = False
        
        # modules
        self.modules: Dict[str, VisualizerModule] = {}
        self.active_module: Optional[str] = None
        
        # elements
        self.module_selector = None
        self._updating_selector = False  # Flag to prevent callback loops
        self.fps_slider = None
        
        # scene
        self.setup_scene()

        # global fps control
        self.fps_slider = self.server.gui.add_slider(
            "FPS",
            min=15,
            max=100,
            step=1,
            initial_value=int(self.target_fps),
        )

        @self.fps_slider.on_update
        def _on_fps_change(event) -> None:
            self.target_fps = float(event.target.value)

        # global recorder control
        self.recorder = VideoRecordingManager(self.server)
        
    def setup_scene(self) -> None:
        self.server.scene.add_grid("/grid", 30, 30)
        self.frame_root = self.server.scene.add_frame(
            "/frame_root", 
            position=(0, 0, 0), 
            wxyz=(1, 0, 0, 0), 
            axes_length=0.4, 
            axes_radius=0.02
        )
    
    def register_module(self, module: VisualizerModule) -> None:
        self.modules[module.name] = module
        
        # set robot_vis for robot visualizer module
        if module.name == "Robot Joint Control" and hasattr(module, 'set_robot_vis'):
            module.set_robot_vis(self.robot_vis)
        if hasattr(module, 'set_visualizer'):
            module.set_visualizer(self)
        
        module.build_ui()
        
        # update module selector if it exists
        if self.module_selector is not None:
            module_names = list(self.modules.keys())
            self.module_selector.options = module_names
            if self.active_module is None and module_names:
                self.active_module = module_names[0]
                self._updating_selector = True
                self.module_selector.value = self.active_module
                self._updating_selector = False
                self._update_module_states()
        elif len(self.modules) == 1:
            # first module registered, set as active
            self.active_module = module.name
            module.set_enabled(True)
    
    def auto_register_plugins(self) -> None:
        import sys
        import os

        old_stderr_fd = os.dup(2)
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, 2)
        
        try:
            plugins, plugin_status = discover_and_instantiate_plugins(self.server)
            
            # register all discovered plugins
            for plugin in plugins:
                self.register_module(plugin)
        finally:
            # Restore stderr
            os.dup2(old_stderr_fd, 2)
            os.close(old_stderr_fd)
            os.close(devnull_fd)
        
        # Print unified startup info if not already printed
        if not self.startup_printed:
            print_startup_info(self.host, self.port, plugin_status, config_status="default")
            self.startup_printed = True
        
    def set_active_module(self, module_name: Optional[str]) -> None:
        if module_name is not None and module_name not in self.modules:
            raise ValueError(f"Module '{module_name}' not registered")
        self.active_module = module_name
        self._update_module_states()
        
        # update selector if it exists
        if self.module_selector is not None and module_name is not None:
            self._updating_selector = True
            self.module_selector.value = module_name
            self._updating_selector = False
    
    def _update_module_states(self) -> None:
        # update module enabled states and ui visibility
        for name, module in self.modules.items():
            is_active = (name == self.active_module)
            module.set_enabled(is_active)
    
    def create_module_selector(self) -> None:
        # create ui dropdown to select active module
        if not self.modules:
            return
        
        module_names = list(self.modules.keys())
        initial_value = self.active_module if self.active_module else module_names[0]
        
        self.module_selector = self.server.gui.add_dropdown(
            "Active Module",
            options=module_names,
            initial_value=initial_value,
        )
        
        @self.module_selector.on_update
        def _on_module_change(event) -> None:
            # prevent callback loop when we programmatically set the value
            if self._updating_selector:
                return
            new_module = event.target.value
            self.set_active_module(new_module)
        
        # set initial state
        if self.active_module is None:
            self.active_module = initial_value
        self._update_module_states()
        
    def update_robot(self, position: np.ndarray, quaternion: np.ndarray, joint_angles: np.ndarray) -> None:
        # update robot visualization
        self.robot_vis.update_base(position, quaternion)
        self.robot_vis.update_cfg(joint_angles)
    
    def set_robot_visible(self, visible: bool) -> None:
        self.robot_vis.set_frame_visible(visible)
    
    def main_loop(self) -> None:
        # main visualization loop
        import time
        from termcolor import cprint
        
        self.running = True
        
        try:
            # initialize next frame time using current fps
            frame_duration = 1.0 / max(self.target_fps, 1e-3)
            next_frame_time = time.perf_counter() + frame_duration
            
            while self.running:
                # recompute frame duration each loop to reflect live fps changes
                frame_duration = 1.0 / max(self.target_fps, 1e-3)
                # wait for next frame
                now = time.perf_counter()
                sleep_time = next_frame_time - now
                if sleep_time > 0:
                    time.sleep(min(sleep_time, 0.02))
                    continue
                
                # update all modules and get robot state
                robot_state = None
                for module in self.modules.values():
                    if module.enabled:
                        state = module.update()
                        # only use state from the active module
                        if state is not None and (self.active_module is None or module.name == self.active_module):
                            robot_state = state
                
                # update robot if we have new state
                if robot_state is not None:
                    with self.server.atomic():
                        self.update_robot(
                            robot_state.get('position', np.array([0.0, 0.0, 0.82], dtype=np.float32)),
                            robot_state.get('quaternion', np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)),
                            robot_state.get('joint_angles', np.zeros(self.robot_vis.num_joints, dtype=np.float32))
                        )
                
                # schedule next frame
                next_frame_time += frame_duration
                if (time.perf_counter() - next_frame_time) > frame_duration:
                    next_frame_time = time.perf_counter() + frame_duration
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        # clean up resources
        self.running = False
        for module in self.modules.values():
            if hasattr(module, 'shutdown'):
                module.shutdown()


if __name__ == "__main__":
    visualizer = BaseVisualizer()
    visualizer.main_loop()

