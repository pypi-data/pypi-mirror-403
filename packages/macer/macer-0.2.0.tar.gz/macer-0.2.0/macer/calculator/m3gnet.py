_M3GNET_AVAILABLE = False
try:
    import matgl
    from matgl.ext.ase import PESCalculator
    _M3GNET_AVAILABLE = True
except Exception:
    pass

from macer.defaults import resolve_model_path

def get_m3gnet_calculator(model_path=None, device="cpu", **kwargs):
    if not _M3GNET_AVAILABLE:
        raise RuntimeError("M3GNet (matgl) is not installed. Please install with 'pip install .[m3gnet]'")

    # M3GNet requires loading a potential object first.
    # The model_path argument will specify which pre-trained model to load.
    # If no model_path is given, we can default to a standard one mentioned in the docs.
    if model_path is None:
        model_path = "M3GNet-MP-2021.2.8-PES"
    else:
        model_path = resolve_model_path(model_path)
    
    potential = matgl.load_model(model_path)
    
    # The PESCalculator does not seem to take a device argument directly,
    # it might be inferred from the potential object's device.
    # We will assume the default behavior of matgl handles the device.
    return PESCalculator(potential=potential)
