import os
import torch
import logging
import sys
import subprocess
from macer.defaults import DEFAULT_DEVICE

# Setup logger
logger = logging.getLogger("macer.training.mace")

def train_mace_model(
    data_path: str,
    save_path: str,
    model_name: str = "mace_model",
    model_size: str = "medium",
    epochs: int = 100,
    device: str = "cpu",
    batch_size: int = 10,
    lr: float = 0.01,
    seed: int = 123,
    valid_data_path: str = None,
    valid_fraction: float = 0.1,
    patience: int = 20,
    energy_weight: float = 1.0,
    forces_weight: float = 100.0,
    stress_weight: float = 10.0,
    compute_stress: bool = False,
    max_L: int = 1,
    r_max: float = 5.0,
    dtype: str = "float64",
    keep_checkpoints: bool = False,
    restart: bool = False,
):
    """
    Train a MACE model using the bundled MACE library.
    
    Args:
        data_path: Path to the training data (XYZ).
        save_path: Directory to save results.
        model_name: Name of the output model file (without extension).
        model_size: 'small', 'medium', or 'large'. Controls hidden channels.
        epochs: Number of training epochs.
        device: 'cpu', 'cuda', or 'mps'.
        batch_size: Batch size.
        lr: Learning rate.
        seed: Random seed.
        valid_data_path: Path to validation data. If None, splits train data.
        valid_fraction: Fraction of data to use for validation if valid_data_path is None.
        patience: Early stopping patience.
        energy_weight: Weight for energy loss.
        forces_weight: Weight for force loss.
        stress_weight: Weight for stress loss.
        compute_stress: Whether to compute/train on stress.
        max_L: Max spherical harmonic degree (0=invariant, 1=vector, etc.)
        r_max: Cutoff radius.
        dtype: 'float32' or 'float64'.
        keep_checkpoints: Whether to keep all intermediate checkpoints and compile them to .model files.
    """
    # Determine model hyperparameters based on size
    if model_size == "small":
        hidden_irreps = "32x0e" if max_L == 0 else "32x0e + 32x1o"
        num_interactions = 2
        mlp_hidden_dims = [64, 64]
    elif model_size == "medium":
        hidden_irreps = "64x0e" if max_L == 0 else "64x0e + 64x1o"
        num_interactions = 2
        mlp_hidden_dims = [128, 128]
    elif model_size == "large":
        hidden_irreps = "128x0e" if max_L == 0 else "128x0e + 128x1o"
        num_interactions = 2
        mlp_hidden_dims = [256, 256]
    else:
        raise ValueError(f"Unknown model size: {model_size}")

    os.makedirs(save_path, exist_ok=True)
    save_path = os.path.abspath(save_path)
    checkpoints_dir = os.path.join(save_path, "checkpoints")
    os.makedirs(checkpoints_dir, exist_ok=True)
    
    # Handle validation split
    train_file = os.path.abspath(data_path)
    valid_file = os.path.abspath(valid_data_path) if valid_data_path else None

    config = {
        "name": model_name,
        "train_file": train_file,
        "valid_file": valid_file,
        "valid_fraction": valid_fraction,
        "test_file": None,
        "E0s": "average",
        "model": "MACE",
        "num_interactions": num_interactions,
        "num_channels": None,
        "max_L": max_L,
        "r_max": r_max,
        "hidden_irreps": hidden_irreps,
        "mlp_hidden_dims": mlp_hidden_dims,
        "forces_weight": forces_weight,
        "energy_weight": energy_weight,
        "stress_weight": stress_weight,
        "optimizer_name": "adam",
        "lr": lr,
        "batch_size": batch_size,
        "max_num_epochs": epochs,
        "patience": patience,
        "eval_interval": 1,
        "keep_checkpoints": keep_checkpoints,
        "restart_latest": restart,
        "save_cpu": False,
        "device": device,
        "seed": seed,
        "log_dir": save_path,
        "model_dir": save_path,
        "checkpoints_dir": checkpoints_dir,
        "results_dir": os.path.join(save_path, "results"),
        "error_table": "PerAtomMAE",
        "loss": "weighted",
        "amsgrad": True,
        "scheduler_patience": patience // 2,
        "lr_scheduler_gamma": 0.5,
        "compute_stress": compute_stress,
    }
    
    if restart:
        logger.info(f"Restart requested. Looking for checkpoints in {checkpoints_dir} with name {model_name}_run-{seed}...")
    
    # Start background checkpoint monitor if keep_checkpoints is enabled
    stop_monitor = None
    if keep_checkpoints:
        import threading
        import time
        from macer.utils.model_tools import compile_mace_model
        
        stop_monitor = threading.Event()
        processed_checkpoints = set()
        
        def monitor_checkpoints():
            logger.info("Checkpoint monitor started.")
            while not stop_monitor.is_set():
                if os.path.exists(checkpoints_dir):
                    # List all .pt files in checkpoints_dir
                    pts = [f for f in os.listdir(checkpoints_dir) if f.endswith(".pt")]
                    for pt in pts:
                        if pt not in processed_checkpoints:
                            pt_path = os.path.join(checkpoints_dir, pt)
                            model_out = pt_path.replace(".pt", ".model")
                            if not os.path.exists(model_out):
                                logger.info(f"Monitor: New checkpoint detected: {pt}. Compiling...")
                                try:
                                    # Use the utility to compile
                                    compile_mace_model(pt_path, model_out, model_size=model_size, device="cpu")
                                    processed_checkpoints.add(pt)
                                except Exception as e:
                                    logger.warning(f"Monitor: Failed to compile {pt}: {e}")
                time.sleep(10)
        
        monitor_thread = threading.Thread(target=monitor_checkpoints, daemon=True)
        monitor_thread.start()

    # Log config
    logger.info(f"Starting MACE training with config: {config}")
    
    # Try executing MACE CLI via subprocess
    try:
        # Determine the python executable to use
        python_exe = sys.executable
        
        # Prepare environment
        env = os.environ.copy()
        env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

        # Check if we should use bundled mace
        use_bundled = False
        try:
            import mace
        except ImportError:
            use_bundled = True

        if use_bundled:
            externals_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "externals"))
            env["PYTHONPATH"] = externals_path + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
            mace_module = "mace_bundled.cli.run_train"
        else:
            mace_module = "mace.cli.run_train"

        # Use patch wrapper for MPS
        if config["device"] == "mps":
            patch_script = os.path.join(os.path.dirname(__file__), "mace_mps_patch.py")
            cmd = [python_exe, patch_script, mace_module]
        else:
            cmd = [python_exe, "-m", mace_module]

        cmd.extend([
            "--name", config["name"],
            "--train_file", config["train_file"],
            "--E0s", str(config["E0s"]),
            "--num_interactions", str(config["num_interactions"]),
            "--max_L", str(config["max_L"]),
            "--r_max", str(config["r_max"]),
            "--hidden_irreps", config["hidden_irreps"],
            "--forces_weight", str(config["forces_weight"]),
            "--energy_weight", str(config["energy_weight"]),
            "--stress_weight", str(config["stress_weight"]),
            "--batch_size", str(config["batch_size"]),
            "--max_num_epochs", str(config["max_num_epochs"]),
            "--patience", str(config["patience"]),
            "--device", config["device"],
            "--seed", str(config["seed"]),
            "--log_dir", config["log_dir"],
            "--model_dir", config["model_dir"],
            "--checkpoints_dir", config["checkpoints_dir"],
            "--results_dir", config["results_dir"],
            "--energy_key", "energy",
            "--forces_key", "forces",
            "--stress_key", "stress",
            "--default_dtype", dtype,
        ])
        
        if config["valid_file"]:
            cmd.extend(["--valid_file", config["valid_file"]])
        else:
            cmd.extend(["--valid_fraction", str(config["valid_fraction"])])
            
        cmd.extend(["--compute_stress", str(config["compute_stress"])])
        
        if config["device"] == "mps":
            cmd.extend(["--pin_memory", "False"])
        
        if config["keep_checkpoints"]:
            cmd.append("--keep_checkpoints")
        if config["restart_latest"]:
            cmd.append("--restart_latest")
        if config["save_cpu"]:
            cmd.append("--save_cpu")

        logger.info(f"Executing MACE via subprocess: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, env=env, check=True)
        
        if result.returncode == 0:
            logger.info("MACE training finished successfully.")
        else:
            raise RuntimeError(f"MACE training exited with return code {result.returncode}")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"MACE training subprocess failed with error: {e}")
        raise e
    except Exception as e:
        logger.error(f"MACE training failed: {e}")
        raise e
    finally:
        if stop_monitor:
            logger.info("Stopping checkpoint monitor.")
            stop_monitor.set()

