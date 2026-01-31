import sys
import logging
from phonopy.structure.symmetry import Symmetry

def apply_dynaphopy_patch():
    """
    Patches the installed dynaphopy package at runtime to fix compatibility issues
    with Phonopy 2.x (specifically the removal of get_reciprocal_operations).
    """
    try:
        # Try bundled version first
        import macer.externals.dynaphopy_bundled.interface.phonopy_link as ph_link
    except ImportError:
        try:
            # Fallback to system version
            import dynaphopy.interface.phonopy_link as ph_link
        except ImportError:
            # Dynaphopy not installed, nothing to patch
            return
    except Exception:
        # Any other error (e.g. NumPy 2.x crash on system dynaphopy)
        return

    # 2. Check if the patch is needed (look for the offending code logic or just force patch)
    # We redefine the specific function that causes the crash.
    
    # Original signature: get_equivalent_q_points_by_symmetry(q_point, bulk, symprec=1e-5)
    def patched_get_equivalent_q_points_by_symmetry(q_point, bulk, symprec=1e-5):
        # --- PATCH START ---
        import numpy as np
        
        # Ensure q_point is a numpy array (NumPy 2.x safety)
        q_point = np.array(q_point, dtype=float)
        
        # DynaPhoPy passes its own 'Structure' object, but Phonopy 2.x's Symmetry class
        # expects a PhonopyAtoms-like object with attributes like 'magnetic_moments'.
        # We must convert 'bulk' to PhonopyAtoms to avoid AttributeError.
        
        from phonopy.structure.atoms import PhonopyAtoms
        
        # Convert DynaPhoPy Structure -> PhonopyAtoms
        # DynaPhoPy Structure attributes: get_cell(), get_scaled_positions(), get_atomic_numbers()
        phonopy_cell = PhonopyAtoms(cell=bulk.get_cell(),
                                    scaled_positions=bulk.get_scaled_positions(),
                                    numbers=bulk.get_atomic_numbers())
        
        # Use property .reciprocal_operations instead of getter
        try:
            # Phonopy 2.x style
            ops = Symmetry(phonopy_cell, symprec=symprec).reciprocal_operations
        except AttributeError:
            # Fallback for very old Phonopy (unlikely, but safe)
            ops = Symmetry(phonopy_cell, symprec=symprec).get_reciprocal_operations()
        
        for operation_matrix in ops:
            q_point_rot =  np.dot(operation_matrix, q_point)
            diff = q_point_rot - q_point
            if (np.abs(diff - np.rint(diff)) < symprec).all():
                return [q_point]  # Return as a list containing the vector
        return [q_point]          # Return as a list containing the vector
        # --- PATCH END ---


    # 3. Apply the Monkey Patch
    # We need numpy for the function above to work, ensuring it's in the module's scope
    import numpy as np
    
    # Inject numpy into the module scope if it's missing (usually it's there)
    ph_link.np = np 
    
    # Swap the broken function with our fixed one
    ph_link.get_equivalent_q_points_by_symmetry = patched_get_equivalent_q_points_by_symmetry
    
    # logger = logging.getLogger("macer")
    # logger.debug("Applied runtime patch to dynaphopy.interface.phonopy_link for Phonopy 2.x compatibility.")
    # print("DEBUG: Applied runtime patch to dynaphopy.interface.phonopy_link")

