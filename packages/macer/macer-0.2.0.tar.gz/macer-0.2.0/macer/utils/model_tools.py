import torch
import os
import sys
import subprocess
import shutil
from pathlib import Path

def get_mace_modules():
    """Helper to get mace modules from environment or bundled."""
    try:
        import mace.data as mace_data
        import mace.modules as mace_modules
        import mace.tools as mace_tools
        return True, {
            'data': mace_data,
            'modules': mace_modules,
            'tools': mace_tools
        }
    except ImportError:
        try:
            import macer.externals.mace_bundled.data as mace_data
            import macer.externals.mace_bundled.modules as mace_modules
            import macer.externals.mace_bundled.tools as mace_tools
            return True, {
                'data': mace_data,
                'modules': mace_modules,
                'tools': mace_tools
            }
        except ImportError:
            return False, {}

def compile_mace_model(checkpoint_path: str, output_path: str = None, model_size: str = "small", device: str = "cpu"):
    """
    Compiles a MACE checkpoint (.pt) into a full model file (.model) that macer can use.
    Uses a wrapper script to patch deepcopy and avoid MACE 0.3.14 bugs.
    """
    if not os.path.exists(checkpoint_path):
        print(f"Error: Checkpoint '{checkpoint_path}' not found.")
        return

    checkpoint_path = os.path.abspath(checkpoint_path)
    ckpt_dir = os.path.dirname(checkpoint_path)
    
    # We use a fixed temporary name to ensure MACE loads it regardless of original name
    model_name = "mace_compile_tmp"
    tmp_ckpt_name = f"{model_name}_run-123.pt"
    tmp_ckpt_path = os.path.join(ckpt_dir, tmp_ckpt_name)
    
    if output_path is None:
        p = Path(checkpoint_path)
        output_path = f"{p.stem}_compiled.model"

    print(f"Compiling MACE model from checkpoint: {checkpoint_path}")
    
    # 1. Symlink or copy the checkpoint to the temporary name
    has_temp_ckpt = False
    try:
        if os.path.exists(tmp_ckpt_path):
            os.remove(tmp_ckpt_path)
        try:
            os.symlink(checkpoint_path, tmp_ckpt_path)
        except OSError:
            shutil.copy2(checkpoint_path, tmp_ckpt_path)
        has_temp_ckpt = True
    except Exception as e:
        print(f"Warning: Could not create temporary checkpoint link: {e}")

    try:
        python_exe = sys.executable
        wrapper_script = "mace_compile_wrapper_tmp.py"
        
        # Create the wrapper script on the fly to patch deepcopy and torch.save
        wrapper_content = """
import sys
import os
import copy
import torch

# Patch deepcopy to avoid the ScriptFunction pickling error in MACE 0.3.14
original_deepcopy = copy.deepcopy
def patched_deepcopy(x, memo=None):
    if isinstance(x, torch.nn.Module):
        return x # Don't deepcopy modules
    return original_deepcopy(x, memo)

copy.deepcopy = patched_deepcopy

# Patch torch.save to ignore errors (since we only care about the JIT version)
original_save = torch.save
def patched_save(obj, f, **kwargs):
    try:
        return original_save(obj, f, **kwargs)
    except Exception as e:
        # Just log to stdout for the wrapper to see
        sys.stdout.write(f"DEBUG: torch.save failed (expected for full model in 0.3.14): {e}\\n")
        return None

torch.save = patched_save

# Now import and run MACE
from mace.cli.run_train import main

if __name__ == "__main__":
    main()
"""
        with open(wrapper_script, "w") as f:
            f.write(wrapper_content)

        # 3. Load checkpoint to extract atomic numbers for dummy XYZ
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        atomic_numbers = [1]
        try:
            if "atomic_numbers" in checkpoint:
                atomic_numbers = checkpoint["atomic_numbers"].tolist()
            elif "model" in checkpoint and "atomic_numbers" in checkpoint["model"]:
                atomic_numbers = checkpoint["model"]["atomic_numbers"].tolist()
        except: pass

        # Create dummy XYZ
        dummy_xyz = "dummy_compile.xyz"
        from ase.data import chemical_symbols
        with open(dummy_xyz, "w") as f:
            for _ in range(2): 
                f.write(f"{len(atomic_numbers)}\n")
                f.write("Lattice=\"1.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 1.0\" Properties=species:S:1:pos:R:3:forces:R:3 energy=0.0\n")
                for z in atomic_numbers:
                    symbol = chemical_symbols[int(z)]
                    f.write(f"{symbol} 0.0 0.0 0.0 0.0 0.0 0.0\n")

        cmd = [
            python_exe, wrapper_script,
            "--name", model_name,
            "--seed", "123",
            "--model_dir", ".",
            "--checkpoints_dir", ckpt_dir,
            "--results_dir", "./tmp_results",
            "--log_dir", ".",
            "--restart_latest",
            "--max_num_epochs", "0",
            "--device", device,
            "--default_dtype", "float32" if device == "mps" else "float64",
            "--train_file", dummy_xyz,
            "--valid_file", dummy_xyz, 
            "--batch_size", "1",
            "--energy_key", "energy",
            "--forces_key", "forces",
            "--stress_key", "stress",
            "--E0s", "average",
        ]

        env = os.environ.copy()
        env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
        env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

        print(f"Starting compilation subprocess via wrapper...")
        process = subprocess.Popen(
            cmd, 
            env=env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(f"  [MACE] {line.strip()}")
        
        process.wait(timeout=60)

        # Cleanup dummy and temp ckpt
        if os.path.exists(dummy_xyz): os.remove(dummy_xyz)
        if has_temp_ckpt and os.path.exists(tmp_ckpt_path): os.remove(tmp_ckpt_path)
        if os.path.exists(wrapper_script): os.remove(wrapper_script)

        # Search for output
        possible_patterns = [
            f"{model_name}_compiled.model",
            f"{model_name}_run-123_compiled.model",
            f"{model_name}_run-123.model",
            f"{model_name}.model",
            f"{model_name}_run-123_epoch-0.model"
        ]
        possible_dirs = [".", ckpt_dir, "./tmp_results", "./results/checkpoints"]
        
        final_src = None
        for d in possible_dirs:
            if not os.path.exists(d): continue
            for p in possible_patterns:
                path = os.path.join(d, p)
                if os.path.exists(path):
                    final_src = path
                    break
            if final_src: break
        
        if not final_src:
            import glob
            model_files = glob.glob("**/*.model", recursive=True)
            if model_files:
                relevant = [f for f in model_files if model_name in f]
                if relevant: final_src = relevant[0]

        if final_src:
            shutil.move(final_src, output_path)
            print(f"Successfully compiled model to: {output_path}")
            # Cleanup
            if os.path.exists("./tmp_results"): shutil.rmtree("./tmp_results")
            if os.path.exists("./results"): shutil.rmtree("./results")
        else:
            print("Error: Could not find compiled model file.")

    except Exception as e:
        print(f"Error: {e}")


def convert_model_precision(input_path: str, output_path: str = None):
    """
    Converts a MACE/MLFF model from float64 to float32 precision.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        return

    if output_path is None:
        p = Path(input_path)
        output_path = f"{p.stem}-fp32{p.suffix}"

    print(f"Loading model from '{input_path}'...")
    try:
        # Load the model on the CPU
        model_fp64 = torch.load(input_path, map_location=torch.device('cpu'), weights_only=False)

        print("Converting model to float32 precision...")
        model_fp32 = model_fp64.to(dtype=torch.float32)

        print(f"Saving converted model to '{output_path}'...")
        torch.save(model_fp32, output_path)
        print("Conversion complete!")
    except Exception as e:
        print(f"Error during model conversion: {e}")

def list_models():
    """
    List available models in the mlff-model directory and custom mlff_directory.
    """
    from macer.defaults import _macer_root, DEFAULT_MLFF_DIRECTORY, _model_root
    
    dirs_to_check = [Path(_model_root)]
    if DEFAULT_MLFF_DIRECTORY:
        dirs_to_check.insert(0, Path(DEFAULT_MLFF_DIRECTORY))

    for model_dir in dirs_to_check:
        if not model_dir.exists():
            print(f"Warning: Model directory '{model_dir}' not found.")
            continue

        print(f"\nAvailable models in {model_dir}:")
        print("-" * 50)
        models = sorted(list(model_dir.glob("*.pth")) + list(model_dir.glob("*.model")))
        if not models:
            print("  (No models found)")
        else:
            for m in models:
                size_mb = m.stat().st_size / (1024 * 1024)
                print(f"  - {m.name:<40} ({size_mb:>6.1f} MB)")
        print("-" * 50)