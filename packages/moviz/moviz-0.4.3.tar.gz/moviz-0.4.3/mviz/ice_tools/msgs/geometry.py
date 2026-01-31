import ctypes
from typing import Iterable

from mviz.ice_tools.msgs.imu import Quaternion, Vector3


def _format_number(value: float) -> str:
    abs_value = abs(value)
    if abs_value == 0.0:
        return "0.0"
    elif abs_value >= 1.0:
        formatted = f"{value:.6f}"
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted
    elif abs_value >= 0.001:
        formatted = f"{value:.6f}"
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted
    else:
        return f"{value:.4e}"


class Point(ctypes.Structure):
    IOX2_TYPE_NAME = "Point"
    
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
    ]

    def __str__(self) -> str:
        return f"Point {{ x: {self.x}, y: {self.y}, z: {self.z} }}"

    @staticmethod
    def type_name() -> str:
        return "Point"


class Pose(ctypes.Structure):
    IOX2_TYPE_NAME = "Pose"
    
    _fields_ = [
        ("position", Point),
        ("orientation", Quaternion),
    ]

    def __str__(self) -> str:
        return (
            "Pose {\n"
            f"  position: ({_format_number(self.position.x)}, "
            f"{_format_number(self.position.y)}, "
            f"{_format_number(self.position.z)}),\n"
            f"  orientation: ({_format_number(self.orientation.x)}, "
            f"{_format_number(self.orientation.y)}, "
            f"{_format_number(self.orientation.z)}, "
            f"{_format_number(self.orientation.w)})\n"
            "}"
        )

    @staticmethod
    def type_name() -> str:
        return "Pose"


PoseCovarianceArray = ctypes.c_double * 36


def set_pose_covariance(target: PoseCovarianceArray, values: Iterable[float]) -> None:
    for idx, value in enumerate(values):
        if idx >= 36:
            break
        target[idx] = value


class PoseWithCovariance(ctypes.Structure):
    IOX2_TYPE_NAME = "PoseWithCovariance"
    
    _fields_ = [
        ("pose", Pose),
        ("covariance", PoseCovarianceArray),
    ]

    def __str__(self) -> str:
        pose_str = str(self.pose)
        indented_pose = "\n".join("  " + line if line else line for line in pose_str.split("\n"))
        return f"PoseWithCovariance {{\n  pose: {indented_pose}\n}}"

    @staticmethod
    def type_name() -> str:
        return "PoseWithCovariance"


class Twist(ctypes.Structure):
    IOX2_TYPE_NAME = "Twist"
    
    _fields_ = [
        ("linear", Vector3),
        ("angular", Vector3),
    ]

    def __str__(self) -> str:
        return (
            "Twist {\n"
            f"  linear: ({_format_number(self.linear.x)}, "
            f"{_format_number(self.linear.y)}, "
            f"{_format_number(self.linear.z)}),\n"
            f"  angular: ({_format_number(self.angular.x)}, "
            f"{_format_number(self.angular.y)}, "
            f"{_format_number(self.angular.z)})\n"
            "}"
        )

    @staticmethod
    def type_name() -> str:
        return "Twist"


TwistCovarianceArray = ctypes.c_double * 36


def set_twist_covariance(target: TwistCovarianceArray, values: Iterable[float]) -> None:
    for idx, value in enumerate(values):
        if idx >= 36:
            break
        target[idx] = value


class TwistWithCovariance(ctypes.Structure):
    IOX2_TYPE_NAME = "TwistWithCovariance"
    
    _fields_ = [
        ("twist", Twist),
        ("covariance", TwistCovarianceArray),
    ]

    def __str__(self) -> str:
        twist_str = str(self.twist)
        indented_twist = "\n".join("  " + line if line else line for line in twist_str.split("\n"))
        return f"TwistWithCovariance {{\n  twist: {indented_twist}\n}}"

    @staticmethod
    def type_name() -> str:
        return "TwistWithCovariance"

