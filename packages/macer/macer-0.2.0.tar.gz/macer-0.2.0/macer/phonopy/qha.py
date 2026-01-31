import argparse
import os
import sys
import subprocess
import shutil
import numpy as np
from pathlib import Path
import math
import yaml
from tqdm import tqdm
from scipy.interpolate import interp1d, CubicSpline
from scipy.optimize import minimize_scalar
import matplotlib.pyplot as plt

from ase.io import read, write
from ase import Atoms
from types import SimpleNamespace

# Import necessary components from macer
from macer.defaults import DEFAULT_MODELS, _macer_root, _model_root, DEFAULT_DEVICE, DEFAULT_FF, resolve_model_path
from macer.calculator.factory import get_available_ffs, get_calculator, ALL_SUPPORTED_FFS
from macer.relaxation.bulk_modulus import get_bulk_modulus_and_volume
from macer.utils.logger import Logger
from macer import __version__

# Phonopy (Python API)
from phonopy.physical_units import get_physical_units
from phonopy import Phonopy, load as load_phonopy
from phonopy.interface.vasp import read_vasp, write_vasp
from phonopy.file_IO import write_FORCE_SETS, write_FORCE_CONSTANTS


# Determine default force field based on installed extras
available_ffs = get_available_ffs()
_dynamic_default_ff = available_ffs[0] if available_ffs else None


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


def _get_strain_scaling_factor(B_GPa: float) -> float:
    """
    Calculates a scaling factor for strain based on the bulk modulus.
    The function is an exponential decay of the form f(B) = 2**(1.4 - B/50).
    """
    if B_GPa <= 0:
        return 1.0
    return 2.5**(2.5 - B_GPa / 40.0)


def _plot_qha_results(output_dir, results):
    """Plots all QHA results and saves them to PDF files."""
    
    def _plot_single(filename_pdf, xlabel, ylabel, key_x, key_y):
        fig, ax = plt.subplots()
        ax.xaxis.set_ticks_position("both")
        ax.yaxis.set_ticks_position("both")
        ax.xaxis.set_tick_params(which="both", direction="in")
        ax.yaxis.set_tick_params(which="both", direction="in")
        
        # Filter out non-finite values to avoid plotting errors
        finite_mask = np.isfinite(results[key_x]) & np.isfinite(results[key_y])
        x_data = np.array(results[key_x])[finite_mask]
        y_data = np.array(results[key_y])[finite_mask]

        if len(x_data) > 0:
            ax.plot(x_data, y_data, 'r-')
            ax.set_xlim(left=0, right=max(x_data))
        
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True)
        plt.savefig(output_dir / filename_pdf)
        plt.close(fig)
        print(f"  {filename_pdf} generated.")

    _plot_single("gibbs-temperature.pdf", "Temperature (K)", "Gibbs free energy (eV)", 'temperature', 'gibbs')
    _plot_single("volume-temperature.pdf", "Temperature (K)", r"Volume $(\AA^3)$", 'temperature', 'volume')
    _plot_single("bulk_modulus-temperature.pdf", "Temperature (K)", "Bulk modulus (GPa)", 'temperature', 'bulk_modulus')
    _plot_single("thermal_expansion.pdf", "Temperature (K)", r"Thermal expansion ($10^{-6} \mathrm{K}^{-1}$)", 'temperature', 'thermal_expansion')
    _plot_single("Cp-temperature.pdf", "Temperature (K)", r"$C_P$ $\mathrm{(J/mol\cdot K)}$", 'temperature', 'cp')
    _plot_single("gruneisen-temperature.pdf", "Temperature (K)", "Gruneisen parameter", 'temperature', 'gruneisen')


def _plot_helmholtz_volume_polyfit(
    output_dir,
    temperatures,
    volumes,
    all_helmholtz_energies,
    all_fit_polynomials,
    all_equilibrium_points,
    thin_number=10
):
    fig, ax = plt.subplots()
    ax.xaxis.set_ticks_position("both")
    ax.yaxis.set_ticks_position("both")
    ax.xaxis.set_tick_params(which="both", direction="in")
    ax.yaxis.set_tick_params(which="both", direction="in")

    volume_range = np.linspace(min(volumes), max(volumes), 100)
    
    e_min = all_equilibrium_points[0]['energy'] if all_equilibrium_points else 0

    for i, T in enumerate(temperatures):
        if i % thin_number == 0 and all_fit_polynomials[i] is not None:
            ax.plot(volumes, all_helmholtz_energies[i] - e_min, 'bo', markersize=3)
            ax.plot(volume_range, all_fit_polynomials[i](volume_range) - e_min, 'b-')

    eq_volumes = [p['volume'] for p in all_equilibrium_points if p]
    eq_energies = [p['energy'] for p in all_equilibrium_points if p]
    ax.plot(eq_volumes, np.array(eq_energies) - e_min, 'ro-', markersize=3)

    ax.set_xlabel(r"Volume $(\AA^3)$")
    ax.set_ylabel("Free energy (eV)")
    ax.grid(True)
    plt.savefig(output_dir / "helmholtz-volume.pdf")
    plt.close(fig)
    print(f"  helmholtz-volume.pdf generated.")


