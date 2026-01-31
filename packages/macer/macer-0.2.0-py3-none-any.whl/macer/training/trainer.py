import os
import subprocess
import mattersim
import logging
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

def train_mattersim(
    data_path: str,
    base_model_path: str,
    save_path: str,
    epochs: int = 100,
    device: str = "cpu",
    include_stresses: bool = True,
    batch_size: int = 16,
    lr: float = 2e-4,
    force_loss_ratio: float = 1.0,
    stress_loss_ratio: float = 0.1,
    patience: int = 10,
    valid_data_path: str = None,
    mae_energy_threshold: float = None,
    mae_force_threshold: float = None,
    mae_stress_threshold: float = None,
    model_name: str = None,
    ensemble_size: int = 1,
    seed: int = 42,
    reset_head: bool = False,
    head_lr: float = None,
    backbone_lr: float = None,
    dtype: str = "float64",
    energy_weight: float = 1.0,
    forces_weight: float = 100.0,
    stress_weight: float = 10.0,
):
    """
    Wraps the vendorized MatterSim fine-tuning script.
    """
    import macer.training.finetune
    script_path = macer.training.finetune.__file__
    
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Vendorized training script not found at {script_path}")

    os.makedirs(save_path, exist_ok=True)

    base_cmd = [
        "torchrun",
        "--nproc_per_node=1", 
        script_path,
        "--train_data_path", data_path,
        "--load_model_path", base_model_path,
        "--save_path", save_path,
        "--save_checkpoint",
        "--device", device,
        "--epochs", str(epochs),
        "--batch_size", str(batch_size),
        "--lr", str(lr),
        "--force_loss_ratio", str(forces_weight / energy_weight), # Handle ratio mapping
        "--stress_loss_ratio", str(stress_weight / energy_weight),
        "--early_stop_patience", str(patience),
        "--dtype", dtype
    ]
    
    if valid_data_path:
        base_cmd.extend(["--valid_data_path", valid_data_path])
    
    if include_stresses:
        base_cmd.append("--include_stresses")
    else:
        base_cmd.append("--no-include_stresses")

    if mae_energy_threshold is not None:
        base_cmd.extend(["--mae_energy_threshold", str(mae_energy_threshold)])
    if mae_force_threshold is not None:
        base_cmd.extend(["--mae_force_threshold", str(mae_force_threshold)])
    if mae_stress_threshold is not None:
        base_cmd.extend(["--mae_stress_threshold", str(mae_stress_threshold)])

    if reset_head:
        base_cmd.append("--reset_head")
    if head_lr is not None:
        base_cmd.extend(["--head_lr", str(head_lr)])
    if backbone_lr is not None:
        base_cmd.extend(["--backbone_lr", str(backbone_lr)])
        
    # Prepare environment for unbuffered output
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
        
    for i in range(ensemble_size):
        current_seed = seed + i
        cmd = base_cmd + ["--seed", str(current_seed)]
        
        logger.info(f"--- Ensemble {i+1}/{ensemble_size} (Seed={current_seed}) ---")
        
        # Setup logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(save_path, f"macer_finetune_{timestamp}.log")
        
        print(f"Logging to: {log_file}")
        
        with open(log_file, "w") as f:
            # Write setup info to log file header
            f.write("="*60 + "\n")
            f.write(f"MACER FINETUNE SESSION: {timestamp}\n")
            f.write(f"Data Path: {data_path}\n")
            f.write(f"Base Model: {base_model_path}\n")
            f.write(f"Command: {' '.join(cmd)}\n")
            f.write("="*60 + "\n\n")
            f.flush()

            # Use Popen to stream output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Merge stderr into stdout
                text=True,
                bufsize=1, # Line buffered
                env=env
            )
            
            # Tee output to stdout and log file
            for line in process.stdout:
                sys.stdout.write(line)
                f.write(line)
                f.flush() # Ensure it's written to disk
                
            process.wait()
            
            if process.returncode != 0:
                err_msg = f"Training failed with exit code {process.returncode}"
                logger.error(err_msg)
                f.write(f"\nERROR: {err_msg}\n")
                f.flush()
                raise subprocess.CalledProcessError(process.returncode, cmd)

        # Post-processing (rename model)
        default_output = os.path.join(save_path, "best_model.pth")
        if os.path.exists(default_output):
            if model_name:
                base_name, ext = os.path.splitext(model_name)
                final_name = f"{base_name}_{i}{ext}" if ensemble_size > 1 else model_name
                os.rename(default_output, os.path.join(save_path, final_name))
            elif ensemble_size > 1:
                os.rename(default_output, os.path.join(save_path, f"best_model_{i}.pth"))
