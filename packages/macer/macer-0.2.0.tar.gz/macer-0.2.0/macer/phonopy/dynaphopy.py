import argparse
import sys
import os
import shutil
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm

from ase.io import read as ase_read
from ase.io import write as ase_write
from ase.io.trajectory import Trajectory
from ase.units import fs

import phonopy
from phonopy import Phonopy

# --- Import DynaPhoPy (Bundled preferred for NumPy 2.x compatibility) ---
try:
    import macer.externals.dynaphopy_bundled as dynaphopy
    import macer.externals.dynaphopy_bundled.interface.iofile as dynaphopy_io
    import macer.externals.dynaphopy_bundled.interface.iofile.trajectory_parsers as dynaphopy_parsers
    from macer.externals.dynaphopy_bundled.interface.phonopy_link import ForceConstants
    _HAS_DYNAPHOPY = True
except ImportError:
    try:
        import dynaphopy
        import dynaphopy.interface.iofile as dynaphopy_io
        import dynaphopy.interface.iofile.trajectory_parsers as dynaphopy_parsers
        from dynaphopy.interface.phonopy_link import ForceConstants
        _HAS_DYNAPHOPY = True
    except ImportError as e:
        _HAS_DYNAPHOPY = False

from macer.calculator.factory import get_calculator, ALL_SUPPORTED_FFS
from macer.defaults import DEFAULT_MODELS, resolve_model_path, DEFAULT_DEVICE, DEFAULT_FF
from macer.utils.logger import Logger
from macer.phonopy.phonon_band import run_macer_workflow
# from macer import __version__

MACER_LOGO = r"""
███╗   ███╗  █████╗   ██████╗ ███████╗ ██████╗
████╗ ████║ ██╔══██╗ ██╔════╝ ██╔════╝ ██╔══██╗
██╔████╔██║ ███████║ ██║      █████╗   ██████╔╝
██║╚██╔╝██║ ██╔══██║ ██║      ██╔══╝   ██╔══██╗
██║ ╚═╝ ██║ ██║  ██║ ╚██████╗ ███████╗ ██║  ██║
╚═╝     ╚═╝ ╚═╝  ╚═╝  ╚═════╝ ╚══════╝ ╚═╝  ╚═╝
ML-accelerated Atomic Computational Environment for Research
"""

def _resolve_model_path(ff: str, model_path: str | None) -> str | None:
    if model_path: return resolve_model_path(str(model_path))
    FFS_USING_MODEL_NAME = {"fairchem", "orb", "chgnet", "m3gnet"}
    default_model_name = DEFAULT_MODELS.get(ff)
    if default_model_name:
        if ff in FFS_USING_MODEL_NAME: return default_model_name
        else: return resolve_model_path(default_model_name)
    return None

def _plot_spectra_to_pdf(label, output_dir):
    """Helper to plot generated .out spectra files to PDF."""
    output_dir = Path(output_dir).resolve()
    files = {
        "Full": output_dir / f"power_spectrum_full_{label}.out",
        "Q-vector": output_dir / f"power_spectrum_q_vector_{label}.out",
        "Modes": output_dir / f"power_spectrum_phonon_modes_{label}.out"
    }
    
    plt.figure(figsize=(8, 6))
    plotted = False
    for spectrum_type, fpath in files.items():
        if fpath.exists():
            try:
                data = np.loadtxt(fpath)
                if data.ndim == 2 and data.shape[0] > 0:
                    plotted = True
                    # data[:, 0] is freq, data[:, 1:] are intensities
                    for i in range(1, data.shape[1]):
                        plt.plot(data[:, 0], data[:, i], label=f"{spectrum_type}" if i==1 else None, alpha=0.7)
            except Exception:
                continue
    
    if plotted:
        plt.title(f"Power Spectrum - {label}")
        plt.xlabel("Frequency (THz)")
        plt.ylabel("Intensity (Arb. Units)")
        plt.legend()
        plt.grid(True, linestyle=':', alpha=0.6)
        save_path = output_dir / f"power_spectrum_{label}.pdf"
        plt.savefig(save_path)
        print(f"    Saved power spectrum plot to: {save_path.name}")
    plt.close()

