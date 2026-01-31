import numpy as np
from typing import List, Optional, Dict
import viser
from termcolor import cprint
from mviz.viser_tools.base_visualizer import VisualizerModule, BaseVisualizer
from mviz.viser_tools.plugin_registry import register_plugin
from mviz import G1_URDF_PATH as URDF_PATH


@register_plugin
class RobotPlayerModule(VisualizerModule):
    plugin_cfg = {
        'default_position': [0.0, 0.0, 0.75],
        'transform_scale': 0.2,
        'axes_length': 0.4,
        'axes_radius': 0.02,
    }
    
    def __init__(self, server: viser.ViserServer):
        super().__init__("Robot Joint Control", server)
        self.default_position = self.plugin_cfg['default_position']
        self.transform_scale = self.plugin_cfg['transform_scale']
        self.axes_length = self.plugin_cfg['axes_length']
        self.axes_radius = self.plugin_cfg['axes_radius']
        
        # robot configuration
        self.robot_vis = None
        self.num_joints = 0
        self.joint_names = []
        self.default_joint_angles = np.array([], dtype=np.float32)
        
        # UI elements
        self.gui_joints: List[viser.GuiInputHandle[float]] = []
        self.gui_transform: Optional[viser.TransformControlsHandle] = None
        self.gui_show_controls: Optional[viser.GuiInputHandle[bool]] = None
        self.gui_reset_button: Optional[viser.GuiInputHandle] = None
        
        # State tracking
        self._has_changes = True  # Start with True to initialize robot pose
        self._current_position = np.array(self.default_position, dtype=np.float32)
        self._current_quaternion = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        self._current_joint_angles = self.default_joint_angles.copy()
    
    def set_robot_vis(self, robot_vis) -> None:
        self.robot_vis = robot_vis
        self.num_joints = robot_vis.num_joints
        self.joint_names = robot_vis.joint_names
        self.default_joint_angles = robot_vis.default_joint_angles
        self._current_joint_angles = self.default_joint_angles.copy()
    
    def build_ui(self, parent_folder: Optional[str] = None) -> None:
        self.ui_folder = self.server.gui.add_folder(self.name)
        
        with self.ui_folder:
            # create tab group for organization
            tab_group = self.server.gui.add_tab_group()
            
            # view tab
            with tab_group.add_tab("View", viser.Icon.VIEWFINDER):
                self.gui_show_controls = self.server.gui.add_checkbox(
                    "Show Handles", 
                    initial_value=True
                )
                
                @self.gui_show_controls.on_update
                def _(_):
                    if self.gui_transform is not None:
                        self.gui_transform.visible = self.gui_show_controls.value
            
            # joints tab
            with tab_group.add_tab("Joints", viser.Icon.ANGLE):
                self.gui_reset_button = self.server.gui.add_button("Reset Joints")
                
                @self.gui_reset_button.on_click
                def _(_):
                    for i, gui_joint in enumerate(self.gui_joints):
                        gui_joint.value = float(self.default_joint_angles[i])
                    self._has_changes = True
                
                # create joint sliders
                self.gui_joints = []
                for i, joint_name in enumerate(self.joint_names):
                    gui_joint = self.server.gui.add_number(
                        label=f"{joint_name}",
                        step=0.05,
                        initial_value=float(self.default_joint_angles[i]),
                        hint=f"Joint {i}"
                    )
                    self.gui_joints.append(gui_joint)
                    
                    # use closure to capture the correct joint index
                    def make_callback(idx: int):
                        @gui_joint.on_update
                        def _(_):
                            self._has_changes = True
                    make_callback(i)
        
        # create transform controls in the scene
        self.gui_transform = self.server.scene.add_transform_controls(
            "/robot_control_handle",
            depth_test=False,
            scale=self.transform_scale,
            disable_axes=False,
            disable_sliders=False,
            visible=self.gui_show_controls.value if self.gui_show_controls else True,
            position=tuple(self._current_position),
            wxyz=tuple(self._current_quaternion)
        )
        
        @self.gui_transform.on_update
        def _(_):
            self._has_changes = True
    
    def update(self) -> Optional[Dict[str, np.ndarray]]:
        if not self.enabled or not self._has_changes:
            return None
        
        self._has_changes = False
        
        # get current values from ui
        if self.gui_transform is not None:
            self._current_position = np.array(self.gui_transform.position, dtype=np.float32)
            self._current_quaternion = np.array(self.gui_transform.wxyz, dtype=np.float32)
        
        self._current_joint_angles = np.array(
            [gui_joint.value for gui_joint in self.gui_joints],
            dtype=np.float32
        )
        
        return {
            'position': self._current_position,
            'quaternion': self._current_quaternion,
            'joint_angles': self._current_joint_angles
        }
    
    def set_enabled(self, enabled: bool) -> None:
        super().set_enabled(enabled)
        if self.gui_transform is not None:
            self.gui_transform.visible = enabled and (
                self.gui_show_controls.value if self.gui_show_controls else True
            )

if __name__ == "__main__":
    from termcolor import cprint
    
    cprint("="*60, 'cyan')
    cprint("Robot Player Module", 'cyan', attrs=['bold'])
    cprint("="*60, 'cyan')
    
    visualizer = BaseVisualizer(target_fps=30.0)
    robot_module = RobotPlayerModule(
        visualizer.server,
    )
    visualizer.register_module(robot_module)
    visualizer.set_active_module("Robot Joint Control")
    visualizer.main_loop()
