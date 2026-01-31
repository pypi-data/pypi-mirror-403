_FAIRCHEM_AVAILABLE = False
try:
    from fairchem.core import pretrained_mlip, FAIRChemCalculator
    _FAIRCHEM_AVAILABLE = True
except Exception:
    pass

from macer.defaults import resolve_model_path

def get_fairchem_calculator(model_path="uma-s-1p1", device="cpu", **kwargs):
    """
    Constructs a FAIRChem UMA calculator.
    Requires user to be logged into Hugging Face: `huggingface-cli login`
    """
    if not _FAIRCHEM_AVAILABLE:
        raise RuntimeError("fairchem-core is not installed. Please install with 'pip install .[fairchem]'")

    # For UMA models, model_path is the model name, e.g., "uma-s-1p1"
    # Or it can be a local path resolved via resolve_model_path
    if model_path:
        model_path = resolve_model_path(model_path)
    # The task_name is crucial for materials science calculations.
    task_name = "omat" 

    print(f"Loading FAIRChem UMA model: {model_path} for task: {task_name}")
    print("Note: This requires a Hugging Face account and access to the UMA model repository.")
    
    try:
        # pretrained_mlip.get_predict_unit handles the download from Hugging Face
        predictor = pretrained_mlip.get_predict_unit(model_path, device=device)
        calc = FAIRChemCalculator(predictor, task_name=task_name)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load FAIRChem UMA model '{model_path}'. "
            "Please ensure you have requested access on Hugging Face and are logged in (`huggingface-cli login`). "
            f"Original error: {e}"
        )

    return calc