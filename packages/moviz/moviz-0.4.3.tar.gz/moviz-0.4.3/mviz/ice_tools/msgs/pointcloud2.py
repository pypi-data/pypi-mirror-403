import ctypes
import os


def _validate_positive(name: str, value: int) -> int:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


FRAME_ID_MAX_LEN = _validate_positive(
    "FRAME_ID_MAX_LEN",
    int(os.getenv("LIVOX_FRAME_ID_MAX_LEN", "64")),
)


class Time(ctypes.Structure):
    IOX2_TYPE_NAME = "Time"
    
    _fields_ = [
        ("sec", ctypes.c_uint32),
        ("nanosec", ctypes.c_uint32),
    ]

    @staticmethod
    def type_name() -> str:
        return "Time"


class Header(ctypes.Structure):
    IOX2_TYPE_NAME = "Header"
    
    _fields_ = [
        ("stamp", Time),
        ("frame_id", ctypes.c_char * FRAME_ID_MAX_LEN),
    ]

    @staticmethod
    def type_name() -> str:
        return "Header"


class IceoryxMessageOverflow(RuntimeError):
    """Raised when data exceeds the statically allocated message capacity."""


def write_c_string(owner: ctypes.Structure, field_name: str, value: str) -> None:
    field = getattr(type(owner), field_name)
    capacity = getattr(field, "size", 0)
    if capacity <= 0:
        return
    encoded = value.encode("utf-8")
    if len(encoded) >= capacity:
        encoded = encoded[: capacity - 1]
    setattr(owner, field_name, encoded)


POINT_FIELD_NAME_MAX_LEN = _validate_positive(
    "POINT_FIELD_NAME_MAX_LEN",
    int(os.getenv("LIVOX_POINT_FIELD_NAME_MAX_LEN", "32")),
)
POINT_FIELD_CAPACITY = _validate_positive(
    "POINT_FIELD_CAPACITY",
    int(os.getenv("LIVOX_POINT_FIELD_CAPACITY", "6")),
)
POINTCLOUD_MAX_POINTS = _validate_positive(
    "POINTCLOUD_MAX_POINTS",
    int(os.getenv("LIVOX_POINTCLOUD_MAX_POINTS", "200000")),
)
POINTCLOUD_POINT_STEP = _validate_positive(
    "POINTCLOUD_POINT_STEP",
    int(os.getenv("LIVOX_POINTCLOUD_POINT_STEP", "20")),
)
POINTCLOUD_MAX_DATA_BYTES = _validate_positive(
    "POINTCLOUD_MAX_DATA_BYTES",
    POINTCLOUD_MAX_POINTS * POINTCLOUD_POINT_STEP,
)


class PointFieldDataType:
    INT8 = 1
    UINT8 = 2
    INT16 = 3
    UINT16 = 4
    INT32 = 5
    UINT32 = 6
    FLOAT32 = 7
    FLOAT64 = 8


class PointField(ctypes.Structure):
    IOX2_TYPE_NAME = "PointField"
    
    _fields_ = [
        ("name", ctypes.c_char * POINT_FIELD_NAME_MAX_LEN),
        ("offset", ctypes.c_uint32),
        ("datatype", ctypes.c_uint8),
        ("count", ctypes.c_uint32),
        ("_padding", ctypes.c_uint8 * 3),
    ]

    @staticmethod
    def type_name() -> str:
        return "PointField"


class PointCloud2(ctypes.Structure):
    IOX2_TYPE_NAME = "PointCloud2"
    
    _fields_ = [
        ("header", Header),
        ("height", ctypes.c_uint32),
        ("width", ctypes.c_uint32),
        ("fields_count", ctypes.c_uint32),
        ("fields", PointField * POINT_FIELD_CAPACITY),
        ("is_bigendian", ctypes.c_bool),
        ("point_step", ctypes.c_uint32),
        ("row_step", ctypes.c_uint32),
        ("data_length", ctypes.c_uint32),
        ("data", ctypes.c_uint8 * POINTCLOUD_MAX_DATA_BYTES),
        ("is_dense", ctypes.c_bool),
        ("_padding", ctypes.c_uint8 * 3),
    ]

    def __str__(self) -> str:
        return (
            "PointCloud2 { "
            f"height: {self.height}, width: {self.width}, "
            f"fields_count: {self.fields_count}, "
            f"point_step: {self.point_step}, row_step: {self.row_step}, "
            f"data_length: {self.data_length}, is_dense: {self.is_dense} "
            "}"
        )

    @staticmethod
    def type_name() -> str:
        return "PointCloud2"

    def set_field_name(self, index: int, value: str) -> None:
        if index >= POINT_FIELD_CAPACITY:
            raise IceoryxMessageOverflow(
                f"fields[{index}] exceeds capacity {POINT_FIELD_CAPACITY}"
            )
        write_c_string(self.fields[index], "name", value)

