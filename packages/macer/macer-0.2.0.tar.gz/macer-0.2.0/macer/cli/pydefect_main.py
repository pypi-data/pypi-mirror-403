"""
Macer: Machine-learning accelerated Atomic Computational Environment for automated Research workflows
Copyright (c) 2025 The Macer Package Authors
Author: Soungmin Bae <soungminbae@gmail.com>
License: MIT
"""

import argparse
import sys
import glob
import copy
import os
from macer.pydefect.cpd import run_cpd_workflow
from macer.pydefect.defect import run_defect_workflow
from macer.pydefect.full import run_full_workflow
from macer.calculator.factory import get_available_ffs, ALL_SUPPORTED_FFS
from macer.defaults import DEFAULT_DEVICE, DEFAULT_FF
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

def add_pydefect_parsers(subparsers):
    """Add pydefect sub-commands (cpd, defect, full) directly to the provided subparsers."""
    
    # CPD command
    cpd_parser = subparsers.add_parser(
        "cpd",
        description=MACER_LOGO + "\nRun Chemical Potential Diagram (CPD) workflow.",
        help="Generate CPD and target vertices.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    cpd_general = cpd_parser.add_argument_group('General & Input')
    cpd_general.add_argument("-f", "--formula", type=str, help="Formula to retrieve from Materials Project (e.g., MgAl2O4)")
    cpd_general.add_argument("-m", "--mpid", type=str, help="Materials Project ID (e.g., mp-3536)")
    cpd_general.add_argument("-d", "--doping", type=str, nargs='+', help="Dopant element(s) (e.g., Cl)")
    cpd_general.add_argument("-p", "--poscar", type=str, nargs='+', help="Input POSCAR file(s) (Optional)")
    _add_mlff_group(cpd_parser)
    cpd_calc = cpd_parser.add_argument_group('Calculation Settings')
    cpd_calc.add_argument("--fmax", type=float, default=0.03, help="Force convergence threshold (eV/Å). Default: 0.03")
    cpd_calc.add_argument("--energy-shift-target", type=float, default=0.0, help="Manually shift target energy (eV/atom). Default: 0.0")
    cpd_parser.set_defaults(func=run_batch_workflow, workflow_func=run_cpd_workflow)

    # Defect command
    defect_parser = subparsers.add_parser(
        "defect",
        description=MACER_LOGO + "\nRun Defect Analysis workflow (Supercell generation, Relaxation, Analysis).",
        help="Calculate defect formation energies.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    defect_general = defect_parser.add_argument_group('General & Input')
    defect_general.add_argument("-p", "--poscar", type=str, nargs='+', help="Input POSCAR file(s) (Perfect Unitcell)")
    defect_general.add_argument("-d", "--doping", type=str, nargs='+', help="Dopant element(s) (e.g., Cl)")
    defect_general.add_argument("-s", "--std_energies", type=str, help="Path to standard_energies.yaml")
    defect_general.add_argument("-t", "--target_vertices", type=str, help="Path to target_vertices.yaml")
    _add_mlff_group(defect_parser)
    defect_sc = defect_parser.add_argument_group('Supercell & Symmetry')
    defect_sc.add_argument("--matrix", nargs="+", type=int, help="Supercell matrix applied to the conventional cell.")
    defect_sc.add_argument("--min_atoms", type=int, default=50, help="Minimum number of atoms (default: 50)")
    defect_sc.add_argument("--max_atoms", type=int, default=300, help="Maximum number of atoms (default: 300)")
    defect_sc.add_argument("--no_symmetry_analysis", dest="analyze_symmetry", action="store_false", help="Disable symmetry analysis.")
    defect_parser.set_defaults(analyze_symmetry=True)
    defect_sc.add_argument("--sites_yaml", type=str, dest="sites_yaml_filename", help="Path to sites.yaml file.")
    defect_relax = defect_parser.add_argument_group('Relaxation Settings')
    defect_relax.add_argument("--fmax", type=float, default=0.03, help="Force threshold (default: 0.03)")
    defect_parser.set_defaults(func=run_batch_workflow, workflow_func=run_defect_workflow)

    # Full command
    full_parser = subparsers.add_parser(
        "full",
        description=MACER_LOGO + "\nRun Full Defect Analysis workflow (CPD + Defect Analysis).",
        help="Run both CPD and Defect Analysis workflows.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    full_general = full_parser.add_argument_group('General & Input')
    full_general.add_argument("-f", "--formula", type=str, help="Formula (e.g., MgAl2O4)")
    full_general.add_argument("-m", "--mpid", type=str, help="Materials Project ID (e.g., mp-3536)")
    full_general.add_argument("-p", "--poscar", type=str, nargs='+', help="Input POSCAR file(s)")
    full_general.add_argument("-d", "--doping", type=str, nargs='+', help="Dopant element(s)")
    _add_mlff_group(full_parser)
    full_sc = full_parser.add_argument_group('Supercell & Symmetry')
    full_sc.add_argument("--matrix", nargs="+", type=int, help="Supercell matrix.")
    full_sc.add_argument("--min_atoms", type=int, default=50, help="Min atoms (default: 50)")
    full_sc.add_argument("--max_atoms", type=int, default=300, help="Max atoms (default: 300)")
    full_sc.add_argument("--no_symmetry_analysis", dest="analyze_symmetry", action="store_false", help="Disable symmetry analysis.")
    full_parser.set_defaults(analyze_symmetry=True)
    full_sc.add_argument("--sites_yaml", type=str, dest="sites_yaml_filename", help="Path to sites.yaml file.")
    full_relax = full_parser.add_argument_group('Relaxation & Correction')
    full_relax.add_argument("--fmax", type=float, default=0.03, help="Global force threshold (default: 0.03)")
    full_relax.add_argument("--fmax-cpd", type=float, help="CPD force threshold.")
    full_relax.add_argument("--fmax-defect", type=float, help="Defect force threshold.")
    full_relax.add_argument("--energy-shift-target", type=float, default=0.0, help="Shift target energy. Default: 0.0")
    full_parser.set_defaults(func=run_batch_workflow, workflow_func=run_full_workflow)

    return {
        "cpd": cpd_parser,
        "defect": defect_parser,
        "full": full_parser
    }

def _add_mlff_group(parser):
    """Helper to add MLFF arguments to a parser group."""
    mlff_group = parser.add_argument_group('MLFF Model Settings')
    mlff_group.add_argument("--ff", type=str, default=DEFAULT_FF, choices=ALL_SUPPORTED_FFS, help=f"Force field to use. (default: {DEFAULT_FF})")
    mlff_group.add_argument("--model", type=str, default=None, help="Path to the MLFF model file.")
    mlff_group.add_argument("--device", type=str, default=DEFAULT_DEVICE, choices=["cpu", "mps", "cuda"], help="Compute device.")
    mlff_group.add_argument("--modal", type=str, default=None, help="Modal for SevenNet model.")

def run_batch_workflow(args):
    workflow_func = args.workflow_func
    if hasattr(args, 'poscar') and args.poscar:
        input_patterns = args.poscar
        input_files = []
        for pat in input_patterns:
            if os.path.exists(pat): input_files.append(pat)
            else: input_files.extend(glob.glob(pat))
        input_files = sorted(list(set(input_files)))
        if not input_files:
            print(f"No input files found matching: {input_patterns}")
            sys.exit(1)
        original_cwd = os.getcwd()
        for f in input_files:
            os.chdir(original_cwd)
            print(f"\n{'='*60}\nProcessing Input File: {f}\n{'='*60}\n")
            single_args = copy.copy(args)
            single_args.poscar = f
            try: workflow_func(single_args)
            except Exception as e:
                print(f"Error processing {f}: {e}")
                import traceback
                traceback.print_exc()
                continue
    else: workflow_func(args)

def main():
    from macer import __version__
    parser = argparse.ArgumentParser(
        description=MACER_LOGO + f"\nmacer_pydefect (v{__version__}): Automated Point Defect Calculations with MLFFs",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", "-v", action="version", version=f"macer_pydefect {__version__}")
    subparsers = parser.add_subparsers(dest="subcommand", help="Available commands")
    p_map = add_pydefect_parsers(subparsers)
    args = parser.parse_args()

    if not args.subcommand:
        parser.print_help()
        return

    # Manual checks
    if args.subcommand == "cpd" and not (args.formula or args.mpid or args.poscar):
        p_map["cpd"].print_help(); return
    if args.subcommand == "defect" and not (args.poscar and args.std_energies and args.target_vertices):
        p_map["defect"].print_help(); return
    if args.subcommand == "full" and not (args.formula or args.mpid or args.poscar):
        p_map["full"].print_help(); return

    if hasattr(args, "func"): args.func(args)
    else: parser.print_help(); sys.exit(1)

if __name__ == "__main__":
    main()
