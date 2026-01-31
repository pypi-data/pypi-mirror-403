import ctypes


class Kpose(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
        ("qx", ctypes.c_double),
        ("qy", ctypes.c_double),
        ("qz", ctypes.c_double),
        ("qw", ctypes.c_double),
    ]

    def __str__(self) -> str:
        return f"Kpose {{ x: {self.x}, y: {self.y}, z: {self.z}, qx: {self.qx}, qy: {self.qy}, qz: {self.qz}, qw: {self.qw} }}"

    @staticmethod
    def type_name() -> str:
        return "Kpose"