import argparse
import sys
import os
import datetime
import logging
import glob
from pathlib import Path

# Fix OpenMP runtime conflict on macOS (common with PyTorch/Anaconda)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# from macer import __version__
from macer.defaults import DEFAULT_DEVICE, resolve_model_path, DEFAULT_FF, DEFAULT_MODELS
from macer.calculator.factory import ALL_SUPPORTED_FFS

MACER_LOGO = r"""
███╗   ███╗  █████╗   ██████╗ ███████╗ ██████╗ 
████╗ ████║ ██╔══██╗ ██╔════╝ ██╔════╝ ██╔══██╗
██╔████╔██║ ███████║ ██║      █████╗   ██████╔╝
██║╚██╔╝██║ ██╔══██║ ██║      ██╔══╝   ██╔══██╗
██║ ╚═╝ ██║ ██║  ██║ ╚██████╗ ███████╗ ██║  ██║
╚═╝     ╚═╝ ╚═╝  ╚═╝  ╚═════╝ ╚══════╝ ╚═╝  ╚═╝
ML-accelerated Atomic Computational Environment for Research
"""

def _add_common_train_args(parser, default_lr=None, lr_help="Learning rate.", default_weights=(1.0, 1.0, 0.1)):
    """Add arguments common to both MatterSim and MACE training with grouping."""
    e_w, f_w, s_w = default_weights
    
    # 1. Data & Output Group
    io_group = parser.add_argument_group("Input & Output Options")
    io_group.add_argument("--data", "-d", type=str, help="Path to input data (VASP ML_AB, .xyz, etc.).")
    io_group.add_argument("--valid-data", type=str, default=None, help="Path to validation data (optional).")
    io_group.add_argument("--save-path", type=str, default="./mlff_results", help="Directory to save results (default: ./mlff_results).")
    io_group.add_argument("--model-name", type=str, default=None, help="Output filename for the trained model.")
    
    # 2. Training Loop Group
    loop_group = parser.add_argument_group("Training Loop Options")
    loop_group.add_argument("--epochs", type=int, default=100, help="Number of training epochs (default: 100).")
    loop_group.add_argument("--batch-size", type=int, default=16, help="Batch size (default: 16).")
    loop_group.add_argument("--lr", type=float, default=default_lr, help=lr_help)
    loop_group.add_argument("--patience", type=int, default=20, help="Early stopping patience (default: 20).")
    loop_group.add_argument("--seed", type=int, default=42, help="Random seed (default: 42).")
    
    # 3. Loss Weights Group
    loss_group = parser.add_argument_group("Loss Weights & Objective Options")
    loss_group.add_argument("--energy-weight", type=float, default=e_w, help=f"Loss weight for energy (default: {e_w}).")
    loss_group.add_argument("--forces-weight", type=float, default=f_w, help=f"Loss weight for forces (default: {f_w}).")
    loss_group.add_argument("--stress-weight", type=float, default=s_w, help=f"Loss weight for stress (default: {s_w}).")
    loss_group.add_argument("--no-stresses", action="store_true", help="Disable stress training.")
    
    # 4. Thresholds Group
    threshold_group = parser.add_argument_group("Stop Thresholds (MAE based early-exit)")
    threshold_group.add_argument("--mae-energy", type=float, default=None, 
                                 help="Stop if MAE Energy (eV/atom) < threshold. Default: Disabled.")
    threshold_group.add_argument("--mae-force", type=float, default=None, 
                                 help="Stop if MAE Force (eV/A) < threshold. Default: Disabled.")
    threshold_group.add_argument("--mae-stress", type=float, default=None, 
                                 help="Stop if MAE Stress (eV/A^3) < threshold. Default: Disabled.")

    # 5. Computing Group
    compute_group = parser.add_argument_group("Optimization & Device Options")
    compute_group.add_argument("--device", type=str, default=DEFAULT_DEVICE, choices=["cpu", "cuda", "mps"], help=f"Device (default: {DEFAULT_DEVICE}).")
    compute_group.add_argument("--dtype", type=str, default=None, choices=["float32", "float64"], help="Data type.")

    return {
        "io": io_group,
        "loop": loop_group,
        "loss": loss_group,
        "threshold": threshold_group,
        "compute": compute_group
    }

