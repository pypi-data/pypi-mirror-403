import argparse
import os
import sys
import csv
import numpy as np
import time
import shutil
from pathlib import Path
from tqdm import tqdm

from ase.io import read, write
from ase.io.trajectory import Trajectory
from ase.md.npt import NPT
from ase.md.langevin import Langevin
from ase.build import make_supercell
import ase.units as u

try:
    from ase.md.nose_hoover_chain import NoseHooverChainNVT as NVT_NHC
except ImportError:
    NVT_NHC = None
try:
    from ase.md.nvtberendsen import NVTBerendsen as NVT_Ber
except ImportError:
    NVT_Ber = None
try:
    from ase.md.nptberendsen import NPTBerendsen as NPT_Ber
except ImportError:
    NPT_Ber = None

from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary, ZeroRotation
from ase.geometry import cellpar_to_cell

from macer.calculator.factory import get_calculator, get_available_ffs, ALL_SUPPORTED_FFS
from macer.defaults import DEFAULT_MODELS, DEFAULT_DEVICE, DEFAULT_FF, resolve_model_path, _model_root
from macer.utils.logger import Logger
# from macer import __version__  <-- Moved inside function

# Constants
EV_A3_TO_GPa = 160.21766208
KB_EV_K = 8.617333262145e-5 # Boltzmann constant in eV/K
KJ_MOL_TO_EV = 0.0103642697 # 1 kJ/mol in eV/unit-cell
J_K_MOL_TO_EV_K = 0.0000103642697 # 1 J/mol*K in eV/K/unit-cell

# Global parser storage
_GIBBS_PARSER = None

