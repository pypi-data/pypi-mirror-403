import argparse
import sys
import os
import shutil
import numpy as np
from pathlib import Path
import traceback
import math
from tqdm import tqdm

from ase.io import read as ase_read
from ase import Atoms as AseAtoms
import matplotlib.pyplot as plt

try:
    import phono3py
    from phono3py import Phono3py
    from phono3py.file_IO import write_FORCES_FC3, write_FORCES_FC2, write_fc3_to_hdf5, write_fc2_to_hdf5
    _HAS_PHONO3PY = True
except ImportError:
    _HAS_PHONO3PY = False

from macer.calculator.factory import get_available_ffs, get_calculator, ALL_SUPPORTED_FFS
from macer.defaults import DEFAULT_MODELS, _macer_root, _model_root, DEFAULT_DEVICE, DEFAULT_FF, resolve_model_path
from macer.relaxation.optimizer import relax_structure
from macer.utils.logger import Logger
# from macer import __version__
from macer.phonopy.band_path import generate_band_conf

# Conversion constants if needed
EV_TO_J = 1.6021766208e-19
ANGSTROM_TO_M = 1e-10

MACER_LOGO = r"""
███╗   ███╗  █████╗   ██████╗ ███████╗ ██████╗
████╗ ████║ ██╔══██╗ ██╔════╝ ██╔════╝ ██╔══██╗
██╔████╔██║ ███████║ ██║      █████╗   ██████╔╝
██║╚██╔╝██║ ██╔══██║ ██║      ██╔══╝   ██╔══██╗
██║ ╚═╝ ██║ ██║  ██║ ╚██████╗ ███████╗ ██║  ██║
╚═╝     ╚═╝ ╚═╝  ╚═╝  ╚═════╝ ╚══════╝ ╚═╝  ╚═╝
ML-accelerated Atomic Computational Environment for Research
"""

available_ffs = get_available_ffs()
_dynamic_default_ff = available_ffs[0] if available_ffs else None

def _resolve_model_path(ff: str, model_path: str | None) -> str | None:
    """Resolve model path: prefer user-provided, else DEFAULT_MODELS."""
    if model_path:
        return resolve_model_path(str(model_path))
    
    FFS_USING_MODEL_NAME = {"fairchem", "orb", "chgnet", "m3gnet"}
    default_model_name = DEFAULT_MODELS.get(ff)

    if default_model_name:
        if ff in FFS_USING_MODEL_NAME:
            return default_model_name
        else:
            return resolve_model_path(default_model_name)
    return None

def _auto_determine_supercell(unitcell, min_length):
    cell = unitcell.cell
    vector_lengths = [np.linalg.norm(v) for v in cell]
    if any(v == 0 for v in vector_lengths):
        raise ValueError("Lattice vector length is zero.")
    scaling_factors = [int(np.ceil(min_length / v)) if v > 0 else 1 for v in vector_lengths]
    return np.diag(scaling_factors)

