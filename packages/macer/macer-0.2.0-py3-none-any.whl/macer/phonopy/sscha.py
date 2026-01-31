import argparse
import sys
import os
import shutil
import numpy as np
from pathlib import Path
import subprocess
import yaml
import re
import traceback
import csv
import math # Added import for math module
from tqdm import tqdm
from io import StringIO

from ase.io import read as ase_read, write as ase_write
from ase import Atoms as AseAtoms
from ase.md.langevin import Langevin
from ase.md.verlet import VelocityVerlet
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.units import fs, kB
import phonopy
from phonopy.interface.vasp import read_vasp, write_vasp
try:
    from phonopy.file_IO import write_FORCE_CONSTANTS, parse_FORCE_CONSTANTS, write_fc3_to_hdf5
    _HAS_WRITE_FC3 = True
except ImportError:
    from phonopy.file_IO import write_FORCE_CONSTANTS, parse_FORCE_CONSTANTS
    _HAS_WRITE_FC3 = False
    write_fc3_to_hdf5 = None

from phonopy.structure.atoms import PhonopyAtoms
from phonopy.structure.cells import get_primitive
from phonopy.cui.settings import PhonopyConfParser
from phonopy.phonon.band_structure import get_band_qpoints
from phonopy.physical_units import get_physical_units
from phonopy.phonon.thermal_displacement import ThermalDisplacementMatrices
from phonopy.phonon.random_displacements import RandomDisplacements
from symfc import Symfc
from symfc.utils.utils import SymfcAtoms
from symfc.basis_sets import FCBasisSetO2, FCBasisSetO3
from symfc.solvers import FCSolverO2O3


from scipy.optimize import minimize_scalar
from macer.relaxation.optimizer import relax_structure
import matplotlib.pyplot as plt

from macer.calculator.factory import get_available_ffs, get_calculator, ALL_SUPPORTED_FFS
from macer.defaults import DEFAULT_MODELS, _macer_root, _model_root, DEFAULT_DEVICE, DEFAULT_FF, resolve_model_path
from macer.phonopy.band_path import generate_band_conf
from macer.utils.logger import Logger
# from macer import __version__

# Conversion factor from eV/Angstrom^3 to GPa
EV_A3_TO_GPA = 160.21766208

MACER_LOGO = r"""
███╗   ███╗  █████╗   ██████╗ ███████╗ ██████╗
████╗ ████║ ██╔══██╗ ██╔════╝ ██╔════╝ ██╔══██╗
██╔████╔██║ ███████║ ██║      █████╗   ██████╔╝
██║╚██╔╝██║ ██╔══██║ ██║      ██╔══╝   ██╔══██╗
██║ ╚═╝ ██║ ██║  ██║ ╚██████╗ ███████╗ ██║  ██║
╚═╝     ╚═╝ ╚═╝  ╚═╝  ╚═════╝ ╚══════╝ ╚═╝  ╚═╝
ML-accelerated Atomic Computational Environment for Research
"""


# Helper function copied from macer/phonopy/qha.py to resolve model paths
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

# Determine default force field based on installed extras
available_ffs = get_available_ffs()
_dynamic_default_ff = available_ffs[0] if available_ffs else None


# --- Reweighting SSCHA Utility Functions ---

def compute_weights_from_harmonic_ref(U, FC_ref, FC_trial, beta):
    """
    Calculates reweighting factors for an ensemble generated from a harmonic reference (FC_ref).
    w_i = exp(-0.5 * beta * (u_i^T (FC_trial - FC_ref) u_i))
    """
    diff = FC_trial - FC_ref
    # einsum computes the quadratic form u^T * delta_FC * u for each snapshot n
    quad = np.einsum("ijab,nia,njb->n", diff, U, U)
    exponent = -0.5 * beta * quad
    
    # Subtract max for numerical stability before exp
    exponent -= np.max(exponent)

    w = np.exp(exponent)
    w /= np.sum(w)
    return w

def compute_weights_from_md(U, E, FC_trial, beta):
    """
    Calculates reweighting factors for an ensemble generated from MD (true potential).
    w_i = exp(-beta * (V_harm(FC_trial) - V_true))
    """
    V_harm_trial = 0.5 * np.einsum("ijab,nia,njb->n", FC_trial, U, U)
    V_true = E
    exponent = -beta * (V_harm_trial - V_true)
    
    # Subtract max for numerical stability before exp
    exponent -= np.max(exponent)
    
    w = np.exp(exponent)
    w /= np.sum(w)
    return w

def need_regeneration(w, FC_new, FC_old, ess_threshold):
    """
    Check if ensemble regeneration is needed based on ESS, weight entropy, and FC drift.
    """
    ess = 1.0 / np.sum(w**2)
    print(f"  Effective sample size (ESS) ~ {ess:.1f} / {len(w)}")
    if ess < ess_threshold:
        print(f"  INFO: Regeneration triggered by low ESS ({ess:.1f} < {ess_threshold:.1f})")
        return True

    # Weight entropy check
    H = -np.sum(w * np.log(w + 1e-15))
    # Compare with entropy of a uniform distribution
    if H < 0.1 * np.log(len(w)):
        print(f"  INFO: Regeneration triggered by low weight entropy (H={H:.3f}).")
        return True

    # FC drift check
    if FC_old is not None:
        fc_diff = np.linalg.norm(FC_new - FC_old)
        fc_norm = np.linalg.norm(FC_old)
        if fc_norm > 1e-9 and (fc_diff / fc_norm) > 0.1:
            print(f"  INFO: Regeneration triggered by large FC drift (diff={fc_diff/fc_norm:.3f} > 0.1)")
            return True
            
    return False

def fit_weighted_fc(U, F, w, ph, include_third_order=False):
    """
    Performs a weighted least-squares fitting of the force constants
    by rescaling the displacements and forces with the square root of the weights.
    """
    sqrtw = np.sqrt(w)[:, None, None]
    U_scaled = sqrtw * U
    F_scaled = sqrtw * F

    if not include_third_order:
        ph.dataset = {'displacements': U_scaled, 'forces': F_scaled}
        ph.produce_force_constants(fc_calculator="symfc")
        return ph.force_constants.copy(), None
    else:
        try:
            fc2, fc3 = _fit_fc2_and_fc3(U_scaled, F_scaled, ph)
            return fc2, fc3
        except RuntimeError as e:
            print(f"  WARNING: FC3 fitting failed with error: {e}")
            print("           Falling back to FC2-only fitting for this iteration.")
            ph.dataset = {'displacements': U_scaled, 'forces': F_scaled}
            ph.produce_force_constants(fc_calculator="symfc")
            return ph.force_constants.copy(), None


