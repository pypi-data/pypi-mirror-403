import os
import sys
from macer.defaults import DEFAULT_MODELS, _macer_root, resolve_model_path
from macer.utils.model_manager import ensure_model, print_model_help

try:
    from mattersim.forcefield import MatterSimCalculator
    _MATTERSIM_AVAILABLE = True
except Exception:
    _MATTERSIM_AVAILABLE = False
    MatterSimCalculator = None  # Define as None if import fails

def get_mattersim_calculator(model_path, device="cpu", **kwargs):
    if not _MATTERSIM_AVAILABLE:
        raise RuntimeError("MatterSim is not installed. Please install with 'pip install .[mattersim]'")

    if model_path is None:
        default_mattersim_model_name = DEFAULT_MODELS.get("mattersim")
        if default_mattersim_model_name:
            # Check and Provision
            ensure_model("mattersim", default_mattersim_model_name)
            model_path = resolve_model_path(default_mattersim_model_name)
            print(f"No specific MatterSim model path provided; using default: {model_path}")
        else:
            raise ValueError("A model path (load_path) is required for MatterSim. No default model found in default-model.yaml.")
    else:
        # Check if the file exists. If not, try to auto-provision.
        if not os.path.exists(model_path):
            basename = os.path.basename(model_path)
            provisioned = ensure_model("mattersim", basename)
            if provisioned:
                model_path = provisioned
            else:
                # Provisioning failed or model unknown
                print_model_help("mattersim")
                raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # If it was a relative path and exists (or was just provisioned), resolve it to absolute if needed
        # (Though ensure_model returns absolute path, and existing absolute path is fine)
        if not os.path.isabs(model_path):
             model_path = resolve_model_path(model_path)

    # MatterSimCalculator takes device and load_path arguments.
    return MatterSimCalculator(device=device, load_path=model_path)
