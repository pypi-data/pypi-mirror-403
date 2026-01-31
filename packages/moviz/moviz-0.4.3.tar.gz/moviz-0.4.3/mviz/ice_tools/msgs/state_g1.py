import ctypes

from mviz.ice_tools.msgs.kpose import Kpose


class G1State(ctypes.Structure):
    _fields_ = [
        ("root_joint", Kpose),
        ("left_hip_pitch_joint", ctypes.c_double),
        ("left_hip_roll_joint", ctypes.c_double),
        ("left_hip_yaw_joint", ctypes.c_double),
        ("left_knee_joint", ctypes.c_double),
        ("left_ankle_pitch_joint", ctypes.c_double),
        ("left_ankle_roll_joint", ctypes.c_double),
        ("right_hip_pitch_joint", ctypes.c_double),
        ("right_hip_roll_joint", ctypes.c_double),
        ("right_hip_yaw_joint", ctypes.c_double),
        ("right_knee_joint", ctypes.c_double),
        ("right_ankle_pitch_joint", ctypes.c_double),
        ("right_ankle_roll_joint", ctypes.c_double),
        ("waist_yaw_joint", ctypes.c_double),
        ("waist_roll_joint", ctypes.c_double),
        ("waist_pitch_joint", ctypes.c_double),
        ("left_shoulder_pitch_joint", ctypes.c_double),
        ("left_shoulder_roll_joint", ctypes.c_double),
        ("left_shoulder_yaw_joint", ctypes.c_double),
        ("left_elbow_joint", ctypes.c_double),
        ("left_wrist_roll_joint", ctypes.c_double),
        ("left_wrist_pitch_joint", ctypes.c_double),
        ("left_wrist_yaw_joint", ctypes.c_double),
        ("right_shoulder_pitch_joint", ctypes.c_double),
        ("right_shoulder_roll_joint", ctypes.c_double),
        ("right_shoulder_yaw_joint", ctypes.c_double),
        ("right_elbow_joint", ctypes.c_double),
        ("right_wrist_roll_joint", ctypes.c_double),
        ("right_wrist_pitch_joint", ctypes.c_double),
        ("right_wrist_yaw_joint", ctypes.c_double),
    ]

    def __str__(self) -> str:
        entries = [
            ("root_joint", self.root_joint),
            ("left_hip_pitch_joint", self.left_hip_pitch_joint),
            ("left_hip_roll_joint", self.left_hip_roll_joint),
            ("left_hip_yaw_joint", self.left_hip_yaw_joint),
            ("left_knee_joint", self.left_knee_joint),
            ("left_ankle_pitch_joint", self.left_ankle_pitch_joint),
            ("left_ankle_roll_joint", self.left_ankle_roll_joint),
            ("right_hip_pitch_joint", self.right_hip_pitch_joint),
            ("right_hip_roll_joint", self.right_hip_roll_joint),
            ("right_hip_yaw_joint", self.right_hip_yaw_joint),
            ("right_knee_joint", self.right_knee_joint),
            ("right_ankle_pitch_joint", self.right_ankle_pitch_joint),
            ("right_ankle_roll_joint", self.right_ankle_roll_joint),
            ("waist_yaw_joint", self.waist_yaw_joint),
            ("waist_roll_joint", self.waist_roll_joint),
            ("waist_pitch_joint", self.waist_pitch_joint),
            ("left_shoulder_pitch_joint", self.left_shoulder_pitch_joint),
            ("left_shoulder_roll_joint", self.left_shoulder_roll_joint),
            ("left_shoulder_yaw_joint", self.left_shoulder_yaw_joint),
            ("left_elbow_joint", self.left_elbow_joint),
            ("left_wrist_roll_joint", self.left_wrist_roll_joint),
            ("left_wrist_pitch_joint", self.left_wrist_pitch_joint),
            ("left_wrist_yaw_joint", self.left_wrist_yaw_joint),
            ("right_shoulder_pitch_joint", self.right_shoulder_pitch_joint),
            ("right_shoulder_roll_joint", self.right_shoulder_roll_joint),
            ("right_shoulder_yaw_joint", self.right_shoulder_yaw_joint),
            ("right_elbow_joint", self.right_elbow_joint),
            ("right_wrist_roll_joint", self.right_wrist_roll_joint),
            ("right_wrist_pitch_joint", self.right_wrist_pitch_joint),
            ("right_wrist_yaw_joint", self.right_wrist_yaw_joint),
        ]
        contents = ", ".join(f"{name}: {value}" for name, value in entries)
        return f"G1State {{ {contents} }}"

    @staticmethod
    def type_name() -> str:
        return "G1State"