def _fit_fc2_and_fc3(U_scaled, F_scaled, ph):
    """
    Performs simultaneous fitting of 2nd and 3rd order force constants using symfc.
    Takes pre-scaled displacements and forces for weighted fitting.
    """
    print("    Fitting 2nd and 3rd order force constants simultaneously using symfc...")
    supercell = ph.supercell
    symfc_supercell = SymfcAtoms(
        cell=supercell.cell,
        scaled_positions=supercell.scaled_positions,
        numbers=supercell.numbers
    )

    print("    Computing FC2 basis set...")
    basis_set_o2 = FCBasisSetO2(symfc_supercell).run()
    if basis_set_o2._blocked_basis_set is None:
        raise RuntimeError("FC2 basis set computation failed, _blocked_basis_set is None.")

    print("    Computing FC3 basis set...")
    basis_set_o3 = FCBasisSetO3(symfc_supercell).run()
    if basis_set_o3._blocked_basis_set is None:
        raise RuntimeError("FC3 basis set computation failed, _blocked_basis_set is None.")

    print("    Solving for FC2 and FC3...")
    solver = FCSolverO2O3([basis_set_o2, basis_set_o3])
    solver.solve(U_scaled, F_scaled)

    # The original call used is_compact_fc=False, so we get the full FCs.
    fc2, fc3 = solver.full_fc

    if fc2 is None or fc3 is None:
        raise RuntimeError("symfc failed to compute FC2/FC3.")

    print("    symfc fitting complete.")
    return fc2, fc3


def _compute_fc3_free_energy(fc3, U, w):
    """
    Computes anharmonic FC3 contribution:
        F(3) = -1/6 * sum_i w_i * u_i^T fc3 u_i u_i
    """
    if fc3 is None:
        return 0.0

    # tensor contraction: u_i_a u_i_b u_i_c Φ_{abc}
    cubic = np.einsum("ijklmn,sil,sjm,skn->s", fc3, U, U, U)
    F3 = -np.sum(w * cubic) / 6.0
    return F3


def compute_weighted_free_energy(U, E, FC, FC3, w, ph, T, mesh, return_components=False):
    """
    Computes the total SSCHA free energy using the reweighting formula.
    """
    # Update the phonopy object with the new force constants to get F_harm
    ph.force_constants = FC
    ph.run_mesh(mesh)
    ph.run_thermal_properties(t_min=T, t_max=T, t_step=T)
    hfe_kJmol = ph.get_thermal_properties_dict()['free_energy'][0]
    hfe = hfe_kJmol / get_physical_units().EvTokJmol

    # Weighted averages of potential energy and harmonic potential energy
    V_mean = np.sum(w * E)
    V_harm = 0.5 * np.sum(w * np.einsum("ijab,nia,njb->n", FC, U, U))

    n_prim = len(ph.supercell) / len(ph.primitive)
    
    # Anharmonic free energy correction from FC3
    F3 = _compute_fc3_free_energy(FC3, U, w)
    
    F_total = hfe + (V_mean - V_harm) / n_prim + F3 / n_prim
    
    if return_components:
        # Note: F3 is included in F_total, but not returned as a separate component yet.
        return F_total, hfe, V_mean / n_prim, V_harm / n_prim
    else:
        return F_total


def _write_ensemble_text(output_path, U, F, E, Stress=None):
    """Writes ensemble data to a human-readable text file."""
    n_snapshots, n_atoms, _ = U.shape
    with open(output_path, 'w') as f:
        f.write(f"# Ensemble data\n")
        f.write(f"# Number of snapshots: {n_snapshots}\n")
        f.write(f"# Number of atoms: {n_atoms}\n")
        f.write("-" * 40 + "\n\n")

        for i in range(n_snapshots):
            f.write(f"## Snapshot: {i+1}\n")
            f.write(f"# Energy: {E[i]:.8f} eV\n")
            if Stress is not None:
                s = Stress[i]
                f.write(f"# Stress (Voigt): {s[0]:.6f} {s[1]:.6f} {s[2]:.6f} {s[3]:.6f} {s[4]:.6f} {s[5]:.6f} eV/A^3\n")
            f.write("\n")
            
            f.write("# Displacements (U) [Angstrom]\n")
            f.write("# Atom        Ux          Uy          Uz\n")
            for j in range(n_atoms):
                f.write(f"{j+1:6d}  {U[i, j, 0]:11.6f} {U[i, j, 1]:11.6f} {U[i, j, 2]:11.6f}\n")
            f.write("\n")

            f.write("# Forces (F) [eV/Angstrom]\n")
            f.write("# Atom        Fx          Fy          Fz\n")
            for j in range(n_atoms):
                f.write(f"{j+1:6d}  {F[i, j, 0]:11.6f} {F[i, j, 1]:11.6f} {F[i, j, 2]:11.6f}\n")
            f.write("\n" + "-" * 40 + "\n\n")


def _read_ensemble_text(input_path):
    """Reads ensemble data from a human-readable text file."""
    with open(input_path, 'r') as f:
        lines = f.readlines()

    # Split by snapshot marker and filter out empty strings
    snapshots_text = "".join(lines).split("## Snapshot:")
    snapshots_text = [s for s in snapshots_text if s.strip()]

    if not snapshots_text:
        raise ValueError("No snapshots found in the text ensemble file.")

    U_list, F_list, E_list, Stress_list = [], [], [], []
    has_stress = "# Stress" in snapshots_text[0]

    for snapshot_text in snapshots_text:
        lines = snapshot_text.strip().split('\n')
        
        current_line = 0
        # Parse Energy
        try:
            E_list.append(float(lines[current_line].split(":")[1].split("eV")[0]))
            current_line += 1
        except (IndexError, ValueError) as e:
            raise ValueError(f"Could not parse energy from line: {lines[0]}") from e

        if has_stress:
            try:
                stress_line = lines[current_line]
                stress_voigt = [float(s) for s in stress_line.split(":")[1].split("eV/A^3")[0].strip().split()]
                Stress_list.append(stress_voigt)
                current_line += 1
            except (IndexError, ValueError) as e:
                raise ValueError(f"Could not parse stress from line: {stress_line}") from e

        # Parse U and F
        snapshot_U, snapshot_F = [], []
        mode = None
        for line in lines[current_line:]:
            line = line.strip()
            if not line:
                mode = None
                continue
            
            if line.startswith("# Displacements"):
                mode = 'U'
                continue
            elif line.startswith("# Forces"):
                mode = 'F'
                continue
            elif line.startswith("#"):
                continue

            try:
                parts = [float(p) for p in line.split()[1:]]
                if mode == 'U':
                    snapshot_U.append(parts)
                elif mode == 'F':
                    snapshot_F.append(parts)
            except (ValueError, IndexError) as e:
                raise ValueError(f"Could not parse data from line: {line}") from e
        
        if snapshot_U: U_list.append(snapshot_U)
        if snapshot_F: F_list.append(snapshot_F)

    if len(U_list) != len(F_list) or len(U_list) != len(E_list):
        raise ValueError("Inconsistent number of snapshots for E, U, and F.")

    stress_array = np.array(Stress_list) if Stress_list else None
    return np.array(U_list), np.array(F_list), np.array(E_list), stress_array


# --- End of Utility Functions ---


def _read_band_yaml_data(band_yaml_path):

    """Reads data from a band.yaml file."""
    with open(band_yaml_path, 'r') as f:
        data = yaml.load(f, Loader=yaml.CLoader)

    frequencies = []
    distances = []
    qpoints = []
    for v in data["phonon"]:
        frequencies.append([f["frequency"] for f in v["band"]])
        distances.append(v["distance"])
        qpoints.append(v["q-position"])
    
    distances = np.array(distances)
    frequencies = np.array(frequencies)
    qpoints = np.array(qpoints)
    segment_nqpoint = data["segment_nqpoint"]
    
    bands = []
    q_idx = 0
    for nq in segment_nqpoint:
        bands.append(qpoints[q_idx:q_idx + nq])
        q_idx += nq
        
    return distances, frequencies, bands, segment_nqpoint


