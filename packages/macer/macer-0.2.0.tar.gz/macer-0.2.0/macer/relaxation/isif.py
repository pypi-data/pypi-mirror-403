import numpy as np
from ase.constraints import FixAtoms
from ase.filters import ExpCellFilter

def build_axis_mask(fix_axis: list[str]):
    """Create a 3x3 mask for ExpCellFilter from a list of axes to fix."""
    mask = np.ones((3, 3), dtype=bool)
    # ASE's ExpCellFilter mask: True allows change, False fixes.
    # We fix the rows of the cell matrix.
    axis_map = {'a': 0, 'b': 1, 'c': 2}
    for ax in fix_axis:
        ax_lower = ax.lower()
        if ax_lower in axis_map:
            mask[axis_map[ax_lower], :] = False
            print(f"  - Fixing axis '{ax_lower}' (cell vector {axis_map[ax_lower]}).")
    return mask

def get_relax_target(atoms, isif: int, fix_axis: list[str]):
    """
    Get the appropriate ASE filter for a given ISIF value, matching VASP-like behavior.
    """
    mask = build_axis_mask(fix_axis) if fix_axis else None

    # ISIF values where only volume changes (hydrostatic), fix_axis is not applicable
    hydrostatic_isifs = {7, 8}

    if fix_axis and isif in hydrostatic_isifs:
        print(f"WARNING: --fix-axis is not compatible with ISIF={isif} which only changes volume hydrostatically. Ignoring --fix-axis.")
        mask = None # Override mask

    if isif in (0, 1, 2):
        print(f" ISIF={isif} → Relax positions (cell fixed).")
        return atoms
        
    elif isif == 3:
        print("️ ISIF=3 → Relax positions, cell shape, and volume.")
        return ExpCellFilter(atoms, mask=mask)
        
    elif isif == 4:
        print("️ ISIF=4 → Relax positions and cell shape (volume fixed).")
        return ExpCellFilter(atoms, constant_volume=True, mask=mask)
        
    elif isif == 5:
        print("️ ISIF=5 → Relax cell shape (positions and volume fixed).")
        atoms.set_constraint(FixAtoms(range(len(atoms))))
        return ExpCellFilter(atoms, constant_volume=True, mask=mask)
        
    elif isif == 6:
        print("️ ISIF=6 → Relax cell shape and volume (positions fixed).")
        atoms.set_constraint(FixAtoms(range(len(atoms))))
        return ExpCellFilter(atoms, mask=mask)
        
    elif isif == 7:
        print("️ ISIF=7 → Relax volume only (positions and cell shape fixed).")
        atoms.set_constraint(FixAtoms(range(len(atoms))))
        return ExpCellFilter(atoms, hydrostatic_strain=True)

    elif isif == 8:
        print("️ ISIF=8 → Relax positions and volume (cell shape fixed).")
        return ExpCellFilter(atoms, hydrostatic_strain=True)
        
    else:
        raise ValueError(f"Unsupported ISIF value: {isif}. Choose from 0–8.")
