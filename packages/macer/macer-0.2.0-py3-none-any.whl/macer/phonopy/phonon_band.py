#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
phonon_band.py
Make phonopy band.conf directly from POSCAR using SeeK-path.
Also includes Gruneisen parameter calculation workflow.
"""

import math
import sys
import subprocess
import shutil
import numpy as np
import os
from pathlib import Path
import traceback
import tempfile
import yaml
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib.collections import LineCollection
from types import SimpleNamespace

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import macer.externals.spglib_bundled as spglib
import seekpath
from phonopy import Phonopy, PhonopyGruneisen
from phonopy.cui.load import load as load_phonopy
from phonopy.interface.vasp import read_vasp, write_vasp
from ase.io import read as ase_read, write as ase_write
from ase import Atoms
from macer.defaults import DEFAULT_MODELS, _macer_root, _model_root, resolve_model_path
from macer.calculator.factory import get_calculator
from phonopy.file_IO import write_FORCE_SETS, write_FORCE_CONSTANTS, parse_FORCE_CONSTANTS
from phonopy.phonon.band_structure import get_band_qpoints

from macer.phonopy.band_path import generate_band_conf, read_poscar
from macer.relaxation.bulk_modulus import get_bulk_modulus_and_volume


def _pb_resolve_model_path(ff: str, model_path: Path | None) -> str | None:
    """Resolve model path: prefer user-provided, else DEFAULT_MODELS."""
    if model_path:
        return resolve_model_path(str(model_path))
    default_model_name = DEFAULT_MODELS.get(ff)
    if default_model_name:
        return resolve_model_path(default_model_name)
    return None


def _get_strain_scaling_factor(B_GPa: float) -> float:
    """
    Calculates a scaling factor for strain based on the bulk modulus.
    The function is an exponential decay of the form f(B) = 2**(1.4 - B/50).
    """
    if B_GPa <= 0:
        return 1.0
    return 2**(1.4 - B_GPa / 50.0)


def _pb_generate_displacements(
    input_path: Path,
    min_length: float,
    displacement_distance: float,
    is_plusminus: bool,
    is_diagonal: bool,
    tolerance_phonopy: float,
    fix_axis: list[str] | None,
    dim_override: str | None,
):
    """Helper function to generate displacements with phonopy."""
    print("\n--- Step 1: Generating displacements with phonopy ---")
    unitcell = read_vasp(str(input_path))
    cell = unitcell.cell
    vector_lengths = [np.linalg.norm(v) for v in cell]

    if any(v == 0 for v in vector_lengths):
        raise RuntimeError("One of the lattice vectors has a length of zero.")

    supercell_matrix = None
    if dim_override:
        try:
            parts = [int(p) for p in dim_override.split()]
        except ValueError:
            sys.exit("Error: --dim must be followed by integers.")

        if len(parts) == 3:
            supercell_matrix = np.diag(parts)
            print(f"Using user-provided diagonal supercell DIM = {parts}")
        elif len(parts) == 9:
            supercell_matrix = np.array(parts).reshape(3, 3)
            print(f"Using user-provided supercell matrix:\n{supercell_matrix}")
        else:
            sys.exit("Error: --dim must be followed by 3 or 9 integers.")
    else:
        # Auto-determine from min_length
        scaling_factors_list = [math.ceil(min_length / v) if v > 0 else 1 for v in vector_lengths]
        supercell_matrix = np.diag(scaling_factors_list)
        print(f"Auto-determining supercell from --min-length. DIM = {scaling_factors_list}")

    # Handle fix_axis for diagonal matrices
    if fix_axis:
        if np.count_nonzero(supercell_matrix - np.diag(np.diagonal(supercell_matrix))) == 0:
             scaling_factors = np.diagonal(supercell_matrix).astype(int).tolist()
             axis_map = {'a': 0, 'b': 1, 'c': 2, 'x': 0, 'y': 1, 'z': 2}
             for axis_name in fix_axis:
                 idx = axis_map.get(axis_name.lower())
                 if idx is not None and 0 <= idx < len(scaling_factors):
                     scaling_factors[idx] = 1
             supercell_matrix = np.diag(scaling_factors)
             print(f"Applied --fix-axis, new DIM = {scaling_factors}")
        else:
             print("Warning: --fix-axis is ignored when a non-diagonal --dim matrix is provided.")

    if np.count_nonzero(supercell_matrix - np.diag(np.diagonal(supercell_matrix))) == 0:
        sf_print = np.diagonal(supercell_matrix).astype(int).tolist()
        print(f"Supercell (DIM): {sf_print[0]} {sf_print[1]} {sf_print[2]}")

    try:
        phonon = Phonopy(
            unitcell,
            supercell_matrix=supercell_matrix,
            primitive_matrix="auto",
            symprec=tolerance_phonopy
        )
    except RuntimeError as e:
        if "Determinant of primitive_matrix" in str(e):
            print(f"Warning: Phonopy auto-primitive determination failed ({e}).")
            print("Falling back to primitive_matrix=np.eye(3) (assuming input cell is primitive).")
            phonon = Phonopy(
                unitcell,
                supercell_matrix=supercell_matrix,
                primitive_matrix=np.eye(3),
                symprec=tolerance_phonopy
            )
        else:
            raise e
    phonon.generate_displacements(
        distance=displacement_distance,
        is_plusminus=is_plusminus,
        is_diagonal=is_diagonal,
    )
    phonon.save("phonopy_disp.yaml")
    print("Wrote phonopy_disp.yaml")
    write_vasp("SPOSCAR", phonon.supercell)
    print("Wrote SPOSCAR")
    return phonon


def _pb_produce_fc_and_save(phonon: Phonopy, force_sets: list):
    """Helper function to produce force constants and save files."""
    print("\n--- Step 3: Creating FORCE_SETS and FORCE_CONSTANTS ---")
    # Set forces into the phonon object
    phonon.forces = force_sets
    # Produce force constants from forces
    phonon.produce_force_constants()
    print("Force constants produced via API.")
    
    # Save files
    write_FORCE_SETS(phonon.dataset, filename="FORCE_SETS")
    print("FORCE_SETS created successfully.")
    write_FORCE_CONSTANTS(phonon.force_constants, filename="FORCE_CONSTANTS")
    print("FORCE_CONSTANTS created successfully.")


def _calculate_phonons_for_gruneisen(
    input_path: Path,
    min_length: float,
    displacement_distance: float,
    is_plusminus: bool,
    is_diagonal: bool,
    macer_ff: str,
    macer_model_path: Path | None,
    macer_device: str,
    macer_modal: str | None,
    tolerance_phonopy: float,
    fix_axis: list[str] | None,
    dim_override: str | None,
    calculator=None,
):
    """Helper function to calculate force constants for a given structure."""
    phonon = _pb_generate_displacements(
        input_path, min_length, displacement_distance, 
        is_plusminus, is_diagonal, tolerance_phonopy, fix_axis, dim_override
    )

    print("\n--- Step 2: Calculating forces with macer ---")
    if calculator is None:
        print(f"Device: {macer_device}")
        current_macer_model_path = resolve_model_path(str(macer_model_path)) if macer_model_path else None
        if current_macer_model_path is None:
            default_model_name = DEFAULT_MODELS.get(macer_ff)
            if default_model_name:
                current_macer_model_path = resolve_model_path(default_model_name)

        if macer_ff == "mace" and macer_device == "mps":
            print(
                "\nWARNING: The 'mps' device is often incompatible with 'mace-torch' due to an internal "
                "bug related to float64 data types. Falling back to 'cpu' for force calculations to prevent a crash. "
                "For a permanent solution and better performance, please upgrade your 'mace-torch' package.",
                file=sys.stderr,
            )
            macer_device = "cpu"

        print(f"Loading MLFF model ({macer_ff})...")
        calc_kwargs = {"device": macer_device, "modal": macer_modal}
        if macer_ff == "mace":
            calc_kwargs["model_paths"] = [current_macer_model_path]
        else:
            calc_kwargs["model_path"] = current_macer_model_path
        calculator = get_calculator(macer_ff, **calc_kwargs)

    force_sets = []
    for cell in tqdm(phonon.supercells_with_displacements, desc="Calculating forces"):
        ase_atoms = Atoms(
            symbols=cell.symbols,
            cell=cell.cell,
            scaled_positions=cell.scaled_positions,
            pbc=True
        )
        ase_atoms.calc = calculator
        forces = ase_atoms.get_forces()
        force_sets.append(forces)
    print("Force calculations completed successfully.")

    _pb_produce_fc_and_save(phonon, force_sets)
    
    return phonon


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
    labels = data.get("labels", [])
    
    # Reconstruct segmented q-points list for set_band_structure
    bands = []
    q_idx = 0
    for nq in segment_nqpoint:
        bands.append(qpoints[q_idx:q_idx + nq])
        q_idx += nq
        
    return distances, frequencies, bands, segment_nqpoint, labels


def _write_band_dat(band_yaml_path, dat_filename):
    """Writes a band.yaml file to a gnuplot-friendly .dat file."""
    distances, frequencies, _, segment_nqpoint, _ = _read_band_yaml_data(band_yaml_path)

    with open(dat_filename, 'w') as f:
        f.write("# q-distance, frequency\n")
        for i, freqs_band in enumerate(frequencies.T):  # Iterate over bands
            f.write(f"# mode {i + 1}\n")
            q_idx = 0
            for nq in segment_nqpoint:  # Iterate over segments
                for d, freq in zip(distances[q_idx:q_idx + nq], 
                                   freqs_band[q_idx:q_idx + nq]):
                    f.write(f"{d:12.8f} {freq:15.8f}\n")
                q_idx += nq
                f.write("\n")  # Blank line between segments for gnuplot
            f.write("\n")  # Another blank line between bands
    
    print(f"Band structure data written to {dat_filename}")


def _write_gruneisen_dat(distances, frequencies, gruneisen_params, segment_nqpoint, dat_filename="gruneisen.dat"):
    """Write band structure data to a text file in gnuplot-friendly format."""
    num_bands = frequencies.shape[1]

    with open(dat_filename, 'w') as f:
        f.write("# q-distance, frequency, gruneisen\n")
        for j in range(num_bands):  # Loop over bands (modes)
            f.write(f"# mode {j + 1}\n")
            q_idx = 0
            for nq in segment_nqpoint: # Iterate over segments
                for k in range(nq): # Loop over q-points in segment
                    idx = q_idx + k
                    dist = distances[idx]
                    freq = frequencies[idx, j]
                    g = gruneisen_params[idx, j]
                    if freq < 0.05:
                        g = 0.0
                    f.write(f"{dist:12.8f} {freq:15.8f} {g:15.8f}\n")
                q_idx += nq
                f.write("\n") # Blank line between segments
            f.write("\n\n")  # Two blank lines for gnuplot index separation
            
    print(f"Gruneisen data written to {dat_filename}")


def _plot_gruneisen_from_dat(dat_filename, distances, segment_nqpoint, labels, gmin, gmax, filter_outliers_factor, output_filename="gruneisen_band.pdf"):
    """Plot phonon dispersion colored by Gruneisen parameter from a data file."""
    data_points = []
    try:
        with open(dat_filename, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                parts = line.split()
                if len(parts) == 3:
                    data_points.append([float(p) for p in parts])
    except (IOError, ValueError) as e:
        print(f"Error reading or parsing {dat_filename}: {e}")
        return

    if not data_points:
        print(f"No data found in {dat_filename}")
        return

    data = np.array(data_points)
    data = data[np.isfinite(data).all(axis=1)]

    x = data[:, 0]
    y = data[:, 1]
    g = data[:, 2]

    # Determine limits and filtering
    q1, q3 = np.percentile(g, [25, 75])
    iqr = q3 - q1
    f_factor = filter_outliers_factor if filter_outliers_factor is not None else 3.0
    auto_vmin, auto_vmax = q1 - f_factor * iqr, q3 + f_factor * iqr
    
    vmin = gmin if gmin is not None else float(math.floor(max(g.min(), auto_vmin)))
    vmax = gmax if gmax is not None else float(math.ceil(min(g.max(), auto_vmax)))
    
    mask = (g >= vmin) & (g <= vmax)
    print(f"Plotting range: [{vmin:.2f}, {vmax:.2f}]. Points outside this range are hidden.")
    x_filt, y_filt, g_filt = x[mask], y[mask], g[mask]

    fig, ax = plt.subplots(figsize=(8, 6))
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["font.family"] = "serif"

    # Color range handling: use TwoSlopeNorm to keep 0 as white even if asymmetric
    from matplotlib.colors import TwoSlopeNorm, Normalize
    if vmin < 0 < vmax:
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
        n_side = 4 
        ticks = np.concatenate([np.linspace(vmin, 0, n_side + 1), 
                                np.linspace(0, vmax, n_side + 1)[1:]])
    else:
        norm = Normalize(vmin=vmin, vmax=vmax)
        ticks = None

    sc = ax.scatter(x_filt, y_filt, c=g_filt, cmap='bwr', s=5, norm=norm, alpha=0.8)
    cb = fig.colorbar(sc, ax=ax, ticks=ticks)
    cb.set_label('Grüneisen parameter')

    # Ticks and labels extraction
    tick_pos = [distances[0]]
    tick_labels_raw = [labels[0][0]]
    curr_idx = 0
    for i, nq in enumerate(segment_nqpoint):
        curr_idx += nq
        tick_pos.append(distances[curr_idx - 1])
        tick_labels_raw.append(labels[i][1])

    clean_labels = [l.replace("GAMMA", "$\\Gamma$").replace("GM", "$\\Gamma$") for l in tick_labels_raw]
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(clean_labels)
    ax.set_xlim(distances[0], distances[-1])
    ax.set_ylabel('Frequency (THz)')
    
    for tp in tick_pos:
        ax.axvline(tp, color='k', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.axhline(0, linestyle='-', color='k', linewidth=0.5)

    plt.tight_layout()
    plt.savefig(output_filename)
    plt.close()
    print(f"Gruneisen band structure plot saved to {output_filename}")


def _plot_mode_gruneisen_from_dat(dat_filename, distances, segment_nqpoint, labels, gmin, gmax, filter_outliers_factor, output_filename="gruneisen_mode_parameter.pdf"):
    """Plot Mode Grüneisen parameter vs Wave vector from a data file."""
    data_points = []
    try:
        with open(dat_filename, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                parts = line.split()
                if len(parts) == 3:
                    data_points.append([float(p) for p in parts])
    except (IOError, ValueError) as e:
        print(f"Error reading or parsing {dat_filename}: {e}")
        return

    if not data_points:
        return

    data = np.array(data_points)
    data = data[np.isfinite(data).all(axis=1)]

    x = data[:, 0]
    g = data[:, 2] 

    # Determine limits and filtering
    q1, q3 = np.percentile(g, [25, 75])
    iqr = q3 - q1
    f_factor = filter_outliers_factor if filter_outliers_factor is not None else 3.0
    auto_vmin, auto_vmax = q1 - f_factor * iqr, q3 + f_factor * iqr
    
    vmin = gmin if gmin is not None else float(math.floor(max(g.min(), auto_vmin)))
    vmax = gmax if gmax is not None else float(math.ceil(min(g.max(), auto_vmax)))
    
    mask = (g >= vmin) & (g <= vmax)
    x_filt, g_filt = x[mask], g[mask]

    fig, ax = plt.subplots(figsize=(8, 6))
    plt.rcParams["pdf.fonttype"] = 42
    plt.rcParams["font.family"] = "serif"

    from matplotlib.colors import TwoSlopeNorm, Normalize
    if vmin < 0 < vmax:
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
        n_side = 4 
        ticks = np.concatenate([np.linspace(vmin, 0, n_side + 1), 
                                np.linspace(0, vmax, n_side + 1)[1:]])
        
        from matplotlib.scale import FuncScale
        def forward(y): return np.where(y > 0, y / vmax, y / abs(vmin))
        def inverse(y): return np.where(y > 0, y * vmax, y * abs(vmin))
        ax.set_yscale('function', functions=(forward, inverse))
        ax.set_yticks(ticks)
    else:
        norm = Normalize(vmin=vmin, vmax=vmax)
        ticks = None

    sc = ax.scatter(x_filt, g_filt, c=g_filt, cmap='bwr', s=5, norm=norm, alpha=0.8)
    cb = fig.colorbar(sc, ax=ax, ticks=ticks)
    cb.set_label('Grüneisen parameter')

    # Ticks and labels extraction
    tick_pos = [distances[0]]
    tick_labels_raw = [labels[0][0]]
    curr_idx = 0
    for i, nq in enumerate(segment_nqpoint):
        curr_idx += nq
        tick_pos.append(distances[curr_idx - 1])
        tick_labels_raw.append(labels[i][1])

    clean_labels = [l.replace("GAMMA", "$\\Gamma$").replace("GM", "$\\Gamma$") for l in tick_labels_raw]
    ax.set_xticks(tick_pos)
    ax.set_xticklabels(clean_labels)
    ax.set_xlim(distances[0], distances[-1])
    ax.set_ylim(vmin, vmax)
    
    ax.set_ylabel('Mode Grüneisen parameter')
    for tp in tick_pos:
        ax.axvline(tp, color='k', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.axhline(0, linestyle=':', color='gray', linewidth=0.8, alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_filename)
    plt.close()
    print(f"Mode Grüneisen parameter plot saved to {output_filename}")



def _run_gruneisen_on_top(
    phonons: list[Phonopy],
    strain: float,
    band_yaml_path: Path,
    output_prefix: str,
):
    """Calculate Gruneisen parameters using pre-calculated phonon objects."""
    print("\n===== Gruneisen calculation: START ====")
    
    gruneisen = PhonopyGruneisen(phonons[0], phonons[1], phonons[2], delta_strain=strain)
    
    distances, frequencies, bands, segment_nqpoint, labels = _read_band_yaml_data(band_yaml_path)
    
    gruneisen.set_band_structure(bands)
    _, _, _, _, gruneisen_params_list = gruneisen.get_band_structure()

    # Flatten the list of lists into single arrays
    gruneisen_params = np.vstack(gruneisen_params_list)

    dat_filename = Path.cwd() / f"gruneisen_band-{output_prefix}.dat"
    _write_gruneisen_dat(distances, frequencies, gruneisen_params, segment_nqpoint, dat_filename)
    
    return dat_filename, distances, segment_nqpoint, labels


def run_macer_workflow(
    input_path: Path,
    min_length: float,
    displacement_distance: float,
    is_plusminus: bool,
    is_diagonal: bool,
    symprec_seekpath: float = 1e-5,
    gamma_label: str = "GM",
    macer_device: str = "cpu",
    macer_model_path: Path | None = None,
    model_info_str: str = "",
    yaml_path_arg: Path | None = None,
    out_path_arg: Path | None = None,
    dim_override: str | None = None,
    no_defaults_band_conf: bool = False,
    atom_names_override: str | None = None,
    rename_override: str | None = None,
    output_prefix: str | None = None,
    tolerance_sr: float = 0.01,
    tolerance_phonopy: float = 5e-3,
    macer_optimizer_name: str = "FIRE",
    fix_axis: list[str] | None = None,
    macer_ff: str = "mace",
    macer_modal: str | None = None,
    plot_gruneisen: bool = False,
    gruneisen_strain: float | None = None,
    gmin: float | None = None,
    gmax: float | None = None,
    gruneisen_target_energy: float = 10.0,
    filter_outliers_factor: float | None = None,
    use_relax_unit: bool = False,
    initial_fmax: float = 0.005,
    initial_symprec: float = 1e-5,
    initial_isif: int = 3,
    show_irreps: bool = False,
    irreps_qpoint: list[float] | None = None,
    tolerance_irreps: float = 1e-5,
    write_arrow: bool = False,
    arrow_length: float = 1.7,
    arrow_min_cutoff: float = 0.1,
    arrow_qpoint_gamma: bool = False,
    arrow_qpoint: list[float] | None = None,
    mass_map: dict | None = None,
    output_dir_arg: str | None = None,
    plot_dos: bool = False,
    mesh: list[int] = [20, 20, 20],
    with_eigenvectors: bool = False,
    read_fc_path: Path | None = None,
    skip_initial_relax: bool = False,
):
    import traceback # Ensure local availability
    print("\n===== macer phonon workflow: START =====")
    print(f"Command: {' '.join(sys.argv)}")
    if macer_model_path:
        print(f"  MLFF Model: {macer_model_path}{model_info_str}")
    else:
        print(f"  MLFF Model:{model_info_str}")

    final_symmetrized_sg_symbol = "N/A"
    final_symmetrized_sg_number = None

    input_path = Path(input_path).resolve()
    initial_atoms = ase_read(input_path, format="vasp")

    # Determine output directory
    if output_dir_arg:
        output_dir = Path(output_dir_arg).resolve()
    else:
        base_output_dir = input_path.parent / f"phonon_band-{input_path.name}-mlff={macer_ff}"
        output_dir = base_output_dir
        if output_dir.exists():
            i = 1
            while output_dir.exists():
                output_dir = Path(f"{base_output_dir}-NEW{i:02d}")
                i += 1

    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    
    print(f"Output directory: {output_dir}")

    # Copy input file to output directory and update input_path
    local_input_path = output_dir / input_path.name
    if input_path.resolve() != local_input_path.resolve():
        shutil.copy(input_path, local_input_path)
    os.chdir(output_dir)
    input_path = local_input_path

    if output_prefix is None:
        output_prefix = input_path.stem

    unitcell_poscar_path = Path.cwd() / f"{input_path.stem}-symmetrized"
    
    print(f"Input structure: {input_path}")
    print(f"Output directory: {Path.cwd()}")
    print(f"Displacement distance: {displacement_distance:g} Å")

    # === Step 0: Initial Relaxation ===
    print("\n--- Step 0: Initial structure preparation ---")
    symmetrized_input_path = None

    if read_fc_path and skip_initial_relax:
        print(f"Skipping Step 0-3: Using provided FORCE_CONSTANTS from {read_fc_path}")
        symmetrized_input_path = output_dir / "POSCAR"
        if not symmetrized_input_path.exists():
            shutil.copy(local_input_path, symmetrized_input_path)
    elif use_relax_unit:
        print("Using iterative relaxation/symmetrization (macer_phonopy sr).")
        macer_ru_command = [
            sys.executable, '-m', 'macer.cli.phonopy_main', 'sr', '-p', str(input_path), '--output-prefix', input_path.stem,
            '--tolerance', str(tolerance_sr), '--ff', macer_ff,
        ]
        if macer_model_path:
            macer_ru_command.extend(['--model', str(macer_model_path)])
        else: # Logic to find default model if not provided
            default_model_name = DEFAULT_MODELS.get(macer_ff)
            if default_model_name:
                # This logic needs to be careful about FFS_USING_MODEL_NAME
                FFS_USING_MODEL_NAME = {"fairchem", "orb", "chgnet", "m3gnet"}
                if macer_ff in FFS_USING_MODEL_NAME:
                    macer_ru_command.extend(['--model', default_model_name])
                else:
                    macer_ru_command.extend(['--model', os.path.join(_model_root, default_model_name)])

        if macer_modal: macer_ru_command.extend(['--modal', macer_modal])
        if fix_axis: macer_ru_command.extend(['--fix-axis', ','.join(fix_axis)])
        
        print(f"Running command: {' '.join(macer_ru_command)}")
        try:
            subprocess.run(macer_ru_command, check=True, text=True)
            symmetrized_input_path = unitcell_poscar_path
        except subprocess.CalledProcessError as e:
            print("Error during macer_phonopy sr execution.")
            return
    else:
        if initial_isif == 0:
            print("ISIF=0 specified, skipping initial relaxation.")
            symmetrized_input_path = output_dir / input_path.name
            if not symmetrized_input_path.exists():
                shutil.copy(input_path, symmetrized_input_path)
        else:
            print(f"Using simple 'macer relax' (ISIF={initial_isif}).")
            copied_input_poscar_path = output_dir / input_path.name
            if not copied_input_poscar_path.exists(): # Avoid overwriting if input is in output dir
                 shutil.copy(input_path, copied_input_poscar_path)

            relaxed_poscar_name = f"CONTCAR-{copied_input_poscar_path.stem}"
            macer_relax_command = [
                sys.executable, '-m', 'macer.cli.main', 'relax', '-p', str(copied_input_poscar_path), '--isif', str(initial_isif),
                '--fmax', str(initial_fmax), '--device', macer_device,
                '--contcar', relaxed_poscar_name, '--no-pdf',
                '--symprec', str(initial_symprec)
            ]
            if macer_ff: macer_relax_command.extend(['--ff', macer_ff])
            if macer_model_path: macer_relax_command.extend(['--model', str(macer_model_path)])
            if macer_modal: macer_relax_command.extend(['--modal', macer_modal])
            
            print(f"Running command: {' '.join(macer_relax_command)}")
            try:
                subprocess.run(macer_relax_command, check=True, text=True)
                symmetrized_input_path = output_dir / relaxed_poscar_name
                if not symmetrized_input_path.exists():
                    raise FileNotFoundError(f"Relaxed CONTCAR not found at {symmetrized_input_path}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print("Error during initial 'macer relax' execution:", e)
                return

    # --- Post-relaxation info gathering ---
    symmetrized_atoms = ase_read(str(symmetrized_input_path), format="vasp")
    cell_tuple = (symmetrized_atoms.get_cell(),
                  symmetrized_atoms.get_scaled_positions(),
                  symmetrized_atoms.get_atomic_numbers())
    dataset = spglib.get_symmetry_dataset(cell_tuple, symprec=tolerance_sr)
    if dataset:
        final_symmetrized_sg_number = dataset.get('number')
        final_symmetrized_sg_symbol = dataset.get('international', "N/A")
    print(f"  Space group of prepared structure ({symmetrized_input_path.name}): {final_symmetrized_sg_symbol} (No. {final_symmetrized_sg_number})")

    # === Step 1: Displacement Generation & Force Calculation ===
    base_phonon = None
    all_phonons = []

    if read_fc_path:
        print("\n--- Step 1-3: Initializing Phonopy with existing FORCE_CONSTANTS ---")
        unitcell = read_vasp(str(symmetrized_input_path))
        # Reuse supercell matrix detection logic or use provided dim_override
        # (For simplicity here, we assume detected supercell matches provided FC)
        dummy_ph = _pb_generate_displacements(
            input_path=symmetrized_input_path, min_length=min_length, displacement_distance=displacement_distance,
            is_plusminus=is_plusminus, is_diagonal=is_diagonal, tolerance_phonopy=tolerance_phonopy,
            fix_axis=fix_axis, dim_override=dim_override
        )
        base_phonon = dummy_ph
        base_phonon.force_constants = parse_FORCE_CONSTANTS(read_fc_path)
        all_phonons = [base_phonon]
        # Copy to local FORCE_CONSTANTS for consistency
        shutil.copy(read_fc_path, output_dir / "FORCE_CONSTANTS")
    else:
        # 1.1 Pre-load MLFF model
        print(f"\n--- Step 1: Loading MLFF model ({macer_ff}) ---")
        current_macer_model_path = resolve_model_path(str(macer_model_path)) if macer_model_path else None
        if current_macer_model_path is None:
            default_model_name = DEFAULT_MODELS.get(macer_ff)
            if default_model_name:
                current_macer_model_path = resolve_model_path(default_model_name)

        if macer_ff == "mace" and macer_device == "mps":
            print(
                "\nWARNING: The 'mps' device is often incompatible with 'mace-torch' due to an internal "
                "bug related to float64 data types. Falling back to 'cpu' for force calculations to prevent a crash. ",
                file=sys.stderr,
            )
            macer_device = "cpu"

        calc_kwargs = {"device": macer_device, "modal": macer_modal}
        if macer_ff == "mace":
            calc_kwargs["model_paths"] = [current_macer_model_path]
        else:
            calc_kwargs["model_path"] = current_macer_model_path
        workflow_calculator = get_calculator(macer_ff, **calc_kwargs)

        # 1.2 Grüneisen strain estimation (Optional)
        final_gruneisen_strain = None
        if plot_gruneisen:
            final_gruneisen_strain = gruneisen_strain
            log_messages = []
            if final_gruneisen_strain is None:
                print("\n--- Estimating optimal strain for Grüneisen from bulk modulus ---")
                log_messages.append("Grüneisen strain not provided, estimating from bulk modulus.")
                calc_args = SimpleNamespace(ff=macer_ff, model=current_macer_model_path, device=macer_device, modal=macer_modal)
                B_GPa, V0_per_atom = get_bulk_modulus_and_volume(initial_atoms, calc_args)
                if B_GPa and V0_per_atom:
                    try:
                        E_target_eV = gruneisen_target_energy / 1000.0
                        B_eV_per_A3 = B_GPa / 160.21766208
                        epsilon_V = math.sqrt(2 * E_target_eV / (B_eV_per_A3 * V0_per_atom))
                        scaling_factor = _get_strain_scaling_factor(B_GPa)
                        final_gruneisen_strain = epsilon_V * scaling_factor
                        log_messages.extend([
                            f"  - Calculated Bulk Modulus: {B_GPa:.2f} GPa",
                            f"  - Equilibrium Volume: {V0_per_atom * len(symmetrized_atoms):.2f} \u00c5\u00b3",
                            f"  - Base estimated strain: \u00b1{epsilon_V:.4f}",
                            f"  - Exponential scaling factor for strain: {scaling_factor:.3f}",
                            f"  - Final estimated volumetric strain for Gr\u00fcneisen: \u00b1{final_gruneisen_strain:.4f}"
                        ])
                    except Exception as e:
                        final_gruneisen_strain = 0.01
                        log_messages.append(f"  Bulk modulus estimate failed ({e}); fallback to 0.01.")
                else:
                    final_gruneisen_strain = 0.01
                    log_messages.append("  Bulk modulus estimate failed; fallback to 0.01.")
            else:
                log_messages.append(f"User-provided strain for Gr\u00fcneisen: \u00b1{final_gruneisen_strain:.4f}")
            
            for msg in log_messages: print(msg)
            log_path = output_dir / f"gruneisen_strain-{output_prefix}.log"
            log_path.write_text("\n".join(log_messages))

    if not read_fc_path:
        # 1.3 Generate displacements for all phonons
        # 1.3.1 Base phonon
        base_phonon = _pb_generate_displacements(
            input_path=symmetrized_input_path, min_length=min_length, displacement_distance=displacement_distance,
            is_plusminus=is_plusminus, is_diagonal=is_diagonal, tolerance_phonopy=tolerance_phonopy,
            fix_axis=fix_axis, dim_override=dim_override
        )
        
        # 1.3.2 Strained phonons (Optional)
        strained_jobs = []
        if plot_gruneisen:
            original_cell = ase_read(str(symmetrized_input_path), format="vasp")
            gruneisen_dir = output_dir / "gruneisen"
            gruneisen_dir.mkdir(exist_ok=True)
            for s in [final_gruneisen_strain, -final_gruneisen_strain]:
                vol_dir = gruneisen_dir / ("plus" if s > 0 else "minus")
                vol_dir.mkdir(exist_ok=True)
                scaled_cell = original_cell.copy()
                scaled_cell.set_cell(original_cell.cell * (1 + s)**(1/3.0), scale_atoms=True)
                strained_poscar_path = vol_dir / "POSCAR"
                ase_write(str(strained_poscar_path), scaled_cell, format="vasp", vasp5=True)
                os.chdir(vol_dir)
                phonon = _pb_generate_displacements(
                    input_path=strained_poscar_path, min_length=min_length, displacement_distance=displacement_distance,
                    is_plusminus=is_plusminus, is_diagonal=is_diagonal, tolerance_phonopy=tolerance_phonopy,
                    fix_axis=fix_axis, dim_override=dim_override
                )
                strained_jobs.append({'strain': s, 'dir': vol_dir, 'phonon': phonon})
                os.chdir(output_dir)

        # 1.4 Batch calculate forces
        all_atoms_for_batch = []
        # Base supercells
        for cell in base_phonon.supercells_with_displacements:
            all_atoms_for_batch.append(Atoms(symbols=cell.symbols, cell=cell.cell, scaled_positions=cell.scaled_positions, pbc=True))
        # Strained supercells
        for job in strained_jobs:
            for cell in job['phonon'].supercells_with_displacements:
                all_atoms_for_batch.append(Atoms(symbols=cell.symbols, cell=cell.cell, scaled_positions=cell.scaled_positions, pbc=True))
                
        all_forces = []
        for atoms in tqdm(all_atoms_for_batch, desc="Batch calculating forces"):
            atoms.calc = workflow_calculator
            all_forces.append(atoms.get_forces())

        # 1.5 Produce Force Constants
        # 1.5.1 Base phonon
        base_num = len(base_phonon.supercells_with_displacements)
        _pb_produce_fc_and_save(base_phonon, all_forces[:base_num])
        
        # 1.5.2 Strained phonons
        offset = base_num
        all_phonons = [base_phonon]
        for job in strained_jobs:
            num = len(job['phonon'].supercells_with_displacements)
            os.chdir(job['dir'])
            _pb_produce_fc_and_save(job['phonon'], all_forces[offset : offset + num])
            all_phonons.append(job['phonon'])
            offset += num
            os.chdir(output_dir)

    # Apply mass override if provided
    if mass_map:
        print("\n--- Applying mass override ---")
        for ph in all_phonons:
            symbols = ph.primitive.symbols
            ph.masses = [mass_map.get(s, m) for s, m in zip(symbols, ph.masses)]
        print(f"  Applied mass override: {mass_map}")

    print("\n--- Step 4: Creating band.conf ---")
    band_conf_path = output_dir / (out_path_arg or "band.conf")
    disp_yaml_path = output_dir / (yaml_path_arg or "phonopy_disp.yaml")
    try:
        generate_band_conf(
            poscar_path=symmetrized_input_path, yaml_path=disp_yaml_path, out_path=band_conf_path,
            gamma_label=gamma_label, symprec=symprec_seekpath, dim_override=dim_override,
            no_defaults=no_defaults_band_conf, atom_names_override=atom_names_override,
            rename_override=rename_override,
        )
        print(f"{band_conf_path.name} created successfully.")
    except Exception:
        import traceback
        print("Error during band.conf generation:", traceback.format_exc())
        return

    # === Step 5: Plotting band structure ===
    print("\n--- Step 5: Plotting band structure ---")
    band_pdf_path = output_dir / "band.pdf"
    band_yaml_path = output_dir / "band.yaml"
    
    try:
        print(f"Generating band structure from {band_conf_path.name} using phonopy API...")
        
        # 1. Read band.conf settings using PhonopyConfParser
        from phonopy.cui.settings import PhonopyConfParser
        conf_parser = PhonopyConfParser(filename=str(band_conf_path))
        settings = conf_parser.settings

        # 2. Get q-points for the band path
        npoints = settings.band_points
        if npoints is None:
            npoints = 51  # Default value in phonopy
        
        qpoints = get_band_qpoints(
            settings.band_paths,
            npoints=npoints
        )
        labels = settings.band_labels
        path_connections = []
        for paths in settings.band_paths:
            path_connections += [True, ] * (len(paths) - 2)
            path_connections.append(False)

        # 3. Run calculation on the existing phonon object
        base_phonon.run_band_structure(qpoints,
                                       path_connections=path_connections,
                                       labels=labels,
                                       with_eigenvectors=with_eigenvectors)

        # 4. Save YAML and Plot
        base_phonon.write_yaml_band_structure(filename=str(band_yaml_path))
        print(f"{band_yaml_path.name} created successfully.")
        
        band_plot = base_phonon.plot_band_structure()
        band_plot.savefig(str(band_pdf_path))
        print(f"{band_pdf_path.name} created successfully.")

        # 5. Write .dat file (existing logic)
        band_dat_path = output_dir / "band.dat"
        _write_band_dat(band_yaml_path, band_dat_path)

    except Exception as e:
        print("Error during API-based band structure plotting:", e)
        import traceback
        traceback.print_exc()
        return

    # === Step 5.1: Phonon DOS (optional) ===
    if plot_dos:
        print("\n--- Step 5.1: Calculating and Plotting Phonon DOS ---")
        try:
            # We use default filenames initially, then rename them in Step 6
            # New unified filenames
            dos_dat_filename = "phonon_dos.dat"
            dos_pdf_filename = "phonon_dos.pdf"
            
            # For PDOS, we need eigenvectors and no mesh symmetry
            print(f"Calculating DOS with mesh: {mesh} (with_eigenvectors=True, is_mesh_symmetry=False)")
            base_phonon.run_mesh(mesh, with_eigenvectors=True, is_mesh_symmetry=False)
            
            # 1. Calculate Total DOS
            # Run without args first to let it auto-determine range
            base_phonon.run_total_dos()
            total_dos_dict = base_phonon.get_total_dos_dict()
            freqs = total_dos_dict['frequency_points']
            total_dos_val = total_dos_dict['total_dos']
            
            # Extract frequency grid parameters to ensure PDOS matches exactly
            f_min = freqs[0]
            f_max = freqs[-1]
            n_points = len(freqs)
            print(f"DOS frequency range: {f_min:.4f} to {f_max:.4f} (n_points={n_points})")

            # 2. Calculate Projected DOS (PDOS) and Group by Element
            # run_projected_dos does NOT take mesh parameters in API, it uses the mesh object's settings
            base_phonon.run_projected_dos()
            pdos_dict = base_phonon.get_projected_dos_dict()
            raw_pdos = np.array(pdos_dict['projected_dos'])
            
            print(f"DEBUG: raw_pdos shape: {raw_pdos.shape}")
            # Ensure shape is (n_freqs, n_atoms)
            # If shape is (n_atoms, n_freqs) [which is (16, 201) in this case], transpose it
            if raw_pdos.shape[0] == len(base_phonon.primitive) and raw_pdos.shape[1] != len(base_phonon.primitive):
                 print("DEBUG: Transposing raw_pdos to (n_freqs, n_atoms)")
                 raw_pdos = raw_pdos.T
            
            primitive = base_phonon.primitive
            symbols = primitive.symbols
            unique_symbols = sorted(list(set(symbols)))
            print(f"Grouping PDOS by elements: {unique_symbols}")
            
            grouped_pdos = {}
            for sym in unique_symbols:
                indices = [i for i, s in enumerate(symbols) if s == sym]
                # Sum over atoms of the same element
                # raw_pdos has shape (n_freq, n_atoms)
                grouped_pdos[sym] = np.sum(raw_pdos[:, indices], axis=1)

            # Ensure PDOS frequency grid matches Total DOS
            # If they differ slightly in length (e.g. Total DOS has auto-grid), we might need to interpolation or just use PDOS grid
            # But usually run_total_dos and run_projected_dos on same mesh should be consistent.
            # Let's check lengths.
            if len(freqs) != len(grouped_pdos[unique_symbols[0]]):
                print(f"WARNING: Frequency point mismatch! Total: {len(freqs)}, PDOS: {len(grouped_pdos[unique_symbols[0]])}")
                # Fallback: Use PDOS frequency points if available
                if 'frequency_points' in pdos_dict:
                     freqs = pdos_dict['frequency_points']
                     # Re-calculate Total DOS on this grid? 
                     # Or just assume Total DOS is close enough? 
                     # If lengths differ, we can't write them in same file side-by-side easily without processing.
                     # But typically they match.
            
            # 3. Write Combined Data File
            header = f"# Tetrahedron method\n# Frequency          Total               {'              '.join(unique_symbols)}\n"
            
            with open(dos_dat_filename, 'w') as f:
                f.write(header)
                for i, freq in enumerate(freqs):
                    line_parts = [f"{freq:18.10f}", f"{total_dos_val[i]:18.10f}"]
                    for sym in unique_symbols:
                        line_parts.append(f"{grouped_pdos[sym][i]:18.10f}")
                    f.write("".join(line_parts) + "\n")
            print(f"{dos_dat_filename} created successfully.")
            
            # 4. Plot Combined DOS (Total + Projected)
            fig, ax = plt.subplots()
            ax.plot(freqs, total_dos_val, 'k-', linewidth=1.5, label='Total')
            
            # Use a colormap or cycle for different elements
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_symbols)))
            for i, sym in enumerate(unique_symbols):
                ax.plot(freqs, grouped_pdos[sym], linewidth=1.0, label=sym, color=colors[i])
            
            ax.set_xlabel('Frequency (THz)')
            ax.set_ylabel('Density of States')
            ax.legend(loc='best')
            ax.grid(True, linestyle='--', alpha=0.6)
            
            plt.tight_layout()
            plt.savefig(dos_pdf_filename)
            plt.close(fig)
            print(f"{dos_pdf_filename} created successfully (Total + Projected).")
            
        except Exception as e:
            print("Error during DOS calculation/plotting:", e)
            import traceback
            traceback.print_exc()

    # === Step 5.5: Irreducible Representations (optional) ===
    if show_irreps:
        print("\n--- Step 5.5: Calculating Irreducible Representations ---")
        try:
            q_point = irreps_qpoint if irreps_qpoint else [0.0, 0.0, 0.0]
            
            # Determine tolerance for irreps
            # If tolerance_irreps is not provided, use tolerance_phonopy
            irreps_tol = tolerance_irreps if tolerance_irreps is not None else tolerance_phonopy
            
            print(f"Calculating irreps at q-point: {q_point} (tolerance: {irreps_tol})")
            
            # Using set_irreps and show_irreps as verified in Phonopy API
            base_phonon.set_irreps(
                q_point,
                is_little_cogroup=False,
                nac_q_direction=None,
                degeneracy_tolerance=irreps_tol
            )
            base_phonon.show_irreps() # Prints to stdout
            
            # Write to yaml file
            base_phonon.write_yaml_irreps(show_irreps=True)

        except Exception as e:
            print("Error during irreducible representation calculation:", e)
            import traceback
            traceback.print_exc()

    # === Step 5.6: Gruneisen workflow (optional) ===
    if plot_gruneisen:
        dat_filename, plot_distances, plot_segment_nqpoint, plot_labels = _run_gruneisen_on_top(
            phonons=all_phonons,
            strain=final_gruneisen_strain,
            band_yaml_path=band_yaml_path,
            output_prefix=output_prefix,
        )
        if dat_filename and dat_filename.exists():
            pdf_filename = f"gruneisen_band-{output_prefix}.pdf"
            _plot_gruneisen_from_dat(
                dat_filename=dat_filename, 
                distances=plot_distances,
                segment_nqpoint=plot_segment_nqpoint,
                labels=plot_labels,
                gmin=gmin, gmax=gmax,
                output_filename=pdf_filename,
                filter_outliers_factor=filter_outliers_factor,
            )
            
            mode_pdf_filename = f"gruneisen_mode_parameter-{output_prefix}.pdf"
            _plot_mode_gruneisen_from_dat(
                dat_filename=dat_filename, 
                distances=plot_distances,
                segment_nqpoint=plot_segment_nqpoint,
                labels=plot_labels,
                gmin=gmin, gmax=gmax,
                output_filename=mode_pdf_filename,
                filter_outliers_factor=filter_outliers_factor,
            )

    # === Step 6: Renaming outputs ===
    print("\n--- Step 6: Renaming outputs ---")
    
    # Files to simply rename
    rename_map = {
        "phonopy_disp.yaml": f"phonopy_disp-{output_prefix}.yaml",
        band_conf_path.name: f"band-{output_prefix}.conf",
        band_pdf_path.name: f"band-{output_prefix}.pdf",
        band_yaml_path.name: f"band-{output_prefix}.yaml",
        "band.dat": f"band-{output_prefix}.dat",
        "irreps.yaml": f"irreps-{output_prefix}.yaml",
        "phonon_dos.dat": f"phonon_dos-{output_prefix}.dat",
        "phonon_dos.pdf": f"phonon_dos-{output_prefix}.pdf",
    }

    for old, new in rename_map.items():
        old_path = output_dir / old
        if old_path.exists():
            try:
                if old == "phonopy_disp.yaml":
                    shutil.copy(old_path, output_dir / new)
                    print(f"Copied {old} -> {new}")
                else:
                    old_path.rename(output_dir / new)
                    print(f"Renamed {old} -> {new}")
            except FileNotFoundError:
                print(f"Warning: Could not find {old} to rename.")
    
    # Update paths to point to renamed files for subsequent steps
    band_conf_path = output_dir / f"band-{output_prefix}.conf"
    band_yaml_path = output_dir / f"band-{output_prefix}.yaml"

    # Files to copy and keep original (FORCE_SETS, FORCE_CONSTANTS, SPOSCAR)
    copy_map = {
        "FORCE_SETS": f"FORCE_SETS_{output_prefix}",
        "FORCE_CONSTANTS": f"FORCE_CONSTANTS_{output_prefix}",
    }
    
    # Check for SPOSCAR and add to copy map
    if (output_dir / "SPOSCAR").exists():
        copy_map["SPOSCAR"] = f"SPOSCAR_{output_prefix}"

    for original, copy_name in copy_map.items():
        original_path = output_dir / original
        if original_path.exists():
            try:
                shutil.copy(original_path, output_dir / copy_name)
                print(f"Copied {original} -> {copy_name}")
            except Exception as e:
                print(f"Warning: Could not copy {original}: {e}")

    # Copy input POSCAR to POSCAR-input and POSCAR
    if input_path.exists():
        try:
            shutil.copy(input_path, output_dir / "POSCAR-input")
            shutil.copy(input_path, output_dir / "POSCAR")
            print(f"Copied input {input_path.name} -> POSCAR-input and POSCAR")
        except Exception as e:
            print(f"Warning: Could not copy input POSCAR: {e}")

    # === Step 7: Write VESTA files for arrows (optional) ===
    if write_arrow or show_irreps:
        write_arrow = True # Force True if show_irreps is on
        print("\n--- Step 7: Writing VESTA files for phonon modes ---")
        try:
            from macer.phonopy.write_arrow_phonopy import write_vesta_files_for_arrows
            
            # 1. Determine unique output directory
            base_arrow_dir = output_dir / f"ARROW-{output_prefix}"
            arrow_dir = base_arrow_dir
            if arrow_dir.exists():
                i = 1
                while arrow_dir.exists():
                    arrow_dir = output_dir / f"ARROW-{output_prefix}-NEW{i:02d}"
                    i += 1
            arrow_dir.mkdir(parents=True)

            # 2. Determine execution targets
            target_points = []
            
            # Pinpoint mode: Calculate specific points
            if show_irreps:
                q_irr = np.array(irreps_qpoint) if irreps_qpoint else np.array([0.0, 0.0, 0.0])
                target_points.append((q_irr, "IRR", 1))
                print(f"  Mode: Writing arrows for Irreps Q-point: {q_irr}")

            elif arrow_qpoint_gamma:
                 target_points.append((np.array([0.0, 0.0, 0.0]), "GM", 1))
                 print("  Mode: Writing arrows for Gamma point only.")
            
            elif arrow_qpoint is not None:
                 q_vec = np.array(arrow_qpoint)
                 target_points.append((q_vec, "SELECTIVE", 1))
                 print(f"  Mode: Writing arrows for user-specified Q-point: {q_vec}")
            
            else:
                 # Default: Special Points from band.conf
                 print("  Mode: Writing arrows for Special Q-points detected in band path.")
                 from phonopy.cui.settings import PhonopyConfParser
                 conf_parser = PhonopyConfParser(filename=str(band_conf_path))
                 settings = conf_parser.settings
                 
                 q_sequence = []
                 l_sequence = []
                 
                 def clean_l(s):
                     s = s.strip()
                     # Handle LaTeX and common Gamma variations
                     if s.upper() in ["GAMMA", "G", "GM", r"$\Gamma$", r"$\GAMMA$", r"\GAMMA"]:
                         return "GM"
                     return s.replace("$", "").replace("\\", "").replace("_", "")

                 if settings.band_paths:
                     labels_flat = []
                     if settings.band_labels:
                         for l_seg in settings.band_labels:
                             if isinstance(l_seg, list): labels_flat.extend(l_seg)
                             else: labels_flat.append(l_seg)
                     
                     q_idx_in_flat = 0
                     for path_seg in settings.band_paths:
                         for q in path_seg:
                             q_np = np.array(q)
                             l_raw = labels_flat[q_idx_in_flat] if q_idx_in_flat < len(labels_flat) else "QP"
                             l_c = clean_l(l_raw)
                             
                             is_duplicate = False
                             for sq, sl in zip(q_sequence, l_sequence):
                                 if np.allclose(q_np, sq, atol=1e-4) and l_c == sl:
                                     is_duplicate = True
                                     break
                             
                             if not is_duplicate:
                                 q_sequence.append(q_np)
                                 l_sequence.append(l_c)
                             q_idx_in_flat += 1
                 
                 for i, (q, l) in enumerate(zip(q_sequence, l_sequence)):
                     target_points.append((q, l, i+1))

            # Execute Loop for Target Points
            for q_pos, label, idx in target_points:
                q_str = f"{q_pos[0]:.3f}_{q_pos[1]:.3f}_{q_pos[2]:.3f}"
                
                # If Irreps mode and only one point, write directly to arrow_dir
                if show_irreps and len(target_points) == 1:
                    sub_dir = arrow_dir
                    print(f"  - Processing Q-point: {q_pos} (writing directly to {arrow_dir.name})")
                elif label == "SELECTIVE":
                    sub_dir_name = f"QPOINTS_SELECTIVE={q_str}"
                    sub_dir = arrow_dir / sub_dir_name
                    sub_dir.mkdir(parents=True, exist_ok=True)
                    print(f"  - Processing Q-point: {label} {q_pos}")
                else:
                    sub_dir_name = f"QPOINTS_{idx:03d}-{label}={q_str}"
                    sub_dir = arrow_dir / sub_dir_name
                    sub_dir.mkdir(parents=True, exist_ok=True)
                    print(f"  - Processing Q-point {idx}: {label} {q_pos}")
                
                # Run q-point calculation
                base_phonon.run_qpoints([q_pos], with_eigenvectors=True)
                
                # Write temp qpoints.yaml
                base_phonon.write_yaml_qpoints_phonon() # Writes to qpoints.yaml
                
                temp_yaml = output_dir / "qpoints.yaml"
                if not temp_yaml.exists():
                     print("    Error: qpoints.yaml not generated.")
                     continue
                
                # If this is a pinpoint case with a single point, save as eigenvector-{prefix}.yaml for convenience
                if (arrow_qpoint_gamma or show_irreps or arrow_qpoint is not None) and len(target_points) == 1:
                    eigenvector_yaml_path = output_dir / f"eigenvector-{output_prefix}.yaml"
                    shutil.copy(temp_yaml, eigenvector_yaml_path)
                    print(f"    Saved eigenvector data to {eigenvector_yaml_path.name}")

                # Generate VESTA
                irreps_yaml_path_to_pass = output_dir / f"irreps-{output_prefix}.yaml" if show_irreps else None
                write_vesta_files_for_arrows(
                    band_yaml_path=temp_yaml,
                    poscar_path=symmetrized_input_path, # Use the actual cell used for calculation
                    output_dir=sub_dir,
                    arrow_length=arrow_length,
                    arrow_min_cutoff=arrow_min_cutoff,
                    target_q_point=q_pos, 
                    irreps_yaml_path=irreps_yaml_path_to_pass
                )
                
                if temp_yaml.exists():
                    temp_yaml.unlink() # Cleanup temp file

        except Exception as e:
            print("Error during VESTA file generation for arrows:", e)
            import traceback
            traceback.print_exc()

    # === Step 8: Write modulation-example.conf ===
    print("\n--- Step 8: Writing modulation-example.conf ---")
    dim_str_mod = " ".join(map(str, base_phonon.supercell_matrix.diagonal().astype(int)))
    if np.count_nonzero(base_phonon.supercell_matrix - np.diag(base_phonon.supercell_matrix.diagonal())) != 0:
         dim_str_mod = " ".join(map(str, base_phonon.supercell_matrix.flatten().astype(int)))

    modulation_content = f"""# supercell dim