def _plot_band_and_dos(ph3, output_dir, mesh):
    """Generates Band Structure and DOS plots using in-memory FC2."""
    print("  Generating Band Structure and DOS plots...")
    
    # 1. Initialize Phonopy object from scratch
    try:
        from phonopy import Phonopy
        from phonopy.interface.vasp import read_vasp
        
        unitcell_path = output_dir / "POSCAR"
        
        if not unitcell_path.exists():
            print("    Skipping Band/DOS plots: POSCAR not found.")
            return

        unitcell = read_vasp(str(unitcell_path))
        
        # Use phonon_supercell_matrix from ph3 if available, else derive from ph3.supercell_matrix
        supercell_matrix = ph3.phonon_supercell_matrix
        if supercell_matrix is None:
             supercell_matrix = ph3.supercell_matrix

        ph = Phonopy(unitcell, supercell_matrix=supercell_matrix, primitive_matrix="auto")
        
        # Use in-memory FC2
        if ph3.fc2 is None:
             print("    Skipping Band/DOS plots: FC2 not found in memory.")
             return
        ph.force_constants = ph3.fc2
        
    except Exception as e:
        print(f"    Failed to initialize Phonopy for plotting: {e}")
        return

    # 2. Band Structure
    try:
        band_conf_path = output_dir / "band.conf"
        # dim string for band.conf
        dim_fc2 = ph.supercell_matrix
        if np.count_nonzero(dim_fc2 - np.diag(np.diagonal(dim_fc2))) == 0:
             dim_str = " ".join(map(str, dim_fc2.diagonal().astype(int)))
        else:
             dim_str = " ".join(map(str, dim_fc2.flatten().astype(int)))
        
        generate_band_conf(
            poscar_path=unitcell_path, 
            out_path=band_conf_path,
            dim_override=dim_str,
            print_summary_flag=False
        )
        
        # Parse band.conf and run
        from phonopy.cui.settings import PhonopyConfParser
        from phonopy.phonon.band_structure import get_band_qpoints
        import yaml
        
        conf_parser = PhonopyConfParser(filename=str(band_conf_path))
        settings = conf_parser.settings
        
        npoints = settings.band_points if settings.band_points else 51
        qpoints = get_band_qpoints(settings.band_paths, npoints=npoints)
        
        path_connections = []
        if settings.band_paths:
             for paths in settings.band_paths:
                 path_connections += [True, ] * (len(paths) - 2)
                 path_connections.append(False)

        ph.run_band_structure(qpoints, path_connections=path_connections, labels=settings.band_labels)
        ph.plot_band_structure().savefig(output_dir / "band.pdf")
        print("    Saved band.pdf")
        
        ph.write_yaml_band_structure(filename=str(output_dir / "band.yaml"))
        
        # Write band.dat (Simplified)
        with open(output_dir / "band.yaml", 'r') as f:
            data = yaml.safe_load(f)
        
        frequencies = []
        distances = []
        for v in data["phonon"]:
            frequencies.append([f["frequency"] for f in v["band"]])
            distances.append(v["distance"])
        
        frequencies = np.array(frequencies) # (n_q, n_band)
        distances = np.array(distances)
        segment_nqpoint = data["segment_nqpoint"]
        
        with open(output_dir / "band.dat", 'w') as f:
            f.write("# q-distance, frequency\n")
            for i in range(frequencies.shape[1]): # Iterate bands
                f.write(f"# mode {i + 1}\n")
                q_idx = 0
                for nq in segment_nqpoint:
                    for j in range(nq):
                        idx = q_idx + j
                        f.write(f"{distances[idx]:12.8f} {frequencies[idx, i]:15.8f}\n")
                    q_idx += nq
                    f.write("\n")
                f.write("\n")
        print("    Saved band.dat")

    except Exception as e:
        print(f"    Failed to plot Band Structure: {e}")
        # traceback.print_exc()

    # 3. DOS
    try:
        ph.run_mesh(mesh)
        ph.run_total_dos()
        ph.plot_total_dos().savefig(output_dir / "total_dos.pdf")
        print("    Saved total_dos.pdf")
        
        # Write dat
        dos_dict = ph.get_total_dos_dict()
        with open(output_dir / "total_dos.dat", "w") as f:
            f.write("# Frequency  Total_DOS\n")
            for freq, val in zip(dos_dict['frequency_points'], dos_dict['total_dos']):
                f.write(f"{freq:15.8f} {val:15.8f}\n")
        print("    Saved total_dos.dat")
                
    except Exception as e:
        print(f"    Failed to plot DOS: {e}")

