import numpy as np
import viser.transforms as vtf

from typing import Optional

from mviz.utils.models import BatchUrdf
from mviz.ice_tools.msgs import G1Quat, Quaternion
from mviz import G1_URDF_PATH as URDF_PATH


class FKStandalone:
    def __init__(self, urdf_path: Optional[str] = None) -> None:
        self._urdf_path = urdf_path or URDF_PATH
        self._model: Optional[BatchUrdf] = None

    def _ensure_model(self) -> None:
        if self._model is None:
            self._model = BatchUrdf(self._urdf_path)

    def compute_g1_quat(
        self,
        root_pos_xyz: np.ndarray,
        root_rot_xyzw: np.ndarray,
        joint_angles: np.ndarray,
    ) -> G1Quat:
        self._ensure_model()

        # base
        base_R = vtf.SO3.from_quaternion_xyzw(root_rot_xyzw).as_matrix()
        base_T = np.zeros((1, 4, 4), dtype=np.float32)
        base_T[:, :3, :3] = base_R
        base_T[:, 3, 3] = 1.0
        base_T[:, :3, 3] = root_pos_xyz[None, :]
        self._model.update_base(base_T)

        # fk
        cfg = np.array(joint_angles, dtype=np.float32)[None, :]
        fk_results = self._model.forward_kinematics(cfg)

        def link_quat(link_name: str) -> Quaternion:
            T = fk_results[link_name]["T"][0]
            wxyz = vtf.SO3.from_matrix(T[:3, :3]).wxyz
            return Quaternion(qx=float(wxyz[1]), qy=float(wxyz[2]), qz=float(wxyz[3]), qw=float(wxyz[0]))

        gq = G1Quat()
        gq.pelvis = link_quat("pelvis")
        gq.left_hip_pitch_link = link_quat("left_hip_pitch_link")
        gq.left_hip_roll_link = link_quat("left_hip_roll_link")
        gq.left_hip_yaw_link = link_quat("left_hip_yaw_link")
        gq.left_knee_link = link_quat("left_knee_link")
        gq.left_ankle_pitch_link = link_quat("left_ankle_pitch_link")
        gq.left_ankle_roll_link = link_quat("left_ankle_roll_link")
        gq.right_hip_pitch_link = link_quat("right_hip_pitch_link")
        gq.right_hip_roll_link = link_quat("right_hip_roll_link")
        gq.right_hip_yaw_link = link_quat("right_hip_yaw_link")
        gq.right_knee_link = link_quat("right_knee_link")
        gq.right_ankle_pitch_link = link_quat("right_ankle_pitch_link")
        gq.right_ankle_roll_link = link_quat("right_ankle_roll_link")
        gq.waist_yaw_link = link_quat("waist_yaw_link")
        gq.waist_roll_link = link_quat("waist_roll_link")
        gq.torso_link = link_quat("torso_link")
        gq.left_shoulder_pitch_link = link_quat("left_shoulder_pitch_link")
        gq.left_shoulder_roll_link = link_quat("left_shoulder_roll_link")
        gq.left_shoulder_yaw_link = link_quat("left_shoulder_yaw_link")
        gq.left_elbow_link = link_quat("left_elbow_link")
        gq.left_wrist_roll_link = link_quat("left_wrist_roll_link")
        gq.left_wrist_pitch_link = link_quat("left_wrist_pitch_link")
        gq.left_wrist_yaw_link = link_quat("left_wrist_yaw_link")
        gq.right_shoulder_pitch_link = link_quat("right_shoulder_pitch_link")
        gq.right_shoulder_roll_link = link_quat("right_shoulder_roll_link")
        gq.right_shoulder_yaw_link = link_quat("right_shoulder_yaw_link")
        gq.right_elbow_link = link_quat("right_elbow_link")
        gq.right_wrist_roll_link = link_quat("right_wrist_roll_link")
        gq.right_wrist_pitch_link = link_quat("right_wrist_pitch_link")
        gq.right_wrist_yaw_link = link_quat("right_wrist_yaw_link")
        return gq


