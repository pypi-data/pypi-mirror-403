import os
import shutil
import sys
import subprocess
from pathlib import Path
from macer.defaults import MODEL_SOURCES, _model_root, AVAILABLE_MODELS

def get_installed_models():
    """Returns a list of models currently in the mlff-model directory."""
    if not os.path.exists(_model_root):
        return []
    return [f for f in os.listdir(_model_root) if f.endswith(('.pth', '.model', '.pt'))]

def list_models_status(ff_filter=None):
    """Prints the status of available models."""
    installed = get_installed_models()
    
    print("\nThis utility allows you to check availability and download pre-trained MLFF models.")
    print("Downloaded models are stored in the 'mlff-model' directory and managed centrally.")

    target_ffs = [ff_filter] if ff_filter else AVAILABLE_MODELS.keys()
    
    # 1. Macer Managed Models
    print(f"\n[ Macer Managed Models (Downloadable) ]")
    print(f"{'='*80}")
    print(f"{'Force Field':<12} {'Model Name':<30} {'Size':<10} {'Status'}")
    print(f"{'-'*80}")
    
    # Define preferred display order
    preferred_order = ["mattersim", "sevennet", "mace", "allegro"]
    managed_ffs = [ff for ff in preferred_order if ff in target_ffs] + [ff for ff in target_ffs if ff not in preferred_order]

    external_models = []

    for ff in managed_ffs:
        if ff not in AVAILABLE_MODELS: continue
        for model in AVAILABLE_MODELS[ff]:
            source_info = MODEL_SOURCES.get(model)
            
            if source_info:
                target_name = source_info["target"]
                size_str = source_info.get("size", "Unknown")
                status = "[INSTALLED]" if target_name in installed else "[MISSING]"
                print(f"{ff:<12} {model:<30} {size_str:<10} {status}")
            else:
                external_models.append((ff, model))
    print(f"{'='*80}")

    # 2. External / Library Managed Models
    if external_models:
        print(f"\n[ External / Library Managed Models ]")
        print(f"These models are managed internally by their respective libraries (HuggingFace cache, etc.)")
        print(f"{'='*80}")
        print(f"{'Force Field':<12} {'Model Name':<30} {'Info'}")
        print(f"{'-'*80}")
        
        for ff, model in external_models:
             print(f"{ff:<12} {model:<30} Check library documentation")
        print(f"{'='*80}")
    
    print("\nUsage Examples:")
    print("  1. List all models (current view):")
    print("     macer util gm")
    print("  2. Download ALL missing models:")
    print("     macer util gm --model all")
    print("  3. Download all models for a specific force field (e.g., MACE):")
    print("     macer util gm --model all --ff mace")
    print("  4. Download a specific model by name:")
    print("     macer util gm --model sevennet-omni")
    print("\n")

def download_all_models(ff_filter=None, force=False):
    """
    Lists all available models (filtered by ff if provided), shows sizes,
    asks for confirmation, and downloads them. Handles skipping existing models unless force=True.
    """
    installed = get_installed_models()
    to_download = []
    already_installed_list = []
    
    # Define preferred display order
    preferred_order = ["mattersim", "sevennet", "mace", "fairchem", "orb", "m3gnet", "chgnet"]
    all_ffs = list(AVAILABLE_MODELS.keys())
    target_ffs = [ff for ff in preferred_order if ff in all_ffs] + [ff for ff in all_ffs if ff not in preferred_order]
    
    if ff_filter:
        target_ffs = [ff for ff in target_ffs if ff == ff_filter]
    
    print(f"\n{'='*80}")
    print(f" Bulk Download Preview: {'All Models' if not ff_filter else ff_filter.upper()}")
    print(f"{'='*80}")
    print(f"{'Force Field':<12} {'Model Name':<30} {'Size':<10} {'Status'}")
    print(f"{'-'*80}")

    for ff in target_ffs:
        if ff not in AVAILABLE_MODELS: continue
        for model in AVAILABLE_MODELS[ff]:
            source_info = MODEL_SOURCES.get(model)
            
            if not source_info: 
                # External model
                print(f"{ff:<12} {model:<30} {'-':<10} [EXTERNAL]")
                continue
            
            target_name = source_info["target"]
            size_str = source_info.get("size", "Unknown")
            
            if target_name in installed:
                if force:
                    status = "[RE-DOWNLOAD]"
                    to_download.append((ff, model))
                else:
                    status = "[INSTALLED]"
                    already_installed_list.append(model)
            else:
                status = "[QUEUED]"
                to_download.append((ff, model))
            
            print(f"{ff:<12} {model:<30} {size_str:<10} {status}")
    print(f"{'='*80}\n")
    
    if not to_download:
        print("All downloadable models are already installed. Use --replace to force re-download.")
        return

    print(f"Models to download: {len(to_download)}")
    if already_installed_list and not force:
        print(f"Skipping {len(already_installed_list)} already installed models.")

    confirm = input("Do you want to proceed with the download? [y/N]: ").strip().lower()
    
    if confirm == 'y':
        print("\nStarting batch download...")
        success_count = 0
        skipped_count = 0
        failed_count = 0
        
        for ff, model in to_download:
            print(f"\n[{success_count + failed_count + 1}/{len(to_download)}] Processing {model}...")
            # We already filtered for force logic above, but pass force=True to be safe/consistent
            result = download_model(ff, model, force=True) 
            if result:
                success_count += 1
            elif result is False: # Skipped (shouldn't happen here due to filtering but logic handles it)
                skipped_count += 1
            else:
                failed_count += 1
                
        print(f"\nBatch download completed.")
        print(f"  Success: {success_count}")
        print(f"  Failed : {failed_count}")
        if already_installed_list:
            print(f"  Skipped (Existing): {len(already_installed_list)}")
            # Optional: Print skipped names? user said "skip한 리스트도 보여주고"
            # print(f"    {', '.join(already_installed_list)}") 
    else:
        print("Download cancelled.")