def _load_band_segmented(fpath):
    """Loads band.dat and splits it into multiple modes/segments."""
    if not os.path.exists(fpath): return []
    try:
        data = np.loadtxt(fpath)
        if data.size == 0: return []
        # Detect where distance resets (new mode starts)
        diffs = np.diff(data[:, 0])
        resets = np.where(diffs < -0.0001)[0] + 1
        return np.split(data, resets)
    except Exception:
        return []

def _run_md_for_dynaphopy(poscar_path, temp, supercell_matrix, calculator, output_dir, nsteps=10000, time_step=1.0, equil_steps=2000, 
                          thermostat='nose-hoover', ttau=0, mass_map=None):
    """
    Fixed-volume MD runner (NVT) saving results directly with temperature labels.
    """
    output_dir = Path(output_dir).resolve()
    temp_label = f"T{temp}K"
    print(f"  Running MD (NVT) at {temp} K for {nsteps} steps (dt={time_step} fs)...")
    atoms = ase_read(str(poscar_path), format='vasp')
    
    if mass_map:
        for sym, m in mass_map.items():
            indices = [atom.index for atom in atoms if atom.symbol == sym]
            if indices:
                new_masses = atoms.get_masses()
                new_masses[indices] = m
                atoms.set_masses(new_masses)

    sc_mat = np.array(supercell_matrix)
    if sc_mat.ndim == 1:
        if sc_mat.size == 3: sc_mat = np.diag(sc_mat)
        elif sc_mat.size == 9: sc_mat = sc_mat.reshape(3, 3)
    
    from ase.build import make_supercell
    atoms = make_supercell(atoms, sc_mat)
    atoms.calc = calculator

    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary, ZeroRotation
    MaxwellBoltzmannDistribution(atoms, temperature_K=temp, force_temp=True)
    Stationary(atoms)
    ZeroRotation(atoms)

    ttau_val = ttau if ttau > 0 else 40.0 * time_step
    timestep_ase = time_step * fs

    def create_dynamics(atoms_obj):
        if thermostat == 'langevin':
            from ase.md.langevin import Langevin
            return Langevin(atoms_obj, timestep_ase, temperature_K=temp, friction=1.0/(ttau_val*fs))
        else:
            from ase.md.nvtberendsen import NVTBerendsen
            return NVTBerendsen(atoms_obj, timestep_ase, temperature_K=temp, taut=ttau_val*fs)

    if equil_steps > 0:
        dyn_eq = create_dynamics(atoms)
        with tqdm(total=equil_steps, desc="    Equilibration") as pbar:
            def update_pbar_eq(): pbar.update(10)
            dyn_eq.attach(update_pbar_eq, interval=10)
            dyn_eq.run(equil_steps)
    
    print(f"    Production run for {nsteps} steps...")
    dyn_prod = create_dynamics(atoms)
    
    # Define exact paths
    traj_filename = f"md_{temp_label}.traj"
    xdatcar_filename = f"XDATCAR_{temp_label}"
    vel_filename = f"velocities_{temp_label}.npy"
    
    traj_path = output_dir / traj_filename
    xdatcar_path = output_dir / xdatcar_filename
    vel_path = output_dir / vel_filename

    traj = Trajectory(str(traj_path), 'w', atoms)
    dyn_prod.attach(traj.write, interval=1)

    with tqdm(total=nsteps, desc="    Production   ") as pbar:
        def update_pbar(): pbar.update(10)
        dyn_prod.attach(update_pbar, interval=10)
        dyn_prod.run(nsteps)
    
    frames = []
    velocities = []
    r_traj = Trajectory(str(traj_path), 'r')
    for a in r_traj:
        a.wrap()
        frames.append(a)
        velocities.append(a.get_velocities() * (fs * 1000.0))
    
    # Manual XDATCAR writing to handle Selective Dynamics flags correctly
    with open(str(xdatcar_path), 'w') as xdat_f:
        all_symbols = atoms.get_chemical_symbols()
        species = list(dict.fromkeys(all_symbols))
        counts = [all_symbols.count(spec) for spec in species]
        
        # Header (only once for NVT)
        xdat_f.write(" ".join(species) + "\n")
        xdat_f.write("    1.000000\n")
        for vec in atoms.cell:
            xdat_f.write(f"     {vec[0]:11.6f} {vec[1]:11.6f} {vec[2]:11.6f}\n")
        xdat_f.write(" " + " ".join(f"{s:>2}" for s in species) + "\n")
        xdat_f.write(" " + " ".join(f"{c:16d}" for c in counts) + "\n")
        
        from ase.constraints import FixAtoms
        fix_atoms = [c for c in atoms.constraints if isinstance(c, FixAtoms)]
        has_selective = len(fix_atoms) > 0
        if has_selective:
            fixed_mask = np.zeros(len(atoms), dtype=bool)
            for c in fix_atoms:
                fixed_mask[c.index] = True
        
        for idx, a in enumerate(frames):
            xdat_f.write(f"Direct configuration= {idx+1:5d}\n")
            scaled_pos = a.get_scaled_positions(wrap=False)
            for i, s in enumerate(scaled_pos):
                if has_selective:
                    flag = "  F  F  F" if fixed_mask[i] else "  T  T  T"
                    xdat_f.write(f"   {s[0]:.8f}   {s[1]:.8f}   {s[2]:.8f}{flag}\n")
                else:
                    xdat_f.write(f"   {s[0]:.8f}   {s[1]:.8f}   {s[2]:.8f}\n")
    
    np.save(str(vel_path), np.array(velocities))
    print(f"    MD results saved: {xdatcar_filename}, {vel_filename}")
    return xdatcar_path, vel_path

