import ctypes


class Quaternion(ctypes.Structure):
    _fields_ = [
        ("qx", ctypes.c_double),
        ("qy", ctypes.c_double),
        ("qz", ctypes.c_double),
        ("qw", ctypes.c_double),
    ]

    def __str__(self) -> str:
        return f"Quaternion {{ qx: {self.qx}, qy: {self.qy}, qz: {self.qz}, qw: {self.qw} }}"

    @staticmethod
    def type_name() -> str:
        return "Quaternion"
    
if __name__ == "__main__":
    q = Quaternion(1.0, 0.0, 0.0, 0.0)
    print(q)
    print(Quaternion.type_name())