def get_gibbs_parser(subparsers):
    global _GIBBS_PARSER
    parser = subparsers.add_parser(
        "gibbs",
        help="Calculate Gibbs Free Energy vs Temperature via Temperature Integration (NPT MD)",
        description="Calculate Gibbs Free Energy vs Temperature via Temperature Integration (NPT MD).",
        epilog="""
Examples:
  # 1. Standard Run (Recommended for ScF3 NTE reproduction)
  #    - 2x2x2 Supercell, 100K to 1000K every 50K
  #    - Sufficient sampling (50ps production after 10ps equil)
  macer gibbs -p POSCAR --dim 2 2 2 --temp-start 100 --temp-end 1000 --temp-step 50 --nsteps 50000 --equil-steps 10000

  # 2. Quick Test (Fast check of workflow)
  #    - Coarse grid (200K step), short run (2ps)
  macer gibbs -p POSCAR --dim 2 2 2 --temp-start 100 --temp-end 500 --temp-step 200 --nsteps 2000 --equil-steps 500

  # 3. Absolute Gibbs Energy (Hybrid QHA + MD)
  #    Step A: Generate reference data using Phonopy QHA
  #      macer phonopy qha -p POSCAR --dim 2 2 2 --tmax 300
  #      (This creates 'thermal_properties.yaml' with low-T free energy)
  #
  #    Step B: Run MD integration anchored to the QHA reference
  #      macer gibbs -p POSCAR --dim 2 2 2 --qha-ref thermal_properties.yaml --temp-start 10 --temp-end 1000

  # 4. NVT Mode (Fixed Volume)
  #    - Calculates Helmholtz Free Energy change (F) at fixed volume
  macer gibbs -p POSCAR --ensemble nvt --temp-start 300 --temp-end 1000
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Input
    input_group = parser.add_argument_group("Input")
    input_group.add_argument("-p", "--poscar", required=False, help="Input structure file (POSCAR).")
    input_group.add_argument("--qha-ref", help="Optional: Path to thermal_properties.yaml (from phonopy) for absolute G reference.")

    # Temperature Scan
    temp_group = parser.add_argument_group("Temperature Scan Settings")
    temp_group.add_argument("--temp-start", type=float, default=100.0, help="Starting temperature (K). Default: 100.0")
    temp_group.add_argument("--temp-end", type=float, default=1000.0, help="Ending temperature (K). Default: 1000.0")
    temp_group.add_argument("--temp-step", type=float, default=50.0, help="Temperature step (K). Default: 50.0")
    temp_group.add_argument("--temps", type=float, nargs='+', help="Specific temperatures to sample. Overrides scan settings.")

    # MD Settings
    md_group = parser.add_argument_group("MD Settings")
    md_group.add_argument("--nsteps", type=int, default=50000, help="Total MD steps per temperature. Default: 50000")
    md_group.add_argument("--equil-steps", type=int, default=10000, help="Equilibration steps to discard per temperature. Default: 10000")
    md_group.add_argument("--tstep", type=float, default=1.0, help="Time step (fs). Default: 1.0")
    md_group.add_argument("--ensemble", choices=["npt", "nvt"], default="npt", help="MD ensemble. Default: npt")
    md_group.add_argument("--press", type=float, default=0.0, help="External pressure (GPa). Default: 0.0")
    md_group.add_argument("--thermostat", choices=["langevin", "nose-hoover", "berendsen"], default="langevin", help="Thermostat algorithm. Default: langevin")
    md_group.add_argument("--ttau", type=float, default=100.0, help="Thermostat time constant (fs). Default: 100.0")
    md_params_group = md_group.add_mutually_exclusive_group() # Placeholder for ptau/friction logic
    md_params_group.add_argument("--ptau", type=float, default=1000.0, help="Barostat time constant (fs). Default: 1000.0")
    md_params_group.add_argument("--friction", type=float, default=1.0, help="Langevin friction (ps^-1). Default: 1.0")
    md_group.add_argument("--dim", type=int, nargs='+', help="Supercell dimension (e.g. '2 2 2').")

    # MLFF Settings
    mlff_group = parser.add_argument_group("MLFF Model Settings")
    mlff_group.add_argument("--ff", choices=ALL_SUPPORTED_FFS, default=DEFAULT_FF, help="Force field to use.")
    mlff_group.add_argument("--model", help="Path to MLFF model file.")
    mlff_group.add_argument("--device", choices=["cpu", "mps", "cuda"], default=DEFAULT_DEVICE, help=f"Compute device (default: {DEFAULT_DEVICE}).")

    # Output
    out_group = parser.add_argument_group("Output")
    out_group.add_argument("--output-dir", help="Directory for output files.")
    out_group.add_argument("--prefix", default="gibbs", help="Prefix for output files. Default: gibbs")

    parser.set_defaults(func=run_gibbs_workflow)
    _GIBBS_PARSER = parser
    return parser

def run_gibbs_workflow(args):
    # Check for required POSCAR (manual check since required=False in parser)
    if args.poscar is None:
        print("Error: -p/--poscar argument is required for Gibbs workflow.")
        # If running via 'macer md --gibbs', the main help might be more useful, but simple error is fine.
        sys.exit(1)

    from macer import __version__
    print(f"--- macer gibbs (v{__version__}): Starting Free Energy Workflow ---")

    # 1. Setup & Directories
    input_path = Path(args.poscar).resolve()
    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        output_dir = input_path.parent / f"gibbs_{input_path.stem}_mlff={args.ff}"
    
    i = 1
    base_output_dir = output_dir
    while output_dir.exists():
        output_dir = Path(f"{base_output_dir}-NEW{i:03d}")
        i += 1
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save input structure for record
    shutil.copy(input_path, output_dir / "POSCAR-input")
    
    log_file = output_dir / f"{args.prefix}.log"
    csv_file = output_dir / f"{args.prefix}_results.csv"

    # 2. Temperature List
    if args.temps:
        temp_list = sorted(args.temps)
    else:
        # Use args.temp as start, args.temp_end as end
        start_t = args.temp
        end_t = args.temp_end
        if end_t is None: end_t = 1000.0 # Fallback default
        
        temp_list = np.arange(start_t, end_t + args.temp_step/2, args.temp_step).tolist()
    
    if len(temp_list) < 2:
        print("Error: At least two temperatures are required for integration.")
        sys.exit(1)

    # 3. Reference Energy & Entropy (QHA)
    g_ref_val = None
    s_ref_val = None
    t_ref = temp_list[0]
    
    if args.qha_ref:
        try:
            import yaml
            with open(args.qha_ref, 'r') as f:
                qha_data = yaml.safe_load(f)
            
            # Find closest temperature or interpolate
            qha_temps = np.array([p['temperature'] for p in qha_data['thermal_properties']])
            qha_free_energies = np.array([p['free_energy'] for p in qha_data['thermal_properties']])
            qha_entropies = np.array([p['entropy'] for p in qha_data['thermal_properties']])
            
            # Use linear interpolation for exact matching
            g_ref_raw = float(np.interp(t_ref, qha_temps, qha_free_energies))
            s_ref_raw = float(np.interp(t_ref, qha_temps, qha_entropies))
            
            # Convert units: Phonopy (kJ/mol, J/K/mol) -> Macer (eV, eV/K)
            g_ref_val = g_ref_raw * KJ_MOL_TO_EV
            s_ref_val = s_ref_raw * J_K_MOL_TO_EV_K
            
            print(f"Loaded QHA Reference @ {t_ref} K (Converted from kJ/mol):")
            print(f"  G = {g_ref_val:.6f} eV")
            print(f"  S = {s_ref_val:.6f} eV/K")
            
        except Exception as e:
            print(f"Warning: Failed to load QHA reference from {args.qha_ref}: {e}")

    # 4. Logger Start
    orig_stdout = sys.stdout
    with Logger(str(log_file)) as lg:
        sys.stdout = lg
        print(f"--- Macer Gibbs Free Energy Workflow ---")
        print(f"Command: {' '.join(sys.argv)}")
        print(f"Input POSCAR: {input_path}")
        print(f"Force Field: {args.ff}")
        print(f"Device: {args.device}")
        print(f"Ensemble: {args.ensemble.upper()}")
        print(f"Temperature Range: {temp_list[0]} to {temp_list[-1]} K ({len(temp_list)} steps)")
        print(f"Steps per T: {args.nsteps} (Equil: {args.equil_steps})")

        # 5. Initialize Atoms & Calculator
        atoms = read(str(input_path))
        if args.dim:
            if len(args.dim) == 3: sc_matrix = np.diag(args.dim)
            elif len(args.dim) == 9: sc_matrix = np.array(args.dim).reshape(3, 3)
            else: raise ValueError("--dim must be 3 or 9 integers.")
            atoms = make_supercell(atoms, sc_matrix)
            print(f"Applied Supercell: {args.dim} (Atoms: {len(atoms)})")
            # Save SPOSCAR
            write(str(output_dir / "SPOSCAR"), atoms, format='vasp')
        else:
            # If no dim, input is SPOSCAR
            write(str(output_dir / "SPOSCAR"), atoms, format='vasp')
        
        # Upper triangular cell for NPT
        tri_cell = cellpar_to_cell(atoms.cell.cellpar())
        atoms.set_cell(tri_cell, scale_atoms=True)
        atoms.pbc = True

        # Species for XDATCAR
        symbols = atoms.get_chemical_symbols()
        species = list(dict.fromkeys(symbols))
        counts = [symbols.count(s) for s in species]

        # Calculator
        model_path = args.model
        if model_path is None:
            default_model_name = DEFAULT_MODELS.get(args.ff)
            if default_model_name:
                model_path = resolve_model_path(default_model_name)
        else:
            model_path = resolve_model_path(model_path)
            
        calc_kwargs = {"device": args.device}
        if args.ff == "mace": calc_kwargs["model_paths"] = [model_path]
        else: calc_kwargs["model_path"] = model_path
        
        calculator = get_calculator(ff_name=args.ff, **calc_kwargs)
        atoms.calc = calculator

        # 6. Data Loop
        results = []
        n_atoms = len(atoms)
        
        for idx, target_temp in enumerate(temp_list):
            print(f"\n>>> Temperature Step: {target_temp} K ({idx+1}/{len(temp_list)})")
            
            # Setup specific output files for this temperature
            xdatcar_path = output_dir / f"XDATCAR-{target_temp:.0f}K"
            md_log_path = output_dir / f"md-{target_temp:.0f}K.log"
            
            xdat_f = open(xdatcar_path, 'w')
            md_log_f = open(md_log_path, 'w')
            
            # MD Log Header
            md_log_f.write("Step      Time[ps]      Etot[eV]     Epot[eV]     Ekin[eV]    T[K]      a[A]       b[A]       c[A]      Vol[A^3]\n")

            # Initial velocities
            if idx == 0:
                MaxwellBoltzmannDistribution(atoms, temperature_K=target_temp, force_temp=True)
                Stationary(atoms); ZeroRotation(atoms)
            
            # Setup Integrator
            timestep = args.tstep * u.fs
            
            # Handle defaults (cli.py sets 0 for auto, gibbs defaults were 100/1000)
            ttau_val = args.ttau if args.ttau > 0 else 100.0
            ptau_val = args.ptau if args.ptau > 0 else 1000.0
            
            ttime = ttau_val * u.fs
            
            if args.ensemble == "npt":
                extstress = args.press * u.GPa
                # Standard ASE NPT pfactor calculation:
                # pfactor should be in units of (time)^2 * (energy)/(volume)
                # We use a robust default bulk modulus (~75 GPa) for the estimate
                bulk_modulus = 75.0 * u.GPa
                pfact = (ptau_val * u.fs)**2 * bulk_modulus
                
                if args.thermostat == "langevin":
                    effective_tau = 1000.0 / args.friction if args.friction > 0 else ttau_val
                    ttime = effective_tau * u.fs
                    # Note: ASE NPT uses 'ttime' for thermostat damping
                    dyn = NPT(atoms, timestep=timestep, temperature_K=target_temp,
                              externalstress=extstress, ttime=ttime, pfactor=pfact)
                else:
                    dyn = NPT(atoms, timestep=timestep, temperature_K=target_temp,
                              externalstress=extstress, ttime=ttime, pfactor=pfact)
            else: # NVT
                if args.thermostat == "langevin":
                    fric_val = (args.friction * 1e-3) if args.friction else (1.0 / args.ttau)
                    dyn = Langevin(atoms, timestep=timestep, temperature_K=target_temp, friction=fric_val)
                elif args.thermostat == "berendsen" and NVT_Ber:
                    dyn = NVT_Ber(atoms, timestep=timestep, temperature_K=target_temp, taut=ttime)
                else:
                    if NVT_NHC:
                        dyn = NVT_NHC(atoms, timestep=timestep, temperature_K=target_temp, tdamp=ttime)
                    else:
                        dyn = NVT_Ber(atoms, timestep=timestep, temperature_K=target_temp, taut=ttime)

            # Sampling holders
            epot_vals = []
            vol_vals = []
            a_vals, b_vals, c_vals = [], [], []
            step_counter = 0

            def sample():
                nonlocal step_counter
                step_counter += 1
                
                epot = atoms.get_potential_energy()
                ekin = atoms.get_kinetic_energy()
                etot = epot + ekin
                temp = atoms.get_temperature()
                vol = atoms.get_volume()
                abc = atoms.cell.lengths()
                
                epot_vals.append(epot)
                vol_vals.append(vol)
                a_vals.append(abc[0])
                b_vals.append(abc[1])
                c_vals.append(abc[2])
                
                # Write to MD Log
                time_ps = step_counter * args.tstep / 1000.0
                md_log_f.write(f"{step_counter:<10d} {time_ps:<12.4f} {etot:<12.4f} {epot:<12.4f} {ekin:<11.4f} {temp:<9.2f} {abc[0]:<10.4f} {abc[1]:<10.4f} {abc[2]:<10.4f} {vol:<10.4f}\n")
                
                # Write to XDATCAR
                if step_counter == 1:
                    xdat_f.write(" ".join(species) + "\n")
                    xdat_f.write("    1.000000\n")
                    for vec in atoms.cell: xdat_f.write(f"     {vec[0]:11.6f} {vec[1]:11.6f} {vec[2]:11.6f}\n")
                    xdat_f.write(" " + " ".join(f"{s:>2}" for s in species) + "\n")
                    xdat_f.write(" " + " ".join(f"{c:16d}" for c in counts) + "\n")
                
                if step_counter > 1 and args.ensemble == "npt":
                    xdat_f.write(" ".join(species) + "\n")
                    xdat_f.write("    1.000000\n")
                    for vec in atoms.cell: xdat_f.write(f"     {vec[0]:11.6f} {vec[1]:11.6f} {vec[2]:11.6f}\n")
                    xdat_f.write(" " + " ".join(f"{s:>2}" for s in species) + "\n")
                    xdat_f.write(" " + " ".join(f"{c:16d}" for c in counts) + "\n")
                
                xdat_f.write(f"Direct configuration= {step_counter:5d}\n")
                for s in atoms.get_scaled_positions(wrap=True):
                    xdat_f.write(f"   {s[0]:.8f}   {s[1]:.8f}   {s[2]:.8f}\n")

            # Helper for progress bar
            def run_with_progress(dynamics, steps, desc):
                pbar = tqdm(total=steps, desc=desc, ncols=80)
                def update_pbar():
                    pbar.update(1)
                dynamics.attach(update_pbar, interval=1)
                dynamics.run(steps)
                pbar.close()

            # 1. Equilibration
            if args.equil_steps > 0:
                run_with_progress(dyn, args.equil_steps, f"  Equilibration ({args.equil_steps})")
            
            # 2. Production
            dyn.attach(sample, interval=1)
            run_with_progress(dyn, args.nsteps, f"  Production    ({args.nsteps})")

            # Close temp files
            xdat_f.close()
            md_log_f.close()

            # Statistics
            avg_epot = np.mean(epot_vals)
            avg_vol = np.mean(vol_vals)
            avg_a, avg_b, avg_c = np.mean(a_vals), np.mean(b_vals), np.mean(c_vals)
            
            avg_ekin = 1.5 * n_atoms * KB_EV_K * target_temp
            pv_term = (args.press * avg_vol) / EV_A3_TO_GPa
            avg_h = avg_epot + avg_ekin + pv_term
            
            std_h = np.std(epot_vals) / np.sqrt(len(epot_vals)) 
            
            results.append({
                'T_K': target_temp,
                'H_avg_eV': avg_h,
                'H_err_eV': std_h,
                'E_pot_avg_eV': avg_epot,
                'V_avg_A3': avg_vol,
                'a_avg_A': avg_a,
                'b_avg_A': avg_b,
                'c_avg_A': avg_c
            })
            
            print(f"  Results: H={avg_h:.4f} eV, V={avg_vol:.2f} A^3, a={avg_a:.4f} A")

        # 7. Integration
        print("\n--- Performing Integration ---")
        temps = np.array([r['T_K'] for r in results])
        enthalpies = np.array([r['H_avg_eV'] for r in results])
        integrands = -enthalpies / (temps**2)
        
        # NumPy 2.0 compatibility for trapezoidal integration
        try:
            trapz = np.trapezoid
        except AttributeError:
            trapz = np.trapz

        integrals = []
        for i in range(len(temps)):
            if i == 0: integrals.append(0.0)
            else:
                val = trapz(integrands[:i+1], temps[:i+1])
                integrals.append(val)
        
        integrals = np.array(integrals)
        delta_g_rel = temps * integrals
        
        g_abs = [None] * len(temps)
        s_abs = [None] * len(temps)
        
        if g_ref_val is not None:
             g_t0_ref = g_ref_val
             if args.dim:
                 scale = np.prod(args.dim)
                 g_t0_ref *= scale
                 # If s_ref_val exists, scale it too
                 if s_ref_val: s_ref_val *= scale
                 print(f"  Scaling Reference by {scale} (Supercell count)")
             
             # Calculate G_abs
             for i in range(len(temps)):
                 g_abs[i] = temps[i] * (g_t0_ref / temps[0] + integrals[i])
             
             # Calculate S_abs = -dG/dT
             # Use gradient for interior, but handle boundaries carefully
             # If we have enough points, np.gradient is good.
             if len(temps) > 1:
                 # G_abs is list, convert to np array
                 g_arr = np.array(g_abs)
                 # Calculate S = -dG/dT
                 s_grad = -np.gradient(g_arr, temps)
                 s_abs = s_grad.tolist()
                 
                 # Fix the first point to match S_ref if available (more accurate than 1-sided diff)
                 if s_ref_val is not None:
                     # Blend or replace? Let's replace for consistency at T0
                     s_abs[0] = s_ref_val
        
        # 8. Save CSV
        print(f"Saving results to {csv_file}")
        EV_K_TO_J_MOL_K = 96485.33212
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ["T_K", "H_avg_eV", "H_err_eV", "V_avg_A3", "a_avg_A", "b_avg_A", "c_avg_A", 
                      "E_pot_avg_eV", "Integrand", "Integral_val", "Delta_G_rel_eV", "G_abs_eV", 
                      "S_grad_eV/K", "S_thermo_eV/K",
                      "Cp_JmolK", "alpha_MK"]
            writer.writerow(header)
            
            for i, res in enumerate(results):
                t = res['T_K']
                h = res['H_avg_eV']
                g_val = g_abs[i] if g_abs[i] is not None else 0.0
                
                # S from (H-G)/T
                s_thermo = (h - g_val) / t if g_abs[i] is not None and t > 0 else 0.0
                
                # S from gradient
                s_grad_val = s_abs[i] if s_abs[i] is not None else 0.0
                
                # Calculate derived properties for CSV (Backward difference)
                cp_val = ""
                al_val = ""
                if i > 0:
                    t_prev = results[i-1]['T_K']
                    h_prev = results[i-1]['H_avg_eV']
                    a_prev = results[i-1]['a_avg_A']
                    dt = t - t_prev
                    
                    if dt > 0:
                        cp_sys = (h - h_prev) / dt
                        cp_val = (cp_sys / n_atoms) * EV_K_TO_J_MOL_K
                        
                        a_mean = (res['a_avg_A'] + a_prev) / 2.0
                        al_val = (1.0 / a_mean) * ((res['a_avg_A'] - a_prev) / dt) * 1e6

                row = [
                    t, h, res['H_err_eV'], res['V_avg_A3'], res['a_avg_A'], res['b_avg_A'], res['c_avg_A'],
                    res['E_pot_avg_eV'], integrands[i], integrals[i], delta_g_rel[i], 
                    g_abs[i] if g_abs[i] is not None else "",
                    s_grad_val if s_abs[i] is not None else "",
                    s_thermo if g_abs[i] is not None else "",
                    cp_val, al_val
                ]
                writer.writerow(row)

        print("\n--- Workflow Completed Successfully ---")
        print(f"Log: {log_file}")
        print(f"CSV: {csv_file}")

        # 9. Summary Table Output
        print("\n" + "="*115)
        print("SUMMARY of GIBBS FREE ENERGY INTEGRATION")
        print("="*115)
        header = f"{'T (K)':>8} | {'H (eV)':>10} | {'Vol (A3)':>10} | {'G_abs (eV)':>12} | {'S (eV/K)':>12} | {'TS (eV)':>12}"
        print(header)
        print("-" * 115)
        
        for i, res in enumerate(results):
            t = res['T_K']
            h = res['H_avg_eV']
            v = res['V_avg_A3']
            
            ga = g_abs[i] if g_abs[i] is not None else float('nan')
            sa = s_abs[i] if s_abs[i] is not None else float('nan')
            
            ga_str = f"{ga:12.4f}" if not np.isnan(ga) else f"{'N/A':>12}"
            sa_str = f"{sa:12.6f}" if not np.isnan(sa) else f"{'N/A':>12}"
            
            ts_val = t * sa if not np.isnan(sa) else float('nan')
            ts_str = f"{ts_val:12.4f}" if not np.isnan(ts_val) else f"{'N/A':>12}"
            
            print(f"{t:8.1f} | {h:10.4f} | {v:10.4f} | {ga_str} | {sa_str} | {ts_str}")
            
        print("="*115)
        print(" * S is calculated via numerical differentiation (-dG/dT).")
        print(" * Check CSV for more details (including (H-G)/T based Entropy).")

        # 10. Derived Properties (Cp, alpha)
        if len(results) >= 2:
            print("\n" + "-"*65)
            print("DERIVED PROPERTIES (Approximate from finite differences)")
            print("-"*65)
            print(f"{'T_mid (K)':>10} | {'Cp (J/molK)':>15} | {'alpha (10^-6/K)':>18}")
            print("-"*65)
            
            # Constants for conversion
            # 1 eV/K = 96485.332 J/mol*K (Faraday constant approx)
            EV_K_TO_J_MOL_K = 96485.33212
            
            for i in range(len(results) - 1):
                t1, t2 = results[i]['T_K'], results[i+1]['T_K']
                h1, h2 = results[i]['H_avg_eV'], results[i+1]['H_avg_eV']
                a1, a2 = results[i]['a_avg_A'], results[i+1]['a_avg_A']
                
                dt = t2 - t1
                t_mid = (t1 + t2) / 2.0
                
                # Heat Capacity: Cp = dH/dT
                # Note: H is for the Supercell. To get molar Cp, we need to normalize by formula unit or atom.
                # Usually Cp is per mol of formula unit.
                # However, without formula info, we can output "per Supercell" or "per Atom" if we know N.
                # The user knows the system size. Let's output "per Atom" to be safe and generic?
                # Or just raw dH/dT (Heat Capacity of the SYSTEM).
                # Standard J/mol*K implies molar heat capacity. 
                # Let's normalize by number of atoms (n_atoms) to get Cp per atom, then maybe user can scale?
                # Actually, J/mol*K usually means per mole of atoms (if monoatomic) or formula.
                # Let's show J/mol-atom*K (Cp per atom * Avogadro).
                
                cp_system_ev_k = (h2 - h1) / dt
                cp_per_atom_ev_k = cp_system_ev_k / n_atoms
                cp_molar_j_mol_k = cp_per_atom_ev_k * EV_K_TO_J_MOL_K
                
                # Thermal Expansion: alpha = (1/a) * da/dT
                a_mean = (a1 + a2) / 2.0
                alpha_val = (1.0 / a_mean) * ((a2 - a1) / dt)
                alpha_mk = alpha_val * 1e6 # in 10^-6 K^-1
                
                print(f"{t_mid:10.1f} | {cp_molar_j_mol_k:15.3f} | {alpha_mk:18.3f}")
            print("-"*65)
            print(" * Cp is normalized per mole-atom (J/mol-atom*K).")
            print(" * Alpha is linear expansion coefficient.")
            print("="*65 + "\n")

    sys.stdout = orig_stdout