def run_dynaphopy_workflow(args):
    """Refactored workflow using macer_phonopy pb as engine."""
    if not _HAS_DYNAPHOPY:
        print("Error: 'dynaphopy' package is not installed. Please run 'pip install dynaphopy'.")
        return

    if args.poscar is None:
        print("Error: -p/--poscar argument is required.")
        sys.exit(1)

    from macer import __version__
    print(f"--- macer phonopy ft (v{__version__}): Finite-Temperature Renormalization ---")
    input_poscar_path = Path(args.poscar).resolve()
    
    if args.output_dir:
        base_output_dir = Path(args.output_dir).resolve()
    else:
        base_output_dir = input_poscar_path.parent / f"finite-phonon-{input_poscar_path.stem}"

    if not base_output_dir.exists():
        output_dir = base_output_dir
        output_dir.mkdir(parents=True)
    else:
        i = 1
        while True:
            output_dir = Path(f"{base_output_dir}-NEW{i:03d}")
            if not output_dir.exists():
                output_dir.mkdir(parents=True)
                break
            i += 1
    
    print(f"Results will be saved in: {output_dir}")

    log_file = output_dir / "macer_finite_temperature.log"
    orig_stdout = sys.stdout

    with Logger(str(log_file)) as lg:
        sys.stdout = lg
        
        # --- PHASE 1: Harmonic Foundation (Standard PB) ---
        print("\n" + "="*60)
        print(" PHASE 1: Harmonic Foundation (Standard PB)")
        print("="*60)
        
        run_macer_workflow(
            input_path=input_poscar_path,
            min_length=args.min_length,
            displacement_distance=0.01,
            is_plusminus=False,
            is_diagonal=True,
            macer_ff=args.ff,
            macer_model_path=Path(args.model) if args.model else None,
            macer_device=args.device,
            macer_modal=args.modal,
            output_prefix="harmonic",
            output_dir_arg=str(output_dir),
            dim_override=" ".join(map(str, args.dim)) if args.dim else None,
            mass_map={args.mass[i]: float(args.mass[i+1]) for i in range(0, len(args.mass), 2)} if args.mass else None
        )
        
        os.chdir(output_dir)
        ph_harmonic = phonopy.load("phonopy_disp-harmonic.yaml")
        supercell_matrix = ph_harmonic.supercell_matrix
        harmonic_fc = ph_harmonic.force_constants

        # Prepare calculator for MD
        model_path = _resolve_model_path(args.ff, args.model)
        calculator = get_calculator(ff_name=args.ff, model_path=model_path, device=args.device, modal=args.modal)

        # --- PHASE 2: Finite-Temperature Loop ---
        band_files_for_comparison = ["band-harmonic.dat"]
        comparison_labels = ["Harmonic (0K)"]

        for temp in args.temp:
            t_label = f"T{temp}K"
            print("\n" + "="*60)
            print(f" PHASE 2: Processing Temperature {temp} K")
            print("="*60)

            # Step 2.1: Run MD
            xdat_p, vel_p = _run_md_for_dynaphopy(
                "POSCAR", temp, supercell_matrix, calculator, Path("."), 
                nsteps=args.md_steps, equil_steps=args.md_equil, time_step=args.time_step
            )
            
            # Step 2.2: Renormalization (DynaPhoPy Engine)
            print(f"  Performing peak-fitting renormalization for {temp} K...")
            print(f"  Algorithm: {args.psm} (1=MEM, 2=FFT/Direct)")
            
            # Rewriting VASP 4 POSCAR for DynaPhoPy structure reading compatibility
            clean_atoms = ase_read("POSCAR", format="vasp")
            ase_write("POSCAR_clean", clean_atoms, format="vasp", vasp5=False)
            
            structure = dynaphopy_io.read_from_file_structure_poscar("POSCAR_clean")
            
            # CRITICAL: Manually inject the supercell expansion into the structure object
            # This ensures robustness even if DynaPhoPy's auto-detection fails.
            structure._supercell_matrix = np.array(supercell_matrix) 
            structure.set_supercell_matrix(np.array(supercell_matrix))
            
            if args.mass:
                m_list = structure.get_masses()
                symbols = structure.get_atomic_types()
                m_map = {args.mass[i]: float(args.mass[i+1]) for i in range(0, len(args.mass), 2)}
                for i, s in enumerate(symbols):
                    if s in m_map: m_list[i] = m_map[s]
                structure.set_masses(m_list)

            # Explicitly ensure supercell_matrix is a 3x3 diagonal array for DynaPhoPy
            sc_mat_3x3 = np.array(supercell_matrix)
            structure.set_force_constants(ForceConstants(harmonic_fc, supercell=sc_mat_3x3))
            
            # Ensure DynaPhoPy uses the full unit cell as primitive to avoid shape mismatch with FCs
            structure.set_primitive_matrix(np.identity(3))
            
            trajectory = dynaphopy_parsers.read_VASP_XDATCAR(str(xdat_p), structure, initial_cut=1, time_step=args.time_step/1000.0)
            trajectory.velocity = np.load(str(vel_p))[1:].astype(complex)
            
            # Also ensure the structure within trajectory has identity primitive matrix
            trajectory.structure.set_primitive_matrix(np.eye(3))
            
            qp = dynaphopy.Quasiparticle(trajectory)
            
            # Select Algorithm
            qp.select_power_spectra_algorithm(args.psm)
            if args.psm == 1:
                # Set MEM coefficients only if using MEM
                print(f"    Setting MEM coefficients: {args.mem}")
                qp.set_number_of_mem_coefficients(args.mem)
            
            # Set FC Symmetrization (Default: True)
            if not args.no_fcsymm:
                try:
                    qp.parameters.degenerate = True
                    print("    Force constant symmetrization enabled.")
                except Exception as e:
                    print(f"    Warning: Could not enable FC symmetrization: {e}")
                    qp.parameters.degenerate = False
            else:
                qp.parameters.degenerate = False
                print("    Force constant symmetrization disabled by user.")

            if args.qpoint:
                print(f"    Setting reduced q-vector for projection: {args.qpoint}")
                qp.set_reduced_q_vector(args.qpoint)

            # Use local string for FC path
            ft_fc_filename = f"FORCE_CONSTANTS_{t_label}"
            qp.write_renormalized_constants(filename=ft_fc_filename)
            
            # --- POWER SPECTRUM OUTPUTS ---
            print(f"    Saving power spectrum data for {temp} K...")
            qp.write_power_spectrum_full(f"power_spectrum_full_{t_label}.out")
            qp.write_power_spectrum_wave_vector(f"power_spectrum_q_vector_{t_label}.out")
            qp.write_power_spectrum_phonon(f"power_spectrum_phonon_modes_{t_label}.out")
            
            # Plot spectrum to PDF
            _plot_spectra_to_pdf(t_label, Path("."))

            if args.save_quasiparticles:
                qp.write_quasiparticles_data(f"quasiparticles_{t_label}.yaml")

            # Step 2.3: Standardized Visualization (PB Engine)
            print(f"  Generating standardized plots for {temp} K...")
            run_macer_workflow(
                input_path=Path("POSCAR"),
                min_length=args.min_length,
                displacement_distance=0.01,
                is_plusminus=False,
                is_diagonal=True,
                macer_ff=args.ff,
                macer_model_path=Path(args.model) if args.model else None,
                macer_device=args.device,
                macer_modal=args.modal,
                output_prefix=t_label,
                output_dir_arg=str(output_dir),
                dim_override=" ".join(map(str, args.dim)) if args.dim else None,
                read_fc_path=Path(ft_fc_filename),
                skip_initial_relax=True
            )
            
            band_files_for_comparison.append(f"band-{t_label}.dat")
            comparison_labels.append(f"{temp} K")

        # --- PHASE 3: Comparison Plot ---
        print("\n" + "="*60)
        print(" PHASE 3: Generating Comparison Plot")
        print("="*60)
        
        plt.figure(figsize=(10, 7))
        colors_map = plt.cm.plasma(np.linspace(0, 0.8, len(band_files_for_comparison)))
        
        for i, (fpath, label) in enumerate(zip(band_files_for_comparison, comparison_labels)):
            modes = _load_band_segmented(fpath)
            if not modes: continue
            
            c = colors_map[i] if i > 0 else 'black'
            s = '-' if i > 0 else '--'
            a = 0.8 if i > 0 else 0.5
            
            for m_idx, mode_data in enumerate(modes):
                plt.plot(mode_data[:, 0], mode_data[:, 1], color=c, 
                         linestyle=s, alpha=a,
                         label=label if (m_idx == 0) else "")
        
        plt.title(f"Phonon Temperature Dependence: {input_poscar_path.name}")
        plt.ylabel("Frequency (THz)")
        plt.legend(loc='upper right')
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.savefig("band_comparison.pdf")
        print("Saved unified comparison to: band_comparison.pdf")

        # --- Power Spectrum Comparison ---
        print("\n  Generating Power Spectrum Comparison Plot...")
        plt.figure(figsize=(10, 7))
        
        # Only plot finite temperatures (skip harmonic/0K)
        temp_labels = comparison_labels[1:] 
        temp_colors = plt.cm.viridis(np.linspace(0, 1, len(temp_labels)))
        
        plotted_ps = False
        for i, label in enumerate(temp_labels):
            # label format is "300 K", but file format is "T300.0K" or "T300K"
            # We reconstruct the file name based on the known temperature list 'args.temp'
            # to be safe, or just strip spaces and prepend T.
            
            # Use the loop index to get the exact temperature float from args.temp
            # args.temp corresponds to temp_labels indices
            current_temp = args.temp[i]
            file_label = f"T{current_temp}K"
            
            ps_file = f"power_spectrum_full_{file_label}.out" 
            if not Path(ps_file).exists():
                 # Try fallback format just in case
                 ps_file = f"power_spectrum_full_{label.replace(' ', '')}.out"

            if Path(ps_file).exists():
                try:
                    data = np.loadtxt(ps_file)
                    if data.ndim == 2 and data.shape[0] > 0:
                        plt.plot(data[:, 0], data[:, 1], color=temp_colors[i], label=label, alpha=0.8)
                        plotted_ps = True
                except Exception as e:
                    print(f"    Warning: Could not plot power spectrum for {label}: {e}")
            else:
                print(f"    Warning: Power spectrum file not found: {ps_file}")
        
        if plotted_ps:
            plt.title(f"Power Spectrum Evolution: {input_poscar_path.name}")
            plt.xlabel("Frequency (THz)")
            plt.ylabel("Intensity (Arb. Units)")
            plt.legend()
            plt.grid(True, linestyle=':', alpha=0.6)
            plt.savefig("power_spectrum_comparison.pdf")
            print("Saved power spectrum comparison to: power_spectrum_comparison.pdf")
        else:
            print("    No power spectrum data found to compare.")
        plt.close()

        # --- Post-Processing: Generate DynaPhoPy Input & Commands ---
        print("\n  Generating input_dynaphopy and command instructions...")
        
        # 1. Read Band Path and DIM from band-harmonic.conf
        band_conf_path = Path("band-harmonic.conf")
        band_str_list = []
        extracted_dim = None

        if band_conf_path.exists():
            with open(band_conf_path, 'r') as f:
                for line in f:
                    if line.startswith("DIM ="):
                        # Format: DIM = 2 0 0 0 2 0 0 0 2
                        try:
                            dim_values = list(map(int, line.split("=")[1].strip().split()))
                            if len(dim_values) == 9:
                                extracted_dim = dim_values
                            elif len(dim_values) == 3: # Just in case it's stored as diagonal
                                extracted_dim = [dim_values[0], 0, 0, 0, dim_values[1], 0, 0, 0, dim_values[2]]
                        except:
                            pass # Keep default if parsing fails

                    if line.startswith("BAND ="):
                        # Format: BAND = 0.0 0.0 0.0  0.5 0.0 0.5  ...
                        # Need to split into pairs for input_dynaphopy BANDS section
                        raw_points = line.split("=")[1].strip().split()
                        # Group by 3 to get points
                        points = [raw_points[i:i+3] for i in range(0, len(raw_points), 3)]
                        # Construct paths: (p1, p2), (p2, p3), ...
                        # But wait, phonopy BAND format is p1 p2 p3 p4 ... -> path p1-p2, p3-p4 ?
                        # Actually phonopy's band.conf usually defines connected paths.
                        # If band_paths in phonopy is [[A, B, C], [D, E]], the BAND string flattens it.
                        # However, for input_dynaphopy, we need explicit start-end pairs.
                        # Let's assume a continuous path for simplicity or just pairwise connected.
                        # A standard phonopy band.conf BAND line usually implies a continuous path unless separated by comma?
                        # In Macer's generation, it's a space-separated list of points.
                        # Let's link them sequentially: 0-1, 1-2, 2-3...
                        # DynaPhoPy expects: X1 Y1 Z1  X2 Y2 Z2
                        for i in range(len(points) - 1):
                            start = ", ".join(points[i])
                            end = ", ".join(points[i+1])
                            band_str_list.append(f"{start:<30}  {end}")
        
        # 2. Write input_dynaphopy
        with open("input_dynaphopy", "w") as f:
            f.write(f"STRUCTURE FILE POSCAR\nPOSCAR\n\n") # Using the initial POSCAR or relaxed? DynaPhoPy usually needs cell info.
            # f.write(f"FORCE CONSTANTS\nphonopy_disp-harmonic.yaml\n\n") # Or use FORCE_CONSTANTS_harmonic if written
            # Note: DynaPhoPy can read FC from phonopy.yaml or FORCE_CONSTANTS. 
            # We generated FORCE_CONSTANTS (via run_macer_workflow -> phonopy save).
            # Let's point to 'FORCE_CONSTANTS' (which is the standard phonopy name)
            # Check if FORCE_CONSTANTS exists, if not try phonopy_disp-harmonic.yaml
            if Path("FORCE_CONSTANTS").exists():
                 f.write(f"FORCE CONSTANTS\nFORCE_CONSTANTS\n\n")
            else:
                 f.write(f"FORCE CONSTANTS\nphonopy_disp-harmonic.yaml\n\n")

            f.write("PRIMITIVE MATRIX\n")
            f.write("1.0 0.0 0.0\n0.0 1.0 0.0\n0.0 0.0 1.0\n\n")
            
            f.write("SUPERCELL MATRIX\n")
            if args.dim:
                if len(args.dim) == 3:
                    d = args.dim
                    f.write(f"{d[0]} 0 0\n0 {d[1]} 0\n0 0 {d[2]}\n")
                elif len(args.dim) == 9:
                    d = args.dim
                    f.write(f"{d[0]} {d[1]} {d[2]}\n{d[3]} {d[4]} {d[5]}\n{d[6]} {d[7]} {d[8]}\n")
            elif extracted_dim:
                d = extracted_dim
                f.write(f"{d[0]} {d[1]} {d[2]}\n{d[3]} {d[4]} {d[5]}\n{d[6]} {d[7]} {d[8]}\n")
            else:
                # Fallback if dim wasn't passed (auto-detect not easily available here without parsing logs)
                # But run_macer_workflow calculates it. For now, assume 1 1 1 if not provided?
                # Actually, in FT workflow, args.dim is either provided or we should rely on what was used.
                # If args.dim is None, we might have an issue generating correct input_dynaphopy.
                # But for now let's write Identity if unknown.
                f.write("1 0 0\n0 1 0\n0 0 1\n") 
            f.write("\n")
            
            f.write("MESH PHONOPY\n20 20 20\n\n") # Default mesh
            
            if band_str_list:
                f.write("BANDS\n")
                for b in band_str_list:
                    f.write(f"{b}\n")
                f.write("\n")

        print("    Generated: input_dynaphopy")

        # 3. Write command-dynaphopy.txt and print to screen
        cmd_file_content = []
        time_step_ps = args.time_step / 1000.0
        
        for temp in args.temp:
            t_label = f"T{temp}K"
            xdatcar_file = f"XDATCAR_{t_label}"
            
            cmd_file_content.append(f"# --- Temperature: {temp} K ---")
            cmd_file_content.append(f"# 1. Interactive Mode (Check renormalized bands)")
            cmd_file_content.append(f"macer util dynaphopy input_dynaphopy {xdatcar_file} -ts {time_step_ps} --normalize_dos -i")
            cmd_file_content.append(f"\n# 2. Batch Mode (Save all data)")
            cmd_file_content.append(f"macer util dynaphopy input_dynaphopy {xdatcar_file} -ts {time_step_ps} -sdata -thm --normalize_dos -sfc FORCE_CONSTANTS_renorm_{t_label}")
            cmd_file_content.append("-" * 60 + "\n")

        with open("command-dynaphopy.txt", "w") as f:
            f.write("\n".join(cmd_file_content))
        
        print("    Generated: command-dynaphopy.txt")
        print("\n" + "="*60)
        print(" SUGGESTED POST-PROCESSING COMMANDS:")
        print("="*60)
        print("\n".join(cmd_file_content))
        print("="*60)

    sys.stdout = orig_stdout
    print(f"\n--- Finite-Temperature Workflow Completed. Results in: {output_dir} ---")

