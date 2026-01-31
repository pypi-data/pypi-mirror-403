import os
import sys
import torch
import numpy as np
import logging
from macer.training.mace_trainer import train_mace_model
from macer.training.data_prep import convert_to_mattersim_format

logger = logging.getLogger(__name__)

def run_mace_training(args):
    """
    Orchestrates the MACE training workflow.
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

    # 1. Setup Device & Dtype
    torch.set_default_dtype(torch.float64)

    # 2. Data Preparation
    # MACE accepts extended XYZ. We use the same helper for consistency across macer.
    data_path = args.data
    is_xyz = data_path.endswith(".xyz") or data_path.endswith(".extxyz")
    if (not is_xyz or "ML_AB" in data_path) and not data_path.endswith(".mattersim.xyz"):
            print("Preparing training data...")
            output_xyz = os.path.basename(data_path) + ".mattersim.xyz"
            convert_to_mattersim_format(data_path, output_xyz)
            data_path = output_xyz
    
    valid_path = args.valid_data
    if valid_path:
        is_val_xyz = valid_path.endswith(".xyz") or valid_path.endswith(".extxyz")
        if (not is_val_xyz or "ML_AB" in valid_path) and not valid_path.endswith(".mattersim.xyz"):
            print("Preparing validation data...")
            output_val_xyz = os.path.basename(valid_path) + ".mattersim.xyz"
            convert_to_mattersim_format(valid_path, output_val_xyz)
            valid_path = output_val_xyz

    # 3. Model Naming
    if args.model_name:
        model_name = args.model_name
    else:
        # Default name
        model_name = f"mace_{args.model_size}_finetuned.model"

    if not model_name.endswith(".model"):
         model_name += ".model"
         
    base_name, ext = os.path.splitext(model_name)
    counter = 1
    while os.path.exists(os.path.join(args.save_path, model_name)):
        model_name = f"{base_name}_{counter:03d}{ext}"
        counter += 1
    
    model_name_prefix = os.path.splitext(model_name)[0]

    # 4. Defaults
    lr = args.lr if args.lr is not None else 0.01
    energy_w = args.energy_weight if args.energy_weight is not None else 1.0
    forces_w = args.forces_weight if args.forces_weight is not None else 100.0
    stress_w = args.stress_weight if args.stress_weight is not None else 10.0

    # 5. Print Info
    print("-" * 60)
    print(f"MACE Training Info:")
    print(f"  - Data: {data_path}")
    print(f"  - Model Size: {args.model_size}")
    print(f"  - Epochs: {args.epochs}")
    print(f"  - LR: {lr}")
    print(f"  - Weights: E={energy_w}, F={forces_w}, S={stress_w}")
    if valid_path:
            print(f"  - Validation Data: {valid_path}")
    print(f"  - Output:")
    print(f"    Directory: {args.save_path}")
    print(f"    Filename Prefix: {model_name_prefix}")
    print("-" * 60)

    # 6. Execute Training
    try:
        train_mace_model(
            data_path=data_path,
            save_path=args.save_path,
            model_name=model_name_prefix,
            model_size=args.model_size,
            epochs=args.epochs,
            device=args.device,
            batch_size=args.batch_size,
            lr=lr,
            valid_path=valid_path,
            energy_weight=energy_w,
            forces_weight=forces_w,
            stress_weight=stress_w,
            keep_checkpoints=args.keep_checkpoints,
            restart=args.restart
        )
    except Exception as e:
        print(f"Training failed: {e}")
        sys.exit(1)
