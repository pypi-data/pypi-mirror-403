import os
from macer.defaults import DEFAULT_MODELS, _macer_root, resolve_model_path
from macer.utils.model_manager import ensure_model, print_model_help

_SEVENNET_AVAILABLE = False
try:
    from sevenn.calculator import SevenNetCalculator
    _SEVENNET_AVAILABLE = True
except Exception:
    pass

def get_sevennet_calculator(model_path: str, device: str = "cpu", modal: str = None):
    """Construct SevenNet calculator."""
    if not _SEVENNET_AVAILABLE:
        raise RuntimeError("SevenNet related libraries are not installed. Please install with 'pip install \"macer[sevennet]\"'")

    if model_path is None:
        # Use the default SevenNet model path from DEFAULT_MODELS
        default_sevennet_model_name = DEFAULT_MODELS.get("sevennet")
        if default_sevennet_model_name:
            # Check and Provision
            ensure_model("sevennet", default_sevennet_model_name)
            model_path = resolve_model_path(default_sevennet_model_name)
            print(f"No specific SevenNet model path provided; using default: {model_path}")
        else:
            raise ValueError("No default SevenNet model specified in default-model.yaml and no model_path provided.")
    else:
        # Check if the file exists. If not, try to auto-provision.
        if not os.path.exists(model_path):
            basename = os.path.basename(model_path)
            provisioned = ensure_model("sevennet", basename)
            if provisioned:
                model_path = provisioned
            else:
                # Provisioning failed or model unknown
                print_model_help("sevennet")
                raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # If it was a relative path and exists (or was just provisioned), resolve it to absolute if needed
        if not os.path.isabs(model_path):
             model_path = resolve_model_path(model_path)

    calc_args = {
        "model": model_path,
        "device": device,
    }
    if modal:
        calc_args["modal"] = modal

    return SevenNetCalculator(**calc_args)

