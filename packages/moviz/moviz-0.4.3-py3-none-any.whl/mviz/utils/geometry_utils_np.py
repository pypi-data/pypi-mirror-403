"""Geometry utilities using NumPy instead of PyTorch."""

import numpy as np
import trimesh


def capsule_transform(capsules: np.ndarray, transform: np.ndarray) -> np.ndarray:
    """
    Apply a transformation to capsules.
    
    Args:
        capsules: [..., 7], 7 = (p0x,p0y,p0z,p1x,p1y,p1z,r)
        transform: [..., 4, 4] transformation matrix
    
    Returns:
        transformed_capsules: [..., 7]
    """
    p0 = capsules[..., :3]  # [...,3]
    p1 = capsules[..., 3:6] # [...,3]
    r = capsules[..., 6]    # [...]

    p0_h = np.concatenate([p0, np.ones_like(p0[..., :1])], axis=-1)  # [...,4]
    p1_h = np.concatenate([p1, np.ones_like(p1[..., :1])], axis=-1)  # [...,4]

    p0_transformed = (transform @ p0_h[..., :, None]).squeeze(-1)[..., :3]  # [...,3]
    p1_transformed = (transform @ p1_h[..., :, None]).squeeze(-1)[..., :3]  # [...,3]

    transformed_capsules = np.concatenate([p0_transformed, p1_transformed, r[..., None]], axis=-1)  # [...,7]

    return transformed_capsules


