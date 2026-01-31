from typing import List, Tuple, Dict, Union, Optional
from termcolor import cprint
import numpy as np
import trimesh
import yourdfpy
import viser
import viser.transforms as vtf
from mviz.utils.math_utils_np import quat_apply, rotation_from_axis_angle, transformation, rotation_from_quat, exp_map_to_quat, quat_mul, quat_inv, quat_from_rotation
from mviz.utils.utils_np import forward_kinematics
class JointTensor:
    def __init__(self, joint, device: str = "cpu"):
        # Note: device parameter kept for compatibility but ignored (numpy doesn't use devices)
        self.name = joint.name
        self.parent = joint.parent
        self.child = joint.child
        if not hasattr(joint, 'origin') or joint.origin is None:
            self.origin = np.eye(4, dtype=np.float32)
        else:
            self.origin = np.array(joint.origin, dtype=np.float32)
        self.axis = np.array(joint.axis, dtype=np.float32)
        if not hasattr(joint, 'limit') or joint.limit is None:
            self.lower = np.array(-np.pi, dtype=np.float32)
            self.upper = np.array(np.pi, dtype=np.float32)
            self.max_effort = np.array(1000.0, dtype=np.float32)
            self.max_vel = np.array(10.0, dtype=np.float32)
        else:
            self.lower = np.array(joint.limit.lower, dtype=np.float32)
            self.upper = np.array(joint.limit.upper, dtype=np.float32)
            self.max_effort = np.array(joint.limit.effort, dtype=np.float32)
            self.max_vel = np.array(joint.limit.velocity, dtype=np.float32)
        self.type = joint.type