def _plot_tc_results(ph3, output_dir, mesh=None):
    """Generates plots for Thermal Conductivity results."""
    print("Generating plots...")
    
    # 0. Band & DOS (if mesh provided)
    if mesh is not None:
        _plot_band_and_dos(ph3, output_dir, mesh)

    tc = ph3.thermal_conductivity
    if tc is None:
        print("Warning: No thermal conductivity object found. Skipping plots.")
        return

    # 1. Thermal Conductivity vs Temperature
    try:
        temps = tc.temperatures
        
        if len(temps) > 1: # Only plot if more than 1 temperature
            kappa = tc.kappa
            # Handle shapes
            if kappa.ndim == 3:
                if kappa.shape[0] == 1: kappa = kappa[0]
                elif kappa.shape[1] == 1: kappa = kappa[:, 0]
                else: kappa = kappa.sum(axis=0)
            
            plt.figure(figsize=(8, 6))
            plt.plot(temps, kappa[:, 0], 'o-', label=r'$\kappa_{xx}$')
            plt.plot(temps, kappa[:, 1], 's-', label=r'$\kappa_{yy}$')
            plt.plot(temps, kappa[:, 2], '^-', label=r'$\kappa_{zz}$')
            plt.xlabel('Temperature (K)')
            plt.ylabel('Thermal Conductivity (W/m-K)')
            plt.title('Thermal Conductivity vs Temperature')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig(output_dir / "kappa_vs_temperature.pdf")
            plt.close()
            print(f"  Saved kappa_vs_temperature.pdf")
        else:
            print("  Skipping kappa_vs_temperature.pdf (only 1 temperature point).")
            
    except Exception as e:
        print(f"  Failed to plot kappa vs temperature: {e}")

    # 2. Phonon Lifetime Distribution (at 300K or first temp)
    try:
        gammas = tc.gamma
        freqs = tc.frequencies
        temps = tc.temperatures
        
        # Check if gammas is valid
        if gammas is None:
            print("  Warning: No gamma data found. Skipping lifetime plot.")
        else:
            # Handle Gamma shape
            # Expected: (n_temp, n_grid, n_band) or (1, n_grid, n_band) or (n_grid, n_band)
            
            target_temp = 300.0
            t_idx = 0
            current_temp = 0.0
            
            if gammas.ndim == 4:
                 # Usually (1, n_temp, n_grid, n_band) or (num_sigma, ...)
                 if gammas.shape[1] == len(temps):
                     # Find t_idx
                     t_idx = (np.abs(temps - target_temp)).argmin() if len(temps) > 0 else 0
                     gamma_at_t = gammas[0, t_idx]
                     current_temp = temps[t_idx]
                 else:
                     print(f"  Unknown gamma shape (4D mismatch): {gammas.shape}. Skipping.")
                     gamma_at_t = None
            elif gammas.ndim == 3:
                 if gammas.shape[0] > 1:
                     t_idx = (np.abs(temps - target_temp)).argmin() if len(temps) > 0 else 0
                     gamma_at_t = gammas[t_idx]
                     current_temp = temps[t_idx]
                 else:
                     gamma_at_t = gammas[0]
                     current_temp = temps[0] if len(temps) > 0 else 0.0
            elif gammas.ndim == 2:
                 gamma_at_t = gammas
                 current_temp = temps[0] if len(temps) > 0 else 0.0
            else:
                 print(f"  Unknown gamma shape: {gammas.shape}. Skipping.")
                 gamma_at_t = None

            if gamma_at_t is not None:
                # Flatten
                flat_freqs = freqs.flatten()
                flat_gammas = gamma_at_t.flatten()
                
                # Calculate lifetime (ps)
                # Lifetime = 1 / (2 * Gamma) assuming Gamma is in THz (linewidth/2)
                # Filter zero/negative/extremely small gamma
                mask = flat_gammas > 1e-10
                f_plot = flat_freqs[mask]
                tau_plot = 1.0 / (2.0 * flat_gammas[mask]) # in ps
                
                plt.figure(figsize=(8, 6))
                plt.scatter(f_plot, tau_plot, s=5, alpha=0.5, c='blue')
                plt.yscale('log')
                plt.xlabel('Frequency (THz)')
                plt.ylabel('Lifetime (ps)')
                plt.title(f'Phonon Lifetime Distribution at {current_temp:.1f} K')
                plt.grid(True, alpha=0.3)
                plt.savefig(output_dir / "lifetime_distribution.pdf")
                plt.close()
                print(f"  Saved lifetime_distribution.pdf")
                
                # Save lifetime distribution data
                with open(output_dir / "lifetime_distribution.dat", "w") as f:
                    f.write(f"# Temperature: {current_temp:.1f} K\n")
                    f.write("# Frequency(THz)  Lifetime(ps)\n")
                    for freq, tau in zip(f_plot, tau_plot):
                        f.write(f"{freq:15.8f} {tau:15.8f}\n")
                print(f"  Saved lifetime_distribution.dat")
        
    except Exception as e:
        print(f"  Failed to plot lifetime distribution: {e}")

    # 3. Cumulative Kappa (Simplified)
    # This requires more complex calculation (group velocity * lifetime * heat capacity)
    # Skipped for basic implementation to avoid errors, as `ph3` object structure for this is complex.
    # Users can use `phono3py-kaccum` CLI with the generated hdf5 file.

