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

from pymatgen.core import Structure, IStructure, Composition
from monty.serialization import loadfn

# pydefect imports
from vise.cli.main_functions import get_poscar_from_mp
from pydefect.cli.vasp.main_vasp_functions import (
    make_competing_phase_dirs, 
    make_composition_energies,
    make_defect_entries,
    make_calc_results
)
from pydefect.cli.main_functions import (
    make_standard_and_relative_energies, 
    make_cpd_and_vertices,
    make_supercell,
    make_defect_energy_infos_main_func,
    make_defect_energy_summary_main_func
)
from pydefect.defaults import defaults as pydefect_defaults
from pydefect.defaults import defaults
from pydefect.input_maker.defect_set_maker import DefectSetMaker
from pydefect.chem_pot_diag.chem_pot_diag import StandardEnergies, TargetVertices, ChemPotDiag, RelativeEnergies, ChemPotDiagMaker
from pydefect.analyzer.unitcell import Unitcell
from pydefect.analyzer.band_edge_states import PerfectBandEdgeState, EdgeInfo, OrbitalInfo

# macer imports
from macer.pydefect.utils import run_macer_relax, write_summary_at_vertices, get_unique_dir_name, stabilize_target, generate_composition_energies_direct
from macer.utils.validation import check_poscar_format