class BatchUrdf:
    def __init__(self, filename: str, device: str = "cpu"):
        # Note: device parameter kept for compatibility but ignored (numpy doesn't use devices)
        self.device = device
        self.robot = yourdfpy.URDF.load(filename, load_collision_meshes=False, build_collision_scene_graph=False)
        self.root = self.robot.scene.graph.base_frame # root name
        self.root_transform = np.eye(4, dtype=np.float32)[None, :, :]  # 1 * 4 * 4
        self._config_joints()
        self._config_links()
        self._prepare_constants()

    def forward_kinematics(self, joint_angles: np.ndarray, verbose=True) -> Dict[str, np.ndarray]:
        if not verbose:
            return forward_kinematics(
                joint_angles, # support multi-dim batch size
                self.link_indices, # (L, ) topo order -> result order
                self.link_fathers, # (L, ) topo order -> result order
                self.link_father_joint_indices, # (L, ) topo order -> result order
                self.root_transform, # support multi-dim batch size
                self.link_origins,
                self.joint_axis,
            ) # (..., L, 4, 4) # T global
        # only supports 1 dim of batch size
        self.results = {}
        batch_size = joint_angles.shape[0]
        rep_count = batch_size // self.root_transform.shape[0]
        self.results[self.root] = {
            "T": np.tile(self.root_transform, (rep_count, 1, 1)), # T global
            "T_p": np.tile(self.root_transform, (rep_count, 1, 1)), # T parent_to_child
        } # transformation matrix
        for link_name in self.ordered_links:
            if link_name in self.results: 
                continue
            joint: JointTensor = self.links[link_name]["parent_joint"]
            joint_origin = np.tile(joint.origin[None, :, :], (batch_size, 1, 1))
            joint_axis = np.tile(joint.axis[None, :], (batch_size, 1))
            if joint.parent not in self.results:
                cprint(f"[Batch URDF] Parent link {joint.parent} not found in results, skipping joint {joint.name}.", "red")
                continue
            if joint.name in self.joints:
                joint_index = list(self.joints.keys()).index(joint.name)
                joint_angle = joint_angles[:, joint_index, None]  # Add dimension
                rotation = transformation(rotation_from_axis_angle(joint_axis, joint_angle), np.zeros((batch_size, 3), dtype=np.float32))
            else:
                rotation = np.tile(np.eye(4, dtype=np.float32)[None, :, :], (batch_size, 1, 1))
            parent_to_child_transform = joint_origin @ rotation # T parent_to_joint @ joint_to_child
            global_transform = self.results[joint.parent]["T"] @ parent_to_child_transform
            self.results[joint.child] = {"T": global_transform, "T_p": parent_to_child_transform}
        return self.results
        
    def update_base(self, transform: np.ndarray) -> None: # 1 or t * 4 * 4
        self.root_transform = transform.astype(np.float32)
    
    def _prepare_constants(self):
        link_indices = [self.link_names.index(link_name) for link_name in self.ordered_links]
        self.link_indices = np.array(link_indices, dtype=np.int64) # (L, )
        self.link_fathers = np.array(
            [self.get_parent_idx(idx) for idx in link_indices], dtype=np.int64
        )
        link_father_joint_indices = []
        for idx in link_indices:
            parent_joint = self.links[self.link_names[idx]]["parent_joint"]
            if parent_joint and parent_joint.name in self.joints:
                link_father_joint_indices.append(self.joint_names.index(parent_joint.name))
            else:
                link_father_joint_indices.append(-1)
        self.link_father_joint_indices = np.array(link_father_joint_indices, dtype=np.int64)
        link_origins = []
        for idx in link_indices:
            parent_joint = self.links[self.link_names[idx]]["parent_joint"]
            if parent_joint is None:
                link_origins.append(np.eye(4, dtype=np.float32))
            else:
                link_origins.append(parent_joint.origin)
        self.link_origins = np.stack(link_origins, axis=0) # (L, 4, 4)
        self.joint_axis = np.stack(
            [joint.axis for joint in self.joints.values()], axis=0
        ) # (J, 3)
  
    def _config_joints(self):
        self.joints = {joint.name: JointTensor(joint) for joint in self.robot.robot.joints if joint.type != "fixed"}
        self.all_joints = {joint.name: JointTensor(joint) for joint in self.robot.robot.joints}
        self.num_joints = len(self.joints)
        self.joint_names = list(self.joints.keys())
        self.upper = np.stack([joint.upper for joint in self.joints.values()], axis=0)
        self.lower = np.stack([joint.lower for joint in self.joints.values()], axis=0)
        self.max_effort = np.stack([joint.max_effort for joint in self.joints.values()], axis=0)
        self.max_vel = np.stack([joint.max_vel for joint in self.joints.values()], axis=0)
    
    def _config_links(self): 
        links = self.robot.robot.links
        self.link_names = [link.name for link in links]
        self.mesh = {}
        ## collect meshes for each link, apply transforms to meshes
        for link in links:
            if link.visuals and hasattr(link.visuals[0].geometry.mesh, "filename"):
                mesh_name = link.visuals[0].geometry.mesh.filename.split("/")[-1]
                self.mesh[link.name] = self.robot.scene.geometry[mesh_name].copy()
                # mesh to link, often identical to link 
                T_parent_child = self.robot.get_transform(
                    mesh_name, self.robot.scene.graph.transforms.parents[mesh_name]
                )
                self.mesh[link.name].apply_transform(T_parent_child)
                
        ## collect link transform information
        self.links = {}
        for link in self.link_names:
            self.links[link] = {}
            parent_joint = [joint for joint in self.all_joints.values() if joint.child == link]
            assert len(parent_joint) <= 1, f"Link {link} has multiple parent joints: {parent_joint}"
            self.links[link]["parent_joint"] = parent_joint[0] if parent_joint else None
            self.links[link]["parent_link"] = parent_joint[0].parent if parent_joint else None
            self.links[link]["child_joint"] = [joint for joint in self.all_joints.values() if joint.parent == link]
            self.links[link]["child_link"] = [joint.child for joint in self.links[link]["child_joint"]]
        ## get topological order of links
        self.ordered_links = []
        visited = set()
        def dfs(link_name: str):
            if link_name in visited:
                return
            visited.add(link_name)
            self.ordered_links.append(link_name)
            for child_link in self.links[link_name]["child_link"]:
                dfs(child_link)
        dfs(self.root)
        
    

    def set_default_pose(self, joint_angles: np.ndarray) -> None:
        assert len(joint_angles) == self.num_joints, f"Expected {self.num_joints} joint angles, got {len(joint_angles)}"
        self.default_joint_angles = joint_angles.astype(np.float32)
        self.default_transforms = self.forward_kinematics(self.default_joint_angles[None, :])
        
    def get_frame_name(self, frame_name: str, root_node_name: str = "/", name_suffix: str = "") -> str:
        frames = []
        while frame_name != self.robot.scene.graph.base_frame:
            frames.append(frame_name + name_suffix)
            frame_name = self.robot.scene.graph.transforms.parents[frame_name]
        if root_node_name != "/":
            frames.append(root_node_name + name_suffix)
        return "/".join(frames[::-1])
    
    def get_parent_idx(self, link_index: int) -> int:
        link_name = self.link_names[link_index]
        parent_link = self.links[link_name]["parent_link"]
        if parent_link is None:
            return -1
        return self.link_names.index(parent_link) if parent_link in self.link_names else -1
        