def _write_band_dat(band_yaml_path, dat_filename):
    """Writes a band.yaml file to a gnuplot-friendly .dat file."""
    try:
        distances, frequencies, _, segment_nqpoint = _read_band_yaml_data(band_yaml_path)

        with open(dat_filename, 'w') as f:
            f.write("# q-distance, frequency\n")
            for i, freqs_band in enumerate(frequencies.T):
                f.write(f"# mode {i + 1}\n")
                q_idx = 0
                for nq in segment_nqpoint:
                    for d, freq in zip(distances[q_idx:q_idx + nq], freqs_band[q_idx:q_idx + nq]):
                        f.write(f"{d:12.8f} {freq:15.8f}\n")
                    q_idx += nq
                    f.write("\n")
                f.write("\n")
        
        print(f"    Band structure data written to {dat_filename}")
    except Exception as e:
        print(f"    Could not write .dat file: {e}")


def _plot_iterative_band_structure(ph, band_conf_path, iter_num, input_poscar_stem):
    """Helper to plot band structure for a given iteration."""
    print(f"  Plotting band structure for iteration {iter_num}...")
    try:
        conf_parser = PhonopyConfParser(filename=str(band_conf_path))
        settings = conf_parser.settings
        
        npoints = settings.band_points if settings.band_points else 51
        qpoints = get_band_qpoints(settings.band_paths, npoints=npoints)
        labels = settings.band_labels
        path_connections = []
        for paths in settings.band_paths:
            path_connections += [True] * (len(paths) - 2)
            path_connections.append(False)

        ph.run_band_structure(qpoints, path_connections=path_connections, labels=labels)
        
        pdf_name = f"band-{input_poscar_stem}_{iter_num}.pdf"
        yaml_name = f"band-{input_poscar_stem}_{iter_num}.yaml"
        dat_name = f"band-{input_poscar_stem}_{iter_num}.dat"

        ph.plot_band_structure().savefig(pdf_name)
        print(f"    Band structure plot saved to {pdf_name}")
        
        ph.write_yaml_band_structure(filename=yaml_name)
        print(f"    Band structure yaml saved to {yaml_name}")
        _write_band_dat(yaml_name, dat_name)

    except Exception as e:
        print(f"    Could not plot band structure for iteration {iter_num}: {e}")
        traceback.print_exc()


def _plot_sscha_convergence(log_file, output_dir, prefix):
    """Plots the SSCHA free energy convergence from a log file."""
    try:
        data = np.loadtxt(log_file, comments='#')
        if data.ndim == 1: data = np.array([data])
        if data.shape[0] < 1: print("  Convergence log is empty, skipping plot."); return

        iterations = data[:, 0]
        free_energies_eV = data[:, 1]
        
        fig, ax1 = plt.subplots(figsize=(6, 4))
        
        ax1.plot(iterations, free_energies_eV, color="tab:blue", marker="o", lw=1.0, label="SSCHA Free Energy (eV)")
        ax1.set_xlabel("SSCHA Iteration")
        ax1.set_ylabel("SSCHA Free Energy (eV)", color="tab:blue")
        ax1.tick_params(axis="y", labelcolor="tab:blue")
        ax1.grid(alpha=0.3)

        if data.shape[0] > 1 and data.shape[1] > 3:
            delta_energies = data[1:, 3]
            ax2 = ax1.twinx()
            ax2.plot(iterations[1:], delta_energies, color="tab:red", marker="s", lw=1.0, label="ΔF (meV/atom)")
            ax2.set_ylabel("Free Energy Change (meV/atom)", color="tab:red")
            ax2.tick_params(axis="y", labelcolor="tab:red")
            ax2.set_yscale('log')
            
            lines, labels = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc="best")
        else:
            ax1.legend(loc="best")

        plt.title(f"SSCHA Convergence ({prefix})")
        plt.tight_layout()
        pdf_name = os.path.join(output_dir, f"sscha_convergence-{prefix}.pdf")
        plt.savefig(pdf_name)
        plt.close(fig)
        print(f"  Saved convergence plot -> {pdf_name}")

    except Exception as e:
        print(f"  Could not plot convergence: {e}")


