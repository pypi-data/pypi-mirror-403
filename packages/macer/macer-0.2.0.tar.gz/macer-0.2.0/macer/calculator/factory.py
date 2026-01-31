"""
Macer: Machine-learning accelerated Atomic Computational Environment for automated Research workflows
Copyright (c) 2025 The Macer Package Authors
Author: Soungmin Bae <soungminbae@gmail.com>
License: MIT
"""

# 1. Import all get_*_calculator functions and _*_AVAILABLE flags.
from .mace import get_mace_calculator, _MACE_AVAILABLE
from .sevennet import get_sevennet_calculator, _SEVENNET_AVAILABLE
from .chgnet import get_chgnet_calculator, _CHGNET_AVAILABLE
from .m3gnet import get_m3gnet_calculator, _M3GNET_AVAILABLE
from .allegro import get_allegro_calculator, _ALLEGRO_AVAILABLE
from .mattersim import get_mattersim_calculator, _MATTERSIM_AVAILABLE
from .orb import get_orb_calculator, _ORB_AVAILABLE
from .fairchem import get_fairchem_calculator, _FAIRCHEM_AVAILABLE
from .emt import get_emt_calculator, _EMT_AVAILABLE

ALL_SUPPORTED_FFS = ["mattersim", "mace", "sevennet", "chgnet", "m3gnet", "allegro", "orb", "fairchem", "emt"]

def get_available_calculators():
    """Dynamically builds the dictionary of available calculators."""
    available_calculators = {}
    if _MACE_AVAILABLE:
        available_calculators["mace"] = get_mace_calculator
    if _SEVENNET_AVAILABLE:
        available_calculators["sevennet"] = get_sevennet_calculator
    if _CHGNET_AVAILABLE:
        available_calculators["chgnet"] = get_chgnet_calculator
    if _M3GNET_AVAILABLE:
        available_calculators["m3gnet"] = get_m3gnet_calculator
    if _ALLEGRO_AVAILABLE:
        available_calculators["allegro"] = get_allegro_calculator
    if _MATTERSIM_AVAILABLE:
        available_calculators["mattersim"] = get_mattersim_calculator
    if _ORB_AVAILABLE:
        available_calculators["orb"] = get_orb_calculator
    if _FAIRCHEM_AVAILABLE:
        available_calculators["fairchem"] = get_fairchem_calculator
    if _EMT_AVAILABLE:
        available_calculators["emt"] = get_emt_calculator
    return available_calculators

# 3. Create the unified creation function.
def get_calculator(ff_name: str, **kwargs):
    """
    Creates an ASE Calculator instance for the given force field name.
    """
    available_calculators = get_available_calculators()
    if ff_name not in available_calculators:
        raise ValueError(f"Unsupported force field: {ff_name}. Available options are: {list(available_calculators.keys())}")
    
    calculator_func = available_calculators[ff_name]
    return calculator_func(**kwargs)

def get_available_ffs():
    """
    Returns a list of currently installed (available) force fields,
    with a preferred order for defaults.
    """
    calculators = get_available_calculators()
    
    # Define the preferred order
    preferred_order = ["mattersim", "mace", "sevennet", "orb", "fairchem"]
    
    # Start with preferred FFs that are available
    available_preferred = [ff for ff in preferred_order if ff in calculators]
    
    # Add the rest of the available FFs that are not in the preferred list
    other_ffs = [ff for ff in calculators if ff not in available_preferred]
    
    return available_preferred + other_ffs