def run_local_poly_qha_analysis(
    volumes,
    electronic_energies,
    thermal_properties_with_volumes,
    output_dir,
    poly_degree,
    poly_points,
    tmax,
    smooth_deg,
):
    """
    Performs QHA analysis using a local polynomial fit for the F-V curve.
    """
    AVOGADRO = 6.02214076e23
    EV_TO_KJ_MOL = get_physical_units().EvTokJmol

    # 1. Load thermal properties
    thermal_props = {}
    for vol, path in thermal_properties_with_volumes:
        with open(path) as f:
            data = yaml.safe_load(f)
        
        temps_list = [item['temperature'] for item in data['thermal_properties']]
        free_energy_list = [item['free_energy'] for item in data['thermal_properties']]
        entropy_list = [item['entropy'] for item in data['thermal_properties']]
        heat_capacity_list = [item['heat_capacity'] for item in data['thermal_properties']]

        thermal_props[vol] = {
            'temperatures': np.array(temps_list),
            'free_energy': np.array(free_energy_list),
            'entropy': np.array(entropy_list),
            'heat_capacity': np.array(heat_capacity_list),
        }

    # 2. Prepare data structures
    volumes = np.array(volumes)
    electronic_energies = np.array(electronic_energies)
    sort_idx = np.argsort(volumes)
    volumes = volumes[sort_idx]
    electronic_energies = electronic_energies[sort_idx]
    sorted_thermal_props = [thermal_props[vol] for vol in volumes]

    temps = np.linspace(0, tmax, 101)
    raw_results = { 'temperature': [], 'volume': [] }
    all_helmholtz_energies, all_fit_polynomials = [], []

    # 3. First pass: Calculate F(V,T) and find raw equilibrium V_eq(T)
    for T in temps:
        helmholtz_energies = []
        for i, V in enumerate(volumes):
            tp = sorted_thermal_props[i]
            f_interp = interp1d(tp['temperatures'], tp['free_energy'], bounds_error=False, fill_value='extrapolate')
            phonon_F_kJ_mol = f_interp(T)
            phonon_F_eV = phonon_F_kJ_mol / EV_TO_KJ_MOL
            helmholtz_energies.append(electronic_energies[i] + phonon_F_eV)
        
        helmholtz_energies = np.array(helmholtz_energies)
        all_helmholtz_energies.append(helmholtz_energies)

        min_F_idx = np.argmin(helmholtz_energies)
        num_fit_points = poly_points if poly_points is not None else len(volumes)
        start = max(0, min_F_idx - num_fit_points // 2)
        end = start + num_fit_points
        if end > len(volumes):
            end = len(volumes)
            start = max(0, end - num_fit_points)
        fit_volumes, fit_energies = volumes[start:end], helmholtz_energies[start:end]

        if len(fit_volumes) < poly_degree + 1:
            p_fit = None
        else:
            coeffs = np.polyfit(fit_volumes, fit_energies, poly_degree)
            p_fit = np.poly1d(coeffs)
        all_fit_polynomials.append(p_fit)
        
        if p_fit is None:
            V_eq = np.nan
        else:
            res = minimize_scalar(p_fit, bounds=(volumes[0], volumes[-1]), method='bounded')
            V_eq = res.x if res.success else np.nan
        
        # Sanity check: V_eq must be within the sampled volume range
        if not (volumes[0] <= V_eq <= volumes[-1]):
            print(f"Warning: Found equilibrium volume ({V_eq:.2f}) is outside the sample range "
                  f"[{volumes[0]:.2f}, {volumes[-1]:.2f}] at T={T:.1f}K. Fit is unreliable. Skipping.")
            V_eq = np.nan
        
        # Stability check: curvature must be positive for a valid minimum
        if np.isfinite(V_eq) and p_fit is not None and p_fit.deriv(2)(V_eq) <= 0:
            print(f"Warning: Non-positive curvature at T={T:.1f}K. Fit is unreliable. Skipping.")
            V_eq = np.nan
        
        # Sanity check: V_eq must be within the sampled volume range
        if not (volumes[0] <= V_eq <= volumes[-1]):
            V_eq = np.nan
        
        # Stability check: curvature must be positive for a valid minimum
        if np.isfinite(V_eq) and p_fit.deriv(2)(V_eq) <= 0:
            V_eq = np.nan

        raw_results['temperature'].append(T)
        raw_results['volume'].append(V_eq)

    # 4. Smooth V(T) curve and re-calculate all properties
    smooth_results = { 'temperature': temps, 'gibbs': [], 'volume': [], 'bulk_modulus': [], 'thermal_expansion': [], 'cp': [], 'entropy': [], 'gruneisen': [] }
    all_eos_parameters = []

    valid_mask = np.isfinite(raw_results['volume'])
    if np.sum(valid_mask) > smooth_deg:
        v_smooth_coeffs = np.polyfit(np.array(raw_results['temperature'])[valid_mask], np.array(raw_results['volume'])[valid_mask], smooth_deg)
        v_smooth_fit = np.poly1d(v_smooth_coeffs)
        
        for i, T in enumerate(temps):
            V_smooth = v_smooth_fit(T)
            p_fit = all_fit_polynomials[i]

            if p_fit is None:
                for key in smooth_results:
                    if key != 'temperature': smooth_results[key].append(np.nan)
                all_eos_parameters.append(None)
                continue

            F_smooth = p_fit(V_smooth)
            B_GPa = V_smooth * p_fit.deriv(2)(V_smooth) * 160.21766208
            B_prime = -1 - V_smooth * p_fit.deriv(3)(V_smooth) / p_fit.deriv(2)(V_smooth) if abs(p_fit.deriv(2)(V_smooth)) > 1e-9 else np.nan
            
            alpha = (1 / V_smooth) * v_smooth_fit.deriv(1)(T) if V_smooth != 0 else 0

            cv_at_T_points = [interp1d(tp['temperatures'], tp['heat_capacity'], bounds_error=False, fill_value='extrapolate')(T) for tp in sorted_thermal_props]
            Cv_at_Veq = interp1d(volumes, cv_at_T_points, bounds_error=False, fill_value='extrapolate')(V_smooth)
            
            # Add entropy interpolation
            entropy_at_T_points = [interp1d(tp['temperatures'], tp['entropy'], bounds_error=False, fill_value='extrapolate')(T) for tp in sorted_thermal_props]
            Entropy_at_Veq = interp1d(volumes, entropy_at_T_points, bounds_error=False, fill_value='extrapolate')(V_smooth)

            V_m3, B_Pa = V_smooth * 1e-30, B_GPa * 1e9
            Cp_corr = T * V_m3 * B_Pa * alpha**2 * AVOGADRO
            Cp = Cv_at_Veq + Cp_corr
            
            Cv_per_cell = Cv_at_Veq / AVOGADRO
            gamma = (alpha * B_Pa * V_m3 / Cv_per_cell) if Cv_per_cell > 1e-12 else 0

            smooth_results['volume'].append(V_smooth); smooth_results['gibbs'].append(F_smooth)
            smooth_results['bulk_modulus'].append(B_GPa); smooth_results['thermal_expansion'].append(alpha * 1e6)
            smooth_results['cp'].append(Cp); smooth_results['entropy'].append(Entropy_at_Veq); smooth_results['gruneisen'].append(gamma)
            all_eos_parameters.append((F_smooth, B_GPa, B_prime, V_smooth))
    else:
        print("Warning: Not enough valid points to create a smooth V(T) curve. Skipping smoothing.")
        smooth_results = raw_results # Fallback to raw results

    # 5. Write and plot results
    print("  Writing result files and generating plots...")

    dat_headers = {
        'gibbs': "# Temperature (K), Gibbs free energy (eV)\n",
        'volume': "# Temperature (K), Equilibrium volume (A^3)\n",
        'bulk_modulus': "# Temperature (K), Bulk modulus (GPa)\n",
        'thermal_expansion': "# Temperature (K), Thermal expansion (10^-6 K^-1)\n",
        'cp': "# Temperature (K), Heat capacity Cp (J/mol-K)\n",
        'entropy': "# Temperature (K), Entropy (J/mol-K)\n",
        'gruneisen': "# Temperature (K), Gruneisen parameter\n"
    }

    def write_dat(filename, header, key1, key2):
        with open(output_dir / filename, 'w') as f:
            f.write(header)
            if key1 in smooth_results and key2 in smooth_results and len(smooth_results[key1]) > 0:
                for val1, val2 in zip(smooth_results[key1], smooth_results[key2]):
                    if np.isfinite(val1) and np.isfinite(val2):
                        f.write(f"{val1:.3f} {val2:.8f}\n")
    
    for key in ['gibbs', 'volume', 'bulk_modulus', 'thermal_expansion', 'cp', 'entropy', 'gruneisen']:
        filename_dat = f'{key}-temperature.dat'
        header = dat_headers.get(key, f"# Temperature (K)  {key}\n")
        write_dat(filename_dat, header, 'temperature', key)
        print(f"  {filename_dat} generated.")

    # Write thermal_properties.yaml
    tp_data = {
        "unit-temperature": "K",
        "unit-free-energy": "kJ/mol",
        "unit-entropy": "J/mol-K",
        "unit-heat-capacity": "J/mol-K",
        "thermal_properties": []
    }
    for i in range(len(smooth_results['temperature'])):
        if i >= len(smooth_results['gibbs']) or np.isnan(smooth_results['gibbs'][i]): continue
        tp_data["thermal_properties"].append({
            "temperature": float(smooth_results['temperature'][i]),
            "free_energy": float(smooth_results['gibbs'][i] * EV_TO_KJ_MOL),
            "entropy": float(smooth_results['entropy'][i]),
            "heat_capacity": float(smooth_results['cp'][i])
        })
    with open(output_dir / "thermal_properties.yaml", "w") as f:
        yaml.dump(tp_data, f, default_flow_style=False, sort_keys=False)
    print("  thermal_properties.yaml generated.")

    with open(output_dir / 'helmholtz-volume.dat', 'w') as f:
        f.write("# Volume (A^3), Free energy (eV)\n")
        for i, T in enumerate(temps):
            if i < len(all_eos_parameters) and all_eos_parameters[i] is not None:
                f.write(f"# Temperature: {T:.5f}\n")
                f.write("# Parameters: %f %f %f %f\n" % all_eos_parameters[i])
                for j, V in enumerate(volumes):
                    f.write(f"{V:20.15f} {all_helmholtz_energies[i][j]:25.15f}\n")
                f.write("\n\n")
    print("  helmholtz-volume.dat generated.")

    valid_points = [{'volume': v, 'energy': p(v)} for v, p in zip(smooth_results.get('volume', []), all_fit_polynomials) if p is not None and np.isfinite(v)]
    if valid_points:
        _plot_helmholtz_volume_polyfit(output_dir, temps, volumes, all_helmholtz_energies, all_fit_polynomials, valid_points)
    
    _plot_qha_results(output_dir, smooth_results)
    print("  Local polynomial QHA analysis finished.")


def _write_standard_qha_extra_outputs(output_dir, e_v_dat, thermal_paths, eos_name):
    """
    Post-processes standard phonopy-qha results to add entropy-temperature.dat
    and thermal_properties.yaml (similar to local_poly output).
    """
    try:
        from phonopy import PhonopyQHA
        from phonopy.file_IO import read_v_e, read_thermal_properties_yaml
        import numpy as np
        import yaml
    except ImportError:
        print("  Warning: Could not import phonopy for post-processing extra QHA outputs.")
        return

    EV_TO_KJ_MOL = 96.485391 # Approximate conversion used by phonopy

    try:
        # Read data
        volumes, electronic_energies = read_v_e(str(e_v_dat))
        (temperatures,
         cv,
         entropy,
         fe_phonon,
         num_modes,
         num_integrated_modes) = read_thermal_properties_yaml([str(p) for p in thermal_paths])

        # Initialize QHA
        phonopy_qha = PhonopyQHA(
            volumes=volumes,
            electronic_energies=electronic_energies,
            temperatures=temperatures,
            free_energy=fe_phonon,
            cv=cv,
            entropy=entropy,
            eos=eos_name,
            verbose=False
        )
        
        # Get results from internal QHA object
        qha = phonopy_qha._qha
        t_qha = qha._temperatures[:qha._len]
        v_eq = qha._equiv_volumes[:qha._len]
        g_qha = qha._equiv_energies[:qha._len]
        cp_qha = qha._cp_numerical[:qha._len]
        
        # Interpolate entropy and Cv at equilibrium volumes
        s_eq = []
        cv_eq = []
        for i, t in enumerate(t_qha):
            s_val = np.interp(v_eq[i], volumes, entropy[i])
            cv_val = np.interp(v_eq[i], volumes, cv[i])
            s_eq.append(s_val)
            cv_eq.append(cv_val)

        s_eq = np.array(s_eq)
        cv_eq = np.array(cv_eq)

        # Write entropy-temperature.dat
        with open(output_dir / "entropy-temperature.dat", "w") as f:
            f.write("# Temperature (K), Entropy (J/mol-K)\n")
            for t, s in zip(t_qha, s_eq):
                f.write(f"{t:20.10f} {s:20.10f}\n")
        print("  entropy-temperature.dat generated.")

        # Write thermal_properties.yaml
        tp_data = {
            "unit-temperature": "K",
            "unit-free-energy": "kJ/mol",
            "unit-entropy": "J/mol-K",
            "unit-heat-capacity": "J/mol-K",
            "thermal_properties": []
        }
        for i in range(len(t_qha)):
            tp_data["thermal_properties"].append({
                "temperature": float(t_qha[i]),
                "free_energy": float(g_qha[i] * EV_TO_KJ_MOL),
                "entropy": float(s_eq[i]),
                "heat_capacity": float(cv_eq[i])
            })
        
        with open(output_dir / "thermal_properties.yaml", "w") as f:
            yaml.dump(tp_data, f, default_flow_style=False, sort_keys=False)
        print("  thermal_properties.yaml generated.")

    except Exception as e:
        print(f"  Warning: Error during standard QHA post-processing: {e}")


def _add_headers_to_qha_dat_files(output_dir):
    """Adds headers with units to .dat files generated by phonopy-qha or macer."""
    headers = {
        "bulk_modulus-temperature.dat": "# Temperature (K), Bulk modulus (GPa)\n",
        "Cv-volume.dat": "# Volume (A^3), Heat capacity Cv (J/mol-K)\n",
        "entropy-temperature.dat": "# Temperature (K), Entropy (J/mol-K)\n",
        "gruneisen-temperature.dat": "# Temperature (K), Gruneisen parameter\n",
        "thermal_expansion.dat": "# Temperature (K), Thermal expansion (K^-1)\n",
        "Cp-temperature_polyfit.dat": "# Temperature (K), Heat capacity Cp (J/mol-K)\n",
        "Cp-temperature.dat": "# Temperature (K), Heat capacity Cp (J/mol-K)\n",
        "entropy-volume.dat": "# Volume (A^3), Entropy (J/mol-K)\n",
        "gibbs-temperature.dat": "# Temperature (K), Gibbs free energy (eV)\n",
        "volume-temperature.dat": "# Temperature (K), Equilibrium volume (A^3)\n",
        "helmholtz-volume.dat": "# Volume (A^3), Free energy (eV)\n",
        "helmholtz-volume_fitted.dat": "# Volume (A^3), Free energy (eV)\n",
        "dsdv-temperature.dat": "# Temperature (K), dS/dV (GPa/K)\n",
        "e-v.dat": "# Volume (A^3), Energy (eV)\n"
    }

    for filename, header in headers.items():
        file_path = output_dir / filename
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = f.read()
            if not content: continue
            
            # If our header is already there, skip
            if header in content: continue
            
            # If there's an existing simple header, we might want to replace it
            # But the simplest is just to prepend if header not in content.
            # phonopy-qha often writes no header.
            with open(file_path, 'w') as f:
                f.write(header + content)


def generate_displacements_for_qha(
    poscar_path: Path,
    supercell_matrix,
    displacement_distance: float,
    is_plusminus: bool | str,
    is_diagonal: bool,
    tolerance_phonopy: float,
):
    """Only generates displacement files, does not calculate forces."""
    unitcell = read_vasp(str(poscar_path))

    phonon = Phonopy(
        unitcell,
        supercell_matrix=supercell_matrix,
        primitive_matrix="auto",
        symprec=tolerance_phonopy,
    )

    phonon.generate_displacements(
        distance=displacement_distance,
        is_plusminus=is_plusminus,
        is_diagonal=is_diagonal,
    )

    phonon.save("phonopy_disp.yaml")
    write_vasp("SPOSCAR", phonon.supercell)
    displaced_cells = phonon.supercells_with_displacements
    for i, cell in enumerate(displaced_cells):
        write_vasp(f"POSCAR-{(i + 1):03d}", cell)
    return phonon.dataset, len(displaced_cells)


def create_force_constants_from_force_sets_api(
    poscar_path,
    supercell_matrix,
    tolerance_phonopy,
    fc_calculator='symfc'
):
    """
    Creates FORCE_CONSTANTS from FORCE_SETS using phonopy API.
    This is an API-based replacement for the CLI command:
    `phonopy -c POSCAR --dim ... --writefc --symfc`
    """
    phonon = load_phonopy(
        unitcell_filename=str(poscar_path),
        supercell_matrix=supercell_matrix,
        primitive_matrix="auto",
        force_sets_filename="FORCE_SETS",
        fc_calculator=fc_calculator,
        produce_fc=True,
        symprec=tolerance_phonopy,
        log_level=0
    )
    
    if phonon.force_constants is None:
        raise RuntimeError("Force constants could not be calculated via API.")

    write_FORCE_CONSTANTS(phonon.force_constants, filename="FORCE_CONSTANTS")


def run_qha_workflow(args):
    # --- Parse selected axes ---
    selected_axes_str = args.select_axis
    if selected_axes_str:
        selected_axes = {axis.strip().lower() for axis in selected_axes_str.split(',')}
        valid_axes = {'a', 'b', 'c'}
        if not selected_axes.issubset(valid_axes):
            raise ValueError(f"Error: Invalid axis in --select-axis. Allowed values are 'a', 'b', 'c'. You provided: {selected_axes_str}")
    else:
        selected_axes = {'a', 'b', 'c'}  # Default is all axes

    # --- Configuration ---
    is_cif_mode = False
    if args.poscar:
        input_poscar_path = Path(args.poscar).resolve()
    elif args.cif:
        input_poscar_path = Path(args.cif).resolve()
        is_cif_mode = True
    else:
        raise ValueError("Error: Please provide structure input via -p (POSCAR) or -c (CIF) option.")

    if not input_poscar_path.is_file():
        raise FileNotFoundError(f"Input file not found at '{input_poscar_path}'. Please provide a valid file.")

    if args.output_dir:
        base_output_dir = Path(args.output_dir).resolve()
    else:
        base_output_dir = input_poscar_path.parent / f"qha_{input_poscar_path.stem}-mlff={args.ff}"
    
    qha_output_dir = base_output_dir
    i = 1
    while qha_output_dir.exists():
        qha_output_dir = Path(f"{base_output_dir}-NEW{i:03d}")
        i += 1
    qha_output_dir.mkdir(parents=True, exist_ok=False)

    log_file = qha_output_dir / "macer_phonopy_qha.log"
    orig_stdout = sys.stdout
    
    with Logger(str(log_file)) as lg:
        sys.stdout = lg
        try:
            from macer import __version__
            print(f"--- Macer QHA Workflow (v{__version__}) ---")
            print(f"Command: {' '.join(sys.argv)}")
            ff = args.ff
            model_path = _resolve_model_path(ff, args.model)
            if model_path and os.path.exists(model_path):
                model_path = os.path.abspath(model_path)

            modal = args.modal
            device = args.device

            length_scale_range = args.length_scale
            lf_min_arg = args.length_factor_min
            lf_max_arg = args.length_factor_max
            num_volumes = args.num_volumes
            mesh_x, mesh_y, mesh_z = args.mesh
            min_length = args.min_length
            displacement_distance = args.amplitude
            is_plusminus = args.is_plusminus
            is_diagonal = args.is_diagonal
            tolerance_phonopy = args.tolerance_phonopy
            tmax = args.tmax
            relax_atom = args.relax_atom

            # --- Parse mass override ---
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
                print(f"--- Atomic mass override ---")
                for sym, m in mass_map.items():
                    print(f"  {sym:3s} : {m:8.4f} amu")
                print("----------------------------")

            # --- Input validation for length scales ---
            if length_scale_range is not None and (lf_min_arg is not None or lf_max_arg is not None):
                raise ValueError("Error: --length-scale cannot be used with --length-factor-min/max.")
            if (lf_min_arg is not None and lf_max_arg is None) or (lf_min_arg is None and lf_max_arg is not None):
                raise ValueError("Error: --length-factor-min and --length-factor-max must be used together.")

            print(f"--- Starting QHA workflow for {input_poscar_path.name} ---")
            print(f"All QHA results will be saved in: {qha_output_dir}")

            model_info_str = ""
            FFS_USING_MODEL_NAME = {"fairchem", "orb", "chgnet", "m3gnet"}
            if args.model:
                model_info_str = f" (from --model option)"
            else:
                default_model_name = DEFAULT_MODELS.get(ff)
                if default_model_name:
                    model_info_str = f" (default for {ff.upper()}: {default_model_name})"
            
            if model_path:
                print(f"  MLFF Model: {model_path}{model_info_str}")
            else:
                print(f"  MLFF Model:{model_info_str}")

            # --- Step 1: Initial Unit Cell Relaxation & Preparation ---
            print("\n--- Step 1: Initial Unit Cell Relaxation & Preparation ---")
            original_cwd = os.getcwd()
            try:
                # Copy and relax initial structure
                if is_cif_mode:
                     atoms_in = read(str(input_poscar_path))
                     copied_input_poscar_path = qha_output_dir / "POSCAR" # Rename to POSCAR
                     write(str(copied_input_poscar_path), atoms_in, format='vasp')
                     print(f"Converted {input_poscar_path.name} to {copied_input_poscar_path}")
                else:
                     copied_input_poscar_path = qha_output_dir / input_poscar_path.name
                     shutil.copy(input_poscar_path, copied_input_poscar_path)
        
                os.chdir(qha_output_dir)

                if args.isif == 0:
                    print("ISIF=0 specified, skipping initial relaxation.")
                    qha_input_poscar_path = copied_input_poscar_path
                else:
                    print(f"Performing initial cell relaxation (ISIF={args.isif}).")
                    relaxed_poscar_name = f"CONTCAR-{copied_input_poscar_path.name}"
                    macer_relax_command = [
                        sys.executable, '-m', 'macer.cli.main', 'relax', '-p', str(copied_input_poscar_path), '--isif', str(args.isif),
                        '--fmax', str(args.initial_fmax), '--device', device,
                        '--contcar', relaxed_poscar_name, '--no-pdf',
                        '--symprec', str(args.initial_symprec)
                    ]
                    if not args.initial_use_symmetry:
                        macer_relax_command.append('--symmetry-off')
                    if ff: macer_relax_command.extend(['--ff', ff])
                    if model_path: macer_relax_command.extend(['--model', str(model_path)])
                    if modal: macer_relax_command.extend(['--modal', modal])
            
                    try:
                        # Run without capturing output to allow seeing segfault details or C-level errors directly
                        subprocess.run(macer_relax_command, check=True, text=True)
                    except subprocess.CalledProcessError as e:
                        print("Error during initial 'macer relax' execution.")
                        # e.stderr is None when not captured, so we don't print it.
                        raise e

                    qha_input_poscar_path = qha_output_dir / relaxed_poscar_name

                if not qha_input_poscar_path.exists():
                    print("Initial relaxation finished successfully but output file was not found.")
                    if 'result' in locals():
                         print("STDOUT:", result.stdout)
                         print("STDERR:", result.stderr)
                    raise FileNotFoundError("Relaxed/symmetrized POSCAR not found.")
        
                base_structure_atoms = read(str(qha_input_poscar_path), format="vasp")
                initial_cell = base_structure_atoms.get_cell()

                # --- Determine supercell matrix ---
                supercell_matrix = None
                if args.dim:
                    if len(args.dim) == 3:
                        supercell_matrix = np.diag(args.dim)
                        print(f"Using user-provided diagonal supercell DIM = {args.dim}")
                    elif len(args.dim) == 9:
                        supercell_matrix = np.array(args.dim).reshape(3, 3)
                        print(f"Using user-provided supercell matrix:\n{supercell_matrix}")
                    else:
                        raise ValueError("Error: --dim must be followed by 3 or 9 integers.")
                else:
                    # Auto-determine from min_length
                    scaling_factors_list = [max(1, math.ceil(min_length / np.linalg.norm(v))) for v in initial_cell]
                    supercell_matrix = np.diag(scaling_factors_list)
                    print(f"Auto-determining supercell from --min-length. DIM = {scaling_factors_list}")

                # For phonopy CLI calls, we need a string representation
                dim_str = " ".join(map(str, supercell_matrix.flatten().astype(int)))
        
                # Determine strain range
                if lf_min_arg is not None:  # Absolute user-provided range
                    length_scales = np.linspace(lf_min_arg, lf_max_arg, num_volumes)
                    print(f"Using user-provided absolute length factor range: {lf_min_arg} to {lf_max_arg}")
                else:
                    if length_scale_range is not None:  # Symmetric user-provided strain range
                        ls_min = ls_max = length_scale_range
                        print(f"Using user-provided symmetric strain range: \u00b1{length_scale_range*100:.1f}%")
                    else:  # Estimate from bulk modulus
                        print("\n--- Estimating optimal length scale from bulk modulus ---")
                        calc_args = SimpleNamespace(ff=ff, model=model_path, device=device, modal=modal)
                        B_GPa, V0_per_atom = get_bulk_modulus_and_volume(base_structure_atoms, calc_args)
                        if B_GPa and V0_per_atom:
                            E_target_eV = args.target_energy / 1000.0
                            B_eV_per_A3 = B_GPa / 160.21766208
                            epsilon_V = math.sqrt(2 * E_target_eV / (B_eV_per_A3 * V0_per_atom))
                    
                            scaling_factor = _get_strain_scaling_factor(B_GPa)
                            estimated_range = epsilon_V * scaling_factor
                            ls_min = ls_max = estimated_range
                    
                            print(f"  - Calculated Bulk Modulus: {B_GPa:.2f} GPa")
                            print(f"  - Base estimated strain: \u00b1{epsilon_V:.4f}")
                            print(f"  - Exponential scaling factor for strain: {scaling_factor:.3f}")
                            print(f"  Final estimated length-scale range: \u00b1{estimated_range*100:.1f}%")
                        else:
                            print("  Bulk modulus estimate failed; fallback to \u00b15%.")
                            ls_min = ls_max = 0.05
                    length_scales = np.linspace(1 - ls_min, 1 + ls_max, num_volumes)

                print(f"Length scales = {length_scales}")

            finally:
                os.chdir(original_cwd)

            # --- Step 2: Generate all displacements for all volumes first ---
            print("\n--- Step 2: Generating all displacements for all volumes ---")
            all_disp_atoms = []
            volume_dirs = []
            datasets = {}
            structure_info = []
            for l_scale in length_scales:
                volume_dir = qha_output_dir / f"length-scale={l_scale:.5f}"
                volume_dirs.append(volume_dir)
                volume_dir.mkdir(exist_ok=True)
                print(f"\n--- Preparing volume for length scale {l_scale:.5f} ---")

                scaled_atoms = read(str(qha_input_poscar_path), format="vasp")
        
                # Apply selective scaling based on --select-axis
                new_cell = initial_cell.copy()
                scale_a = l_scale if 'a' in selected_axes else 1.0
                scale_b = l_scale if 'b' in selected_axes else 1.0
                scale_c = l_scale if 'c' in selected_axes else 1.0
                new_cell[0] *= scale_a
                new_cell[1] *= scale_b
                new_cell[2] *= scale_c
                scaled_atoms.set_cell(new_cell, scale_atoms=True)

                poscar_path_vol = volume_dir / "POSCAR"
                write(str(poscar_path_vol), scaled_atoms, format="vasp")

                os.chdir(volume_dir)
                try:
                    if relax_atom:
                        print("  Relaxing scaled structure (atoms only)...")
                        relax_cmd = ['macer', 'relax', '-p', 'POSCAR', '--isif', '2', '--device', device, '--contcar', 'CONTCAR-POSCAR', '--no-pdf', '--symprec', str(args.initial_symprec)]
                        if not args.initial_use_symmetry:
                            relax_cmd.append('--symmetry-off')
                        if ff: relax_cmd.extend(['--ff', ff])
                        if model_path: relax_cmd.extend(['--model', str(model_path)])
                        if modal: relax_cmd.extend(['--modal', modal])
                        subprocess.run(relax_cmd, check=True, capture_output=True, text=True)
                        shutil.move("CONTCAR-POSCAR", "POSCAR")
            
                    dataset, num_disps = generate_displacements_for_qha(
                        poscar_path=Path("POSCAR"),
                        supercell_matrix=supercell_matrix,
                        displacement_distance=displacement_distance,
                        is_plusminus=is_plusminus,
                        is_diagonal=is_diagonal,
                        tolerance_phonopy=tolerance_phonopy,
                    )
                    datasets[l_scale] = dataset
            
                    # Collect all atoms from POSCAR and POSCAR-xxx for batch calculation
                    all_disp_atoms.append(read("POSCAR", format="vasp")) # Relaxed, undisplaced
                    structure_info.append({'l_scale': l_scale, 'disp_num': 0})
                    for i in range(1, num_disps + 1):
                        all_disp_atoms.append(read(f"POSCAR-{(i):03d}", format="vasp"))
                        structure_info.append({'l_scale': l_scale, 'disp_num': i})
                finally:
                    os.chdir(original_cwd)

                shutil.copy(volume_dir / "SPOSCAR", qha_output_dir / f"SPOSCAR_scale_{l_scale:.5f}")
                print(f"  Copied SPOSCAR to {qha_output_dir.name}/SPOSCAR_scale_{l_scale:.5f}")

            # --- Step 3: Batch Force & Energy Calculation ---
            print("\n--- Step 3: Batch force and energy calculation for all structures ---")
            try:
                calc_kwargs = {"model_path": model_path, "device": device, "modal": modal}
                if ff == "mace":
                    calc_kwargs["model_paths"] = [calc_kwargs["model_path"]]
                    del calc_kwargs["model_path"]
                calculator = get_calculator(ff_name=ff, **calc_kwargs)
        
                all_forces = []
                all_energies = []
        
                for atoms in tqdm(all_disp_atoms, desc="Batch force/energy calculation"):
                    atoms.calc = calculator
                    all_forces.append(atoms.get_forces())
                    all_energies.append(atoms.get_potential_energy())
                print("  All forces and energies calculated in a single batch.")

            except Exception as e:
                print(f"Error during batch calculation: {e}")
                # Use raise instead of sys.exit
                raise e

            # --- Step 4: Process results for each volume ---
            print("\n--- Step 4: Processing results for each volume ---")
            qha_energies, qha_volumes, thermal_properties_with_volumes = [], [], []
            atom_idx_counter = 0
            for l_scale, volume_dir in zip(length_scales, volume_dirs):
                print(f"\n--- Post-processing for length scale {l_scale:.5f} ---")
                os.chdir(volume_dir)
                try:
                    # Get energy and volume for the relaxed, undisplaced structure
                    energy_ev = all_energies[atom_idx_counter]
                    vol_atoms = read("POSCAR", format="vasp")
                    volume_a3 = vol_atoms.get_volume()
                    qha_energies.append(energy_ev)
                    qha_volumes.append(volume_a3)
                    atom_idx_counter += 1

                    # Create FORCE_SETS
                    dataset = datasets[l_scale]
                    num_disps = len(dataset.get('first_atoms', []))
                    force_sets = all_forces[atom_idx_counter : atom_idx_counter + num_disps]
                    atom_idx_counter += num_disps

                    if "first_atoms" in dataset:
                        for i, forces in enumerate(force_sets):
                            dataset["first_atoms"][i]["forces"] = forces
                    else:
                        dataset["forces"] = np.array(force_sets)
            
                    force_sets_path = volume_dir / "FORCE_SETS"
                    write_FORCE_SETS(dataset, filename=str(force_sets_path))
                    print(f"  FORCE_SETS created successfully.")

                    if args.use_force_constants:
                        # Create FORCE_CONSTANTS from FORCE_SETS using API
                        print("  Creating FORCE_CONSTANTS from FORCE_SETS (using API)...")
                        create_force_constants_from_force_sets_api(
                            poscar_path=Path("POSCAR"),
                            supercell_matrix=supercell_matrix,
                            tolerance_phonopy=tolerance_phonopy,
                            fc_calculator='symfc'
                        )
                        print("  FORCE_CONSTANTS created successfully.")
            
                    # Compute thermal properties
                    print(f"  Calculating thermal properties (mesh: {mesh_x} {mesh_y} {mesh_z})...")
            
                    # Load phonopy via API
                    # This automatically picks up FORCE_SETS or FORCE_CONSTANTS in the current directory
                    phonon = load_phonopy(
                        unitcell_filename="POSCAR",
                        supercell_matrix=supercell_matrix,
                        primitive_matrix="auto",
                        log_level=0
                    )

                    # Apply mass override
                    if mass_map:
                        current_masses = phonon.masses
                        symbols = phonon.primitive.symbols # Symbols of the primitive cell atoms
                        new_masses = []
                        for s, m in zip(symbols, current_masses):
                            if s in mass_map:
                                new_masses.append(mass_map[s])
                            else:
                                new_masses.append(m)
                        phonon.masses = new_masses
                        print(f"  Applied mass override for thermal properties.")

                    phonon.run_mesh(
                        mesh=[mesh_x, mesh_y, mesh_z],
                        is_gamma_center=True
                    )
                    phonon.run_thermal_properties(
                        t_step=10,
                        t_max=tmax,
                        t_min=0
                    )
                    phonon.write_yaml_thermal_properties(filename="thermal_properties.yaml")
            
                    thermal_properties_with_volumes.append(
                        (volume_a3, str(volume_dir / "thermal_properties.yaml"))
                    )
                    print(f"  Collected E={energy_ev:.8f} eV, V={volume_a3:.4f} Å³")

                except (subprocess.CalledProcessError, RuntimeError, Exception) as e:
                    print("  Error during post-processing:")
                    if hasattr(e, 'stderr') and e.stderr:
                        print(e.stderr)
                    else:
                        print(e)
                        import traceback
                        traceback.print_exc()
                    raise e
                finally:
                    os.chdir(original_cwd)

            # --- Step 5: Final QHA analysis ---
            print("\n--- Step 5: Running phonopy-qha analysis ---")
            e_v_dat = qha_output_dir / "e-v.dat"
            with open(e_v_dat, "w") as f:
                f.write("# Volume (A^3), Energy (eV)\n")
                for V, E in sorted(zip(qha_volumes, qha_energies)):
                    f.write(f"{V:20.15f} {E:25.15f}\n")
            print(f"  e-v.dat written: {e_v_dat}")

            if args.eos == 'local_poly':
                print("  Using local polynomial fit for EOS.")
                run_local_poly_qha_analysis(
                    volumes=qha_volumes,
                    electronic_energies=qha_energies,
                    thermal_properties_with_volumes=thermal_properties_with_volumes,
                    output_dir=qha_output_dir,
                    poly_degree=args.poly_degree,
                    poly_points=args.poly_points,
                    tmax=args.tmax,
                    smooth_deg=args.smooth_deg
                )
            else:
                print(f"  Using '{args.eos}' EOS with phonopy-qha.")
                thermal_paths = [p for _, p in sorted(thermal_properties_with_volumes)]
                qha_cmd = ["phonopy-qha", "--eos", args.eos, str(e_v_dat)] + thermal_paths + ["--tmax", str(tmax), "-s"]
                os.chdir(qha_output_dir)
                subprocess.run(qha_cmd, check=True, capture_output=True, text=True)
                
                # Post-process for extra outputs (entropy-temperature.dat and thermal_properties.yaml)
                _write_standard_qha_extra_outputs(qha_output_dir, e_v_dat, thermal_paths, args.eos)
                
                os.chdir(original_cwd)

            # Final post-processing to ensure all .dat files have headers
            _add_headers_to_qha_dat_files(qha_output_dir)

        except Exception as e:
            # Catch any other exceptions and re-raise so interactive shell can catch them
            raise e
        finally:
            sys.stdout = orig_stdout

    print("\nQHA workflow completed successfully!")


def add_qha_parser(subparsers):
    qha_parser = subparsers.add_parser(
        "run-qha",
        help="Quasi-Harmonic Approximation (Thermal expansion, Free energy)",
        description=MACER_LOGO + f"\nmacer_phonopy qha (v{__version__}): Perform Quasiharmonic Approximation (QHA) workflow using MLFFs and phonopy.",
        epilog="""
Examples:
  # 1. Standard QHA workflow: Auto-detect strain range, compute up to 1300K
  macer phonopy qha -p POSCAR --dim 2 2 2 --tmax 1300 --ff mattersim

  # 2. Manual strain range: +/- 5% volume change with 11 points
  macer phonopy qha -p POSCAR --dim 2 2 2 --num-volumes 11 --length-scale 0.05

  # 3. Anisotropic QHA: Apply strain only to the c-axis (e.g., 2D materials)
  macer phonopy qha -p POSCAR --dim 3 3 1 --select-axis c --eos vinet

  # 4. High-precision: Relax atomic positions at each volume step
  macer phonopy qha -p POSCAR --dim 2 2 2 --relax-atom --initial-fmax 0.005
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        aliases=["qha"],
    )

    # General & Input
    general_group = qha_parser.add_argument_group("General & Input")
    general_group.add_argument("--poscar", "-p", required=False, default=None, help="Input crystal structure file (e.g., POSCAR).")
    general_group.add_argument("--cif", "-c", required=False, default=None, help="Input CIF file.")
    general_group.add_argument("--output-dir", help="Directory to save all output files.")

    # MLFF Settings
    mlff_group = qha_parser.add_argument_group("MLFF Model Settings")
    mlff_group.add_argument(
        "--ff",
        choices=ALL_SUPPORTED_FFS,
        default=DEFAULT_FF,
        help=f"Force field to use. (default: {DEFAULT_FF})"
    )
    mlff_group.add_argument("--model", type=str, default=None, help="Path to the force field model file.")
    mlff_group.add_argument("--modal", type=str, default=None, help="Modal for certain force fields like SevenNet.")
    mlff_group.add_argument(
        "--device",
        choices=["cpu", "mps", "cuda"],
        default=DEFAULT_DEVICE,
        help=f"Compute device. (default: {DEFAULT_DEVICE})"
    )

    # Relaxation Settings
    relax_group = qha_parser.add_argument_group("Structure Relaxation Settings")
    relax_group.add_argument("--isif", type=int, default=3,
                       help="ISIF flag for initial cell relaxation, passed to 'macer relax'. "
                            "ISIF=3 (default) relaxes atoms, shape, and volume. ISIF=0 skips relaxation.")
    relax_group.add_argument("--initial-fmax", type=float, default=1e-2,
                        help="Force convergence threshold for initial relaxation in eV/Å. (default: 0.001)")
    relax_group.add_argument("--initial-symprec", type=float, default=1e-3,
                        help="Symmetry tolerance for FixSymmetry during initial relaxation (default: 1e-3 Å).")
    relax_group.add_argument(
        "--initial-symmetry-off",
        dest="initial_use_symmetry",
        action="store_false",
        help="Disable FixSymmetry constraint during initial relaxation."
    )
    relax_group.add_argument("--relax-atom", action="store_true",
                       help="Relax atomic positions at each volume scaling. If not set, atoms are fixed. (default: False)")

    # QHA Workflow Settings
    qha_wf_group = qha_parser.add_argument_group("QHA Workflow Settings")
    qha_wf_group.add_argument("--eos", type=str, default="vinet",
                       choices=["vinet", "birch_murnaghan", "murnaghan", "local_poly"],
                       help="Equation of state for fitting Helmholtz free energy. (default: vinet)")
    qha_wf_group.add_argument("--num-volumes", type=int, default=5,
                       help="Number of volume points to sample for the E-V curve. (default: 5)")
    qha_wf_group.add_argument("--length-scale", "-ls", type=float, default=None,
                       help="Symmetric strain range for E-V curve, e.g., 0.05 for \u00b15%%. "
                            "If not set, estimated automatically. Mutually exclusive with --length-factor-*.")
    qha_wf_group.add_argument("--length-factor-min", type=float, default=None,
                       help="Minimum absolute length scaling factor. Requires --length-factor-max. "
                            "Mutually exclusive with --length-scale.")
    qha_wf_group.add_argument("--length-factor-max", type=float, default=None,
                       help="Maximum absolute length scaling factor. Requires --length-factor-min. "
                            "Mutually exclusive with --length-scale.")
    qha_wf_group.add_argument("--target-energy", type=float, default=10.0,
                       help="Target energy in meV for bulk modulus-based strain estimation. (default: 10.0)")
    qha_wf_group.add_argument("--select-axis", type=str, default=None,
                       help="Comma-separated list of axes (a,b,c) to apply length scaling to. "
                            "e.g., 'c' or 'a,b'. Default is all axes ('a,b,c').")

    # Supercell & Displacement Settings
    supercell_group = qha_parser.add_argument_group("Supercell & Displacement Settings")
    supercell_group.add_argument("--dim", type=int, nargs='+', default=None,
                       help='Set supercell dimension. Accepts 3 integers for a diagonal matrix (e.g., "2 2 2") '
                            'or 9 integers for a full matrix (e.g., "1 0 1 -1 1 1 0 -1 1"). '
                            'Overrides --min-length.')
    supercell_group.add_argument("--min-length", "-l", type=float, default=15.0,
                       help="Minimum supercell lattice vector length in Å to determine DIM automatically if --dim is not set. (default: 15.0)")
    supercell_group.add_argument("--amplitude", type=float, default=0.01,
                       help="Displacement amplitude for phonopy in Å. (default: 0.01)")
    pm_group = supercell_group.add_mutually_exclusive_group()
    pm_group.add_argument("--pm", dest="is_plusminus", action="store_true",
                        help="Set plus-minus displacements for all directions.")
    pm_group.add_argument("--no-pm", dest="is_plusminus", action="store_false",
                        help="Do not use plus-minus displacements (default is auto).")
    qha_parser.set_defaults(is_plusminus='auto')
    supercell_group.add_argument("--nodiag", dest="is_diagonal", action="store_false",
                       help="Do not generate diagonal displacements. (default: enabled)")
    supercell_group.add_argument("--mass", nargs='+', help="Specify atomic masses. Format: Symbol Mass Symbol Mass ... (e.g. --mass H 2.014 D 2.014)")

    # Phonopy Settings
    phonopy_group = qha_parser.add_argument_group("Phonopy Settings")
    phonopy_group.add_argument("--tolerance-phonopy", type=float, default=1e-3,
                         help="Symmetry tolerance for phonopy in Å. (default: 1e-3)")
    phonopy_group.add_argument("--mesh", type=int, nargs=3, default=[7, 7, 7],
                       help="Reciprocal space mesh for thermal property calculation. (default: 7 7 7)")
    phonopy_group.add_argument("--tmax", type=int, default=1300,
                       help="Maximum temperature for thermal property calculation in Kelvin. (default: 1300)")
    phonopy_group.add_argument("--use-force-constants", action="store_true",
                       help="Use force constants for phonopy calculation. If not set, FORCE_SETS will be used. (default: False)")

    # Local Polynomial EOS Settings
    poly_group = qha_parser.add_argument_group("Local Polynomial EOS Settings")
    poly_group.add_argument("--poly-degree", type=int, default=2, help="Degree of polynomial for 'local_poly' EOS fit. (default: 2)")
    poly_group.add_argument("--poly-points", type=int, default=3, help="Number of points around the minimum to use for 'local_poly' EOS fit. (default: 3)")
    poly_group.add_argument("--smooth-deg", type=int, default=10, help="Degree of polynomial for smoothing the final V-T curve. (default: 3)")

    qha_parser.set_defaults(func=run_qha_workflow)
    return qha_parser