def _run_sscha_at_volume(args, initial_poscar_path: Path, output_dir: Path, quiet=False, perform_initial_relax: bool = True, mass_map: dict | None = None):
    """
    Performs a single SSCHA calculation for a given structure and temperature.
    Returns the final converged free energy and other results.
    """
    model_path = _resolve_model_path(args.ff, args.model)
    if model_path and os.path.exists(model_path):
        model_path = os.path.abspath(model_path)

    if not quiet:
        print(f"--- Starting SSCHA calculation for {initial_poscar_path.name} at T={args.temperature}K ---")
        if getattr(args, 'qscaild_selfconsistent', False):
            print("  INFO: QSCAILD-style self-consistency enabled. Reference method forced to 'random'.")
            args.reference_method = 'random'
        print(f"Results will be saved in: {output_dir}")

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

    # Determine the number of samples to use, accommodating user input quirks
    num_random_samples = args.reference_n_samples
    if (
        args.reference_method == 'random' and
        args.reference_md_nsteps != 5000 and  # Default for md_nsteps
        args.reference_n_samples == 2000      # Default for n_samples
    ):
        if not quiet:
            print(f"  INFO: --reference-method is 'random' but --reference-md-nsteps was specified.")
            print(f"        Using value from --reference-md-nsteps ({args.reference_md_nsteps}) as the number of random samples.")
        num_random_samples = args.reference_md_nsteps

    original_cwd = os.getcwd()
    os.chdir(output_dir)

    calc_kwargs = {"device": args.device, "modal": args.modal}
    if args.ff == "mace":
        calc_kwargs["model_paths"] = [model_path]
    else:
        calc_kwargs["model_path"] = model_path
    calculator = get_calculator(ff_name=args.ff, **calc_kwargs)

    if perform_initial_relax:
        if not quiet: print("\n--- Step 1: Calculating initial harmonic force constants (T=0K) ---")
        if not quiet: print("Relaxing initial structure...")
        copied_input_poscar_path = output_dir / f"POSCAR_unitcell_{initial_poscar_path.stem}"
        shutil.copy(initial_poscar_path, copied_input_poscar_path)
        relaxed_poscar_name = "CONTCAR-relax"
        try:
            relax_structure(
                input_file=str(copied_input_poscar_path), isif=3, fmax=args.initial_fmax,
                device=args.device, contcar_name=relaxed_poscar_name,
                xml_name=f"vasprun-{initial_poscar_path.stem}.xml", make_pdf=False,
                ff=args.ff, model_path=model_path, modal=args.modal, quiet=True,
                symprec=args.symprec, use_symmetry=getattr(args, 'initial_use_symmetry', True)
            )
            relaxed_poscar_path = output_dir / relaxed_poscar_name
            if not relaxed_poscar_path.exists(): raise FileNotFoundError("Relaxed structure not found.")
            unitcell = read_vasp(str(relaxed_poscar_path))
        except Exception as e:
            print(f"Error during initial relaxation: {e}"); traceback.print_exc()
            os.chdir(original_cwd)
            raise e
    else:
        # When called from volume optimization, do not relax the cell. Use the provided one.
        if not quiet: print("\n--- Step 1: Using pre-scaled structure for this volume step ---")
        unitcell = read_vasp(str(initial_poscar_path))
        relaxed_poscar_path = initial_poscar_path # for band path generation

    supercell_matrix = None
    if args.dim:
        if len(args.dim) == 3: supercell_matrix = np.diag(args.dim)
        elif len(args.dim) == 9: supercell_matrix = np.array(args.dim).reshape(3, 3)
        else: raise ValueError("Error: --dim must be 3 or 9 integers.")
    else:
        cell = unitcell.cell
        vector_lengths = [np.linalg.norm(v) for v in cell]
        if any(v == 0 for v in vector_lengths): raise ValueError("Error: Lattice vector length is zero.")
        scaling_factors = [int(np.ceil(args.min_length / v)) if v > 0 else 1 for v in vector_lengths]
        supercell_matrix = np.diag(scaling_factors)
        if not quiet: print(f"Auto-determined supercell DIM = {scaling_factors}")

    ph = phonopy.Phonopy(unitcell, supercell_matrix=supercell_matrix, primitive_matrix="auto", symprec=args.symprec)
    
    # Apply mass override if provided
    if mass_map:
        if not quiet: print("\n--- Applying mass override ---")
        current_masses = ph.masses
        symbols = ph.primitive.symbols
        new_masses = []
        for s, m in zip(symbols, current_masses):
            if s in mass_map:
                new_masses.append(mass_map[s])
            else:
                new_masses.append(m)
        ph.masses = new_masses
        if not quiet: print(f"  Applied mass override: {mass_map}")

    base_supercell = ph.supercell

    band_conf_path = output_dir / "band.conf" if args.plot_bands and not quiet else None
    if band_conf_path:
        if not quiet: print("\n--- Generating band.conf from relaxed structure ---")
        dim_override = " ".join(map(str, supercell_matrix.flatten().astype(int)))
        generate_band_conf(
            poscar_path=relaxed_poscar_path, out_path=band_conf_path, symprec=args.symprec,
            gamma_label=args.gamma_label, print_summary_flag=not quiet, dim_override=dim_override
        )

    if args.read_initial_fc:
        if not quiet: print(f"\n--- Reading initial FORCE_CONSTANTS from {args.read_initial_fc} ---")
        ph.force_constants = parse_FORCE_CONSTANTS(filename=args.read_initial_fc)
    else:
        ph.generate_displacements(distance=args.amplitude, is_plusminus=args.pm, is_diagonal=not args.nodiag)
        if not quiet: print(f"Calculating forces for {len(ph.supercells_with_displacements)} displaced supercells for initial fc2...")
        forces = [calculator.get_forces(AseAtoms(symbols=scell.symbols, cell=scell.cell, scaled_positions=scell.scaled_positions, pbc=True)) for scell in ph.supercells_with_displacements]
        ph.forces = forces
        ph.produce_force_constants()
    
    write_FORCE_CONSTANTS(ph.force_constants, filename="FORCE_CONSTANTS_init")
    if not quiet: print("Initial FORCE_CONSTANTS_init has been created.")

    if band_conf_path:
        _plot_iterative_band_structure(ph, band_conf_path, "harmonic", initial_poscar_path.stem)

    # --- SSCHA Main Loop with Ensemble Regeneration ---
    FC_ref = ph.force_constants.copy()
    FC_current = FC_ref.copy()
    FC3_current = None
    U_ref, F_ref, E_ref, Stress_ref = None, None, None, None
    sscha_converged = False
    final_free_energy = None
    final_w = None

    with open("sscha_convergence.log", "w") as log_file:
        log_file.write("# Iteration    Free_Energy(eV)    Free_Energy(meV/atom)    Delta_F(meV/atom)\n")
        free_energy_history = []
        
        for regen_step in range(args.max_regen + 1):
            # --- Step 1.5: Generate or Load Reference Ensemble ---
            if regen_step == 0:
                ensemble_path = Path(args.reference_ensemble) if args.reference_ensemble else Path("reference_ensemble.npz")
                if args.reference_ensemble:
                    ensemble_path = Path(original_cwd) / ensemble_path
                
                try:
                    if not quiet: print(f"\n--- Attempting to load reference ensemble from {ensemble_path} ---")
                    if not ensemble_path.exists(): raise FileNotFoundError(f"File not found at {ensemble_path}")
                    
                    if str(ensemble_path).endswith('.txt'):
                        U_ref, F_ref, E_ref, Stress_ref = _read_ensemble_text(ensemble_path)
                    else:
                        data = np.load(ensemble_path)
                        U_ref, F_ref, E_ref = data['U'], data['F'], data['E']
                        Stress_ref = data.get('Stress')
                    
                    if not quiet: print("--- Reference ensemble loaded successfully. ---")
                    if U_ref.shape[1] != len(ph.supercell):
                        raise ValueError(f"Ensemble atom count ({U_ref.shape[1]}) does not match supercell ({len(ph.supercell)}).")

                except (FileNotFoundError, ValueError, KeyError, IsADirectoryError, IndexError) as e:
                    if not quiet: print(f"--- Could not load reference ensemble ({e}), generating a new one. ---")
                    U_ref, F_ref, E_ref, Stress_ref = None, None, None, None # Signal to generate
            
            if U_ref is None:
                method_to_use = args.reference_method if regen_step == 0 else 'random'
                if not quiet: print(f"\n--- Step 1.5: Generating reference ensemble (Method: {method_to_use}, Regen step: {regen_step+1}) ---")
                
                if method_to_use == 'random':
                    if not quiet: print(f"  Generating {num_random_samples} random displacement snapshots...")
                    rd = RandomDisplacements(base_supercell, ph.primitive, FC_ref)
                    rd.run(args.temperature, number_of_snapshots=num_random_samples)
                    U_ref = rd.u
                    
                    if not quiet: print(f"  Calculating forces and energies for {len(U_ref)} new reference structures...")
                    F_list, E_list, Stress_list = [], [], []
                    xdatcar_images = []
                    iterator = tqdm(U_ref, desc="New Ensemble F/E")
                    for disp in iterator:
                        snapshot = base_supercell.copy(); snapshot.positions += disp
                        ase_snapshot = AseAtoms(symbols=snapshot.symbols, positions=snapshot.positions, cell=snapshot.cell, pbc=True)
                        if args.write_xdatcar and not quiet: xdatcar_images.append(ase_snapshot.copy())
                        ase_snapshot.calc = calculator
                        F_list.append(ase_snapshot.get_forces())
                        E_list.append(ase_snapshot.get_potential_energy())
                        if args.optimize_volume:
                            Stress_list.append(ase_snapshot.get_stress(voigt=True))

                    F_ref, E_ref = np.array(F_list), np.array(E_list)
                    Stress_ref = np.array(Stress_list) if args.optimize_volume else None

                    if args.write_xdatcar and not quiet:
                        print(f"    Writing {len(xdatcar_images[::args.xdatcar_step])} frames to XDATCAR-reference-ensemble...")
                        ase_write('XDATCAR-reference-ensemble', xdatcar_images[::args.xdatcar_step], format='vasp-xdatcar')
                        print("    XDATCAR file has been created.")

                elif method_to_use == 'md':
                    if not quiet:
                        print(f"  Generating ensemble via MD ({args.reference_md_nequil} equil. + {args.reference_md_nsteps} sampling steps)...")
                    md_atoms = AseAtoms(symbols=base_supercell.symbols, positions=base_supercell.positions, cell=base_supercell.cell, pbc=True)
                    md_atoms.calc = calculator
                    MaxwellBoltzmannDistribution(md_atoms, temperature_K=args.temperature)
                    
                    if args.md_thermostat == 'langevin':
                        dyn = Langevin(md_atoms, args.reference_md_tstep * fs, temperature_K=args.temperature, friction=args.md_friction)
                        if not quiet: print(f"  Using Langevin thermostat (T={args.temperature}K, friction={args.md_friction} ps^-1)")
                    else:
                        dyn = VelocityVerlet(md_atoms, args.reference_md_tstep * fs)
                        if not quiet: print("  Using NVE (VelocityVerlet) thermostat")

                    if args.reference_md_nequil > 0:
                        if not quiet: print(f"  Running {args.reference_md_nequil} equilibration steps...")
                        with tqdm(total=args.reference_md_nequil, desc="MD Equil.") as pbar:
                            def update_progress(): pbar.update(1)
                            dyn.attach(update_progress, interval=1)
                            dyn.run(args.reference_md_nequil)
                            dyn.observers.pop()

                    if not quiet: print(f"  Running {args.reference_md_nsteps} sampling steps...")
                    U_list, F_list, E_list, Stress_list, csv_data, xdatcar_images = [], [], [], [], [], []
                    R0 = md_atoms.get_positions()
                    csv_header = ["Time[ps]", "Temperature[K]", "E_pot[eV]", "E_kin[eV]", "E_tot[eV]"]

                    def collect_sample(a=md_atoms):
                        U_list.append(a.get_positions() - R0)
                        F_list.append(a.get_forces())
                        E_list.append(a.get_potential_energy())
                        if args.optimize_volume:
                            Stress_list.append(a.get_stress(voigt=True))

                    def log_for_csv(a=md_atoms):
                        epot = a.get_potential_energy(); ekin = a.get_kinetic_energy(); temp = ekin / (1.5 * kB * len(a))
                        time_ps = dyn.get_time() / 1000.0
                        csv_data.append([time_ps, temp, epot, ekin, epot + ekin])
                    
                    with tqdm(total=args.reference_md_nsteps, desc="MD Sampling") as pbar:
                        def update_progress(): pbar.update(1)
                        dyn.attach(collect_sample, interval=1)
                        if not quiet: dyn.attach(log_for_csv, interval=1)
                        dyn.attach(update_progress, interval=1)
                        if args.write_xdatcar and not quiet:
                            def save_for_xdatcar(a=md_atoms): xdatcar_images.append(a.copy())
                            dyn.attach(save_for_xdatcar, interval=args.xdatcar_step)
                        dyn.run(args.reference_md_nsteps)

                    U_ref, F_ref, E_ref = np.array(U_list), np.array(F_list), np.array(E_list)
                    Stress_ref = np.array(Stress_list) if args.optimize_volume else None
                    
                    if not quiet: print("  Correcting for center-of-mass drift in MD trajectory...")
                    U_ref -= np.mean(U_ref, axis=1)[:, np.newaxis, :]

                    if not quiet:
                        print("  Writing MD output files...")
                        with open('reference-ensemble-md.csv', 'w', newline='') as f:
                            writer = csv.writer(f); writer.writerow(csv_header); writer.writerows(csv_data)
                        print("    MD data saved to reference-ensemble-md.csv")
                        if args.write_xdatcar:
                            print(f"    Writing {len(xdatcar_images)} frames to XDATCAR-reference-ensemble...")
                            ase_write('XDATCAR-reference-ensemble', xdatcar_images, format='vasp-xdatcar')
                            print("    XDATCAR file has been created.")

                save_dict = {"U": U_ref, "F": F_ref, "E": E_ref}
                if Stress_ref is not None:
                    save_dict["Stress"] = Stress_ref
                np.savez("reference_ensemble.npz", **save_dict)
                if not quiet:
                    _write_ensemble_text("reference_ensemble.txt", U_ref, F_ref, E_ref, Stress=Stress_ref)
                    print("  Ensemble generation complete.")

            # --- Step 2: Inner SSCHA Reweighting Loop ---
            ess_collapsed = False
            beta = 1.0 / (kB * args.temperature)
            n_atom_primitive = len(ph.primitive)

            for i in range(args.max_iter):
                iter_id = len(free_energy_history) + 1
                if not quiet: print(f"\n--- SSCHA Reweighting Iteration {iter_id} (Regen step {regen_step+1}) at T={args.temperature}K ---")
                try:
                    current_method = args.reference_method if regen_step == 0 else 'random'
                    if current_method == 'md':
                         w = compute_weights_from_md(U_ref, E_ref, FC_current, beta)
                    else:
                         w = compute_weights_from_harmonic_ref(U_ref, FC_ref, FC_current, beta)

                    FC_new, FC3_new = fit_weighted_fc(
                        U_ref, F_ref, w, ph, include_third_order=args.include_third_order
                    )

                    if i > 0 and need_regeneration(w, FC_new, FC_current, args.ess_collapse_ratio * len(w)):
                        if regen_step < args.max_regen:
                            if not quiet: print("  Triggering ensemble regeneration.")
                            ess_collapsed = True
                            break
                        else:
                            if not quiet: print("  WARNING: ESS collapsed but regeneration limit reached. Continuing iteration.")
                    
                    final_free_energy, hfe, v_mean, v_harm = compute_weighted_free_energy(
                        U_ref, E_ref, FC_current, FC3_current, w, ph, args.temperature, args.mesh, return_components=True
                    )
                    if not quiet: print(f"  DEBUG: F_total={final_free_energy:.6f} | F_harm={hfe:.6f} | <V>={v_mean:.6f} | <V_harm>={v_harm:.6f}")

                    f_sscha_mev_atom = (final_free_energy * 1000) / n_atom_primitive
                    delta_f = abs(f_sscha_mev_atom - free_energy_history[-1]) if free_energy_history else 0.0
                    
                    log_file.write(f"{iter_id:8d}    {final_free_energy:20.6f}    {f_sscha_mev_atom:20.6f}    {delta_f:20.6f}\n")
                    log_file.flush()
                    if not quiet: print(f"  SSCHA Free Energy: {f_sscha_mev_atom:.6f} meV/atom")
                    free_energy_history.append(f_sscha_mev_atom)

                    if (iter_id) % args.save_every == 0 and not quiet:
                        iter_fc_filename = f"FORCE_CONSTANTS_SSCHA_T{args.temperature}_i{iter_id}"
                        write_FORCE_CONSTANTS(FC_current, filename=iter_fc_filename)
                        print(f"  Iteration {iter_id} force constants saved to {iter_fc_filename}")

                        if FC3_new is not None:
                            if _HAS_WRITE_FC3:
                                iter_fc3_filename = f"fc3_SSCHA_T{args.temperature}_i{iter_id}.hdf5"
                                write_fc3_to_hdf5(FC3_new, filename=iter_fc3_filename)
                                print(f"  Iteration {iter_id} 3rd order force constants saved to {iter_fc3_filename}")
                            else:
                                print("  WARNING: phonopy version is too old to save fc3.hdf5. Skipping.")

                        if band_conf_path:
                            ph.force_constants = FC_current
                            _plot_iterative_band_structure(ph, band_conf_path, iter_id, initial_poscar_path.stem)

                    alpha = args.fc_mixing_alpha
                    FC_current = (1 - alpha) * FC_current + alpha * FC_new
                    if FC3_new is not None:
                        if FC3_current is None:
                            FC3_current = FC3_new.copy()
                        else:
                            FC3_current = (1 - alpha) * FC3_current + alpha * FC3_new

                    if delta_f < args.free_energy_conv and i > 0:
                        if not quiet: print(f"\nFree energy converged to within {args.free_energy_conv} meV/atom.")
                        sscha_converged = True
                        break

                except Exception as e:
                    print(f"Error during SSCHA iteration {iter_id}: {e}"); traceback.print_exc()
                    os.chdir(original_cwd)
                    raise e
            
            if sscha_converged:
                break 
            
            if ess_collapsed:
                if regen_step < args.max_regen:
                    FC_ref = FC_current.copy()
                    ph.force_constants = FC_ref
                    U_ref, F_ref, E_ref, Stress_ref = None, None, None, None
                    continue
                else:
                    if not quiet: print("  WARNING: Ensemble ESS collapsed but max regeneration limit reached. Proceeding with current ensemble.")
                    break
            
            if not sscha_converged:
                if not quiet: print(f"\nWARNING: SSCHA did not converge after {args.max_iter} iterations.")
                break

    if not quiet:
        _plot_sscha_convergence("sscha_convergence.log", output_dir, initial_poscar_path.stem)
        print("\n--- Step 3: Final analysis ---")
        final_fc_path = output_dir / "FORCE_CONSTANTS_SSCHA_final"
        write_FORCE_CONSTANTS(FC_current, filename=str(final_fc_path))
        print(f"\nFinal effective force constants saved to {final_fc_path.name}")

    ph.force_constants = FC_current

    # Final weights are always calculated now, outside the quiet block
    beta = 1.0 / (kB * args.temperature)
    final_method = args.reference_method if (regen_step == 0 and U_ref is not None) else 'random'
    if final_method == 'md':
         final_w = compute_weights_from_md(U_ref, E_ref, FC_current, beta)
    else:
         final_w = compute_weights_from_harmonic_ref(U_ref, FC_ref, FC_current, beta)

    if not quiet:
        print("\nCalculating weighted average structure and distribution...")
        try:
            U_avg = np.sum(final_w[:, np.newaxis, np.newaxis] * U_ref, axis=0)
            average_supercell = base_supercell.copy()
            average_supercell.positions += U_avg
            write_vasp("POSCAR_average", average_supercell, direct=True)
            print(f"Weighted average structure saved to POSCAR_average")

            dist_file_path = "distribution.dat"
            print(f"Writing atomic distribution data to {dist_file_path}...")
            with open(dist_file_path, 'w') as f:
                f.write("# atom_index  symbol        dx          dy          dz       weight\n")
                for i in range(len(U_ref)):
                    w_i = final_w[i]
                    for j in range(len(base_supercell.symbols)):
                        R_ij = base_supercell.positions[j] + U_ref[i, j]
                        delta_R_ij = R_ij - average_supercell.positions[j]
                        f.write(
                            f"{j+1:11d} {base_supercell.symbols[j]:>6s}  "
                            f"{delta_R_ij[0]:11.6f} {delta_R_ij[1]:11.6f} {delta_R_ij[2]:11.6f}  "
                            f"{w_i:11.6e}\n"
                        )
            print("Distribution data file has been created.")
        except Exception as e:
            print(f"Could not calculate or save the average structure/distribution: {e}")
            traceback.print_exc()

    if band_conf_path:
        _plot_iterative_band_structure(ph, band_conf_path, "final", initial_poscar_path.stem)

    if args.no_save_reference_ensemble and not args.reference_ensemble:
        for ext in ['.npz', '.txt']:
            if (output_dir / f"reference_ensemble{ext}").exists():
                (output_dir / f"reference_ensemble{ext}").unlink()
                if not quiet: print(f"Removed temporary reference ensemble file: reference_ensemble{ext}")

    os.chdir(original_cwd)
    if not quiet: print("\n--- Phonopy SSCHA workflow finished successfully! ---")
    
    ensemble_data = (U_ref, F_ref, E_ref, Stress_ref, final_w, FC_current)
    return ph, FC_current, ensemble_data, unitcell, final_free_energy


