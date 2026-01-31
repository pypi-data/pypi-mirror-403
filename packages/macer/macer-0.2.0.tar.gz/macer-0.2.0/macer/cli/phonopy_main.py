"""
Macer: Machine-learning accelerated Atomic Computational Environment for automated Research workflows
Copyright (c) 2025 The Macer Package Authors
Author: Soungmin Bae <soungminbae@gmail.com>
License: MIT
"""

import argparse
import sys
import os
import glob
import warnings
from pathlib import Path
from ase.io import read, write

# Suppress common warnings from third-party libraries (e.g., Mattersim, Torch)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*weights_only=False.*")
warnings.filterwarnings("ignore", message=".*cuequivariance.*")
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

# Suppress UserWarnings from specific MLFF libraries
for module_name in ["mattersim", "mace", "sevenn", "chgnet", "matgl", "nequip", "orb_models", "fairchem"]:
    warnings.filterwarnings("ignore", category=UserWarning, module=module_name)

from macer.phonopy.relax_unit import run_relax_unit
from macer.phonopy.phonon_band import run_macer_workflow
from macer.phonopy.qha import add_qha_parser
from macer.phonopy.sscha import add_sscha_parser
from macer.phonopy.thermal_conductivity import add_tc_parser
from macer.phonopy.dynaphopy import add_dynaphopy_parser
from macer.defaults import DEFAULT_MODELS, _macer_root, _model_root, DEFAULT_DEVICE, DEFAULT_FF, resolve_model_path
from macer.calculator.factory import get_calculator, get_available_ffs, ALL_SUPPORTED_FFS
from macer.utils.validation import check_poscar_format
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

# Determine default force field based on installed extras
available_ffs = get_available_ffs()
_dynamic_default_ff = available_ffs[0] if available_ffs else None


from macer.utils.logger import Logger


