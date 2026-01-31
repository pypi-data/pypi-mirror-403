_CHGNET_AVAILABLE = False
try:
    from chgnet.model import CHGNetCalculator
    _CHGNET_AVAILABLE = True
except Exception:
    pass

from macer.defaults import resolve_model_path

def get_chgnet_calculator(model_path=None, device="cpu", **kwargs):
    if not _CHGNET_AVAILABLE:
        raise RuntimeError("CHGNet is not installed. Please install with 'pip install .[chgnet]'")
    
    if model_path:
        model_path = resolve_model_path(model_path)

    # From the PDF, CHGNetCalculator might take `use_device`
    # We will pass the device argument to it.
    return CHGNetCalculator(use_device=device)
