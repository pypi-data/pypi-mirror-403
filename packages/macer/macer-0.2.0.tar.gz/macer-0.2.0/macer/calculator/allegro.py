import os
from macer.defaults import DEFAULT_MODELS, _macer_root, resolve_model_path

_ALLEGRO_AVAILABLE = False
try:
    from nequip.ase import NequIPCalculator
    _ALLEGRO_AVAILABLE = True
except Exception:
    pass

def get_allegro_calculator(model_path, device="cpu", **kwargs):
    if not _ALLEGRO_AVAILABLE:
        raise RuntimeError("Allegro (nequip) is not installed. Please install with 'pip install .[allegro]'")

    if model_path is None:
        default_allegro_model_name = DEFAULT_MODELS.get("allegro")
        if default_allegro_model_name:
            model_path = resolve_model_path(default_allegro_model_name)
            print(f"No specific Allegro model path provided; using default: {model_path}")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Default Allegro model not found at {model_path}. Please provide a valid model path with --model or ensure the default model exists.")
        else:
            raise ValueError("A compiled model path (`.pt2`) is required for Allegro/NequIP. No default model found in default-model.yaml.")
    else:
        model_path = resolve_model_path(model_path)

    # Allegro/NequIP uses a class method to load a compiled model.
    # The PDF mentions several other potential arguments for mapping and units.
    # We can pass them via kwargs if needed.
    
    # Default mappings, can be overridden by kwargs
    calc_kwargs = {
        "device": device,
        "energy_units_to_eV": 1.0,
        "length_units_to_A": 1.0,
    }
    calc_kwargs.update(kwargs)

    return NequIPCalculator.from_compiled_model(
        compile_path=model_path,
        **calc_kwargs
    )
