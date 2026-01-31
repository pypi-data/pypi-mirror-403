__version__ = "0.4.2"

from mviz import ice_tools
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
G1_URDF_PATH = os.path.join(ROOT_DIR, 'mviz/robots/unitree/g1/g1_29dof_rev_1_0.urdf')
TMP_DIR = os.path.join(ROOT_DIR, '.tmp')


__all__ = [
    "__version__",
    "ice_tools",
    'ROOT_DIR',
    'G1_URDF_PATH',
    'TMP_DIR',
]