class ViserUrdf:
    def __init__(
        self,
        target: Union[viser.ViserServer, viser.ClientHandle],
        urdf_path: str,
        default_joint_angle_dict: Dict[str, float] = {},
        robot_node_name: str = "/robot",
        mesh_color: Optional[Tuple[int, int, int]] = None,
    ) -> None:
        assert robot_node_name.startswith("/")

        self._target = target
        self._robot = BatchUrdf(urdf_path)
        self._robot_node_name = robot_node_name
        self._mesh_color = mesh_color
        self._meshes: List[viser.SceneNodeHandle] = []
        self._frames: Dict[viser.SceneNodeHandle] = {}
        self._frames[self._robot_node_name] = (target.scene.add_frame(self._robot_node_name, show_axes=True, visible=True, axes_length=0.2, axes_radius=0.02)) #base frame
        self.joint_names = self._robot.joint_names
        self.default_joint_angles = np.zeros((self._robot.num_joints,), dtype=np.float32)
        for joint_name, angle in (default_joint_angle_dict or {}).items():
            if joint_name in self._robot.joint_names:
                self.default_joint_angles[self.joint_names.index(joint_name)] = angle
            else:
                cprint(f"[ViserUrdf] [default angle] Joint {joint_name} not found in robot, setting 0.", "yellow")
        self._robot.set_default_pose(self.default_joint_angles)
        self.num_joints = self._robot.num_joints
        self.default_transforms = self._robot.default_transforms
        
        for link_name, mesh in self._robot.mesh.items():
            mesh:trimesh.Trimesh = mesh.copy()
            if mesh_color is not None:
                mesh.visual = trimesh.visual.ColorVisuals(
                    mesh=mesh,
                    face_colors=np.array([mesh_color[0], mesh_color[1], mesh_color[2], 255], dtype=np.uint8)
                )
            name = self._robot.get_frame_name(link_name, self._robot_node_name)
            self._frames[link_name] = target.scene.add_frame(name, show_axes=True, visible=True, axes_length=0.1, axes_radius=0.01)
            self._meshes.append(target.scene.add_mesh_trimesh(name, mesh))
        
        self.update_base(np.array([-2.0, 0.0, 0.82]), np.array([1.0, 0.0, 0.0, 0.0])) # default position and orientation
        self.update_cfg(self.default_joint_angles)        
    
    def update_cfg(self, configuration: np.ndarray) -> None:
        configuration_array = np.array(configuration, dtype=np.float32)[None, :]  # Add batch dimension
        self.results = self._robot.forward_kinematics(configuration_array)
        for link_name, frame_handle in self._frames.items():
            if link_name == self._robot_node_name:
                continue
            t = self.results[link_name]["T_p"][0]
            frame_handle.wxyz = vtf.SO3.from_matrix(t[:3, :3]).wxyz
            frame_handle.position = t[:3, 3]
        return self.results
    
    def set_frame_visible(self, visible: bool = True) -> None:
        for frame_name, frame_handle in self._frames.items():
            frame_handle.visible = visible

    def update_base(self, position: np.ndarray, wxyz: np.ndarray) -> None:        
        self._frames[self._robot_node_name].position = position
        self._frames[self._robot_node_name].wxyz = wxyz
        position_array = np.array(position, dtype=np.float32)[None, :]  # Add batch dimension
        wxyz_array = np.array(wxyz, dtype=np.float32)[None, :]  # Add batch dimension
        rotation = rotation_from_quat(wxyz_array, 'wxyz')
        transform = transformation(rotation, position_array)
        self._robot.update_base(transform)

    def remove(self) -> None:
        for mesh_handle in self._meshes:
            try:
                mesh_handle.remove()
            except Exception:
                pass
        self._meshes.clear()
        
        root_frame = self._frames.get(self._robot_node_name)
        for frame_name, frame_handle in list(self._frames.items()):
            if frame_name != self._robot_node_name:
                try:
                    frame_handle.remove()
                except Exception:
                    pass
        if root_frame is not None:
            try:
                root_frame.remove()
            except Exception:
                pass
        self._frames.clear()

