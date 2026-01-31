import numpy as np
from mviz.utils.math_utils_np import rotation_from_axis_angle, transformation


def forward_kinematics(
    joint_angles: np.ndarray,  # (..., J) #NOTE batch N can contain multi dims, N = *(N1, N2, ... )
    link_indices: np.ndarray,  # (L, ) topo order -> result order
    link_fathers: np.ndarray,  # (L, ) topo order -> result order
    link_father_joint_indices: np.ndarray,  # (L, ) -> topo order -> joint idx
    base_trans: np.ndarray,  # (..., 4, 4) base transformation in world frame
    link_origins: np.ndarray,  # (L, 4, 4) child link origins in fatherlink frame  
    joint_axises: np.ndarray,  # (J, 3) joint axes in link frame
) -> np.ndarray:
    batch_shape = joint_angles.shape[:-1]
    num_links = link_indices.shape[0]
    results = np.zeros((*batch_shape, num_links, 4, 4), dtype=joint_angles.dtype)
    root_index = link_indices[0]
    results[..., root_index, :, :] = base_trans    
    
    for i in range(1, num_links):  # i is the index in topo order
        link_index = link_indices[i]
        father_index = link_fathers[i]
        joint_index = link_father_joint_indices[i]
        
        # Broadcast joint_origin to batch shape
        joint_origin = np.broadcast_to(link_origins[i], (*batch_shape, 4, 4))
        
        if joint_index < 0:
            results[..., link_index, :, :] = results[..., father_index, :, :] @ joint_origin
            continue
        
        # Broadcast joint_axis to batch shape
        joint_axis = np.broadcast_to(joint_axises[joint_index], (*batch_shape, 3))
        joint_angle = joint_angles[..., joint_index, None]  # Add dimension for angle
        
        rotation = transformation(
            rotation_from_axis_angle(joint_axis, joint_angle), 
            np.zeros((*batch_shape, 3), dtype=joint_angles.dtype)
        )  # (B, 4, 4)
        
        results[..., link_index, :, :] = results[..., father_index, :, :] @ joint_origin @ rotation
    
    return results

