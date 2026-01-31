import os
import sys

_ORB_AVAILABLE = False
try:
    from orb_models.forcefield import pretrained
    from orb_models.forcefield.calculator import ORBCalculator
    _ORB_AVAILABLE = True
except Exception:
    pass

from macer.defaults import resolve_model_path

def get_orb_calculator(model_path="orb-v2", device="cpu", **kwargs):
    """
    Constructs ORB calculator from a pretrained model name.
    """
    if not _ORB_AVAILABLE:
        raise RuntimeError("orb-models is not installed. Please install with 'pip install .[orb]'")

    # Fix for macOS: Disable torch.compile to avoid library loading errors (@rpath/libc++.1.dylib)
    if sys.platform == "darwin" and "TORCH_COMPILE_DISABLE" not in os.environ:
        os.environ["TORCH_COMPILE_DISABLE"] = "1"

    # Resolve local path if provided, otherwise assume it's a pretrained name
    if model_path:
        model_path = resolve_model_path(model_path)

    if hasattr(pretrained, model_path):
        # Get the function from the pretrained module, e.g., pretrained.orb_v2
        model_func = getattr(pretrained, model_path)
        print(f"Loading ORB pretrained model: {model_path}")
        # Call the function to get the force field object
        orbff = model_func(device=device)
    else:
        available_models = [name for name in dir(pretrained) if not name.startswith('_') and callable(getattr(pretrained, name))]
        raise ValueError(f"Unsupported ORB model: '{model_path}'.\nAvailable models in orb_models.forcefield.pretrained are: {available_models}")

    return ORBCalculator(orbff, device=device)