def run_phonon_band_cli(args):
    """
    Helper function to adapt parsed arguments to run_macer_workflow.
    Handles multiple input POSCAR files.
    """
    is_cif_mode = False
    if args.input_files:
        input_patterns = args.input_files
    elif args.cif_files:
        input_patterns = args.cif_files
        is_cif_mode = True
    else:
        # Should be caught by main.py, but for safety:
        return

    input_files = []
    for pat in input_patterns:
        if os.path.exists(pat):
            input_files.append(pat)
        else:
            input_files.extend(glob.glob(pat))
    
    if not input_files:
        raise FileNotFoundError(f"Position input file (POSCAR format) not found at: {', '.join(input_patterns)}. Please provide a valid position file in POSCAR format. If you provide a cif file, please use -c option.")

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

    original_cwd = os.getcwd()

    is_plusminus_val = 'auto'
    if args.is_plusminus:
        is_plusminus_val = True

    is_diagonal_val = True
    if not args.is_diagonal:
        is_diagonal_val = False

    # Determine symprec for seekpath
    symprec_for_seekpath = args.symprec
    if args.symprec == 1e-5 and args.tolerance_sr != 0.01:
        symprec_for_seekpath = args.tolerance_sr

    for filepath_str in sorted(list(set(input_files))):
        original_input_path = Path(filepath_str).resolve()
        
        if not is_cif_mode:
            try:
                check_poscar_format(original_input_path)
            except ValueError as e:
                print(f"Error: {e}")
                continue
        
        # Automatically enable write_arrow if a specific arrow q-point mode is selected
        if args.arrow_qpoint_gamma or (args.arrow_qpoint is not None):
            args.write_arrow = True
        
        # Default input path is the file itself
        input_path = original_input_path
        output_prefix = original_input_path.stem
        
        # Handle conversion
        if is_cif_mode:
            try:
                # Convert to POSCAR in the same directory
                target_dir = original_input_path.parent
                poscar_out = target_dir / "POSCAR"
                
                atoms_in = read(str(original_input_path))
                write(str(poscar_out), atoms_in, format='vasp')
                print(f"Converted {original_input_path.name} to {poscar_out}")
                
                input_path = poscar_out
                # Use the CIF stem as prefix
                output_prefix = original_input_path.stem
            except Exception as e:
                print(f"Error converting CIF {filepath_str}: {e}")
                continue

        output_dir = input_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        # Setup logger
        log_name = output_dir / f"macer_phonopy_pb-{output_prefix}.log"
        orig_stdout = sys.stdout
        
        try:
            with Logger(str(log_name)) as lg:
                sys.stdout = lg

                # Determine model path and info string
                current_model_path = args.model
                model_info_str = ""
                # Define FFs that expect a model NAME, not a file path from mlff-model
                FFS_USING_MODEL_NAME = {"fairchem", "orb", "chgnet", "m3gnet"}

                if current_model_path:
                    model_info_str = f" (from --model option)"
                    current_model_path = resolve_model_path(current_model_path)
                else:
                    default_model_name = DEFAULT_MODELS.get(args.ff)
                    if default_model_name:
                        if args.ff in FFS_USING_MODEL_NAME:
                            # For these FFs, the default is a model name to be used directly
                            current_model_path = default_model_name
                        else:
                            # For other FFs, the default is a filename in the mlff-model directory
                            current_model_path = resolve_model_path(default_model_name)
                        model_info_str = f" (default for {args.ff.upper()}: {default_model_name})"
                    else:
                        if args.ff:
                            model_info_str = f" (no model specified, using {args.ff.upper()} internal default)"
                        else:
                            sys.stderr.write("Error: No force field specified. Please use the --ff option.\n")
                            # We raise exception instead of sys.exit for interactive usage
                            raise ValueError("No force field specified. Please use the --ff option.")

                os.chdir(output_dir)

                dim_override_str = " ".join(map(str, args.dim)) if args.dim else None

                run_macer_workflow(
                    input_path=input_path,
                    min_length=args.length,
                    displacement_distance=args.amplitude,
                    is_plusminus=is_plusminus_val,
                    is_diagonal=is_diagonal_val,
                    macer_device=args.device,
                    macer_model_path=current_model_path,
                    model_info_str=model_info_str,
                    yaml_path_arg=args.yaml,
                    out_path_arg=args.out,
                    gamma_label=args.gamma,
                    symprec_seekpath=symprec_for_seekpath,
                    dim_override=dim_override_str,
                    no_defaults_band_conf=args.no_defaults,
                    atom_names_override=args.atom_names,
                    rename_override=args.rename,
                    tolerance_sr=args.tolerance_sr,
                    tolerance_phonopy=args.tolerance_phonopy,
                    macer_optimizer_name=args.optimizer,
                    fix_axis=args.fix_axis,
                    macer_ff=args.ff,
                    macer_modal=args.modal,
                    plot_gruneisen=args.plot_gruneisen,
                    gruneisen_strain=args.strain,
                    gmin=args.gmin,
                    gmax=args.gmax,
                    gruneisen_target_energy=args.target_energy,
                    filter_outliers_factor=args.filter_outliers,
                    use_relax_unit=args.use_relax_unit,
                    initial_fmax=args.initial_fmax,
                    initial_symprec=args.initial_symprec,
                    initial_isif=args.initial_isif,
                    output_prefix=output_prefix, # Added this argument
                    show_irreps=args.irreps,
                    irreps_qpoint=args.qpoint,
                    tolerance_irreps=args.tolerance_irreps,
                    write_arrow=args.write_arrow,
                    arrow_length=args.arrow_length,
                    arrow_min_cutoff=args.arrow_min_cutoff,
                    arrow_qpoint_gamma=args.arrow_qpoint_gamma,
                    arrow_qpoint=args.arrow_qpoint,
                    mass_map=mass_map,
                    output_dir_arg=args.output_dir,
                    plot_dos=args.dos,
                    mesh=args.mesh
                )

        except Exception as e: # Catch all exceptions
            sys.stdout = orig_stdout # Restore stdout before printing error
            import traceback
            # Re-raise instead of sys.exit(1)
            raise e

        finally:
            sys.stdout = orig_stdout # Restore stdout
            os.chdir(original_cwd)


