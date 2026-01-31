
"""
Macer: Machine-learning accelerated Atomic Computational Environment for automated Research workflows
Copyright (c) 2025 The Macer Package Authors
Author: Soungmin Bae <soungminbae@gmail.com>
License: MIT
"""

import yaml
import os
from pathlib import Path

_current_dir = os.path.dirname(os.path.abspath(__file__))
_macer_root = os.path.join(_current_dir, "..")
_model_root = os.path.join(_current_dir, "mlff-model")
_default_yaml_path = Path(_current_dir) / "default.yaml"
_user_yaml_path = Path.home() / ".macer.yaml"

DEFAULT_SETTINGS = {}
DEFAULT_MODELS = {}
DEFAULT_DEVICE = "cpu"
DEFAULT_FF = "mattersim"
DEFAULT_MLFF_DIRECTORY = None

# Available model candidates for configuration hints & interactive mode
AVAILABLE_MODELS = {
    "sevennet": ["7net-0", "sevennet-omni", "7net-omat", "7net-l3i5", "7net-mf-ompa"],
    "mace": ["small", "medium", "large", "mace-matpes-pbe-0", "mace-matpes-r2scan-0"],
    "mattersim": ["mattersim-v1.0.0-1M.pth", "mattersim-v1.0.0-5M.pth"],
    "fairchem": ["uma-s-1p1", "uma-s-1", "uma-m-1"],
    "orb": ["orb_v2", "orb-v2", "orb-d3-v2", "orb_v3_conservative_inf_omat"],
    "chgnet": ["v0.3.0"],
    "m3gnet": ["MP-2021.2.8-EFS"]
}

# Mapping specific keywords/names to their download strategies and expected filenames
MODEL_SOURCES = {
    # SevenNet
    "7net-0": {"type": "sevenn", "keyword": "7net-0", "target": "checkpoint_sevennet_0.pth", "size": "9.8 MB"},
    "sevennet-omni": {"type": "sevenn", "keyword": "sevennet-omni", "target": "checkpoint_sevennet_omni.pth", "size": "98 MB"},
    "7net-omat": {"type": "sevenn", "keyword": "7net-omat", "target": "checkpoint_sevennet_omat.pth", "size": "60 MB"},
    "7net-l3i5": {"type": "sevenn", "keyword": "7net-l3i5", "target": "checkpoint_sevennet_l3i5.pth", "size": "14 MB"},
    "7net-mf-ompa": {"type": "sevenn", "keyword": "7net-mf-ompa", "target": "checkpoint_sevennet_mf_ompa.pth", "size": "99 MB"},
    
    # MACE
    "small": {"type": "mace", "keyword": "small", "target": "mace-omat-0-small.model", "size": "31 MB"},
    "medium": {"type": "mace", "keyword": "medium", "target": "mace-omat-0-medium.model", "size": "42 MB"},
    "large": {"type": "mace", "keyword": "large", "target": "mace-omat-0-large.model", "size": "128 MB"},
    "mace-matpes-r2scan-0": {"type": "mace", "keyword": "mace-matpes-r2scan-0", "target": "mace-matpes-r2scan-0.model", "size": "76 MB"},
    "mace-matpes-pbe-0": {"type": "mace", "keyword": "mace-matpes-pbe-0", "target": "mace-matpes-pbe-0.model", "size": "76 MB"}, # Estimated same as r2scan
    
    # MatterSim
    "mattersim-v1.0.0-1M.pth": {"type": "mattersim", "keyword": "mattersim-v1.0.0-1M.pth", "target": "mattersim-v1.0.0-1M.pth", "size": "17 MB"},
    "mattersim-v1.0.0-5M.pth": {"type": "mattersim", "keyword": "mattersim-v1.0.0-5M.pth", "target": "mattersim-v1.0.0-5M.pth", "size": "87 MB"},
    
    # Allegro (Direct download support needs URL, but size is known)
    "Allegro-OAM-L-0.1.ase.nequip.pth": {"type": "manual", "keyword": "Allegro", "target": "Allegro-OAM-L-0.1.ase.nequip.pth", "size": "38 MB"},
}

def ensure_user_config():
    if not _user_yaml_path.exists():
        try:
            if _default_yaml_path.exists():
                import shutil
                shutil.copy(_default_yaml_path, _user_yaml_path)
        except Exception:
            pass

ensure_user_config()

def _load_config(path, settings, models, is_user_config=False):
    global DEFAULT_DEVICE, DEFAULT_FF, DEFAULT_MLFF_DIRECTORY
    if path.exists():
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
                if config:
                    if "models" in config:
                        models.update(config["models"])
                    if "device" in config:
                        DEFAULT_DEVICE = config["device"]
                    if "default_mlff" in config:
                        DEFAULT_FF = config["default_mlff"]
                    if "mlff_directory" in config:
                        DEFAULT_MLFF_DIRECTORY = config["mlff_directory"]
                    settings.update(config)
        except Exception as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            if is_user_config:
                try:
                    import shutil
                    import time
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    backup_path = path.with_suffix(f".yaml.bak.{timestamp}")
                    print(f"  [Auto-Recovery] Corrupted user config detected.")
                    print(f"  [Auto-Recovery] Backing up corrupted file to: {backup_path}")
                    shutil.move(path, backup_path)
                    
                    print(f"  [Auto-Recovery] Regenerating default configuration...")
                    ensure_user_config()
                except Exception as rec_e:
                    print(f"  [Auto-Recovery] Critical Error: Failed to recover config: {rec_e}")

# 1. Load internal package defaults
_load_config(_default_yaml_path, DEFAULT_SETTINGS, DEFAULT_MODELS)

# 2. Load user overrides from ~/.macer.yaml if exists
if _user_yaml_path.exists():
    _load_config(_user_yaml_path, DEFAULT_SETTINGS, DEFAULT_MODELS, is_user_config=True)

def resolve_model_path(model_name: str) -> str:
    """
    Resolves the model path based on the logic:
    1. If model_name is an absolute path and exists, return it.
    2. If DEFAULT_MLFF_DIRECTORY is set, look for model_name there.
    3. Fallback to the project's mlff-model directory.
    """
    if not model_name:
        return None
        
    if os.path.isabs(model_name) and os.path.exists(model_name):
        return model_name
    
    # Check relative path from current working directory
    if os.path.exists(model_name):
        return os.path.abspath(model_name)

    # 1. Check user defined directory
    if DEFAULT_MLFF_DIRECTORY:
        user_path = os.path.join(DEFAULT_MLFF_DIRECTORY, model_name)
        if os.path.exists(user_path):
            return user_path

    # 2. Check project default directory
    pkg_path = os.path.join(_model_root, model_name)
    if os.path.exists(pkg_path):
        return pkg_path
        
    # If not found, return the pkg_path anyway so FileNotFoundError can be raised later with a clear message
    return pkg_path

# These are now dynamically loaded from DEFAULT_MODELS
# DEFAULT_MACE_MODEL_PATH = os.path.join(
#     _macer_root, "mlff-model", "mace-omat-0-small-fp32.model"
# )
# DEFAULT_SEVENNET_MODEL_PATH = os.path.join(
#     _macer_root, "mlff-model", "checkpoint_sevennet_0.pth"
# )
# DEFAULT_ALLEGRO_MODEL_PATH = os.path.join(
#     _macer_root, "mlff-model", "Allegro-OAM-L-0.1.ase.nequip.pth"
# )

