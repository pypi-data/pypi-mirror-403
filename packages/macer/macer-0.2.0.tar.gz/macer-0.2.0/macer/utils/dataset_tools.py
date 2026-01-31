import os
import glob
import random
import logging
import numpy as np
from ase.io import read, write
from macer.io.pymlff import MLAB

logger = logging.getLogger(__name__)

def get_unique_filename(base_path):
    """
    Ensures a unique filename by appending -NEW001, -NEW002, etc.
    """
    if not os.path.exists(base_path):
        return base_path
    
    base, ext = os.path.splitext(base_path)
    counter = 1
    while os.path.exists(f"{base}-NEW{counter:03d}{ext}"):
        counter += 1
    return f"{base}-NEW{counter:03d}{ext}"

def build_dataset(input_patterns, output_path="dataset.xyz", stress_unit="eV/A^3"):
    """
    Combines various VASP outputs (ML_AB, xml, h5) into a single Extended XYZ.
    """
    all_atoms = []
    
    # Resolve all input files from patterns
    input_files = []
    for pattern in input_patterns:
        files = glob.glob(pattern)
        if not files:
            print(f"Warning: No files matched pattern '{pattern}'")
        input_files.extend(files)
    
    if not input_files:
        print("Error: No input files found to build dataset.")
        return None

    unique_output = get_unique_filename(output_path)
    print(f"Building dataset from {len(input_files)} files...")

    processed_count = 0
    skipped_files = []

    for fpath in input_files:
        filename = os.path.basename(fpath)
        print(f"  Processing: {fpath}")
        
        # Determine format
        is_xyz_ext = filename.lower().endswith(".xyz") or filename.lower().endswith(".extxyz")
        is_ml_ab = ("ML_AB" in filename or "ML_ABN" in filename) and not is_xyz_ext
        
        try:
            if is_ml_ab:
                # Use internal pymlff for ML_AB
                mlab = MLAB.from_file(fpath)
                tmp_xyz = fpath + ".tmp.xyz"
                mlab.write_extxyz(tmp_xyz, stress_unit=stress_unit)
                all_atoms.extend(read(tmp_xyz, index=':'))
                os.remove(tmp_xyz)
            else:
                # Use ASE for xml, h5, OUTCAR, etc.
                try:
                    fmt = "vasp-xml" if fpath.lower().endswith(".xml") else None
                    atoms = read(fpath, index=':', format=fmt)
                    if isinstance(atoms, list):
                        all_atoms.extend(atoms)
                    else:
                        all_atoms.append(atoms)
                except Exception as ase_e:
                    # Fallback to pymatgen for XML if ASE fails
                    if fpath.lower().endswith(".xml"):
                        try:
                            from pymatgen.io.vasp import Vasprun
                            from pymatgen.io.ase import AseAtomsAdaptor
                            from ase.calculators.singlepoint import SinglePointCalculator
                            
                            v = Vasprun(fpath, parse_potcar_file=False)
                            for step in v.ionic_steps:
                                s = step['structure']
                                a = AseAtomsAdaptor.get_atoms(s)
                                energy = step.get('e_fr_energy')
                                forces = step.get('forces')
                                stress = step.get('stress')
                                spc = SinglePointCalculator(a, energy=energy, forces=forces, stress=stress)
                                a.calc = spc
                                all_atoms.append(a)
                        except Exception as pm_e:
                            print(f"\n[SKIP] Broken XML: {fpath} ({pm_e})")
                            skipped_files.append(fpath)
                            continue 
                    else:
                        print(f"\n[SKIP] Error parsing {fpath}: {ase_e}")
                        skipped_files.append(fpath)
                        continue

            processed_count += 1

        except Exception as e:
            print(f"\n[SKIP] Unexpected error processing {fpath}: {e}")
            skipped_files.append(fpath)

    if not all_atoms:
        print("\nError: No valid atomic structures found.")
        return None

    print(f"\nSuccessfully collected {len(all_atoms)} structures from {processed_count} files. (Skipped: {len(skipped_files)})")
    if skipped_files:
        print("List of skipped files:")
        for sf in skipped_files:
            print(f"  - {sf}")
    
    write(unique_output, all_atoms, format='extxyz')
    print(f"Saved combined dataset to: {unique_output}")
    return unique_output

def split_dataset(input_path="dataset.xyz", train_ratio=0.8, valid_ratio=0.1, test_ratio=0.1, seed=42, 
                  train_out="train.xyz", valid_out="valid.xyz", test_out="test.xyz"):
    """
    Shuffles and splits an XYZ file into train, valid, and test sets.
    """
    if not os.path.exists(input_path):
        if input_path == "dataset.xyz":
            print("Error: Default 'dataset.xyz' not found. Please provide an extended XYZ file path using -i.")
        else:
            print(f"Error: File not found: {input_path}")
        return False

    print(f"Reading dataset: {input_path}")
    try:
        atoms = read(input_path, index=':')
    except Exception as e:
        print(f"Error reading {input_path}: {e}")
        return False

    random.seed(seed)
    random.shuffle(atoms)
    
    # Normalize ratios so they sum to 1.0
    total_ratio = train_ratio + valid_ratio + test_ratio
    train_ratio /= total_ratio
    valid_ratio /= total_ratio
    test_ratio /= total_ratio
    
    n = len(atoms)
    n_train = int(n * train_ratio)
    n_valid = int(n * valid_ratio)
    
    train_set = atoms[:n_train]
    valid_set = atoms[n_train:n_train + n_valid]
    test_set = atoms[n_train + n_valid:]
    
    print(f"Splitting {n} structures (Ratio {train_ratio:.4f}:{valid_ratio:.4f}:{test_ratio:.4f}):")
    print(f"  - Train: {len(train_set)}")
    print(f"  - Valid: {len(valid_set)}")
    print(f"  - Test : {len(test_set)}")
    
    write(train_out, train_set)
    write(valid_out, valid_set)
    write(test_out, test_set)
    
    print(f"Files created: {train_out}, {valid_out}, {test_out}")
    return True