def add_dynaphopy_parser(subparsers):
    from macer import __version__
    parser = subparsers.add_parser(
        "finite-temperature",
        aliases=["ft"],
        help="Finite-temperature phonon renormalization (MD power spectrum fitting)",
        description=f"macer phonopy ft (v{__version__}): Anharmonic phonon renormalization via DynaPhoPy.\nCalculates frequency shifts and linewidths by fitting MD velocity power spectra to quasiparticle spectral functions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
--------------------------------------------------------------------------------
WORKFLOW OVERVIEW:
  1. Harmonic Calculation (0K): Runs standard phonon workflow to get base force constants.
  2. MD Simulation (NVT): Runs Molecular Dynamics at specified temperature(s) using the MLFF.
  3. Renormalization: Uses DynaPhoPy to extract renormalized force constants from MD trajectories.
  4. Analysis: Generates finite-temperature phonon bands and power spectra.

ALGORITHMS (PSM):
  - FFT (Default, --psm 2): Robust method without information loss. Recommended for shorter trajectories.
  - MEM (Maximum Entropy, --psm 1): Fast approximation providing smoother spectra. Easier to fit but requires longer trajectories for accuracy.

EXAMPLES:
  1. Basic usage for Aluminum at 300K:
     macer phonopy ft -p POSCAR_Al -T 300 --dim 2 2 2

  2. Run for multiple temperatures (300K, 800K) with increased MD steps:
     macer phonopy ft -p POSCAR_Si -T 300 800 --md-steps 20000 --md-equil 5000

  3. Use a specific GPU-accelerated model (e.g., MACE) on CUDA:
     macer phonopy ft -p POSCAR_GaN -T 300 --ff mace --device cuda

OUTPUTS:
  - finite-phonon-{POSCAR}/: Contains all results.
  - band-{T}K.dat: Phonon band structure data.
  - power_spectrum_*.pdf: Power spectrum plots.
  - band_comparison.pdf: Comparison of bands across temperatures.
--------------------------------------------------------------------------------
"""
    )

    # General & Input
    input_group = parser.add_argument_group('General & Input')
    input_group.add_argument("-p", "--poscar", help="Input POSCAR file.")
    input_group.add_argument("-c", "--cif", help="Input CIF file.")
    input_group.add_argument("--output-dir", help="Directory to save output files.")

    # Simulation Settings
    sim_group = parser.add_argument_group('Temperature & MD Settings')
    sim_group.add_argument("-T", "--temp", type=float, nargs='+', help="Temperatures (K).")
    sim_group.add_argument("--md-steps", type=int, default=8000, help="Production steps (default: 8000).")
    sim_group.add_argument("--md-equil", type=int, default=2000, help="Equilibration steps (default: 2000).")
    sim_group.add_argument("--time-step", type=float, default=1.0, help="Time step in fs (default: 1.0).")
    sim_group.add_argument("--thermostat", choices=["nose-hoover", "langevin"], default="nose-hoover", help="Thermostat (default: nose-hoover).")
    sim_group.add_argument("--ttau", type=float, default=0, help="Thermostat time constant in fs (default: 0).")

    # Structure Settings
    struct_group = parser.add_argument_group('Supercell & Structure Settings')
    struct_group.add_argument("--dim", type=int, nargs='+', help="Explicit supercell dimension.")
    struct_group.add_argument("-l", "--min-length", "--length", dest="min_length", type=float, default=15.0, help="Minimum supercell length in Å (default: 15.0).")
    struct_group.add_argument("--no-supercell", action="store_true", help="Force dim=1 1 1.")
    struct_group.add_argument("--mass", nargs='+', help="Atomic mass override: Symbol Mass ...")

    # MLFF Settings
    mlff_group = parser.add_argument_group('MLFF Model Settings')
    mlff_group.add_argument("--ff", choices=ALL_SUPPORTED_FFS, default=DEFAULT_FF, help=f"Force field to use (default: {DEFAULT_FF}).")
    mlff_group.add_argument("--model", help="Path to MLFF model.")
    mlff_group.add_argument("--device", default=DEFAULT_DEVICE, help=f"Device (default: {DEFAULT_DEVICE}).")
    mlff_group.add_argument("--modal", help="Modal for specific models.")

    # DynaPhoPy Settings
    dp_group = parser.add_argument_group('DynaPhoPy Settings')
    dp_group.add_argument("--psm", type=int, default=2, help="Power spectrum algorithm (1: MEM [Approx/Smooth], 2: FFT [Direct/Robust]). Default: 2.")
    dp_group.add_argument("--mem", type=int, default=1000, help="MEM coefficients (default: 1000). Only used if --psm 1.")
    dp_group.add_argument("--qpoint", type=float, nargs=3, help="Q-point for power spectrum projection (3 floats).")
    dp_group.add_argument("--save-quasiparticles", action="store_true", help="Save shifts/linewidths to YAML.")
    dp_group.add_argument("--read-fc", help="Read existing harmonic FORCE_CONSTANTS.")
    dp_group.add_argument("--no-fcsymm", action="store_true", help="Disable force constant symmetrization.")

    parser.set_defaults(func=run_dynaphopy_workflow)
    return parser