def run_tc_workflow(args):
    if not _HAS_PHONO3PY:
        print("Error: phono3py is not installed. Please install it to use this command.")
        sys.exit(1)

    print("--- Starting macer_phonopy tc workflow ---")

    # --- 1. Setup & Inputs ---
    is_cif_mode = False
    if args.poscar:
        input_poscar_path = Path(args.poscar).resolve()
    elif args.cif:
        input_poscar_path = Path(args.cif).resolve()
        is_cif_mode = True
    else:
        raise ValueError("Please provide structure input via -p (POSCAR) or -c (CIF) option.")

    if not input_poscar_path.is_file():
        raise FileNotFoundError(f"Input file not found at '{input_poscar_path}'.")

    if args.output_dir:
        base_output_dir = Path(args.output_dir).resolve()
    else:
        base_output_dir = input_poscar_path.parent / f"tc_{input_poscar_path.stem}_mlff={args.ff}"
    
    output_dir = base_output_dir
    i = 1
    while output_dir.exists():
        output_dir = Path(f"{base_output_dir}-NEW{i:03d}")
        i += 1
    output_dir.mkdir(parents=True, exist_ok=False)
    print(f"Output directory: {output_dir}")

    # Log setup
    log_file = output_dir / "macer_phonopy_tc.log"
    orig_stdout = sys.stdout

    with Logger(str(log_file)) as lg:
        sys.stdout = lg
        print(f"--- Macer Phono3py TC Calculation ---")
        print(f"Command: {' '.join(sys.argv)}")
        print(f"Input: {input_poscar_path}")
        print(f"Force Field: {args.ff}")
        print(f"Device: {args.device}")

        model_path = _resolve_model_path(args.ff, args.model)
        model_info_str = ""
        FFS_USING_MODEL_NAME = {"fairchem", "orb", "chgnet", "m3gnet"}
        if args.model:
            model_info_str = f" (from --model option)"
        else:
            default_model_name = DEFAULT_MODELS.get(args.ff)
            if default_model_name:
                model_info_str = f" (default for {args.ff.upper()}: {default_model_name})"
        
        if model_path:
            print(f"  MLFF Model: {model_path}{model_info_str}")
        else:
            print(f"  MLFF Model:{model_info_str}")

        # Handle CIF conversion if needed
        if is_cif_mode:
            try:
                from ase.io import read as ase_read
                from ase.io import write as ase_write
                atoms_in = ase_read(str(input_poscar_path))
                converted_poscar = output_dir / "POSCAR_input"
                ase_write(str(converted_poscar), atoms_in, format='vasp')
                print(f"Converted {input_poscar_path.name} to {converted_poscar.name}")
                input_poscar_path = converted_poscar
            except Exception as e:
                raise ValueError(f"Error converting CIF: {e}")
        else:
            # Copy input to output dir
            shutil.copy(input_poscar_path, output_dir / "POSCAR_input")
            input_poscar_path = output_dir / "POSCAR_input"

        os.chdir(output_dir)

        # --- 2. Initial Relaxation (Optional) ---
        if args.isif > 0:
            print(f"\n--- Step 1: Initial Relaxation (ISIF={args.isif}) ---")
            relaxed_poscar_name = "CONTCAR-relax"
            model_path = _resolve_model_path(args.ff, args.model)
            try:
                relax_structure(
                    input_file=str(input_poscar_path), isif=args.isif, fmax=args.initial_fmax,
                    device=args.device, contcar_name=relaxed_poscar_name,
                    make_pdf=False, ff=args.ff, model_path=model_path, modal=args.modal,
                    symprec=args.initial_symprec, quiet=False, output_dir_override=output_dir,
                    xml_name=os.devnull # Suppress vasprun.xml
                )
                input_poscar_path = output_dir / relaxed_poscar_name
                shutil.copy(input_poscar_path, output_dir / "POSCAR") # Use relaxed as main POSCAR
                print(f"Relaxed structure saved to {input_poscar_path.name} and copied to POSCAR")
            except Exception as e:
                print(f"Error during relaxation: {e}")
                raise e
        else:
            print("\n--- Step 1: Using input structure (no relaxation) ---")
            shutil.copy(input_poscar_path, output_dir / "POSCAR")
            input_poscar_path = output_dir / "POSCAR"

        # Read Unit Cell
        from phonopy.interface.vasp import read_vasp, write_vasp
        unitcell = read_vasp(str(input_poscar_path))

        # --- 3. Determine Supercell Dimensions ---
        # FC3 Dimension
        if args.dim:
            if len(args.dim) == 3:
                dim_fc3 = np.diag(args.dim)
            elif len(args.dim) == 9:
                dim_fc3 = np.array(args.dim).reshape(3, 3)
            else:
                raise ValueError("--dim must be 3 or 9 integers.")
            print(f"Supercell Matrix FC3 (User defined): {args.dim}")
        else:
            dim_fc3 = _auto_determine_supercell(unitcell, args.length)
            print(f"Supercell Matrix FC3 (Auto, l={args.length}): {dim_fc3.diagonal()}")
        
        # FC2 Dimension (Dual Supercell)
        dim_fc2 = None
        if args.dim_fc2:
            if len(args.dim_fc2) == 3:
                dim_fc2 = np.diag(args.dim_fc2)
            elif len(args.dim_fc2) == 9:
                dim_fc2 = np.array(args.dim_fc2).reshape(3, 3)
            else:
                raise ValueError("--dim-fc2 must be 3 or 9 integers.")
            print(f"Supercell Matrix FC2 (User defined): {args.dim_fc2}")
        else:
            # Auto-determine FC2 dimension based on length_fc2
            # Only if it differs from FC3 do we use it
            auto_dim_fc2 = _auto_determine_supercell(unitcell, args.length_fc2)
            if not np.array_equal(auto_dim_fc2, dim_fc3):
                dim_fc2 = auto_dim_fc2
                print(f"Supercell Matrix FC2 (Auto, l2={args.length_fc2}): {dim_fc2.diagonal()} (Dual Supercell Mode)")
            else:
                print(f"FC2 Supercell matches FC3 ({args.length_fc2}Å requirement met by FC3). Using Single Supercell.")

        # --- 4. Initialize Phono3py & Generate Displacements ---
        print("\n--- Step 2: Generating Displacements ---")
        ph3 = Phono3py(
            unitcell,
            supercell_matrix=dim_fc3,
            phonon_supercell_matrix=dim_fc2,
            primitive_matrix="auto",
            symprec=args.symprec,
            log_level=1
        )
        
        # Apply mass override if needed
        mass_map = {}
        if args.mass:
            if len(args.mass) % 2 != 0:
                raise ValueError("Error: --mass option requires pairs of Symbol Mass (e.g. H 2.014).")
            for i in range(0, len(args.mass), 2):
                sym = args.mass[i]
                try:
                    m = float(args.mass[i+1])
                    mass_map[sym] = m
                except ValueError:
                    raise ValueError(f"Error: Invalid mass value for {sym}: {args.mass[i+1]}")
            print(f"Applying mass override: {mass_map}")
            # Update masses in ph3.primitive
            current_masses = ph3.primitive.masses
            symbols = ph3.primitive.symbols
            new_masses = [mass_map.get(s, m) for s, m in zip(symbols, current_masses)]
            ph3.primitive.masses = new_masses

        ph3.generate_displacements(
            distance=args.amplitude,
            is_plusminus=args.is_plusminus,
            is_diagonal=args.is_diagonal
        )

        if dim_fc2 is not None:
            # Generate phonon (FC2) displacements if dual supercell
            # phono3py API generates these automatically if phonon_supercell_matrix is set
            pass

        ph3.save("phono3py_disp.yaml")
        print("Saved phono3py_disp.yaml")
        
        # Save SPOSCARs
        write_vasp("SPOSCAR_FC3", ph3.supercell)
        print("Saved SPOSCAR_FC3")
        if ph3.phonon_supercell is not None:
            write_vasp("SPOSCAR_FC2", ph3.phonon_supercell)
            print("Saved SPOSCAR_FC2")

        # --- 5. Batch Force Calculation ---
        print("\n--- Step 3: Calculating Forces ---")
        
        # Prepare calculator
        model_path = _resolve_model_path(args.ff, args.model)
        calc_kwargs = {"device": args.device, "modal": args.modal}
        if args.ff == "mace":
            calc_kwargs["model_paths"] = [model_path]
        else:
            calc_kwargs["model_path"] = model_path
        calculator = get_calculator(ff_name=args.ff, **calc_kwargs)

        # 5.1 FC3 Forces
        supercells_fc3 = ph3.supercells_with_displacements
        forces_fc3 = []
        if supercells_fc3:
            print(f"Calculating forces for {len(supercells_fc3)} FC3 supercells...")
            atoms_list = []
            for sc in supercells_fc3:
                if sc is not None:
                     atoms_list.append(AseAtoms(symbols=sc.symbols, cell=sc.cell, scaled_positions=sc.scaled_positions, pbc=True))
                else:
                     atoms_list.append(None) # Should not happen usually
            
            # Batch calculation
            # Handle None if any (though unlikely with standard generation)
            valid_atoms = [a for a in atoms_list if a is not None]
            
            # Use calculator on valid atoms
            # To optimize, we can check if calculator supports batching via list, get_calculator usually returns ASE calc.
            # Macer calculators wrap ASE calc, but get_forces is per atoms.
            # We can loop.
            for atoms in tqdm(valid_atoms, desc="FC3 Forces"):
                atoms.calc = calculator
                forces_fc3.append(atoms.get_forces())
            
        ph3.forces = np.array(forces_fc3)
        write_FORCES_FC3(ph3.dataset, filename="FORCES_FC3")
        print("Saved FORCES_FC3")

        # 5.2 FC2 Forces (if dual)
        forces_fc2 = []
        if dim_fc2 is not None:
            supercells_fc2 = ph3.phonon_supercells_with_displacements
            if supercells_fc2:
                print(f"Calculating forces for {len(supercells_fc2)} FC2 supercells (Dual)...")
                atoms_list_fc2 = [AseAtoms(symbols=sc.symbols, cell=sc.cell, scaled_positions=sc.scaled_positions, pbc=True) 
                                  for sc in supercells_fc2 if sc is not None]
                
                for atoms in tqdm(atoms_list_fc2, desc="FC2 Forces"):
                    atoms.calc = calculator
                    forces_fc2.append(atoms.get_forces())
                
                ph3.phonon_forces = np.array(forces_fc2)
                write_FORCES_FC2(ph3.phonon_dataset, filename="FORCES_FC2")
                print("Saved FORCES_FC2")

        # --- 6. Produce Force Constants ---
        print("\n--- Step 4: Producing Force Constants ---")
        ph3.produce_fc3()
        
        if args.save_hdf5:
            write_fc3_to_hdf5(ph3.fc3, filename="fc3.hdf5")
            print("Saved fc3.hdf5")
        else:
            print("Skipping save of fc3.hdf5 (use --save-hdf5 to save)")

        ph3.produce_fc2()
        
        if args.save_hdf5:
            write_fc2_to_hdf5(ph3.fc2, filename="fc2.hdf5")
            print("Saved fc2.hdf5")
        else:
            print("Skipping save of fc2.hdf5 (use --save-hdf5 to save)")

        # --- 7. Thermal Conductivity Calculation ---
        print("\n--- Step 5: Calculating Thermal Conductivity ---")
        
        if args.mesh:
            mesh = args.mesh
        else:
            # Auto-mesh logic could be added here, but simplest to require it.
            raise ValueError("--mesh is required for thermal conductivity calculation.")

        ph3.mesh_numbers = mesh
        
        # Temperatures
        if args.temp is not None:
            temperatures = args.temp
        else:
            temperatures = np.linspace(args.tmin, args.tmax, int((args.tmax - args.tmin) / args.tstep) + 1)
        
        print(f"Mesh: {mesh}")
        print(f"Temperatures: {temperatures}")

        print("Initializing phonon-phonon interaction...")
        ph3.init_phph_interaction()

        print(f"Running thermal conductivity calculation ({args.method.upper()} mode)...")
        ph3.run_thermal_conductivity(
            temperatures=temperatures,
            is_LBTE=(args.method == "lbte"),
            write_kappa=args.save_hdf5, # Only save kappa-mXXX.hdf5 if requested
        )
        
        if args.save_hdf5:
            print(f"Thermal conductivity results saved to kappa-m{mesh[0]}{mesh[1]}{mesh[2]}.hdf5")
        else:
            print("Thermal conductivity calculation complete (HDF5 not saved).")
        
        # Extract and print simple results
        tc_obj = ph3.thermal_conductivity
        if tc_obj is not None:
            def _clean_kappa(k_array):
                if k_array is None: return None
                # Squeeze unitary dimensions if it's 3D like (1, n_temp, 6) or (n_temp, 1, 6)
                if k_array.ndim == 3:
                    if k_array.shape[0] == 1: k_array = k_array[0]
                    elif k_array.shape[1] == 1: k_array = k_array[:, 0]
                    else: k_array = k_array.sum(axis=0)
                return k_array

            kappa_main = _clean_kappa(tc_obj.kappa)
            kappa_rta = _clean_kappa(getattr(tc_obj, 'kappa_RTA', None))
            temps_results = tc_obj.temperatures
            
            print(f"Debug: kappa shape = {tc_obj.kappa.shape}")
            
            header = f"{'T (K)':>8} {'k_xx':>10} {'k_yy':>10} {'k_zz':>10}"
            if kappa_rta is not None and args.method == "lbte":
                print("\n--- Summary of Thermal Conductivity (W/m-K) [LBTE vs RTA] ---")
                print(f"{'T (K)':>8} {'k_xx (LBTE)':>12} {'k_xx (RTA)':>12}")
            else:
                print("\n--- Summary of Thermal Conductivity (W/m-K) ---")
                print(header)
            
            # Save kappa to dat file
            kappa_dat_path = output_dir / "kappa_vs_temperature.dat"
            with open(kappa_dat_path, 'w') as f:
                if kappa_rta is not None and args.method == "lbte":
                    f.write("# Temperature(K)  k_xx(LBTE)  k_yy(LBTE)  k_zz(LBTE)  k_xx(RTA)  k_yy(RTA)  k_zz(RTA)\n")
                else:
                    f.write("# Temperature(K)      k_xx       k_yy       k_zz       k_yz       k_xz       k_xy\n")
                
                for i in range(len(kappa_main)):
                    if i >= len(temps_results):
                        break
                    t = temps_results[i]
                    k = kappa_main[i]
                    
                    if kappa_rta is not None and args.method == "lbte":
                        k_r = kappa_rta[i]
                        print(f"{t:8.1f} {k[0]:12.3f} {k_r[0]:12.3f}")
                        f.write(f"{t:14.4f} {k[0]:10.4f} {k[1]:10.4f} {k[2]:10.4f} {k_r[0]:10.4f} {k_r[1]:10.4f} {k_r[2]:10.4f}\n")
                    else:
                        print(f"{t:8.1f} {k[0]:10.3f} {k[1]:10.3f} {k[2]:10.3f}")
                        f.write(f"{t:14.4f} {k[0]:10.4f} {k[1]:10.4f} {k[2]:10.4f} {k[3]:10.4f} {k[4]:10.4f} {k[5]:10.4f}\n")
            
            print(f"Saved thermal conductivity data to {kappa_dat_path.name}")

        if args.plot:
            _plot_tc_results(ph3, output_dir, mesh=mesh)

    sys.stdout = orig_stdout
    
    # Post-processing Guide
    print("\n" + "="*60)
    print("--- Macer Phono3py TC workflow finished successfully! ---")
    print("\n[Post-processing Guide: How to use Phono3py CLI with these files]")
    print(f"1. Go to output directory: cd {output_dir}")
    
    if not args.save_hdf5:
        print("\n2. Create HDF5 force constants from the saved FORCES files:")
        if ph3.phonon_supercell is not None: # Dual supercell case
            print("   phono3py phono3py_disp.yaml --fc3 --fc2")
        else:
            print("   phono3py phono3py_disp.yaml --fc3")
        print("   (This will generate fc3.hdf5 and fc2.hdf5)")

    print("\n3. Perform advanced analysis (e.g. Kappa, Lifetime, JDOS):")
    mesh_str = ' '.join(map(str, mesh))
    temp_str = ' '.join(map(str, temperatures)) if len(temperatures) < 5 else f"{temperatures[0]} {temperatures[-1]}"
    
    print(f"   # Re-calculate Thermal Conductivity (using RTA or LBTE)")
    print(f"   phono3py-load --mesh {mesh_str} --br --ts {temp_str}")
    print(f"   phono3py-load --mesh {mesh_str} --lbte --ts {temp_str}")
    
    print(f"\n   # Extract Detailed Properties (Linewidth/Gamma, etc.)")
    print(f"   phono3py-load --mesh {mesh_str} --br --write-gamma")
    
    print(f"\n   # Calculate Joint Density of States (JDOS)")
    print(f"   phono3py-load --mesh {mesh_str} --jdos")
    
    if args.save_hdf5:
        print(f"\n   # Analyze Cumulative Thermal Conductivity (requires kappa hdf5)")
        print(f"   phono3py-kaccum kappa-m{mesh[0]}{mesh[1]}{mesh[2]}.hdf5 | tee kaccum.dat")

    print("\n" + "="*60 + "\n")


