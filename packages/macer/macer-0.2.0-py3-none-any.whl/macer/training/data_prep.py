
import os
import logging
from typing import Optional

from macer.io.pymlff import MLAB
from ase.io import read, write

logger = logging.getLogger(__name__)

def convert_to_mattersim_format(input_path: str, output_path: str, stress_unit: str = "eV/A^3"):
    """
    Converts VASP ML_AB or other ASE-readable files to MatterSim-compatible extxyz.
    MatterSim requires specific keys: energy, forces, stress.
    
    Args:
        input_path: Path to input file (ML_AB, vasprun.xml, OUTCAR, etc.)
        output_path: Path to output .xyz file
        stress_unit: Unit conversion for stress (passed to pymlff for ML_AB). 
                     Default "eV/A^3" converts VASP kbar to ASE standard.
    """
    logger.info(f"Converting {input_path} to {output_path} for MatterSim training.")
    
    filename = os.path.basename(input_path)
    
    # Check if it looks like an ML_AB file (either named ML_AB or starts with ML_AB string content)
    # BUT, exclude files that clearly have xyz extension
    is_xyz_ext = filename.lower().endswith(".xyz") or filename.lower().endswith(".extxyz")
    is_ml_ab = ("ML_AB" in filename or "ML_ABN" in filename) and not is_xyz_ext
    
    if not is_ml_ab and not is_xyz_ext:
        # Peek at content just in case for ML_AB without extension or clear name
        try:
            with open(input_path, 'r') as f:
                header = f.read(100)
                if "1.0 Version" in header: # VASP ML_AB header signature
                    is_ml_ab = True
        except:
            pass

    if is_ml_ab:
        logger.info("Detected ML_AB format. Using internal pymlff parser.")
        mlab = MLAB.from_file(input_path)
        mlab.write_extxyz(output_path, stress_unit=stress_unit)
    else:
        logger.info("Using ASE to read input file.")
        atoms_list = read(input_path, index=':')
        if not atoms_list:
            raise ValueError(f"No atoms found in {input_path}")
        
        logger.info(f"Read {len(atoms_list)} structures.")
        write(output_path, atoms_list, format='extxyz')
    
    logger.info(f"Successfully wrote {output_path}")
