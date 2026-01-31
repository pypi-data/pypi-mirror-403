import ctypes
from typing import Iterable

from mviz.ice_tools.msgs.pointcloud2 import Header


class Quaternion(ctypes.Structure):
    IOX2_TYPE_NAME = "Quaternion"
    
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
        ("w", ctypes.c_double),
    ]

    @staticmethod
    def type_name() -> str:
        return "Quaternion"


class Vector3(ctypes.Structure):
    IOX2_TYPE_NAME = "Vector3"
    
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
    ]

    @staticmethod
    def type_name() -> str:
        return "Vector3"


CovarianceArray = ctypes.c_double * 9


def set_covariance(target: CovarianceArray, values: Iterable[float]) -> None:
    for idx, value in enumerate(values):
        if idx >= 9:
            break
        target[idx] = value


class Imu(ctypes.Structure):
    IOX2_TYPE_NAME = "Imu"
    
    _fields_ = [
        ("header", Header),
        ("orientation", Quaternion),
        ("orientation_covariance", CovarianceArray),
        ("angular_velocity", Vector3),
        ("angular_velocity_covariance", CovarianceArray),
        ("linear_acceleration", Vector3),
        ("linear_acceleration_covariance", CovarianceArray),
    ]

    def __str__(self) -> str:
        return (
            "Imu { "
            f"orientation: ({self.orientation.x}, {self.orientation.y}, "
            f"{self.orientation.z}, {self.orientation.w}), "
            f"angular_velocity: ({self.angular_velocity.x}, "
            f"{self.angular_velocity.y}, {self.angular_velocity.z}), "
            f"linear_acceleration: ({self.linear_acceleration.x}, "
            f"{self.linear_acceleration.y}, {self.linear_acceleration.z}) "
            "}"
        )

    @staticmethod
    def type_name() -> str:
        return "Imu"

