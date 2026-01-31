import ctypes

from mviz.ice_tools.msgs.geometry import PoseWithCovariance, TwistWithCovariance
from mviz.ice_tools.msgs.pointcloud2 import Header


class Odometry(ctypes.Structure):
    IOX2_TYPE_NAME = "Odometry"
    
    _fields_ = [
        ("header", Header),
        ("pose", PoseWithCovariance),
        ("twist", TwistWithCovariance),
    ]

    def __str__(self) -> str:
        pose_str = str(self.pose)
        twist_str = str(self.twist)
        indented_pose = "\n".join("  " + line if line else line for line in pose_str.split("\n"))
        indented_twist = "\n".join("  " + line if line else line for line in twist_str.split("\n"))
        frame_id = self.header.frame_id.decode('utf-8', errors='ignore').rstrip('\x00')
        header_str = f"header: Header {{ stamp: ({self.header.stamp.sec}, {self.header.stamp.nanosec}), frame_id: \"{frame_id}\" }}"
        return f"Odometry {{\n  {header_str},\n  pose: {indented_pose},\n  twist: {indented_twist}\n}}"

    @staticmethod
    def type_name() -> str:
        return "Odometry"