# qpoint
# band index
# amplitude
# degree
DIM = {dim_str_mod}
MODULATION = 2 2 1, 0.5 0.5 0.0 1 10 0
#MODULATION = 3 3 1, 0.0 0.0 0.0 6 5 0
#FORCE_CONSTANTS = READ
"""
    (output_dir / "modulation-example.conf").write_text(modulation_content)
    print(f"Created modulation-example.conf")

    # === Cleanup ===
    print("\n--- Cleaning up ---")
    cleanup_patterns = ['vasprun-*.xml', 'OUTCAR-*', 'CONTCAR-*', 'relax-*.log.*', 'phonopy.yaml']
    for pattern in cleanup_patterns:
        for item in output_dir.glob(pattern):
            try:
                if item.is_dir(): shutil.rmtree(item)
                else: item.unlink()
            except OSError as e:
                print(f"Error cleaning up {item}: {e}")

    print(f"\nWorkflow for {input_path.name} completed.")
    print("\n--- Final summary ---")
    print(f"  Space group of {symmetrized_input_path.name}: {final_symmetrized_sg_symbol} (No. {final_symmetrized_sg_number})")
    
    # Get the supercell dimension string for the help message
    dim_str_help = " ".join(map(str, base_phonon.supercell_matrix.diagonal().astype(int)))
    if np.count_nonzero(base_phonon.supercell_matrix - np.diag(base_phonon.supercell_matrix.diagonal())) != 0:
         dim_str_help = " ".join(map(str, base_phonon.supercell_matrix.flatten().astype(int)))

    print("\n--- Post-processing Help ---")
    print(f"Calculation directory: {output_dir}")
    print("To re-calculate irreducible representations (example):")
    print(f'  phonopy --dim="{dim_str_help}" --irreps="0 0 0" -c POSCAR-input --tolerance {tolerance_phonopy}')
    print("To re-plot band structure (example):")
    print(f'  phonopy --dim="{dim_str_help}" -c POSCAR-input -p -s band-{output_prefix}.conf')

    print("===== macer phonon workflow: DONE =====\n")