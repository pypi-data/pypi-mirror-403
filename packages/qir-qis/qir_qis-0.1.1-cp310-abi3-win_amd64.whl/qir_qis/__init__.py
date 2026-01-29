"""""" # start delvewheel patch
def _delvewheel_patch_1_12_0():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'qir_qis.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_12_0()
del _delvewheel_patch_1_12_0
# end delvewheel patch

from .qir_qis import *

__doc__ = qir_qis.__doc__
if hasattr(qir_qis, "__all__"):
    __all__ = qir_qis.__all__