def _run_sscha_workflow_impl(args):
    """Implementation of SSCHA workflow."""
    if args.seed is not None:
        import random
        random.seed(args.seed)
        np.random.seed(args.seed)
        print(f"--- Using random seed: {args.seed} ---")

    print("--- Starting phonopy SSCHA workflow ---")
    
    is_cif_mode = False
    if args.poscar:
        input_poscar_path = Path(args.poscar).resolve()
    elif args.cif:
        input_poscar_path = Path(args.cif).resolve()
        is_cif_mode = True
    else:
        raise ValueError("Error: Please provide structure input via -p (POSCAR) or -c (CIF) option.")

    if not input_poscar_path.is_file():
        raise FileNotFoundError(f"Input file not found at '{input_poscar_path}'.")

    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    else:
        # Fallback if args.output_dir wasn't set by wrapper (should not happen in CLI usage)
        base_output_dir = input_poscar_path.parent / f"sscha_{input_poscar_path.stem}"
        i = 1
        output_dir = base_output_dir
        while output_dir.exists():
            output_dir = Path(f"{base_output_dir}-NEW{i:03d}")
            i += 1
            
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"All results will be saved in: {output_dir}")
    
    # Handle conversion
    if is_cif_mode:
        try:
            converted_poscar = output_dir / "POSCAR_input"
            atoms_in = ase_read(str(input_poscar_path))
            ase_write(str(converted_poscar), atoms_in, format='vasp')
            print(f"Converted {input_poscar_path.name} to {converted_poscar.name}")
            input_poscar_path = converted_poscar
        except Exception as e:
            raise ValueError(f"Error converting CIF {input_poscar_path}: {e}")
    
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

    if not args.optimize_volume:
        _run_sscha_at_volume(args, input_poscar_path, output_dir, mass_map=mass_map)
        return

    # --- Volume Optimization using SciPy Optimizer ---
    print("\n--- Starting self-consistent volume optimization by minimizing Free Energy ---")
    
    # Initial relaxation to get a good starting point
    print("Performing initial relaxation...")
    relaxed_poscar_path = output_dir / "CONTCAR-initial-relax"
    try:
        relax_structure(
            input_file=str(input_poscar_path), isif=3, fmax=args.initial_fmax,
            device=args.device, contcar_name=str(relaxed_poscar_path),
            ff=args.ff, model_path=_resolve_model_path(args.ff, args.model), quiet=True
        )
    except Exception as e:
        print(f"Initial relaxation failed: {e}"); traceback.print_exc()
        raise e

    initial_unitcell = read_vasp(str(relaxed_poscar_path))
    initial_volume = np.linalg.det(initial_unitcell.cell)
    print(f"Initial relaxed volume: {initial_volume:.4f} Å^3")

    # Run a full analysis at the initial relaxed volume
    print("\n--- Running analysis at initial relaxed volume ---")
    initial_dir = output_dir / "initial_relaxed_volume"
    initial_dir.mkdir()
    _run_sscha_at_volume(args, relaxed_poscar_path, initial_dir, quiet=False, perform_initial_relax=False)

    # Set up logging for the volume optimization process
    vol_log_path = output_dir / "volume_optimization.log"
    with open(vol_log_path, 'w') as f:
        f.write("# Step    Volume(A^3)    Free_Energy(eV)    Pressure(GPa)\n")

    # Wrapper for the objective function to be minimized
    _iter_count = 0
    def objective_F(volume, initial_poscar, args, output_dir):
        nonlocal _iter_count
        _iter_count += 1
        
        iter_dir = output_dir / f"vol_opt_{_iter_count:02d}_{volume:.3f}A3"
        iter_dir.mkdir()
        
        scale = (volume / np.linalg.det(initial_poscar.cell))**(1/3)
        scaled_cell = initial_poscar.cell * scale
        scaled_poscar_obj = PhonopyAtoms(
            cell=scaled_cell,
            scaled_positions=initial_poscar.scaled_positions,
            numbers=initial_poscar.numbers
        )
        
        poscar_path = iter_dir / "POSCAR"
        write_vasp(str(poscar_path), scaled_poscar_obj)
        
        print(f"\n--- Optimizing F at V={volume:.4f} Å^3 (Step {_iter_count}/{args.max_volume_iter}) ---")
        
        try:
            # Note: perform_initial_relax=False to prevent re-relaxing the cell
            _ph, _fc, ensemble_data, _ucell, free_energy = _run_sscha_at_volume(
                args, poscar_path, iter_dir, quiet=True, perform_initial_relax=False, mass_map=mass_map
            )
            if free_energy is None:
                print("  SSCHA failed to converge, returning high energy.")
                with open(vol_log_path, 'a') as f:
                    f.write(f"{_iter_count:4d}    {volume:11.4f}    {'N/A':>17}    {'N/A':>15}\n")
                return 1e10 # Return a large number if SSCHA fails

            _, _, _, stress_ref, final_w, _ = ensemble_data
            pressure_gpa = np.nan
            if stress_ref is not None and final_w is not None and stress_ref.size > 0:
                stress_avg_voigt = np.sum(final_w[:, np.newaxis] * stress_ref, axis=0)
                pressure_ev_a3 = -np.mean(stress_avg_voigt[:3])
                pressure_gpa = pressure_ev_a3 * EV_A3_TO_GPA
                pressure_str = f"{pressure_gpa:+.4f} GPa"
            else:
                pressure_str = "N/A"

            print(f"--- F = {free_energy:.6f} eV at V={volume:.4f} Å^3 | P = {pressure_str} ---")
            
            with open(vol_log_path, 'a') as f:
                f.write(f"{_iter_count:4d}    {volume:11.4f}    {free_energy:17.6f}    {pressure_gpa:15.4f}\n")

            return free_energy
        except Exception as e:
            print(f"  SSCHA run failed at V={volume:.4f} Å^3: {e}")
            traceback.print_exc()
            with open(vol_log_path, 'a') as f:
                f.write(f"{_iter_count:4d}    {volume:11.4f}    {'ERROR':>17}    {'ERROR':>15}\n")
            return 1e10

    # Bounded optimization to find the minimum free energy
    bounds = (initial_volume * 0.9, initial_volume * 1.1)
    result = minimize_scalar(
        objective_F,
        bounds=bounds,
        args=(initial_unitcell, args, output_dir),
        method='bounded',
        options={'xatol': 1e-2, 'maxiter': args.max_volume_iter}
    )

    optimal_volume = result.x
    print(f"\n--- Volume optimization finished ---")
    print(f"Optimal volume: {optimal_volume:.4f} Å^3")
    print(f"Final minimum free energy: {result.fun:.6f} eV")

    # Run one final calculation at the optimal volume for detailed output
    print("\n--- Running final calculation at optimal volume ---")
    final_dir = output_dir / "final_optimal_volume"
    final_dir.mkdir()
    
    scale = (optimal_volume / initial_volume)**(1/3)
    final_cell = initial_unitcell.cell * scale
    final_poscar_obj = PhonopyAtoms(
        cell=final_cell,
        scaled_positions=initial_unitcell.scaled_positions,
        numbers=initial_unitcell.numbers
    )
    final_poscar_path = final_dir / "POSCAR_optimal"
    write_vasp(str(final_poscar_path), final_poscar_obj)
    
    _run_sscha_at_volume(args, final_poscar_path, final_dir, quiet=False, perform_initial_relax=False, mass_map=mass_map)
    print("\n--- Full workflow completed successfully! ---")