def add_tc_parser(subparsers):
    from macer import __version__
    parser = subparsers.add_parser(
        "thermal-conductivity",
        aliases=["tc"],
        help="Lattice Thermal Conductivity using Phono3py (LBTE/RTA)",
        description=MACER_LOGO + f"\nmacer_phonopy tc (v{__version__}): Calculate Lattice Thermal Conductivity using phono3py and MLFFs.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Input
    input_group = parser.add_argument_group("Input")
    input_group.add_argument("-p", "--poscar", required=False, default=None, help="Input crystal structure file (e.g., POSCAR).")
    input_group.add_argument("-c", "--cif", required=False, default=None, help="Input CIF file.")
    input_group.add_argument("--output-dir", help="Directory to save all output files.")

    # MLFF Settings
    mlff_group = parser.add_argument_group("MLFF Model Settings")
    mlff_group.add_argument("--ff", choices=ALL_SUPPORTED_FFS, default=DEFAULT_FF, help=f"Force field to use. (default: {DEFAULT_FF})")
    mlff_group.add_argument("--model", type=str, default=None, help="Path to the force field model file.")
    mlff_group.add_argument("--modal", type=str, default=None, help="Modal for certain force fields.")
    mlff_group.add_argument("--device", choices=["cpu", "mps", "cuda"], default=DEFAULT_DEVICE, help=f"Compute device. (default: {DEFAULT_DEVICE})")

    # Supercell & Relaxation
    sc_group = parser.add_argument_group("Supercell & Relaxation")
    sc_group.add_argument("--dim", type=int, nargs='+', required=False, help="FC3 supercell dimension (e.g., '2 2 2').")
    sc_group.add_argument("--dim-fc2", type=int, nargs='+', default=None, help="Optional FC2 supercell dimension (e.g., '4 4 4') for dual supercell calculation.")
    sc_group.add_argument("-l", "--length", type=float, default=12.0, help="Min length for auto-determining FC3 dim (Å). Default: 12.0.")
    sc_group.add_argument("-l2", "--length-fc2", type=float, default=25.0, help="Min length for auto-determining FC2 dim (Å). Default: 25.0.")
    sc_group.add_argument("--amplitude", type=float, default=0.03, help="Displacement amplitude (Å). Default: 0.03.")
    sc_group.add_argument('--pm', dest='is_plusminus', action='store_const', const='auto', default='auto', help='Use plus/minus displacements (default: auto).')
    sc_group.add_argument('--nodiag', dest='is_diagonal', action='store_false', default=True, help='Do not use diagonal displacements.')
    
    sc_group.add_argument("--isif", type=int, default=3, help="ISIF for initial relaxation (default: 3). Set 0 to skip.")
    sc_group.add_argument("--initial-fmax", type=float, default=0.005, help="Relaxation fmax (default: 0.005).")
    sc_group.add_argument("--initial-symprec", type=float, default=1e-5, help="Relaxation symprec (default: 1e-5).")
    sc_group.add_argument("--symprec", type=float, default=1e-5, help="Phono3py symmetry tolerance (default: 1e-5).")
    sc_group.add_argument("--mass", nargs='+', help="Specify atomic masses. Format: Symbol Mass Symbol Mass ...")

    # TC Settings
    tc_group = parser.add_argument_group("Thermal Conductivity Settings")
    tc_group.add_argument("--mesh", type=int, nargs=3, default=[11, 11, 11], help="Q-point mesh (default: 11 11 11).")
    
    method_group = tc_group.add_mutually_exclusive_group()
    method_group.add_argument("--br", "--rta", dest="method", action="store_const", const="br", default="br",
                             help="Use Relaxation Time Approximation (RTA) via 'br' mode. Fast, but may underestimate high-k materials. (default)")
    method_group.add_argument("--lbte", dest="method", action="store_const", const="lbte",
                             help="Solve the full Linearized Boltzmann Transport Equation (LBTE). Accurate for high-k materials, but slower and memory-intensive.")
    
    tc_group.add_argument("--temp", dest="temp", type=float, nargs='+', default=None, help="Specific temperatures (e.g., 300 400).")
    tc_group.add_argument("--temperature", dest="temp", type=float, nargs='+', help="Alias for --temp.") # Compatibility
    tc_group.add_argument("--ts", dest="temp", type=float, nargs='+', help="Alias for --temp (deprecated).") # Backward Compatibility
    tc_group.add_argument("--tmin", type=float, default=0, help="Min temperature (if --temp not set).")
    tc_group.add_argument("--tmax", type=float, default=1000, help="Max temperature (if --temp not set).")
    tc_group.add_argument("--tstep", type=float, default=10, help="Temperature step (if --temp not set).")
    tc_group.add_argument("--boundary-mfp", type=float, default=None, help="Boundary mean free path (micrometers?). Check units.")
    tc_group.add_argument("--no-plot", dest="plot", action="store_false", default=True, help="Disable plotting and data export (band.dat, dos.dat, etc.).")
    tc_group.add_argument("--no-save-hdf5", dest="save_hdf5", action="store_false", default=True, 
                             help="Disable saving heavy HDF5 files (kappa, fc2, fc3). (HDF5 saving is enabled by default)")

    parser.set_defaults(func=run_tc_workflow)
    return parser

    