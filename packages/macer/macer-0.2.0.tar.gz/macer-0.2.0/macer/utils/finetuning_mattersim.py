import os
import sys
import datetime
import torch
import numpy as np
import logging
import glob
from macer.training.data_prep import convert_to_mattersim_format
from macer.training.trainer import train_mattersim
from macer.defaults import resolve_model_path
from macer.utils.evaluation import evaluate_model

logger = logging.getLogger(__name__)

def run_mattersim_finetuning(args):
    """
    Orchestrates the MatterSim fine-tunning workflow.
    """
    # 1. Setup Device & Dtype
    if args.device == "mps" and args.dtype == "float64":
        print("WARNING: MPS device (Apple Silicon GPU) does not support float64. Forcing --dtype float32.")
        args.dtype = "float32"
    
    if args.dtype is None:
        args.dtype = "float32"
        
    if args.dtype == "float32":
        torch.set_default_dtype(torch.float32)
        print("INFO: Set default dtype to torch.float32")
    else:
        torch.set_default_dtype(torch.float64)

    # Simplified: Always start training
    do_train(args)

def do_train(args):
    """
    Handles the training/fine-tuning action.
    """
    # 0. Resolve unique save path
    save_path = args.save_path
    if os.path.exists(save_path):
        base_save = save_path.rstrip('/')
        counter = 1
        while os.path.exists(f"{base_save}-NEW{counter:03d}"):
            counter += 1
        save_path = f"{base_save}-NEW{counter:03d}"
        print(f"INFO: Destination {args.save_path} exists. Using unique path: {save_path}")
    args.save_path = save_path

    # 1. Data Preparation & Auto-splitting
    data_path = args.data
    valid_path = args.valid_data
    test_path = args.test_data 
    
    temp_files = []
    
    if getattr(args, 'full_train', False):
        print("INFO: --full-train enabled. Using 100% of data for training, 10% subset for validation monitor.")
        from ase.io import read, write
        import random
        
        # Ensure we have an ASE-readable file (convert if needed)
        is_xyz = data_path.endswith(".xyz") or data_path.endswith(".extxyz")
        if (not is_xyz or "ML_AB" in data_path) and not data_path.endswith(".mattersim.xyz"):
             print("Converting input to temporary XYZ for full-train preparation...")
             tmp_all = data_path + ".tmp_all.xyz"
             convert_to_mattersim_format(data_path, tmp_all)
             data_path = tmp_all
             temp_files.append(tmp_all)

        # Load all atoms to create overlapping sets
        all_atoms = read(data_path, index=':')
        random.seed(args.seed)
        random.shuffle(all_atoms)
        
        # 100% for training
        train_full = "train_full.xyz"
        write(train_full, all_atoms)
        data_path = train_full
        
        # 10% for validation (overlap with train)
        val_full = "valid_monitor.xyz"
        n_val = max(1, int(len(all_atoms) * 0.1))
        write(val_full, all_atoms[:n_val])
        valid_path = val_full
        
        test_path = None # No standalone test in full-train mode
        temp_files.extend([train_full, val_full])

    # Unified Mode Logic: Split if only a single data file is provided
    elif valid_path is None:
        r = args.ratio
        print(f"INFO: No validation data provided. Auto-splitting learning data (Ratio {r[0]}:{r[1]}:{r[2]})...")
        from macer.utils.dataset_tools import split_dataset
        
        is_xyz = data_path.endswith(".xyz") or data_path.endswith(".extxyz")
        if (not is_xyz or "ML_AB" in data_path) and not data_path.endswith(".mattersim.xyz"):
             print("Converting input to temporary XYZ for splitting...")
             tmp_all = data_path + ".tmp_all.xyz"
             convert_to_mattersim_format(data_path, tmp_all)
             data_path = tmp_all
             temp_files.append(tmp_all)

        if split_dataset(data_path, train_ratio=r[0], valid_ratio=r[1], test_ratio=r[2], seed=args.seed):
            data_path = "train.xyz"
            valid_path = "valid.xyz"
            test_path = "test.xyz"
            
            # Check for empty sets (e.g. ratio 0 or very small dataset)
            if os.path.exists(valid_path) and os.path.getsize(valid_path) == 0:
                valid_path = None
            if os.path.exists(test_path) and os.path.getsize(test_path) == 0:
                test_path = None
                
            temp_files.extend([f for f in ["train.xyz", "valid.xyz", "test.xyz"] if f])
        else:
            print("Error: Auto-splitting failed.")
            sys.exit(1)

    if data_path not in temp_files:
        is_xyz = data_path.endswith(".xyz") or data_path.endswith(".extxyz")
        if (not is_xyz or "ML_AB" in data_path) and not data_path.endswith(".mattersim.xyz"):
                print("Preparing training data...")
                output_xyz = os.path.basename(data_path) + ".mattersim.xyz"
                convert_to_mattersim_format(data_path, output_xyz)
                data_path = output_xyz

    if valid_path and valid_path not in temp_files:
        is_val_xyz = valid_path.endswith(".xyz") or valid_path.endswith(".extxyz")
        if (not is_val_xyz or "ML_AB" in valid_path) and not valid_path.endswith(".mattersim.xyz"):
            print("Preparing validation data...")
            output_val_xyz = os.path.basename(valid_path) + ".mattersim.xyz"
            convert_to_mattersim_format(valid_path, output_val_xyz)
            valid_path = output_val_xyz

    # 2. Output Model Naming
    if args.model_name:
        model_name = args.model_name
        if not model_name.endswith(".pth"):
            model_name += ".pth"
    else:
        model_name = "mattersim_finetuned.pth"

    # 3. Resolve Input (Base) Model
    try:
        input_model = resolve_model_path(args.model)
    except Exception:
        input_model = args.model
        if not os.path.exists(input_model):
            print(f"Error: Base model not found: {input_model}")
            sys.exit(1)

    # 4. Defaults
    lr = args.lr if args.lr is not None else 2e-4
    energy_w = args.energy_weight if args.energy_weight is not None else 1.0
    forces_w = args.forces_weight if args.forces_weight is not None else 1.0
    stress_w = args.stress_weight if args.stress_weight is not None else 0.1

    # 5. Print Info
    print("-" * 60)
    print(f"Fine-tunning Info:")
    print(f"  - Engine: MATTERSIM")
    print(f"  - Train Data: {data_path}")
    print(f"  - Valid Data: {valid_path}")
    if test_path:
        print(f"  - Test Data : {test_path} (to be evaluated after training)")
    print(f"  - Base Model: {input_model}")
    print(f"  - LR: {lr}")
    print(f"  - Weights: E={energy_w}, F={forces_w}, S={stress_w}")
    print(f"  - Output:")
    print(f"    Directory: {args.save_path}")
    print(f"    Filename : {model_name}")
    print("-" * 60)

    # 6. Execute Training
    try:
        train_mattersim(
            data_path=data_path,
            base_model_path=input_model,
            save_path=args.save_path,
            epochs=args.epochs,
            device=args.device,
            batch_size=args.batch_size,
            lr=lr,
            include_stresses=not args.no_stresses,
            patience=args.patience,
            valid_data_path=valid_path,
            mae_energy_threshold=args.mae_energy,
            mae_force_threshold=args.mae_force,
            mae_stress_threshold=args.mae_stress,
            model_name=model_name,
            ensemble_size=args.ensemble,
            seed=args.seed,
            reset_head=args.reset_head,
            head_lr=args.head_lr,
            backbone_lr=args.backbone_lr,
            dtype=args.dtype,
            energy_weight=energy_w,
            forces_weight=forces_w,
            stress_weight=stress_w
        )
    except Exception as e:
        print(f"Training failed: {e}")
        sys.exit(1)

    # 7. Post-training Evaluation
    if test_path and os.path.exists(test_path) and os.path.getsize(test_path) > 0:
        print("\n" + "="*60)
        print(" TRAINING COMPLETE. STARTING FINAL EVALUATION...")
        print("="*60)
        
        final_model_path = os.path.join(args.save_path, model_name)
        eval_metrics = evaluate_model(
            data_path=test_path,
            ff="mattersim",
            model_path=final_model_path,
            device=args.device,
            output_dir=args.save_path
        )
        if eval_metrics:
            print(eval_metrics)
        
        log_files = glob.glob(os.path.join(args.save_path, "macer_finetune_*.log"))
        if log_files:
            latest_log = max(log_files, key=os.path.getctime)
            with open(latest_log, "a") as lf:
                lf.write("\n" + "="*40 + "\n")
                lf.write(" FINAL TEST EVALUATION RESULTS\n")
                lf.write("-"*40 + "\n")
                lf.write(f"Test Data: {test_path}\n")
                lf.write(eval_metrics + "\n" if eval_metrics else "Evaluation failed.\n")
                lf.write("-"*40 + "\n")
