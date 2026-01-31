import os
from pathlib import Path

_MACE_AVAILABLE = False
try:
    from macer.externals.mace_bundled.calculators import MACECalculator, mace_mp
    _MACE_AVAILABLE = True
except Exception:
    pass

from macer.defaults import DEFAULT_MODELS, _macer_root, resolve_model_path
from macer.utils.model_manager import ensure_model, print_model_help

def get_mace_calculator(model_paths, device="cpu", **kwargs):
    """Construct MACE calculator (use float32 for MPS compatibility)."""
    if not _MACE_AVAILABLE:
        raise RuntimeError("MACE related libraries are not installed. Please install with 'pip install \"macer[mace]\"'")

    # ... (MPS patch logic omitted for brevity, keeping original content intact in replacement) ...
    if device == "mps":
        import torch
        # --- MPS Compatibility Patch (Reinforced) ---
        if not hasattr(torch.Tensor, "_orig_double_macer_patched"):
            print("INFO: Applying reinforced MPS float64 -> float32 patch...")
            torch.Tensor._orig_double_macer_patched = torch.Tensor.double
            torch.Tensor._orig_to_macer_patched = torch.Tensor.to
            
            def mps_safe_double(self):
                if "mps" in str(self.device):
                    return self.float()
                return torch.Tensor._orig_double_macer_patched(self)
            
            def mps_safe_to(self, *args, **kwargs):
                # Check for float64 in args or kwargs
                new_args = list(args)
                if len(args) > 0 and args[0] is torch.float64:
                    if "mps" in str(self.device):
                        new_args[0] = torch.float32
                
                if kwargs.get("dtype") is torch.float64:
                    if "mps" in str(self.device) or "mps" in str(kwargs.get("device", "")):
                        kwargs["dtype"] = torch.float32
                
                return torch.Tensor._orig_to_macer_patched(self, *tuple(new_args), **kwargs)

            torch.Tensor.double = mps_safe_double
            torch.Tensor.to = mps_safe_to
            print("INFO: MPS patch applied successfully.")

    dtype = "float32" if device == "mps" else "float64"

    # Determine the default MACE model path from DEFAULT_MODELS
    default_mace_model_name = DEFAULT_MODELS.get("mace")

    # If no model path is explicitly provided via --model argument (model_paths is [None])
    if not model_paths or (len(model_paths) == 1 and model_paths[0] is None):
        if default_mace_model_name:
            # Check and Provision
            ensure_model("mace", default_mace_model_name)
            default_mace_model_path = resolve_model_path(default_mace_model_name)
            # Use the model specified in default-model.yaml
            print(f"No specific MACE model path provided; using default: {default_mace_model_path}")
            actual_model_paths = [default_mace_model_path]
        else:
            # Fallback to mace_mp "small" if no default is specified in default-model.yaml
            print("No specific MACE model path provided and no default in default-model.yaml; using `mace_mp` 'small' model.")
            return mace_mp(
                model="small",
                device=device,
                default_dtype=dtype
            )
    else:
        # If a specific model path is provided via --model argument
        actual_model_paths = []
        for p in model_paths:
            if p is None: continue
            
            # Check existence first
            if not os.path.exists(p):
                basename = os.path.basename(p)
                provisioned = ensure_model("mace", basename)
                if provisioned:
                    p = provisioned
                else:
                    print_model_help("mace")
                    raise FileNotFoundError(f"Model file not found: {p}")
            
            if not os.path.isabs(p):
                p = resolve_model_path(p)
            actual_model_paths.append(p)
            
        if not actual_model_paths:
            raise ValueError("No valid MACE model path provided.")

    return MACECalculator(
        model_paths=actual_model_paths,
        device=device,
        default_dtype=dtype,
    )
