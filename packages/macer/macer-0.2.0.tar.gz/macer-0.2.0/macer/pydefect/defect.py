"""
Macer: Machine-learning accelerated Atomic Computational Environment for automated Research workflows
Copyright (c) 2025 The Macer Package Authors
Author: Soungmin Bae <soungminbae@gmail.com>
License: MIT
"""

import sys
import os
import shutil
from argparse import Namespace
from pathlib import Path
import yaml

from pymatgen.core import IStructure, Structure
from monty.serialization import loadfn

# pydefect imports
from pydefect.cli.main_functions import (
    make_supercell,
    make_defect_energy_infos_main_func,
    make_defect_energy_summary_main_func
)
from pydefect.cli.vasp.main_vasp_functions import make_defect_entries, make_calc_results
from pydefect.input_maker.defect_set_maker import DefectSetMaker
from pydefect.chem_pot_diag.chem_pot_diag import StandardEnergies
from pydefect.analyzer.unitcell import Unitcell
from pydefect.analyzer.band_edge_states import PerfectBandEdgeState, EdgeInfo, OrbitalInfo

# macer imports
from macer.pydefect.utils import run_macer_relax, write_summary_at_vertices, get_unique_dir_name
from macer.utils.validation import check_poscar_format

def run_defect_workflow(args):
    """
    Auto Defect workflow.
    args requires: poscar, std_energies, target_vertices, matrix, min_atoms, max_atoms, analyze_symmetry, sites_yaml_filename, doping
    """
    
    input_poscar_path = Path(args.poscar).absolute()
    if not input_poscar_path.exists():
        raise FileNotFoundError(f"Error: {input_poscar_path} not found.")
        
    # Validate POSCAR format (VASP 5 check)
    try:
        check_poscar_format(input_poscar_path)
    except ValueError as e:
        raise ValueError(f"\nError: {e}\n")
    
    std_energies_path = Path(args.std_energies).absolute()
    if not std_energies_path.exists():
        raise FileNotFoundError(f"Error: {std_energies_path} not found.")

    target_vertices_path = Path(args.target_vertices).absolute()
    if not target_vertices_path.exists():
        raise FileNotFoundError(f"Error: {target_vertices_path} not found.")

    sites_yaml_path = None
    if args.sites_yaml_filename:
        sites_yaml_path = Path(args.sites_yaml_filename).absolute()
        if not sites_yaml_path.exists():
            raise FileNotFoundError(f"Error: {sites_yaml_path} not found.")

    # 1. Setup Directory
    try:
        structure = Structure.from_file(str(input_poscar_path))
        formula = structure.composition.reduced_formula
        input_poscar_name = input_poscar_path.name
        
        dopants_part = ""
        if args.doping:
            dopants_part = f"-DOPANG={'_'.join(args.doping)}"

        if getattr(args, "output_dir", None):
            base_dir_name = Path(args.output_dir)
        else:
            base_dir_name = input_poscar_path.parent / f"DEFECT-{input_poscar_name}-formula={formula}{dopants_part}-mlff={args.ff}"
            
        work_dir = get_unique_dir_name(base_dir_name)
        
        print(f"Creating workspace: {work_dir}")
        work_dir.mkdir()
        os.chdir(work_dir)
        
        # Copy input POSCAR to POSCAR-unitcell
        shutil.copy(str(input_poscar_path), "POSCAR-unitcell")
        
        # Update poscar_path to the local copy for subsequent steps
        poscar_path = Path("POSCAR-unitcell")
        dopants = args.doping if args.doping else []

    except Exception as e:
        raise RuntimeError(f"Initialization failed: {e}")

    print("--- Step 1: Make Supercell ---")
    unitcell = IStructure.from_file(str(poscar_path))
    args_sc = Namespace(unitcell=unitcell, matrix=args.matrix, 
                        min_num_atoms=args.min_atoms, max_num_atoms=args.max_atoms, 
                        analyze_symmetry=args.analyze_symmetry, 
                        dopants=dopants,
                        sites_yaml_filename=str(sites_yaml_path) if sites_yaml_path else None)
    make_supercell(args_sc)
    
    if not Path("supercell_info.json").exists():
        raise RuntimeError("Error: supercell_info.json not created.")

    print("\n--- Step 2: Make Defect Set (Charge 0 only) ---")
    supercell_info = loadfn("supercell_info.json")
    maker = DefectSetMaker(supercell_info, dopants=dopants)
    
    defect_dict = {defect.name: [0] for defect in maker.defect_set}
    
    with open("defect_in.yaml", "w") as f:
        yaml.dump(defect_dict, f)
    print("defect_in.yaml created with charge states [0].")

    print("\n--- Step 3: Make Defect Entries ---")
    make_defect_entries(Namespace())
    
    # Identify directories to calculate
    dirs_to_calc = []
    if Path("perfect").exists() and Path("perfect/POSCAR").exists():
        dirs_to_calc.append(Path("perfect"))
    
    for name in defect_dict:
        d = Path(f"{name}_0")
        if d.exists() and (d / "POSCAR").exists():
            dirs_to_calc.append(d)
    
    print(f"Directories to calculate: {[d.name for d in dirs_to_calc]}")

    print("\n--- Step 4: Run Macer Relax ---")
    
    # Use ISIF=2 for defects
    successful_dirs = run_macer_relax(
        dirs_to_calc, 
        isif=2, 
        supercell_info=supercell_info, 
        verbose=True, 
        fmax=args.fmax,
        ff=args.ff,
        model_path=args.model,
        device=args.device,
        modal=args.modal
    )

    print("\n--- Step 4.5: Generate calc_results.json ---")
    if successful_dirs:
        make_calc_results(Namespace(dirs=successful_dirs, verbose=False, check_calc_results=False))
    else:
        print("No successful calculations found.")
        return

    print("\n--- Step 5: Generate Defect Energy Info ---")
    
    # Create unitcell.yaml with correct system name
    formula = unitcell.composition.reduced_formula
    system_name = f"{poscar_path.name}-{formula}"
    
    dummy_unitcell_str = f"""system: {system_name}
vbm: 0.0
cbm: 5.0
ele_dielectric_const: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
ion_dielectric_const: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
"""
    Path("unitcell.yaml").write_text(dummy_unitcell_str)
    
    perfect_calc_results_path = Path("perfect/calc_results.json")
    if not perfect_calc_results_path.exists():
        print("Error: perfect/calc_results.json not found.")
        return

    perfect_calc_results = loadfn(str(perfect_calc_results_path))
    unitcell_obj = Unitcell.from_yaml("unitcell.yaml")
    std_energies_obj = StandardEnergies.from_yaml(str(std_energies_path))
    
    defect_dirs = [d for d in successful_dirs if d.name != "perfect"]
    
    args_dei = Namespace(dirs=defect_dirs, check_calc_results=False, perfect_calc_results=perfect_calc_results,
                         std_energies=std_energies_obj, unitcell=unitcell_obj, verbose=False)
    
    make_defect_energy_infos_main_func(args_dei)
    print("Done. Defect energy infos generated.")

    print("\n--- Step 6: Generate Defect Energy Summary ---")
    
    # Dummy Band Edge State
    vbm_info = EdgeInfo(band_idx=0, kpt_coord=(0.0, 0.0, 0.0),
                        orbital_info=OrbitalInfo(energy=0.0, orbitals={}, occupation=1.0))
    cbm_info = EdgeInfo(band_idx=0, kpt_coord=(0.0, 0.0, 0.0),
                        orbital_info=OrbitalInfo(energy=5.0, orbitals={}, occupation=0.0))
    p_state = PerfectBandEdgeState(vbm_info=vbm_info, cbm_info=cbm_info)
    
    args_des = Namespace(
        dirs=defect_dirs,
        verbose=False,
        target_vertices_yaml=str(target_vertices_path),
        unitcell=unitcell_obj,
        p_state=p_state
    )
    
    make_defect_energy_summary_main_func(args_des)
    print("defect_energy_summary.json created.")

    print("\n--- Step 7: Write summary at each vertex ---")
    summary_path = Path("defect_energy_summary.json")
    if summary_path.exists():
        write_summary_at_vertices(summary_path)
    else:
        print("defect_energy_summary.json not found, skipping final summary generation.")