def add_phonopy_parsers(subparsers):
    from macer import __version__
    # phonon-band command (alias: pb)
    phonon_band_parser = subparsers.add_parser(
        "phonon-band",
        aliases=["pb"],
        help="Full phonon dispersion workflow (Force Sets, Band Structure)",
        description=MACER_LOGO + f"\nmacer phonopy pb (v{__version__}): Full phonopy workflow using MLFFs for phonon dispersion calculation, including band.conf generation.",
        epilog="""
Examples:
  # 1. Standard phonon dispersion with auto-determined supercell (min length 20A)
  macer phonopy pb -p POSCAR --length 20.0 --ff mattersim

  # 2. Explicit supercell with DOS calculation and specific Q-point mesh
  macer phonopy pb -p POSCAR --dim 2 2 2 --dos --mesh 20 20 20

  # 3. Gruneisen parameter calculation (estimating strain from bulk modulus)
  macer phonopy pb -p POSCAR --dim 2 2 2 --plot-gruneisen --target-energy 10

  # 4. Visualize phonon modes: Export VESTA files for Gamma-point modes
  macer phonopy pb -p POSCAR --dim 2 2 2 --write-arrow --arrow-qpoint-gamma
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    # General & Input
    general_group = phonon_band_parser.add_argument_group('General & Input')
    general_group.add_argument(
        "-p", "--poscar", dest="input_files", required=False, nargs='+', default=None,
        help="One or more input cell files in VASP POSCAR format."
    )
    general_group.add_argument(
        "-c", "--cif", dest="cif_files", required=False, nargs='+', default=None,
        help="One or more input cell files in CIF format."
    )
    general_group.add_argument("--output-dir", help="Directory to save output files.")

    # MLFF Settings
    mlff_group = phonon_band_parser.add_argument_group('MLFF Model Settings')
    mlff_group.add_argument("--ff", type=str, default=DEFAULT_FF, choices=ALL_SUPPORTED_FFS, help=f"Force field to use. (default: {DEFAULT_FF})")
    mlff_group.add_argument('--model', type=str, default=None, help='Path to the force field model file for macer.')
    mlff_group.add_argument('--device', type=str, default=DEFAULT_DEVICE, choices=['cpu', 'mps', 'cuda'], help='Device for macer computation.')
    mlff_group.add_argument("--modal", type=str, default=None, help="Modal for SevenNet model.")

    # Relaxation Settings
    relax_group = phonon_band_parser.add_argument_group('Structure Relaxation Settings')
    relax_group.add_argument(
        "--use-relax-unit",
        action="store_true",
        help="Use iterative relaxation/symmetrization (macer phonopy sr) for the initial structure preparation. "
             "Default is a single 'macer relax' run."
    )
    relax_group.add_argument("--initial-fmax", type=float, default=0.005,
                        help="Force convergence threshold for initial 'macer relax' in eV/Å. (default: 0.005)")
    relax_group.add_argument("--initial-symprec", type=float, default=1e-5,
                        help="Symmetry tolerance for FixSymmetry during initial 'macer relax' (default: 1e-5 Å).")
    relax_group.add_argument("--initial-isif", type=int, default=3,
                        help="VASP ISIF mode for initial 'macer relax'. (default: 3)")
    relax_group.add_argument('--tolerance-sr', type=float, default=0.01, help='Symmetry tolerance (Å) for macer phonopy sr. Default: 0.01.')
    relax_group.add_argument("--optimizer", type=str, default="FIRE", help="Optimizer to use for relaxation (e.g., FIRE, BFGS, LBFGS).")
    
    # Supercell & Displacement Settings
    supercell_group = phonon_band_parser.add_argument_group('Supercell & Displacement Settings')
    supercell_group.add_argument("--dim", type=int, nargs='+', default=None, help='Set supercell dimension. Accepts 3 integers for a diagonal matrix (e.g., "2 2 2") or 9 for a full matrix. Overrides -l/--length.')
    supercell_group.add_argument(
        "-l", "--length", type=float, default=20.0,
        help="Minimum length of supercell lattice vectors in Å (default: 20.0)."
    )
    supercell_group.add_argument(
        '--fix-axis', type=lambda s: [axis.strip() for axis in s.split(',')],
        help='Fix specified axes (e.g., "a,c" or "x,y,z") for supercell construction. The corresponding dimension will be set to 1.'
    )
    supercell_group.add_argument("--amplitude", type=float, default=0.01, help="Displacement amplitude in Å (default: 0.01).")
    supercell_group.add_argument('--pm', dest='is_plusminus', action="store_true", help='Generate plus and minus displacements for each direction.')
    supercell_group.add_argument('--nodiag', dest='is_diagonal', action="store_false", help='Do not generate diagonal displacements.')
    supercell_group.add_argument("--mass", nargs='+', help="Specify atomic masses. Format: Symbol Mass Symbol Mass ... (e.g. --mass H 2.014 D 2.014)")
    supercell_group.add_argument("--atom-names", default=None, help='Override ATOM_NAME, e.g. "K Zr P O".')
    supercell_group.add_argument("--rename", default=None, help='Rename mapping, e.g. "Na=K,Zr=Zr".')

    # Phonopy & Band Structure Settings
    phonopy_group = phonon_band_parser.add_argument_group('Phonopy & Band Structure Settings')
    phonopy_group.add_argument('--tolerance-phonopy', type=float, default=5e-3, help='Symmetry tolerance for phonopy. Default: 5e-3.')
    phonopy_group.add_argument("--symprec", type=float, default=1e-5, help="Symmetry tolerance passed to SeeK-path (default: 1e-5).")
    phonopy_group.add_argument("--gamma", default="GM", help="Gamma label for BAND_LABELS (e.g., GM or Γ).")
    phonopy_group.add_argument("--yaml", default="phonopy_disp.yaml", type=Path, help="Path to phonopy_disp.yaml to read DIM from (for band.conf).")
    phonopy_group.add_argument("--out", default="band.conf", type=Path, help="Output band.conf file name.")
    phonopy_group.add_argument("--no-defaults", action="store_true", help="Do not include default FORCE_SETS, FC_SYMMETRY, EIGENVECTORS lines.")

    # Grüneisen Parameter Plot Settings
    gruneisen_group = phonon_band_parser.add_argument_group('Grüneisen Parameter Plot Settings')
    gruneisen_group.add_argument(
        '--plot-gruneisen', '-pg', dest='plot_gruneisen', action="store_true",
        help='Plot Gruneisen parameter on phonon dispersion.'
    )
    gruneisen_group.add_argument(
        '--strain', type=float, default=None,
        help='Strain for Gruneisen parameter. If not set, it will be estimated from the bulk modulus.'
    )
    gruneisen_group.add_argument(
        '--gmin', type=float, default=None,
        help='Minimum Gruneisen parameter for color scale.'
    )
    gruneisen_group.add_argument(
        '--gmax', type=float, default=None,
        help='Maximum Gruneisen parameter for color scale.'
    )
    gruneisen_group.add_argument(
        '--filter-outliers', type=float, nargs='?', const=3.0, default=None,
        help='Filter outlier Grüneisen values from the plot. '
             'Optionally provide a factor to multiply the IQR (default: 3.0). '
             'Points outside [Q1 - factor*IQR, Q3 + factor*IQR] will be hidden.'
    )
    gruneisen_group.add_argument(
        '--target-energy', type=float, default=10.0,
        help='Target energy in meV for bulk modulus-based strain estimation (default: 10.0).'
    )

    # DOS & Irreps Settings
    dos_irreps_group = phonon_band_parser.add_argument_group('DOS & Irreps Settings')
    dos_irreps_group.add_argument(
        "--dos", dest="dos", action="store_true",
        help="Calculate and plot phonon Density of States (DOS)."
    )
    dos_irreps_group.add_argument(
        "--mesh", type=int, nargs=3, default=[20, 20, 20],
        help="Q-point mesh for DOS calculation (default: 20 20 20)."
    )
    dos_irreps_group.add_argument(
        "--irreps", "--irreducible-representation", dest="irreps", action="store_true",
        help="Calculate irreducible representations."
    )
    dos_irreps_group.add_argument(
        "--qpoint", nargs=3, type=float, default=[0.0, 0.0, 0.0],
        help="Q-point for irreducible representations calculation. Default is 0 0 0."
    )
    dos_irreps_group.add_argument(
        "--tolerance-irreps", type=float, default=1e-5,
        help="Degeneracy tolerance for irreducible representations (default: 1e-5)."
    )
    
    # Arrow (VESTA) Export Settings
    arrow_group = phonon_band_parser.add_argument_group('Arrow (VESTA) Export Settings')
    arrow_group.add_argument(
        "--write-arrow", "-wa", dest="write_arrow", action="store_true",
        help="Write VESTA files for phonon mode visualization. Default is for special q-points."
    )
    arrow_group.add_argument(
        "--arrow-length", type=float, default=1.8,
        help="Set the length of the longest arrow in the visualization (in Angstroms). Default is 1.8."
    )
    arrow_group.add_argument(
        "--arrow-min-cutoff", type=float, default=0.3,
        help="Do not draw arrows with lengths smaller than this value (in Angstroms). Default is 0.3."
    )
    # Mutually exclusive group for filtering mode
    mode_group = arrow_group.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--arrow-qpoint-gamma", action="store_true",
        help="Write arrows only for the Gamma point."
    )
    arrow_group.add_argument(
        "--arrow-qpoint", nargs=3, type=float, default=None,
        help="Write arrows for a specific q-point vector (3 floats)."
    )

    phonon_band_parser.set_defaults(func=run_phonon_band_cli)

    # Add QHA sub-command
    qha_p = add_qha_parser(subparsers)

    # Add SSCHA sub-command
    sscha_p = add_sscha_parser(subparsers)

    # Add TC sub-command
    tc_p = add_tc_parser(subparsers)

    # Add DynaPhoPy sub-command
    ft_p = add_dynaphopy_parser(subparsers)

    # symmetry-refine command
    symmetry_refine_parser = subparsers.add_parser(
        "symmetry-refine",
        aliases=["sr"],
        help="Iterative relaxation and symmetry refinement",
        description=MACER_LOGO + f"\nmacer phonopy sr (v{__version__}): Iteratively relax and symmetrize a unit cell using MLFFs and spglib.",
        epilog="""
Examples:
  # 1. Standard iterative symmetrization (tolerance 0.01 A)
  macer phonopy sr -p POSCAR --tolerance 0.01 --ff mattersim

  # 2. Tighter convergence for sensitive structures
  macer phonopy sr -p POSCAR --fmax 0.001 --symprec-fix 1e-6 --max-iterations 20

  # 3. Fix the c-axis during relaxation (e.g., for layered materials)
  macer phonopy sr -p POSCAR --fix-axis c --tolerance 0.05
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # ... (arguments same as before) ...
    sr_general_group = symmetry_refine_parser.add_argument_group('General & Input')
    sr_general_group.add_argument(
        "--poscar", "-p", dest="input_files", type=str, nargs='+',
        default=None,
        help="Input POSCAR file(s) or pattern(s) (e.g., POSCAR-*)."
    )
    sr_general_group.add_argument(
        "--cif", "-c", dest="cif_files", type=str, nargs='+',
        default=None,
        help="Input CIF file(s) or pattern(s)."
    )
    sr_general_group.add_argument("--output-prefix", type=str, default=None, help="Prefix for output files. Defaults to the input POSCAR filename.")
    sr_general_group.add_argument("--output-dir", help="Directory to save output files.")

    # MLFF Settings
    sr_mlff_group = symmetry_refine_parser.add_argument_group('MLFF Model Settings')
    sr_mlff_group.add_argument(
        "--ff", type=str, default=DEFAULT_FF,
        choices=ALL_SUPPORTED_FFS,
        help=f"Force field to use. (default: {DEFAULT_FF})"
    )
    sr_mlff_group.add_argument(
        "--model", type=str, default=None,
        help="Path to the MLFF model file."
    )
    sr_mlff_group.add_argument("--modal", type=str, default=None, help="Modal for SevenNet model.")
    sr_mlff_group.add_argument(
        "--device", type=str, default=DEFAULT_DEVICE,
        choices=["cpu", "mps", "cuda"],
        help="Compute device (default: cpu)."
    )

    # Relaxation & Symmetry Settings
    sr_relax_group = symmetry_refine_parser.add_argument_group('Relaxation & Symmetry Settings')
    sr_relax_group.add_argument("--max-iterations", type=int, default=10, help="Maximum number of relaxation-symmetrization iterations.")
    sr_relax_group.add_argument("--fmax", type=float, default=0.005, help="Force convergence threshold for relaxation (eV/Å).")
    sr_relax_group.add_argument("--smax", type=float, default=0.001, help="Stress convergence threshold for relaxation (eV/Å³).")
    sr_relax_group.add_argument(
        "--optimizer", type=str, default="FIRE",
        help="Optimizer to use for relaxation (e.g., FIRE, BFGS, LBFGS).",
    )
    sr_relax_group.add_argument(
        '--fix-axis', type=lambda s: [axis.strip() for axis in s.split(',')],
        help='Fix specified axes (e.g., "a,c" or "x,y,z") during relaxation. Atoms will not move along these axes.'
    )
    sr_relax_group.add_argument("--tolerance", type=float, default=0.01, help="Symmetry tolerance for spglib (in Å).")
    sr_relax_group.add_argument(
        "--tolerance-sym", type=float, default=None,
        help="Symmetry tolerance for space group detection (in Å). If not set, uses --tolerance."
    )
    sr_relax_group.add_argument(
        "--symprec-fix", type=float, default=1e-5,
        help="Symmetry tolerance for FixSymmetry constraint during relaxation (default: 1e-5 Å)."
    )
    sr_relax_group.add_argument(
        "--symmetry-off",
        dest="use_symmetry",
        action="store_false",
        help="Disable the FixSymmetry constraint during relaxation steps."
    )
    sr_relax_group.add_argument("--quiet", action="store_true", help="Suppress verbose output during relaxation steps.")

    symmetry_refine_parser.set_defaults(func=run_relax_unit)

    return {
        "pb": phonon_band_parser,
        "qha": qha_p,
        "sscha": sscha_p,
        "tc": tc_p,
        "ft": ft_p,
        "sr": symmetry_refine_parser
    }

def main():
    from macer import __version__
    parser = argparse.ArgumentParser(
        description=MACER_LOGO + f"\nmacer_phonopy (v{__version__}): Machine-learning accelerated Atomic Computational Environment for automated Research workflows",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", "-v", action="version", version=f"macer_phonopy {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_map = add_phonopy_parsers(subparsers)

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    # Manual required argument checks for phonopy subcommands
    cmd = args.command
    # Map aliases back to canonical keys in p_map
    if cmd == 'pb': cmd = 'pb'
    elif cmd == 'qha': cmd = 'qha'
    elif cmd == 'sscha': cmd = 'sscha'
    elif cmd == 'tc': cmd = 'tc'
    elif cmd == 'ft': cmd = 'ft'
    elif cmd == 'sr': cmd = 'sr'

    if cmd in p_map:
        has_input = False
        if hasattr(args, 'input_files') and args.input_files: has_input = True
        if hasattr(args, 'cif_files') and args.cif_files: has_input = True
        if hasattr(args, 'poscar') and args.poscar: has_input = True 
        if hasattr(args, 'cif') and args.cif: has_input = True
        
        if not has_input:
            p_map[cmd].print_help()
            sys.exit(0)
        
        # Additional check for SSCHA: requires temperature
        if cmd == 'sscha' and not getattr(args, 'temperature', None):
            p_map[cmd].print_help()
            sys.exit(0)
        
        # Additional check for ft (DynaPhoPy): requires temp
        if cmd == 'ft' and not getattr(args, 'temp', None):
            p_map[cmd].print_help()
            sys.exit(0)

    if hasattr(args, "func"):
        if args.command == 'qha' and hasattr(args, 'num_volumes') and args.num_volumes < 4:
            parser.error("For the 'qha' command, number of volume points (--num-volumes) must be at least 4.")
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