def safe_div(numer: np.ndarray, denom: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    """Safe division, returns 0 where denom is too small."""
    return np.where(np.abs(denom) > eps, numer / denom, 0.0)


def _segment_segment_distance(p0_a: np.ndarray, p1_a: np.ndarray, 
                               p0_b: np.ndarray, p1_b: np.ndarray, 
                               eps: float = 1e-9):
    """
    Compute closest points and distance between two line segments.
    All arrays shape [..., 3].
    Returns (dist, pa, pb, s, t).
    """
    u = p1_a - p0_a
    v = p1_b - p0_b
    w = p0_a - p0_b

    a = (u * u).sum(axis=-1)  # [...] 
    b = (u * v).sum(axis=-1)  # [...]
    c = (v * v).sum(axis=-1)  # [...]
    d = (u * w).sum(axis=-1)  # [...]
    e = (v * w).sum(axis=-1)  # [...]

    D = a * c - b * b
    sD = D
    tD = D

    sN = b * e - c * d
    tN = a * e - b * d

    # Initialize s and t
    s = np.zeros_like(a)
    t = np.zeros_like(a)

    # Categorize segments
    small_D = (np.abs(D) < eps)
    small_a = (np.abs(a) < eps)
    small_c = (np.abs(c) < eps)

    neither_small = ~(small_a | small_c | small_D)
    mask_a_only = small_a & ~small_c
    mask_c_only = ~small_a & small_c

    # Case: both degenerate
    if (small_a & small_c).any():
        s[small_a & small_c] = 0.0
        t[small_a & small_c] = 0.0

    # Case: a degenerate
    if mask_a_only.any():
        s[mask_a_only] = 0.0
        t[mask_a_only] = np.clip(safe_div(e[mask_a_only], c[mask_a_only]), 0.0, 1.0)

    # Case: c degenerate
    if mask_c_only.any():
        s[mask_c_only] = np.clip(safe_div(sN[mask_c_only], sD[mask_c_only]), 0.0, 1.0)
        t[mask_c_only] = 0.0

    # General or parallel
    if neither_small.any():
        s_val = safe_div(sN[neither_small], sD[neither_small])
        t_val = safe_div(tN[neither_small], tD[neither_small])
        s[neither_small] = np.clip(s_val, 0.0, 1.0)
        t[neither_small] = np.clip(t_val, 0.0, 1.0)

    pa = p0_a + s[..., None] * u
    pb = p0_b + t[..., None] * v

    diff = pa - pb
    dist2 = np.maximum((diff * diff).sum(axis=-1), eps)
    dist = np.sqrt(dist2)

    return dist, pa, pb, s, t


def capsule_to_capsule_distance(capsules_A: np.ndarray, capsules_B: np.ndarray, 
                                 eps: float = 1e-9) -> np.ndarray:
    """
    capsules_A: [..., 7] with (p0x,p0y,p0z,p1x,p1y,p1z,r)
    capsules_B: [..., 7] broadcastable to capsules_A
    returns:    [...], signed distance (negative => penetration depth)
    """
    p0_A, p1_A, r_A = capsules_A[..., :3], capsules_A[..., 3:6], capsules_A[..., 6]
    p0_B, p1_B, r_B = capsules_B[..., :3], capsules_B[..., 3:6], capsules_B[..., 6]
    dist, _, _, _, _ = _segment_segment_distance(p0_A, p1_A, p0_B, p1_B, eps=eps)
    return dist - (r_A + r_B)


def capsule_distance_matrix(capsules: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    """
    capsules: [..., N, 7]
    returns:  [..., N, N], pairwise signed distances (diagonal set to 0)
    Note: uses broadcasting and computes all pairs at once.
    """
    N = capsules.shape[-2]
    A = capsules[..., :, None, :]  # [..., N, 1, 7]
    B = capsules[..., None, :, :]  # [..., 1, N, 7]
    A = np.repeat(A, N, axis=-2)  # broadcast to [..., N, N, 7]
    B = np.repeat(B, N, axis=-3)  # broadcast to [..., N, N, 7]
    dist = capsule_to_capsule_distance(A, B, eps=eps)  # [..., N, N]
    # Set diagonal to 0
    idx = np.arange(N)
    dist[..., idx, idx] = 0.0
    return dist


def mesh_to_capsule(mesh: trimesh.Trimesh, device: str = 'cpu') -> np.ndarray:
    """
    Get the capsule that tightly fits the mesh.
    (1) compute the principal axis of the mesh
    (2) project all points onto the principal axis
    (3) find the min and max projection points
    (4) compute the radius as the maximum distance from the principal axis

    Args:
        mesh: trimesh.Trimesh
        device: ignored (kept for compatibility)

    Returns:
        capsule: numpy array (7,)  (p0x,p0y,p0z,p1x,p1y,p1z,r)
    """
    vertices = mesh.vertices  # (V,3)

    mean = vertices.mean(axis=0)
    centered = vertices - mean

    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    # get the principal axis (eigenvector with largest eigenvalue)
    principal_axis = eigvecs[:, np.argmax(eigvals)]  # (3,)

    # project points onto principal axis
    projections = centered @ principal_axis  # (V,)
    min_proj, max_proj = projections.min(), projections.max()

    p0 = mean + min_proj * principal_axis
    p1 = mean + max_proj * principal_axis

    # calculate the radius
    direction = p1 - p0
    direction_norm = np.linalg.norm(direction)
    if direction_norm < 1e-8:
        distances = np.linalg.norm(centered, axis=1)
        radius = distances.max()
    else:
        direction_unit = direction / direction_norm
        vecs = vertices - p0  # (V,3)
        cross_prod = np.cross(vecs, direction_unit[np.newaxis, :])  # (V,3)
        distances = np.linalg.norm(cross_prod, axis=1)
        radius = distances.max()

    capsule = np.concatenate([p0, p1, [radius]])
    return capsule.astype(np.float32)


def meshes_to_capsules(mesh_list, device='cpu') -> np.ndarray:
    """
    Args:
        mesh_list: list of trimesh.Trimesh
        device: ignored (kept for compatibility)
    
    Returns:
        capsules: numpy array [N,7]
    """
    capsules = [mesh_to_capsule(mesh, device=device) for mesh in mesh_list]
    return np.stack(capsules, axis=0)