def download_model(ff, keyword, force=False):
    """
    Downloads a model using the respective FF's API and saves it to mlff-model.
    Returns:
        Path (str): If successful
        False: If skipped (already exists and not forced)
        None: If failed
    """
    if keyword not in MODEL_SOURCES:
        pass
    
    source_info = MODEL_SOURCES.get(keyword)
    if not source_info:
        source_type = ff
        target_name = f"{keyword}.pth" if ff == "sevennet" else keyword
    else:
        source_type = source_info["type"]
        keyword = source_info["keyword"]
        target_name = source_info["target"]

    target_path = os.path.join(_model_root, target_name)
    os.makedirs(_model_root, exist_ok=True)

    if os.path.exists(target_path) and not force:
        # print(f"Model '{keyword}' already exists at {target_path}. Skipping.")
        return target_path

    print(f"--- Provisioning {ff.upper()} model: {keyword} ---")

    try:
        if source_type == "sevenn":
            _download_sevennet(keyword, target_path)
        elif source_type == "mace":
            _download_mace(keyword, target_path)
        elif source_type == "mattersim":
            _download_mattersim(keyword, target_path)
        else:
            raise ValueError(f"No download strategy defined for {ff}")
        
        print(f"Successfully saved model to: {target_path}")
        return target_path

    except Exception as e:
        print(f"Failed to download model {keyword}: {e}")
        return None

def _download_sevennet(keyword, target_path):
    import sevenn
    from sevenn.main.sevenn_get_model import run as run_get_model
    from argparse import Namespace
    
    # We need to find where sevenn saves its models
    # Based on our test: /site-packages/sevenn/pretrained_potentials/SevenNet_<name>/checkpoint_...pth
    
    print(f"  Calling SevenNet API for '{keyword}'...")
    # sevenn get_model <keyword>
    # Note: 7net-omni might need --modal mpa as per user example
    modal = None
    if "omni" in keyword: modal = "mpa"
    elif "mf-ompa" in keyword: modal = "mpa"
    
    # Fix: Add output_prefix, get_parallel, enable_flashTP, enable_cueq, and use_mliap to Namespace
    args = Namespace(checkpoint=keyword, modal=modal, output_prefix=None, get_parallel=False, enable_flashTP=False, enable_cueq=False, use_mliap=False)
    
    try:
        run_get_model(args)
    except Exception as e:
        # If run_get_model fails (e.g. modal not specified for deployment), we still check if the checkpoint was downloaded
        print(f"  SevenNet API warning: {e}")
        print("  Checking if checkpoint was downloaded anyway...")
    
    # Locate the file in sevenn package
    sevenn_dir = os.path.dirname(sevenn.__file__)
    # Usually SevenNet_omni, SevenNet_0, etc.
    folder_keyword = keyword.replace("7net-", "SevenNet_").replace("sevennet-", "SevenNet_")
    search_dir = os.path.join(sevenn_dir, "pretrained_potentials", folder_keyword)
    
    found_file = None
    if os.path.exists(search_dir):
        for f in os.listdir(search_dir):
            if f.endswith(".pth"):
                found_file = os.path.join(search_dir, f)
                break
    
    if not found_file:
        # Fallback search if folder name is different
        search_key = keyword.replace("7net-", "").replace("sevennet-", "").replace("-", "_").lower()
        
        for root, dirs, files in os.walk(os.path.join(sevenn_dir, "pretrained_potentials")):
            for f in files:
                if f.endswith(".pth"):
                    f_clean = f.lower().replace("-", "_")
                    if search_key in f_clean:
                        found_file = os.path.join(root, f)
                        break
            if found_file: break

    if found_file:
        print(f"  Found model at {found_file}. Copying to macer...")
        shutil.copy(found_file, target_path)
    else:
        raise FileNotFoundError(f"Could not find downloaded SevenNet model file for {keyword}")

