try:
    from spglib import *
    from spglib import __version__
except ImportError:
    # Fallback to bundled files if system spglib is not available
    from ._internal import *  # noqa: F403
    from ._internal import __all__ as _internal_all
    from ._version import __version__, __version_tuple__
    from .cell import *  # noqa: F403
    from .cell import __all__ as _cell_all
    from .error import *  # noqa: F403
    from .error import __all__ as _error_all
    from .kpoints import *  # noqa: F403
    from .kpoints import __all__ as _kpoints_all
    from .msg import *  # noqa: F403
    from .msg import __all__ as _msg_all
    from .reduce import *  # noqa: F403
    from .reduce import __all__ as _reduce_all
    from .spg import *  # noqa: F403
    from .spg import __all__ as _spg_all
    from .utils import *  # noqa: F403
    from .utils import __all__ as _utils_all

def get_standardized_dataset(cell, symprec=1e-3, angle_tolerance=-1.0):
    """
    Standardized wrapper for spglib.get_symmetry_dataset.
    Ensures consistent defaults and error handling across macer.
    """
    try:
        from spglib import get_symmetry_dataset
    except ImportError:
        from .spg import get_symmetry_dataset
    return get_symmetry_dataset(cell, symprec=symprec, angle_tolerance=angle_tolerance)