def run_sscha_workflow(args):
    """
    Wrapper for SSCHA workflow to handle logging and directory creation.
    """
    # 1. Determine Output Directory
    if args.poscar:
        input_poscar_path = Path(args.poscar).resolve()
    elif args.cif:
        input_poscar_path = Path(args.cif).resolve()
    else:
        # Let impl handle error, or handle here. Impl handles it.
        # Just use current dir for now to proceed to impl
        _run_sscha_workflow_impl(args) 
        return

    if args.output_dir:
        base_output_dir = Path(args.output_dir).resolve()
    else:
        base_output_dir = input_poscar_path.parent / f"sscha_{input_poscar_path.stem}"
    
    i = 1
    output_dir = base_output_dir
    while output_dir.exists():
        output_dir = Path(f"{base_output_dir}-NEW{i:03d}")
        i += 1
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Update args so impl uses this dir
    args.output_dir = str(output_dir)

    # 2. Setup Logger
    log_file = output_dir / "macer_sscha.log"
    orig_stdout = sys.stdout
    
    with Logger(str(log_file)) as lg:
        sys.stdout = lg
        print(f"--- Macer SSCHA Workflow ---")
        print(f"Command: {' '.join(sys.argv)}")
        try:
            _run_sscha_workflow_impl(args)
        finally:
            sys.stdout = orig_stdout


