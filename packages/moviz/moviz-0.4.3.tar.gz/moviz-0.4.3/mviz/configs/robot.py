import numpy as np

# Mapping from Isaac Sim joint order to G1 CSV joint order
# Isaac Sim has 29 joints in a different order than G1 CSV format
# This mapping reorders joints from Isaac Sim format to G1 CSV format
ISAAC_SIM_TO_G1_JOINT_MAPPING = np.array([
    0, 3, 6, 9, 13, 17,  # left leg (6 joints)
    1, 4, 7, 10, 14, 18,  # right leg (6 joints)
    2, 5, 8,  # waist (3 joints)
    11, 15, 19, 21, 23, 25, 27,  # left arm (7 joints)
    12, 16, 20, 22, 24, 26, 28,  # right arm (7 joints)
], dtype=np.int64)