def run_full_workflow(args):
    """
    Full Auto Defect Workflow (CPD + Defects).
    args requires: poscar OR (formula/mpid), matrix, min_atoms, max_atoms, analyze_symmetry, sites_yaml_filename, doping
    """
    
    # ------------------------------------------------------------------
    # Step 1: Get POSCAR and Determine Elements
    # ------------------------------------------------------------------
    input_poscar_path = None
    
    if args.poscar:
        input_poscar_path = Path(args.poscar).absolute()
        if not input_poscar_path.exists():
            raise FileNotFoundError(f"Error: {input_poscar_path} not found.")
        
        # Validate POSCAR format (VASP 5 check)
        try:
            check_poscar_format(input_poscar_path)
        except ValueError as e:
            raise ValueError(f"\nError: {e}\n")

    else:
        # Check if formula or mpid is provided to download
        target_str = args.formula if args.formula else args.mpid
        if not target_str:
            raise ValueError("\nError: No structure specified. Provide -p, -f or -m.")

        print(f"--- Step 0: Retrieve POSCAR for {target_str} ---")
        args_gp = Namespace(mpid=args.mpid, formula=args.formula)
        try:
            get_poscar_from_mp(args_gp)
            if Path("POSCAR").exists():
                print(f"Successfully retrieved POSCAR for {target_str}.")
                input_poscar_path = Path("POSCAR").absolute()
            else:
                raise RuntimeError("Error: POSCAR file was not created.")
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve POSCAR: {e}")

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
        
        # If downloaded, input_poscar_name is just "POSCAR", let's make it more descriptive if possible, 
        # or just rely on formula in directory name.
        
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
        
        # If we downloaded POSCAR, we might want to move prior_info.yaml as well if it exists
        if not args.poscar and Path("prior_info.yaml").exists():
             shutil.copy("prior_info.yaml", work_dir / "prior_info.yaml")

        os.chdir(work_dir)
        
        # Copy input POSCAR to POSCAR-unitcell
        shutil.copy(str(input_poscar_path), "POSCAR-unitcell")
        
        # Reload structure to ensure formula matches the file we work with
        structure = Structure.from_file("POSCAR-unitcell")
        formula = structure.composition.reduced_formula
        host_elements = [str(e) for e in structure.composition.elements]
        dopants = args.doping if args.doping else []
        cpd_elements = list(set(host_elements + dopants))
        
        print(f"Target Formula: {formula}")
        print(f"Host Elements: {host_elements}")
        if dopants:
            print(f"Dopant Elements: {dopants}")

    except Exception as e:
        raise RuntimeError(f"Initialization failed: {e}")

    # ------------------------------------------------------------------
    # Step 2: CPD Workflow
    # ------------------------------------------------------------------
    print("\n--- Starting CPD Workflow ---")
    
    applied_shift = 0.0

    # Determine fmax for each step
    fmax_cpd_val = args.fmax_cpd if args.fmax_cpd is not None else args.fmax
    fmax_defect_val = args.fmax_defect if args.fmax_defect is not None else args.fmax
    
    # Create cpd directory and work inside it
    root_dir = Path.cwd()
    cpd_dir = Path("cpd")
    cpd_dir.mkdir(exist_ok=True)
    shutil.copy("POSCAR-unitcell", cpd_dir / "POSCAR-unitcell")
    
    os.chdir(cpd_dir)
    print(f"Changed working directory to: {os.getcwd()}")
    
    args_mp = Namespace(elements=cpd_elements, e_above_hull=pydefect_defaults.e_above_hull)
    cpd_proceed = True
    try:
        make_competing_phase_dirs(args_mp)
    except Exception as e:
        print(f"Failed to generate competing phase directories: {e}")
        print("Skipping CPD calculations but proceeding to Defect workflow.")
        cpd_proceed = False
    
    if cpd_proceed:
        target_dirs = []
        # Identify competing phase directories.
        for d in Path.cwd().iterdir():
            if d.is_dir() and d.name not in ["cpd", "defect"] and (d / "POSCAR").exists():
                 target_dirs.append(d)
        
        # Ensure host material is also calculated for CPD
        target_comp_dir = Path(f"{formula}_host")
        if not target_comp_dir.exists():
            target_comp_dir.mkdir()
            shutil.copy("POSCAR-unitcell", target_comp_dir / "POSCAR")
        
        if target_comp_dir not in target_dirs:
            target_dirs.append(target_comp_dir)
            
        # Ensure unique directories and run relaxation with single MLFF load
        target_dirs = list(set(target_dirs))
        successful_cpd_dirs = run_macer_relax(
            target_dirs, 
            isif=3, 
            verbose=True, 
            fmax=fmax_cpd_val,
            ff=args.ff,
            model_path=args.model,
            device=args.device,
            modal=args.modal
        )
        
        yaml_filename = "composition_energies.yaml"
        try:
             generate_composition_energies_direct(successful_cpd_dirs, yaml_filename)
        except Exception as e:
             print(f"Failed to create composition_energies.yaml: {e}")
        
        if Path(yaml_filename).exists():
            try:
                with open(yaml_filename, 'r') as f:
                    comp_energies = yaml.safe_load(f)
                
                filtered_comp_energies = {}
                removed_compounds = []
                for formula_key, data in comp_energies.items():
                    comp = Composition(formula_key)
                    elements_in_comp = [str(e) for e in comp.elements]
                    impurities_in_comp = [e for e in elements_in_comp if e not in host_elements]
                    if len(impurities_in_comp) <= 1:
                        filtered_comp_energies[formula_key] = data
                    else:
                        removed_compounds.append(formula_key)
                
                if removed_compounds:
                    print(f"Filtering out compounds with multiple impurities: {removed_compounds}")
                
                with open(yaml_filename, 'w') as f:
                    yaml.dump(filtered_comp_energies, f)
            except Exception as e:
                print(f"Failed to filter composition energies: {e}")

        args_sre = Namespace(composition_energies_yaml=yaml_filename)
        make_standard_and_relative_energies(args_sre)
        
        # Verify target exists in relative energies
        if Path("relative_energies.yaml").exists():
            try:
                # Check for stability and apply shift if necessary
                applied_shift = stabilize_target("relative_energies.yaml", formula, manual_shift=args.energy_shift_target)
                
                with open("relative_energies.yaml") as f:
                    rel_energies_keys = yaml.safe_load(f).keys()
                if formula not in rel_energies_keys:
                    print(f"WARNING: Target '{formula}' not found in relative_energies.yaml keys: {list(rel_energies_keys)}")
            except Exception as e:
                print(f"Error checking relative_energies: {e}")

        # args_cv = Namespace(rel_energy_yaml="relative_energies.yaml", target=formula, elements=cpd_elements)
        
        # Check for unary system to avoid Qhull error
        if len(cpd_elements) == 1:
            print(f"Unary system detected ({cpd_elements[0]}). Manually generating target_vertices.yaml.")
            manual_vertices = {
                "target": formula,
                "A": {
                    "chem_pot": {cpd_elements[0]: 0.0},
                    "competing_phases": [],
                    "impurity_phases": []
                }
            }
            with open("target_vertices.yaml", "w") as f:
                yaml.dump(manual_vertices, f)
            print("Generated target_vertices.yaml manually.")
        else:
            try:
                # Direct API usage instead of make_cpd_and_vertices(args_cv)
                rel_energies = RelativeEnergies.from_yaml("relative_energies.yaml")
                cpd_maker = ChemPotDiagMaker(rel_energies, elements=cpd_elements, target=formula)
                cpd = cpd_maker.chem_pot_diag
                cpd.to_json_file()
                
                target_vertices = cpd.to_target_vertices
                target_vertices.to_yaml_file("target_vertices.yaml")
                print("Generated chem_pot_diag.json and target_vertices.yaml.")
            except Exception as e:
                print(f"Failed to generate chemical potential diagram: {e}")
        
        if applied_shift != 0.0 and Path("target_vertices.yaml").exists():
            with open("target_vertices.yaml", "a") as f:
                f.write(f"# Energy shift applied to make target stable: {applied_shift} eV/atom\n")
            print(f"Appended stability shift info to target_vertices.yaml")
        
        print("CPD Workflow Finished.")
    else:
        print("CPD Workflow Skipped.")
    
    # Return to root directory
    os.chdir(root_dir)

    # ------------------------------------------------------------------
    # Step 3: Defect Workflow
    # ------------------------------------------------------------------
    print("\n--- Starting Defect Workflow ---")
    defect_dir = Path("defect")
    defect_dir.mkdir(exist_ok=True)
    
    shutil.copy("POSCAR-unitcell", defect_dir / "POSCAR-unitcell")
    
    # Paths relative to the defect dir (which we will enter)
    # std_energies_path is in ../cpd/standard_energies.yaml
    std_energies_path = (cpd_dir / "standard_energies.yaml").absolute()
    target_vertices_path = (cpd_dir / "target_vertices.yaml").absolute()
    
    os.chdir(defect_dir)
    
    unitcell_structure = IStructure.from_file("POSCAR-unitcell")
    args_sc = Namespace(
        unitcell=unitcell_structure, 
        matrix=args.matrix, 
        min_num_atoms=args.min_atoms, 
        max_num_atoms=args.max_atoms, 
        analyze_symmetry=args.analyze_symmetry, 
        dopants=dopants,
        sites_yaml_filename=str(sites_yaml_path) if sites_yaml_path else None
    )
    make_supercell(args_sc)
    
    if not Path("supercell_info.json").exists():
        print("Error: supercell_info.json not created.")
        return

    supercell_info = loadfn("supercell_info.json")
    maker = DefectSetMaker(supercell_info, dopants=dopants)
    
    # Restrict to charge 0 only, as per run_auto_defect.py
    defect_dict = {defect.name: [0] for defect in maker.defect_set}
    with open("defect_in.yaml", "w") as f:
        yaml.dump(defect_dict, f)
    
    make_defect_entries(Namespace())
    
    defect_calc_dirs = []
    for d in Path.cwd().iterdir():
        if d.is_dir() and (d / "POSCAR").exists() and (d / "defect_entry.json").exists():
            defect_calc_dirs.append(d)
    if Path("perfect").exists() and Path("perfect/POSCAR").exists():
        defect_calc_dirs.append(Path("perfect"))
    
    defect_calc_dirs = list(set(defect_calc_dirs))
    
    successful_defect_dirs = run_macer_relax(
        defect_calc_dirs, 
        isif=2, 
        supercell_info=supercell_info, 
        verbose=True, 
        fmax=fmax_defect_val,
        ff=args.ff,
        model_path=args.model,
        device=args.device,
        modal=args.modal
    )
    
    # Create unitcell.yaml with correct system name
    system_name = f"{input_poscar_path.name}-{formula}"
    
    dummy_unitcell_str = f"""
system: {system_name}
vbm: 0.0
cbm: 5.0
ele_dielectric_const: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
ion_dielectric_const: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
"""
    Path("unitcell.yaml").write_text(dummy_unitcell_str)
    unitcell_obj = Unitcell.from_yaml("unitcell.yaml")
    
    if successful_defect_dirs:
        make_calc_results(Namespace(dirs=successful_defect_dirs, verbose=False, check_calc_results=False))
    
    perfect_res_path = Path("perfect/calc_results.json")
    if not perfect_res_path.exists():
        print("Error: perfect/calc_results.json not found. Cannot proceed to analysis.")
        return

    perfect_calc_results = loadfn(str(perfect_res_path))
    
    try:
        std_energies_obj = StandardEnergies.from_yaml(str(std_energies_path))
    except FileNotFoundError:
        print(f"Standard energies not found at {std_energies_path}")
        return

    analysis_dirs = [d for d in successful_defect_dirs if d.name != "perfect"]
    
    args_dei = Namespace(dirs=analysis_dirs, check_calc_results=False, perfect_calc_results=perfect_calc_results,
                         std_energies=std_energies_obj, unitcell=unitcell_obj, verbose=False)
    make_defect_energy_infos_main_func(args_dei)
    
    vbm_info = EdgeInfo(band_idx=0, kpt_coord=(0.0, 0.0, 0.0),
                        orbital_info=OrbitalInfo(energy=0.0, orbitals={}, occupation=1.0))
    cbm_info = EdgeInfo(band_idx=0, kpt_coord=(0.0, 0.0, 0.0),
                        orbital_info=OrbitalInfo(energy=5.0, orbitals={}, occupation=0.0))
    p_state = PerfectBandEdgeState(vbm_info=vbm_info, cbm_info=cbm_info)
    
    args_des = Namespace(
        dirs=analysis_dirs,
        verbose=False,
        target_vertices_yaml=str(target_vertices_path),
        unitcell=unitcell_obj,
        p_state=p_state
    )
    make_defect_energy_summary_main_func(args_des)
    
    summary_path = Path("defect_energy_summary.json")
    if summary_path.exists():
        write_summary_at_vertices(summary_path, applied_shift=applied_shift)
    
    print("\nFull Auto Defect Workflow Completed.")