def add_sscha_parser(subparsers):
    """Adds the parser for the 'run-sscha' command."""
    from macer import __version__
    parser = subparsers.add_parser(
        "run-sscha",
        aliases=["sscha"],
        help="Stochastic Self-Consistent Harmonic Approximation (Anharmonic FCs)",
        description=MACER_LOGO + f"\nmacer_phonopy sscha (v{__version__}): Perform reweighting-based SSCHA using MLFFs.",
        epilog="""
Examples:
  # 1. Standard SSCHA at 300K using MD for reference ensemble (default)
  macer phonopy sscha -p POSCAR -T 300 --dim 2 2 2 --ff mattersim

  # 2. Volume optimization with SSCHA (Self-consistent EOS)
  macer phonopy sscha -p POSCAR -T 300 --dim 2 2 2 --optimize-volume --max-volume-iter 10

  # 3. Fast random sampling method with simultaneous 3rd-order FC fitting
  macer phonopy sscha -p POSCAR -T 300 --reference-method random --include-third-order

  # 4. Restart from an existing reference ensemble file
  macer phonopy sscha -p POSCAR -T 300 --reference-ensemble reference_ensemble.npz
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # General & Input
    general_group = parser.add_argument_group("General & Input")
    general_group.add_argument("-p", "--poscar", required=False, default=None, help="Input crystal structure file (e.g., POSCAR).")
    general_group.add_argument("-c", "--cif", required=False, default=None, help="Input CIF file.")
    general_group.add_argument("--output-dir", help="Directory to save all output files.")
    general_group.add_argument("--seed", type=int, help="Random seed for reproducibility.")

    # MLFF Settings
    mlff_group = parser.add_argument_group("MLFF Model Settings")
    mlff_group.add_argument("--ff", choices=ALL_SUPPORTED_FFS, default=DEFAULT_FF, help=f"Force field to use (default: {DEFAULT_FF}).")
    mlff_group.add_argument("--model", help="Path to the force field model file.")
    mlff_group.add_argument("--device", default=DEFAULT_DEVICE, choices=["cpu", "mps", "cuda"], help=f"Compute device (default: {DEFAULT_DEVICE}).")
    mlff_group.add_argument("--modal", type=str, default=None, help="Modal for SevenNet model, if required.")

    # Initial Harmonic FC Settings
    initial_group = parser.add_argument_group("Initial Harmonic FC Settings")
    initial_group.add_argument("--initial-fmax", type=float, default=5e-3, help="Force convergence for initial relaxation (eV/Å).")
    initial_group.add_argument("--dim", type=int, nargs='+', help="Supercell dimension (e.g., '2 2 2').")
    initial_group.add_argument("-l", "--min-length", type=float, default=15.0, help="Minimum supercell length if --dim is not set (Å).")
    initial_group.add_argument("--amplitude", type=float, default=0.03, help="Displacement amplitude for 0K FC calculation (Å).")
    initial_group.add_argument('--pm', action="store_true", help='Use plus/minus displacements.')
    initial_group.add_argument('--nodiag', action="store_true", help='Do not use diagonal displacements.')
    initial_group.add_argument('--symprec', type=float, default=1e-5, help='Symmetry tolerance (Å).')
    initial_group.add_argument("--read-initial-fc", type=str, help="Path to existing FORCE_CONSTANTS to skip initial calculation.")
    initial_group.add_argument("--initial-symmetry-off", dest="initial_use_symmetry", action="store_false", help="Disable FixSymmetry in initial relaxation.")

    # Reference Ensemble Settings
    ensemble_group = parser.add_argument_group("Reference Ensemble Settings")
    ensemble_group.add_argument("--reference-method", choices=["random", "md"], default="md", help="Method to generate reference ensemble (default: md).")
    ensemble_group.add_argument("--reference-n-samples", type=int, default=200, help="Number of samples for 'random' method (default: 200).")
    ensemble_group.add_argument("--reference-md-nsteps", type=int, default=200, help="Number of sampling steps for 'md' method (default: 200).")
    ensemble_group.add_argument("--reference-md-nequil", type=int, default=100, help="Number of equilibration steps to discard in 'md' method (default: 100).")
    ensemble_group.add_argument("--reference-md-tstep", type=float, default=1.0, help="MD timestep in fs (default: 1.0).")
    ensemble_group.add_argument("--md-thermostat", choices=["nve", "langevin"], default="langevin", help="Thermostat for MD ensemble generation (default: langevin).")
    ensemble_group.add_argument("--md-friction", type=float, default=0.01, help="Friction parameter for Langevin thermostat in ps^-1 (default: 0.01).")
    ensemble_group.add_argument("--reference-ensemble", help="Path to an existing reference_ensemble.npz file to use, skipping generation.")
    ensemble_group.add_argument("--no-save-reference-ensemble", action="store_true", help="Do not keep the reference_ensemble.npz file after the run.")
    ensemble_group.add_argument("--write-xdatcar", action="store_true", help="Write XDATCAR file from the MD trajectory (for md method only).")
    ensemble_group.add_argument("--xdatcar-step", type=int, default=50, help="Step interval for writing XDATCAR (for md method only). Default: 50.")

    # SSCHA Reweighting Settings
    sscha_group = parser.add_argument_group("SSCHA Reweighting Settings")
    sscha_group.add_argument("-T", "--temperature", type=float, help="Target temperature in Kelvin.")
    sscha_group.add_argument("--qscaild-selfconsistent", action="store_true", help="Enable QSCAILD-style self-consistency (Sets --reference-method random).")
    sscha_group.add_argument("--max-iter", type=int, default=200, help="Maximum number of SSCHA iterations (default: 200).")
    sscha_group.add_argument("--max-regen", type=int, default=200, help="Maximum number of ensemble regenerations if ESS collapses (default: 200).")
    sscha_group.add_argument("--ess-collapse-ratio", type=float, default=0.5, help="Ratio of ESS to total samples below which the ensemble is regenerated (default: 0.5).")
    sscha_group.add_argument("--free-energy-conv", type=float, default=0.1, help="Free energy convergence threshold in meV/atom (default: 0.1).")
    sscha_group.add_argument("--mesh", type=int, nargs=3, default=[7, 7, 7], help="Q-point mesh for free energy calculation (default: 7 7 7).")
    sscha_group.add_argument("--fc-mixing-alpha", type=float, default=0.5, help="Linear mixing parameter for FC updates (0 < alpha <= 1). (default: 0.5)")
    sscha_group.add_argument("--include-third-order", action="store_true", help="Enable simultaneous fitting of 3rd order force constants.")
    sscha_group.add_argument("--mass", nargs='+', help="Specify atomic masses. Format: Symbol Mass Symbol Mass ... (e.g. --mass H 2.014 D 2.014)")

    # Volume Optimization Settings
    volopt_group = parser.add_argument_group("Volume Optimization Settings")
    volopt_group.add_argument("--optimize-volume", action="store_true", help="Enable self-consistent volume optimization.")
    volopt_group.add_argument("--max-volume-iter", type=int, default=10, help="Maximum number of volume optimization iterations (default: 10).")

    # Output & Plotting Settings
    output_group = parser.add_argument_group("Output & Plotting Settings")
    output_group.add_argument("--save-every", type=int, default=5, help="Save intermediate FORCE_CONSTANTS every N steps (default: 5).")
    output_group.add_argument("--no-plot-bands", dest="plot_bands", action="store_false", help="Do not plot band structures.")
    parser.set_defaults(plot_bands=True)
    output_group.add_argument("--gamma-label", type=str, default="GM", help="Label for Gamma point in plots.")

    parser.set_defaults(func=run_sscha_workflow)
    return parser

    