def _download_mace(keyword, target_path):
    from mace.calculators import mace_mp
    import torch
    
    print(f"  Calling MACE API for '{keyword}'...")
    # This triggers the download to ~/.cache/mace
    try:
        from mace.calculators.foundations_models import download_mace_mp_checkpoint
        # Fix: argument name is likely 'model' not 'model_name' based on typical MACE usage, or positional
        try:
            cache_path = download_mace_mp_checkpoint(model=keyword)
        except TypeError:
             # Fallback: maybe it takes 'model_name' in some versions? No, error said unexpected.
             # Try positional
             cache_path = download_mace_mp_checkpoint(keyword)
             
    except (ImportError, TypeError, Exception) as e:
        print(f"  Direct download failed ({e}), falling back to calculator initialization...")
        # Fallback to initializing calculator which triggers download
        # Use float32 to match typical usage and avoid float64 issues on some systems
        try:
            _ = mace_mp(model=keyword, device="cpu", default_dtype="float32")
        except Exception as e_calc:
             print(f"  Calculator initialization also failed: {e_calc}")
             # Even if calc init fails (e.g. OMP error), download might have succeeded.
             pass

        # Try to find it in cache manually since mace_mp doesn't return path easily
        cache_dir = os.path.expanduser("~/.cache/mace")
        if not os.path.exists(cache_dir):
             raise FileNotFoundError("MACE cache directory not found.")
             
        # Look for the most recently modified file in cache that matches reasonable criteria
        # MACE filenames are cryptic (e.g. 2023-12-03...), so we might just pick the newest one
        # or try to match keyword if possible.
        # But wait, download_mace_mp_checkpoint returns the path!
        # If we are here, we failed to get the path directly.
        
        # Let's try to find a file that *looks* like a model
        candidates = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir) if not f.endswith('.json')] # skip metadata
        if not candidates:
             raise FileNotFoundError(f"No model files found in {cache_dir}")
             
        # Sort by modification time, newest first
        candidates.sort(key=os.path.getmtime, reverse=True)
        cache_path = candidates[0] # Pick the newest one
        print(f"  Assuming newest file in cache is the model: {os.path.basename(cache_path)}")

    if cache_path and os.path.exists(cache_path):
        print(f"  Found MACE model in cache: {cache_path}. Copying to macer...")
        shutil.copy(cache_path, target_path)
    else:
        raise FileNotFoundError(f"Could not find cached MACE model for {keyword}")

def _download_mattersim(keyword, target_path):
    from mattersim.forcefield.potential import Potential
    
    print(f"  Calling MatterSim API for '{keyword}'...")
    # Potential.from_checkpoint handles download to ~/.local/mattersim/pretrained_models
    _ = Potential.from_checkpoint(load_path=keyword, load_training_state=False, device="cpu")
    
    cache_folder = os.path.expanduser("~/.local/mattersim/pretrained_models")
    cache_path = os.path.join(cache_folder, keyword)
    
    if os.path.exists(cache_path):
        print(f"  Found MatterSim model in cache: {cache_path}. Copying to macer...")
        shutil.copy(cache_path, target_path)
    else:
        raise FileNotFoundError(f"Could not find cached MatterSim model for {keyword}")

def ensure_model(ff, model_name):
    """
    Checks if model_name exists in mlff-model. If not, attempts to download it.
    model_name is usually the filename (e.g. mattersim-v1.0.0-1M.pth).
    """
    # 1. Resolve path
    target_path = os.path.join(_model_root, model_name)
    
    if os.path.exists(target_path):
        return target_path
    
    # 2. Identify if we can download it
    # Search in MODEL_SOURCES by target filename
    keyword = None
    for k, info in MODEL_SOURCES.items():
        if info["target"] == model_name:
            keyword = k
            break
    
    if not keyword:
        # If not found in sources, maybe the model_name itself IS the keyword
        if ff in AVAILABLE_MODELS and model_name in AVAILABLE_MODELS[ff]:
            keyword = model_name
        else:
            return None # Cannot download unknown model
            
    return download_model(ff, keyword)

def print_model_help(ff):
    """Prints available models and instructions for the specified force field."""
    print(f"\n{'='*60}")
    print(f" [ERROR] Model not found and auto-download failed.")
    print(f" Force Field: {ff.upper()}")
    print(f"{'='*60}")
    
    print(f"\nAvailable {ff.upper()} Models:")
    if ff in AVAILABLE_MODELS:
        for m in AVAILABLE_MODELS[ff]:
            source = MODEL_SOURCES.get(m)
            size = source.get("size", "Unknown") if source else "-"
            print(f"  - {m:<30} (Size: {size})")
    else:
        print("  (No specific models registered)")
        
    print(f"\nTo download models, use the 'macer util gm' command:")
    print(f"  1. List all models:")
    print(f"     macer util gm")
    print(f"  2. Download all {ff.upper()} models:")
    print(f"     macer util gm --model all --ff {ff}")
    print(f"  3. Download a specific model:")
    print(f"     macer util gm --model <model_name>")
    print(f"\nExample:")
    if ff in AVAILABLE_MODELS and AVAILABLE_MODELS[ff]:
        example_model = AVAILABLE_MODELS[ff][0]
        print(f"     macer util gm --model {example_model}")
    
    print(f"\n[ NOTE: macer util gm (Get-Model) ]")
    print(f"  This is a centralized management tool for MLFF models in Macer.")
    print(f"  It automatically handles downloading from various sources (GitHub, HuggingFace, etc.)")
    print(f"  and organizes them in the 'mlff-model' directory for easy version control.")
    print(f"{'='*60}\n")
