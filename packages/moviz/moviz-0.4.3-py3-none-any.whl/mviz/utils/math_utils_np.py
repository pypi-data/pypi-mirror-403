"""Math utilities using NumPy instead of PyTorch.

NOTE: All functions can calculate multi-dim batch data, so the input can be (..., J) or (N, J)
NOTE: Defaultly, quat is in xyzw order, and quat in wxyz order is called *wxyz* directly
"""

import numpy as np
from typing import Tuple


def normalize(x: np.ndarray) -> np.ndarray:
    """Normalize vector to unit length."""
    norm = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.maximum(norm, 1e-10)


def quat_inv(q: np.ndarray) -> np.ndarray:
    """Inverse of quaternion (xyzw order)."""
    return np.concatenate((-q[..., :3], q[..., 3:]), axis=-1)


def quat_mul_no_normal(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Multiply two quaternions without normalization (xyzw order)."""
    w1, x1, y1, z1 = q1[..., 3], q1[..., 0], q1[..., 1], q1[..., 2]
    w2, x2, y2, z2 = q2[..., 3], q2[..., 0], q2[..., 1], q2[..., 2]
    
    qw = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    qx = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    qy = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    qz = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
    
    xyzw = np.stack([qx, qy, qz, qw], axis=-1)
    return xyzw


def quat_mul(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Multiply two quaternions with normalization (xyzw order)."""
    xyzw = quat_mul_no_normal(q1, q2)
    # Flip quaternion if w < 0 to ensure w >= 0
    xyzw = np.where(xyzw[..., 3:] < 0, -xyzw, xyzw)
    return normalize(xyzw)


def quat_apply(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Apply quaternion rotation to vector (xyzw order)."""
    zero = np.zeros_like(v[..., :1])
    v_q = np.concatenate([v, zero], axis=-1)  # (..., 4)
    q = normalize(q)  # (..., 4)
    q_inv = quat_inv(q)  # (..., 4)
    temp = quat_mul_no_normal(q, v_q)  # (..., 4)
    rotated = quat_mul_no_normal(temp, q_inv)  # (..., 4)
    return rotated[..., :3]


def exp_map_to_quat(exp_map: np.ndarray) -> np.ndarray:
    """Convert exponential map to quaternion (xyzw order)."""
    angle = np.linalg.norm(exp_map, axis=-1)  # (...)
    axis = exp_map / np.maximum(angle[..., None], 1e-9)  # (..., 3)
    half_angle = angle / 2.0
    qw = np.cos(half_angle)
    qx = axis[..., 0] * np.sin(half_angle)
    qy = axis[..., 1] * np.sin(half_angle)
    qz = axis[..., 2] * np.sin(half_angle)
    xyzw = np.stack([qx, qy, qz, qw], axis=-1)
    return normalize(xyzw)  # (..., 4)


def quat_from_rotation(rot: np.ndarray, order: str = 'xyzw') -> np.ndarray:
    """Convert rotation matrix to quaternion."""
    m = rot
    if m.shape[-2:] != (3, 3):
        raise ValueError(f"Invalid rotation matrix shape: {m.shape}")
    
    batch_shape = m.shape[:-2]
    B = int(np.prod(batch_shape)) if batch_shape else 1
    m_flat = m.reshape(B, 3, 3)
    
    qw = np.sqrt(np.maximum(m_flat[:, 0, 0] + m_flat[:, 1, 1] + m_flat[:, 2, 2] + 1.0, 0.0)) / 2.0
    qx = np.sqrt(np.maximum(m_flat[:, 0, 0] - m_flat[:, 1, 1] - m_flat[:, 2, 2] + 1.0, 0.0)) / 2.0
    qy = np.sqrt(np.maximum(m_flat[:, 1, 1] - m_flat[:, 0, 0] - m_flat[:, 2, 2] + 1.0, 0.0)) / 2.0
    qz = np.sqrt(np.maximum(m_flat[:, 2, 2] - m_flat[:, 0, 0] - m_flat[:, 1, 1] + 1.0, 0.0)) / 2.0
    
    qx = np.sign(m_flat[:, 2, 1] - m_flat[:, 1, 2]) * qx
    qy = np.sign(m_flat[:, 0, 2] - m_flat[:, 2, 0]) * qy
    qz = np.sign(m_flat[:, 1, 0] - m_flat[:, 0, 1]) * qz
    
    q = normalize(np.stack([qx, qy, qz, qw], axis=-1)).reshape(*batch_shape, 4)
    
    if order == 'xyzw':
        return q
    elif order == 'wxyz':
        # Reorder from xyzw to wxyz
        return np.concatenate([q[..., 3:], q[..., :3]], axis=-1)
    else:
        raise ValueError(f"Unsupported quaternion order: {order}")


def rotation_from_quat(q: np.ndarray, order: str = 'xyzw') -> np.ndarray:
    """Convert quaternion to rotation matrix."""
    if order == 'xyzw':
        qx, qy, qz, qw = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    elif order == 'wxyz':
        qx, qy, qz, qw = q[..., 1], q[..., 2], q[..., 3], q[..., 0]
    else:
        raise ValueError(f"Unsupported quaternion order: {order}. Use 'xyzw' or 'wxyz'.")
    
    rot = np.zeros((*q.shape[:-1], 3, 3), dtype=q.dtype)
    rot[..., 0, 0] = 1 - 2 * (qy * qy + qz * qz)
    rot[..., 0, 1] = 2 * (qx * qy - qw * qz)
    rot[..., 0, 2] = 2 * (qx * qz + qw * qy)
    rot[..., 1, 0] = 2 * (qx * qy + qw * qz)
    rot[..., 1, 1] = 1 - 2 * (qx * qx + qz * qz)
    rot[..., 1, 2] = 2 * (qy * qz - qw * qx)
    rot[..., 2, 0] = 2 * (qx * qz - qw * qy)
    rot[..., 2, 1] = 2 * (qy * qz + qw * qx)
    rot[..., 2, 2] = 1 - 2 * (qx * qx + qy * qy)
    return rot


def rotation_from_axis_angle(axis: np.ndarray, angle: np.ndarray) -> np.ndarray:
    """Convert axis-angle to rotation matrix using Rodrigues' formula."""
    axis = axis / np.linalg.norm(axis, axis=-1, keepdims=True)  # (..., 3)
    theta = angle  # (..., 1)
    
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    
    batch_shape = axis.shape[:-1]
    K = np.zeros((*batch_shape, 3, 3), dtype=axis.dtype)
    K[..., 0, 1] = -axis[..., 2]
    K[..., 0, 2] = axis[..., 1]
    K[..., 1, 0] = axis[..., 2]
    K[..., 1, 2] = -axis[..., 0]
    K[..., 2, 0] = -axis[..., 1]
    K[..., 2, 1] = axis[..., 0]
    
    eye = np.eye(3, dtype=axis.dtype)
    if batch_shape:
        eye = np.broadcast_to(eye, (*batch_shape, 3, 3)).copy()
    
    rotation = eye + sin_theta[..., None] * K + (1 - cos_theta)[..., None] * (K @ K)
    
    return rotation


def transformation(rot: np.ndarray, pos: np.ndarray) -> np.ndarray:
    """Create 4x4 transformation matrix from rotation and position."""
    t = np.zeros((*rot.shape[:-2], 4, 4), dtype=rot.dtype)
    t[..., :3, :3] = rot
    t[..., :3, 3] = pos
    t[..., 3, 3] = 1.0
    return t


def quat_to_exp_map(q: np.ndarray) -> np.ndarray:
    """Convert quaternion to exponential map (xyzw order)."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        q = normalize(q)
        angle = 2.0 * np.arccos(np.clip(q[..., 3], -1.0, 1.0))  # (...)
        sin_half_angle = np.sin(angle / 2.0)
        
        # Avoid division by zero
        axis = np.where(
            np.abs(sin_half_angle)[..., None] > 1e-5,
            q[..., :3] / sin_half_angle[..., None],
            np.zeros_like(q[..., :3])
        )
        
        exp_map = angle[..., None] * axis
        return exp_map


def quat_diff(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Compute quaternion difference: q_diff = q1 - q2, such that q_diff * q2 = q1."""
    return normalize(quat_mul(q1, quat_inv(q2)))


def quat_to_rpy(q: np.ndarray) -> np.ndarray:
    """Convert quaternion (xyzw) to RPY (roll, pitch, yaw) angles."""
    # Ensure quaternion is normalized
    q = normalize(q)
    qx, qy, qz, qw = q[..., 0], q[..., 1], q[..., 2], q[..., 3]

    # Roll (x-axis rotation)
    sinr_cosp = 2 * (qw * qx + qy * qz)
    cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (qw * qy - qz * qx)
    # Clamp sinp to avoid domain errors with arcsin
    pitch = np.arcsin(np.clip(sinp, -1.0, 1.0))

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (qw * qz + qx * qy)
    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return np.stack((roll, pitch, yaw), axis=-1)


def quat_to_tan_norm(q: np.ndarray) -> np.ndarray:
    """Represent rotation using tangent and normal vectors (6D representation)."""
    ref_tan = np.zeros_like(q[..., 0:3])
    ref_tan[..., 0] = 1
    tan = normalize(quat_apply(q, ref_tan))
    
    ref_norm = np.zeros_like(q[..., 0:3])
    ref_norm[..., -1] = 1
    norm = normalize(quat_apply(q, ref_norm))
    
    norm_tan = np.concatenate([tan, norm], axis=-1)
    return norm_tan


def slerp(q0: np.ndarray, q1: np.ndarray, t: np.ndarray, DOT_THRESHOLD: float = 0.9995) -> np.ndarray:
    """Spherical linear interpolation between two quaternions."""
    q0_norm, q1_norm = normalize(q0), normalize(q1)
    dot = np.sum(q0_norm * q1_norm, axis=-1, keepdims=True)
    
    # Take the shorter path
    q1_corr = np.where(dot < 0.0, -q1_norm, q1_norm)
    dot = np.abs(dot)  # abs after correction for path
    
    needs_lerp = dot > DOT_THRESHOLD
    theta_0 = np.arccos(np.clip(dot, -1.0, 1.0))
    sin_theta_0 = np.sin(theta_0)
    
    s0 = np.sin((1.0 - t) * theta_0) / (sin_theta_0 + 1e-9)
    s1 = np.sin(t * theta_0) / (sin_theta_0 + 1e-9)
    slerp_val = (s0 * q0_norm) + (s1 * q1_corr)
    
    lerp_val = normalize((1.0 - t) * q0_norm + t * q1_corr)
    return np.where(needs_lerp, lerp_val, slerp_val)


def get_vel(data: np.ndarray, type: str, fps: float) -> np.ndarray:
    """Compute velocity from position/rotation data."""
    assert data.ndim <= 3, "Data should be 2D or 3D array (Time, NumLinks, Dim) or (Time, Dim)"
    
    if type == 'linear':  # For positions, joint angles, RPY angles
        vel = np.zeros_like(data)
        vel[1:, ...] = data[1:, ...] - data[:-1, ...]
    elif type == 'angular':  # For quaternions
        # data shape: (Time, NumLinks, 4) or (Time, 4) for root
        q_curr = data[:-1, ...]  # T-1, ..., 4
        q_next = data[1:, ...]   # T-1, ..., 4
        q_rel = quat_diff(q_next, q_curr)  # q_next - q_curr
        exp_map_diff = quat_to_exp_map(q_rel)  # T-1, ..., 3
        
        vel = np.zeros((*data.shape[:-1], 3), dtype=data.dtype)
        vel[1:, ...] = exp_map_diff
    else:
        raise ValueError(f"Unknown type: {type}")
    
    return vel * fps

