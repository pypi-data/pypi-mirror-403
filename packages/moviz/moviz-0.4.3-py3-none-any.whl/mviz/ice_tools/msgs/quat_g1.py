import ctypes

from mviz.ice_tools.msgs.quaternion import Quaternion


class G1Quat(ctypes.Structure):
    _fields_ = [
        ("pelvis", Quaternion),
        ("left_hip_pitch_link", Quaternion),
        ("left_hip_roll_link", Quaternion),
        ("left_hip_yaw_link", Quaternion),
        ("left_knee_link", Quaternion),
        ("left_ankle_pitch_link", Quaternion),
        ("left_ankle_roll_link", Quaternion),
        ("right_hip_pitch_link", Quaternion),
        ("right_hip_roll_link", Quaternion),
        ("right_hip_yaw_link", Quaternion),
        ("right_knee_link", Quaternion),
        ("right_ankle_pitch_link", Quaternion),
        ("right_ankle_roll_link", Quaternion),
        ("waist_yaw_link", Quaternion),
        ("waist_roll_link", Quaternion),
        ("torso_link", Quaternion),
        ("left_shoulder_pitch_link", Quaternion),
        ("left_shoulder_roll_link", Quaternion),
        ("left_shoulder_yaw_link", Quaternion),
        ("left_elbow_link", Quaternion),
        ("left_wrist_roll_link", Quaternion),
        ("left_wrist_pitch_link", Quaternion),
        ("left_wrist_yaw_link", Quaternion),
        ("right_shoulder_pitch_link", Quaternion),
        ("right_shoulder_roll_link", Quaternion),
        ("right_shoulder_yaw_link", Quaternion),
        ("right_elbow_link", Quaternion),
        ("right_wrist_roll_link", Quaternion),
        ("right_wrist_pitch_link", Quaternion),
        ("right_wrist_yaw_link", Quaternion),
    ]

    def __str__(self) -> str:
        entries = [
            ("pelvis", self.pelvis),
            ("left_hip_pitch_link", self.left_hip_pitch_link),
            ("left_hip_roll_link", self.left_hip_roll_link),
            ("left_hip_yaw_link", self.left_hip_yaw_link),
            ("left_knee_link", self.left_knee_link),
            ("left_ankle_pitch_link", self.left_ankle_pitch_link),
            ("left_ankle_roll_link", self.left_ankle_roll_link),
            ("right_hip_pitch_link", self.right_hip_pitch_link),
            ("right_hip_roll_link", self.right_hip_roll_link),
            ("right_hip_yaw_link", self.right_hip_yaw_link),
            ("right_knee_link", self.right_knee_link),
            ("right_ankle_pitch_link", self.right_ankle_pitch_link),
            ("right_ankle_roll_link", self.right_ankle_roll_link),
            ("waist_yaw_link", self.waist_yaw_link),
            ("waist_roll_link", self.waist_roll_link),
            ("torso_link", self.torso_link),
            ("left_shoulder_pitch_link", self.left_shoulder_pitch_link),
            ("left_shoulder_roll_link", self.left_shoulder_roll_link),
            ("left_shoulder_yaw_link", self.left_shoulder_yaw_link),
            ("left_elbow_link", self.left_elbow_link),
            ("left_wrist_roll_link", self.left_wrist_roll_link),
            ("left_wrist_pitch_link", self.left_wrist_pitch_link),
            ("left_wrist_yaw_link", self.left_wrist_yaw_link),
            ("right_shoulder_pitch_link", self.right_shoulder_pitch_link),
            ("right_shoulder_roll_link", self.right_shoulder_roll_link),
            ("right_shoulder_yaw_link", self.right_shoulder_yaw_link),
            ("right_elbow_link", self.right_elbow_link),
            ("right_wrist_roll_link", self.right_wrist_roll_link),
            ("right_wrist_pitch_link", self.right_wrist_pitch_link),
            ("right_wrist_yaw_link", self.right_wrist_yaw_link),
        ]
        contents = ", ".join(f"{name}: {value}" for name, value in entries)
        return f"G1Quat {{ {contents} }}"

    @staticmethod
    def type_name() -> str:
        return "G1Quat"
    
if __name__ == "__main__":
    g1 = G1Quat()
    print(g1)
    print(G1Quat.type_name())