def print_util_banner(category, action=None, ff=None, model=None):
    from macer import __version__
    """Prints a consistent banner for util commands."""
    print(MACER_LOGO)
    print(f"  Version: {__version__}")
    
    cmd_str = f"util {category}"
    if action: cmd_str += f" {action}"
    print(f"  Command: {cmd_str}")
    
    if ff:
        model_display = model if model else DEFAULT_MODELS.get(ff, "Default")
        print(f"  Model  : {ff.upper()} ({model_display})")
        
    print(f"  Web    : https://github.com/soungmin-bae/macer")
    print("-" * 50 + "\n")

def add_util_parsers(subparsers):
    """Adds all util subcommands to the provided subparsers object."""
    from macer import __version__
    
    # --- 1. Fine-tunning (MatterSim) ---
    ft_parser = subparsers.add_parser(
        "fine-tunning",
        aliases=["ft"],
        help="Fine-tune MatterSim models",
        description=MACER_LOGO + f"\nmacer util ft (v{__version__}): Specialized workflow for fine-tunning MatterSim foundation models.\nRefines pre-trained models using DFT data and performs automatic evaluation.",
        epilog="""
Examples:
  1. Standard fine-tuning with auto-splitting (8:1:1) and auto-evaluation:
     macer util ft -d dataset.xyz --epochs 100

  2. Use 100%% of data for training (no test set) with a specific base model:
     macer util ft -d dataset.xyz --full-train --model ./base_model.pth

  3. Custom validation data and differential learning rates (Head vs Backbone):
     macer util ft -d train.xyz --valid-data valid.xyz --head-lr 1e-3 --backbone-lr 1e-5

  4. Fast verification run on CPU with a custom output model name:
     macer util ft -d dataset.xyz --epochs 2 --model-name my_model.pth --device cpu

  5. Fine-tuning when stress data is missing (e.g., ISIF=0 or OUTCAR-based XYZ):
     macer util ft -d dataset.xyz --epochs 10 --no-stresses

MatterSim Fine-tunning Strategy:
  - Higher Head LR (e.g., 1e-3) and lower Backbone LR (e.g., 1e-5) is recommended for small datasets.
  - Use --reset-head to re-initialize the predictive head if the chemical space is very different.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ft_groups = _add_common_train_args(
        ft_parser, 
        default_lr=2e-4, 
        lr_help="Learning rate (default: 2e-4).",
        default_weights=(1.0, 1.0, 0.1)
    )
    ft_groups["io"].add_argument("--model", type=str, default="mattersim-v1.0.0-1M.pth", help="Base model to fine-tune (e.g., mattersim-v1.0.0-1M.pth).")
    ft_groups["io"].add_argument("--test-data", type=str, default=None, help="Optional test set for automatic evaluation after training.")
    ft_groups["io"].add_argument("--ratio", type=float, nargs=3, default=[0.8, 0.1, 0.1], help="Train/Valid/Test ratios for auto-splitting (default: 0.8 0.1 0.1).")
    ft_groups["io"].add_argument("--full-train", action="store_true", help="Use 100%% of data for training (no splitting, no validation, no test).")
    
    ms_train_group = ft_parser.add_argument_group("MatterSim Fine-tunning Strategy")
    ms_train_group.add_argument("--ensemble", type=int, default=1, help="Number of ensemble models.")
    ms_train_group.add_argument("--reset-head", action="store_true", help="Reset predictive head weights.")
    ms_train_group.add_argument("--head-lr", type=float, default=None, help="LR for head.")
    ms_train_group.add_argument("--backbone-lr", type=float, default=None, help="LR for backbone.")

    # --- 2. Evaluate (General Accuracy Assessment) ---
    eval_parser = subparsers.add_parser(
        "evaluate",
        aliases=["eval"],
        help="Evaluate any MLFF model on a dataset",
        description=MACER_LOGO + f"\nmacer util evaluate (v{__version__}): General accuracy assessment for MLFF models.\nCalculates MAE, Pearson Correlation (r²) and generates parity plots.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    eval_parser.add_argument("--data", "-d", help="Path to input XYZ data for evaluation.")
    eval_parser.add_argument("--ff", default=DEFAULT_FF, help=f"Force field to evaluate (default: {DEFAULT_FF}).")
    eval_parser.add_argument("--model", help="Path to model file (default: resolved via macer settings).")
    eval_parser.add_argument("--device", default=DEFAULT_DEVICE, choices=["cpu", "cuda", "mps"], help=f"Device (default: {DEFAULT_DEVICE}).")
    eval_parser.add_argument("--dtype", choices=["float32", "float64"], help="Dtype for evaluation.")

    # --- 3. Train-MACE (MACE) ---
    tm_parser = subparsers.add_parser(
        "train-mace",
        aliases=["tm"],
        help="Train MACE models",
        description=MACER_LOGO + f"\nmacer util tm (v{__version__}): Train lightweight MACE models (e.g. OMAT-Small) from scratch or checkpoints.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    tm_groups = _add_common_train_args(
        tm_parser, 
        default_lr=0.01, 
        lr_help="Learning rate (default: 0.01).",
        default_weights=(1.0, 100.0, 10.0)
    )
    mace_group = tm_parser.add_argument_group("MACE Training Specifics")
    mace_group.add_argument("--model-size", type=str, default="medium", choices=["small", "medium", "large"], help="Model size.")
    mace_group.add_argument("--keep-checkpoints", action="store_true", help="Keep all intermediate checkpoints.")
    mace_group.add_argument("--restart", action="store_true", help="Restart training from the latest checkpoint.")


    # --- 4. Dataset Category ---
    dataset_parser = subparsers.add_parser(
        "dataset", 
        aliases=["ds"],
        help="Dataset management utilities (build, split)",
        description=MACER_LOGO + f"\nmacer util ds (v{__version__}): Dataset management utilities.\nSupports merging VASP outputs and splitting into Train/Valid/Test sets.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    dataset_subparsers = dataset_parser.add_subparsers(dest="action", help="Dataset actions")

    # dataset build
    build_parser = dataset_subparsers.add_parser(
        "build", 
        help="Convert/Merge VASP outputs to dataset.xyz",
        description=MACER_LOGO + "\nConvert and Merge VASP outputs (ML_AB, xml, h5) to a single Extended XYZ file.\nBroken or truncated files will be automatically skipped.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    build_parser.add_argument("-i", "--input", nargs="*", dest="inputs", help="Input files or patterns (e.g., vasprun-*.xml). Supports globs.")
    build_parser.add_argument("-o", "--output", default="dataset.xyz", help="Output XYZ filename (default: dataset.xyz).")
    build_parser.add_argument("--stress-unit", default="eV/A^3", help="Stress unit conversion.")

    # dataset split
    split_parser = dataset_subparsers.add_parser(
        "split", 
        help="Split XYZ dataset into train/valid/test",
        description=MACER_LOGO + "\nRandomly shuffle and split an Extended XYZ dataset into training, validation, and test sets.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    split_parser.add_argument("-i", "--input", help="Input XYZ file (default: dataset.xyz).")
    split_parser.add_argument("--ratio", type=float, nargs=3, default=[0.8, 0.1, 0.1], help="Train/Valid/Test ratios (default: 0.8 0.1 0.1).")
    split_parser.add_argument("--seed", type=int, default=42, help="Random seed for shuffling (default: 42).")
    split_parser.add_argument("--train-out", default="train.xyz", help="Output filename for training set (default: train.xyz).")
    split_parser.add_argument("--valid-out", default="valid.xyz", help="Output filename for validation set (default: valid.xyz).")
    split_parser.add_argument("--test-out", default="test.xyz", help="Output filename for test set (default: test.xyz).")

    # --- 5. Active Learning Category ---
    active_parser = subparsers.add_parser(
        "active", 
        help="Active learning utilities (query uncertain structures)",
        description=MACER_LOGO + "\nmacer util active: Active learning utilities.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    active_subparsers = active_parser.add_subparsers(dest="action", help="Active learning actions")

    # active query
    query_parser = active_subparsers.add_parser("query", help="Query uncertain structures from trajectory")
    query_parser.add_argument("--traj", required=True, help="Path to MD trajectory (md.traj, XDATCAR, etc.)")
    query_parser.add_argument("--models", required=True, nargs='+', help="List of ensemble model paths (.pth)")
    query_parser.add_argument("--top-k", type=int, default=10, help="Number of structures to select (default: 10)")
    query_parser.add_argument("--threshold", type=float, default=0.05, help="Minimum force uncertainty (eV/A) to consider (default: 0.05)")
    query_parser.add_argument("--output-dir", default="active_selection", help="Output directory for selected POSCARs")
    query_parser.add_argument("--device", default="cpu", help="Device to use (cpu/cuda)")
    query_parser.add_argument("--interval", type=int, default=1, help="Trajectory sampling interval")

    # --- 6. MD Category ---
    md_parser = subparsers.add_parser(
        "md", 
        help="MD post-processing utilities (traj2xdatcar, conductivity, rdf, etc.)",
        description=MACER_LOGO + "\nmacer util md: Molecular Dynamics post-processing and analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    md_subparsers = md_parser.add_subparsers(dest="action", help="MD actions")

    # md traj2xdatcar
    t2x_parser = md_subparsers.add_parser("traj2xdatcar", help="Convert md.traj to VASP XDATCAR")
    t2x_parser.add_argument("-i", "--input", required=True, help="Input .traj file")
    t2x_parser.add_argument("-o", "--output", default="XDATCAR", help="Output XDATCAR file (default: XDATCAR)")
    t2x_parser.add_argument("--interval", type=int, default=1, help="Sampling interval used during MD (e.g. 100).")

    # md summary
    summary_parser = md_subparsers.add_parser("summary", help="Print statistical summary of md.csv")
    summary_parser.add_argument("-i", "--input", default="md.csv", help="Input md.csv file (default: md.csv)")

    # md conductivity
    cond_parser = md_subparsers.add_parser("conductivity", help="Calculate ionic conductivity")
    cond_parser.add_argument("-i", "--input", required=True, help="Input trajectory (md.traj or XDATCAR)")
    cond_parser.add_argument("-t", "--temp", type=float, required=True, help="Temperature (K)")
    cond_parser.add_argument("--dt", type=float, default=2.0, help="Timestep (fs)")
    cond_parser.add_argument("--interval", type=int, default=1, help="Sampling interval used during MD (e.g. 50).")
    cond_parser.add_argument("--charges", help="Oxidation states (e.g. \"Li:1,S:-2\")")

    # md cell (new)
    cell_parser = md_subparsers.add_parser("cell", help="Analyze cell evolution (a, b, c, Vol)")
    cell_parser.add_argument("-i", "--input", required=True, help="Input trajectory (md.traj or XDATCAR)")
    cell_parser.add_argument("--dt", type=float, default=2.0, help="Timestep (fs)")
    cell_parser.add_argument("--skip", type=float, default=0.0, help="Initial time to skip for averaging (ps)")
    cell_parser.add_argument("--interval", type=int, default=1, help="Sampling interval used during MD (default: 1)")
    cell_parser.add_argument("-o", "--output", default="cell_evolution", help="Output prefix")
    cell_parser.add_argument("--poscar", default="POSCAR-cell-averaged", help="Output filename for averaged structure")

    # md plot
    pmd_parser = md_subparsers.add_parser("plot", help="Plot MD trajectory data (T, E, P)")
    pmd_parser.add_argument("-i", "--input", default="md.csv", help="Input md.csv")
    pmd_parser.add_argument("-o", "--output", default="md_plot", help="Output PDF prefix")

    # md rdf
    rdf_parser = md_subparsers.add_parser("rdf", help="Plot Radial Distribution Function (RDF)")
    rdf_parser.add_argument("-i", "--input", required=True, help="Input trajectory (md.traj or XDATCAR)")
    rdf_parser.add_argument("-o", "--output", default="rdf_plot", help="Output PDF prefix")
    rdf_parser.add_argument("--rmax", type=float, default=10.0, help="Maximum radius (Å)")
    rdf_parser.add_argument("--bins", type=int, default=200, help="Number of bins")

    # --- 7. Model Category ---
    model_parser = subparsers.add_parser(
        "model", 
        help="Model management utilities (fp32, list, compile)",
        description=MACER_LOGO + "\nmacer util model: MLFF model management.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    model_subparsers = model_parser.add_subparsers(dest="action", help="Model actions")

    # model fp32
    fp32_parser = model_subparsers.add_parser("fp32", help="Convert model to float32 precision")
    fp32_parser.add_argument("-i", "--input", required=True, help="Input model file (.pth or .model)")
    fp32_parser.add_argument("-o", "--output", help="Output model file (optional)")

    # model list
    model_subparsers.add_parser("list", help="List available models in mlff-model/")

    # model compile (new)
    compile_parser = model_subparsers.add_parser("compile", help="Compile a MACE checkpoint (.pt) into a full model (.model)")
    compile_parser.add_argument("-i", "--input", required=True, help="Input checkpoint file (.pt)")
    compile_parser.add_argument("-o", "--output", help="Output model file (.model)")
    compile_parser.add_argument("-s", "--size", default="small", choices=["small", "medium", "large"], help="Model size used during training (default: small)")

    # --- 8. Struct Category ---
    struct_parser = subparsers.add_parser(
        "struct", 
        help="Structure file utilities (vasp4to5)",
        description=MACER_LOGO + "\nmacer util struct: Atomic structure file utilities.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    struct_subparsers = struct_parser.add_subparsers(dest="action", help="Structure actions")

    # struct vasp4to5
    v4to5_parser = struct_subparsers.add_parser("vasp4to5", help="Convert VASP4 POSCAR to VASP5 (add symbols)")
    v4to5_parser.add_argument("-i", "--input", required=True, help="Input VASP4 POSCAR file")
    v4to5_parser.add_argument("-s", "--symbols", help="Element symbols (e.g. \"Li S\"). If omitted, guesses from 1st line.")
    v4to5_parser.add_argument("-o", "--output", help="Output VASP5 POSCAR file (optional)")

    # --- 9. Phonopy Category ---
    phonopy_parser = subparsers.add_parser(
        "phonopy", 
        help="Phonon and Grüneisen post-processing (band, gruneisen plots)",
        description=MACER_LOGO + "\nmacer util phonopy: Phonon analysis and visualization.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    phonopy_subparsers = phonopy_parser.add_subparsers(dest="action", help="Phonopy actions")

    # phonon band
    pband_parser = phonopy_subparsers.add_parser("band", help="Plot phonon dispersion from .dat")
    pband_parser.add_argument("-i", "--input", default="band.dat", help="Input .dat file (default: band.dat)")
    pband_parser.add_argument("-o", "--output", default="phonon_band.pdf", help="Output PDF file (default: phonon_band.pdf)")
    pband_parser.add_argument("-y", "--yaml", help="Optional .yaml file for labels (e.g. band.yaml)")
    pband_parser.add_argument("--fmin", type=float, help="Min frequency (THz)")
    pband_parser.add_argument("--fmax", type=float, help="Max frequency (THz)")
    pband_parser.add_argument("--labels", help="High-symmetry labels (e.g. \"G M K G\")")

    # phonon gruneisen
    pgru_parser = phonopy_subparsers.add_parser("gruneisen", help="Plot Grüneisen parameters from .dat")
    pgru_parser.add_argument("-i", "--input", default="gruneisen.dat", help="Input .dat file (default: gruneisen.dat)")
    pgru_parser.add_argument("-o", "--output", default="gruneisen", help="Output PDF prefix (default: gruneisen)")
    pgru_parser.add_argument("-y", "--yaml", help="Optional .yaml file for labels (e.g. band.yaml)")
    pgru_parser.add_argument("--fmin", type=float, help="Min frequency (THz)")
    pgru_parser.add_argument("--fmax", type=float, help="Max frequency (THz)")
    pgru_parser.add_argument("--gmin", type=float, help="Min Grüneisen parameter")
    pgru_parser.add_argument("--gmax", type=float, help="Max Grüneisen parameter")
    pgru_parser.add_argument("--filter", type=float, default=3.0, help="Outlier filter factor (default: 3.0)")
    pgru_parser.add_argument("--labels", help="High-symmetry labels (e.g. \"G M K G\")")

    # --- 10. Model Download/Provisioning Category ---
    gm_parser = subparsers.add_parser(
        "get-model", 
        aliases=["gm"],
        help="Download and manage MLFF models",
        description=MACER_LOGO + f"\nmacer util gm (v{__version__}): Download and manage pre-trained MLFF models.\nSupports automatic provisioning for SevenNet, MACE, and MatterSim.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    gm_parser.add_argument("--ff", choices=ALL_SUPPORTED_FFS, help="Filter models by force field.")
    gm_parser.add_argument("--model", help="Specific model name to download (or 'all').")
    gm_parser.add_argument("--replace", action="store_true", help="Force re-download existing models.")

    # --- 11. DynaPhoPy Category ---
    dp_parser = subparsers.add_parser(
        "dynaphopy",
        help="Internal DynaPhoPy engine (NumPy 2.x compatible)",
        add_help=False
    )

    return {
        "ft": ft_parser,
        "eval": eval_parser,
        "tm": tm_parser,
        "dataset": dataset_parser,
        "dataset_build": build_parser,
        "dataset_split": split_parser,
        "active": active_parser,
        "md": md_parser,
        "model": model_parser,
        "struct": struct_parser,
        "phonopy": phonopy_parser,
        "gm": gm_parser,
        "dynaphopy": dp_parser
    }

def execute_util(args, unknown_args=None):
    """Execution logic for util commands."""
    dummy_parser = argparse.ArgumentParser(add_help=False)
    subparsers = dummy_parser.add_subparsers(dest="category")
    p_map = add_util_parsers(subparsers)

    if not args.category:
        print(MACER_LOGO)
        print(f"  macer util (v{__version__})")
        print(f"  Utility tools for post-processing and analysis.")
        print("-" * 50 + "\n")
        return

    # --- Execute DynaPhoPy (Special Case) ---
    elif args.category in ["get-model", "gm"]:
        from macer.utils import model_manager
        from macer.defaults import AVAILABLE_MODELS
        
        if args.model:
            # Download mode
            if args.model == "all":
                # Use the new interactive batch downloader
                model_manager.download_all_models(ff_filter=args.ff, force=args.replace)
            else:
                # Specific model
                # Find which FF owns this model
                found_ff = args.ff
                if not found_ff:
                    for ff, models in AVAILABLE_MODELS.items():
                        if args.model in models:
                            found_ff = ff
                            break
                if not found_ff:
                    print(f"Error: Model '{args.model}' not recognized or --ff not specified.")
                    return
                model_manager.download_model(found_ff, args.model, force=args.replace)
        else:
            # List mode
            print_util_banner("gm")
            model_manager.list_models_status(ff_filter=args.ff)

    elif args.category == "dynaphopy":
        from macer.cli.util import run_dynaphopy_full_wrapper
        # Use passed unknown_args if available, otherwise empty list
        run_dynaphopy_full_wrapper(args, unknown_args if unknown_args else [])
        return

    # --- Execute Fine-tunning (MatterSim) ---
    if args.category in ["fine-tunning", "ft"]:
        if not args.data:
            p_map["ft"].print_help()
            return
        print_util_banner("ft", ff="mattersim", model=args.model)
        from macer.utils.finetuning_mattersim import run_mattersim_finetuning
        run_mattersim_finetuning(args)

    # --- Execute General Evaluation ---
    elif args.category in ["evaluate", "eval"]:
        if not args.data:
            p_map["eval"].print_help()
            return
        print_util_banner("evaluate", ff=args.ff, model=args.model)
        from macer.utils.evaluation import evaluate_model
        metrics_str = evaluate_model(
            data_path=args.data,
            ff=args.ff,
            model_path=args.model,
            device=args.device,
            output_dir="."
        )
        if metrics_str:
            print(metrics_str)

    # --- Execute Train-MACE (MACE) ---
    elif args.category in ["train-mace", "tm"]:
        if not args.data:
            p_map["tm"].print_help()
            return
        print_util_banner("tm", ff="mace")
        from macer.utils.training_mace import run_mace_training
        run_mace_training(args)

    # --- Execute Dataset Actions ---
    elif args.category in ["dataset", "ds"]:
        if not args.action:
            p_map["dataset"].print_help()
            return
        
        # Check specific dataset actions
        if args.action == "build" and not args.inputs:
            p_map["dataset_build"].print_help()
            return
        elif args.action == "split":
            # Force help if no arguments provided at all (user just typed 'split')
            # Check if flags are in sys.argv to allow using defaults via explicit flags if desired
            if not any(arg in sys.argv for arg in ["-i", "--input", "--ratio", "--seed"]):
                p_map["dataset_split"].print_help()
                return
            
            # Use default input if not specified
            if not args.input:
                args.input = "dataset.xyz"

        print_util_banner("dataset", action=args.action)
        from macer.utils.dataset_tools import build_dataset, split_dataset
        if args.action == "build":
            build_dataset(args.inputs, args.output, args.stress_unit)
        elif args.action == "split":
            split_dataset(
                args.input, 
                args.ratio[0], args.ratio[1], args.ratio[2], 
                args.seed,
                train_out=args.train_out,
                valid_out=args.valid_out,
                test_out=args.test_out
            )

    elif args.category == "active":
        if args.action == "query":
            from macer.active_learning.query import query_uncertain_structures
            query_uncertain_structures(
                traj_path=args.traj,
                model_paths=args.models,
                top_k=args.top_k,
                threshold=args.threshold,
                output_dir=args.output_dir,
                device=args.device,
                step_interval=args.interval
            )
        else:
            p_map["active"].print_help()

    elif args.category == "md":
        from macer.utils.md_tools import traj2xdatcar, md_summary, calculate_conductivity, analyze_cell_evolution
        from macer.utils.viz_tools import plot_md_log, plot_rdf
        if args.action == "traj2xdatcar":
            traj2xdatcar(args.input, args.output, interval=args.interval)
        elif args.action == "summary":
            md_summary(args.input)
        elif args.action == "conductivity":
            calculate_conductivity(args.input, args.temp, args.dt, interval=args.interval, charges_str=args.charges)
        elif args.action == "cell":
            analyze_cell_evolution(args.input, args.dt, args.skip, args.interval, args.output, args.poscar)
        elif args.action == "plot":
            plot_md_log(args.input, args.output)
        elif args.action == "rdf":
            plot_rdf(args.input, args.output, r_max=args.rmax, n_bins=args.bins)
        else:
            p_map["md"].print_help()

    elif args.category == "model":
        from macer.utils.model_tools import convert_model_precision, list_models, compile_mace_model
        if args.action == "fp32":
            convert_model_precision(args.input, args.output)
        elif args.action == "list":
            list_models()
        elif args.action == "compile":
            compile_mace_model(args.input, args.output, model_size=args.size)
        else:
            p_map["model"].print_help()

    elif args.category == "struct":
        from macer.utils.struct_tools import vasp4to5
        if args.action == "vasp4to5":
            vasp4to5(args.input, args.symbols, args.output)
        else:
            p_map["struct"].print_help()

    elif args.category == "phonopy":
        from macer.utils.viz_tools import plot_phonon_band, plot_gruneisen_band
        if args.action == "band":
            plot_phonon_band(args.input, out_pdf=args.output, fmin=args.fmin, fmax=args.fmax, 
                             labels=args.labels, yaml_path=args.yaml)
        elif args.action == "gruneisen":
            # Auto-discovery logic
            default_input = "gruneisen.dat"
            
            # Case 1: User didn't specify input (args.input is default) AND default file doesn't exist
            if args.input == default_input and not os.path.exists(default_input):
                pattern = "gruneisen-*.dat"
                found_files = sorted(glob.glob(pattern))
                
                if found_files:
                    print(f"Default '{default_input}' not found. Auto-detected {len(found_files)} files matching '{pattern}':")
                    for f in found_files:
                        # Construct output prefix: gruneisen-VO2.dat -> gruneisen-VO2
                        base_name = os.path.splitext(f)[0]
                        # If user specified output, append suffix? Or just use base_name?
                        # User said: "output 을 -* (prefix) 이름 붙여서 생성"
                        # If args.output is default "gruneisen", we use base_name.
                        # If args.output is custom "my_plot", we might want "my_plot-VO2".
                        if args.output == "gruneisen":
                            current_output = base_name
                        else:
                            # Extract suffix from input filename: gruneisen-VO2.dat -> -VO2
                            suffix = base_name.replace("gruneisen", "")
                            current_output = args.output + suffix
                        
                        print(f"  Processing {f} -> Output prefix: {current_output}")
                        try:
                            plot_gruneisen_band(f, out_prefix=current_output, fmin=args.fmin, fmax=args.fmax, 
                                                gmin=args.gmin, gmax=args.gmax, filter_outliers=args.filter, 
                                                labels=args.labels, yaml_path=args.yaml)
                        except Exception as e:
                            print(f"    Error processing {f}: {e}")
                else:
                    # No files found, print help
                    print(f"Error: Default input '{default_input}' not found and no files matching '{pattern}' detected.")
                    p_map["phonopy"].print_help()
            
            # Case 2: Specific input provided OR default file exists
            else:
                plot_gruneisen_band(args.input, out_prefix=args.output, fmin=args.fmin, fmax=args.fmax, 
                                    gmin=args.gmin, gmax=args.gmax, filter_outliers=args.filter, 
                                    labels=args.labels, yaml_path=args.yaml)
        else:
            p_map["phonopy"].print_help()

def main():
    from macer import __version__
    parser = argparse.ArgumentParser(
        description=MACER_LOGO + f"\nmacer_util (v{__version__}): Utility suite for post-processing and model management.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", "-v", action="version", version=f"macer_util {__version__}")

    subparsers = parser.add_subparsers(dest="category", help="Utility categories")
    add_util_parsers(subparsers)

    args, unknown_args = parser.parse_known_args()
    
    if not args.category:
        # Re-parse with main parser logic
        parser.print_help()
        return

    execute_util(args, unknown_args)

if __name__ == "__main__":
    main()