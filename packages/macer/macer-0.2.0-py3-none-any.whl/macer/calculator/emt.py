"""
Macer: Machine-learning accelerated Atomic Computational Environment for automated Research workflows
Copyright (c) 2025 The Macer Package Authors
Author: Soungmin Bae <soungminbae@gmail.com>
License: MIT
"""

import sys
from ase.calculators.emt import EMT

_EMT_AVAILABLE = True
EMT_SUPPORTED_ELEMENTS = ["Al", "Cu", "Ag", "Au", "Ni", "Pd", "Pt"]

def get_emt_calculator(**kwargs):
    """
    Returns an ASE EMT calculator instance.
    Includes validation for supported elements.
    """
    print(f"EMT calculator selected. Supported elements: {', '.join(EMT_SUPPORTED_ELEMENTS)}")
    return EMT()

def validate_emt_elements(atoms):
    """
    Checks if all atoms in the object are supported by EMT.
    Exits if unsupported elements are found.
    """
    symbols = set(atoms.get_chemical_symbols())
    unsupported = [s for s in symbols if s not in EMT_SUPPORTED_ELEMENTS]
    
    if unsupported:
        print(f"\nError: EMT does not support the following elements: {', '.join(unsupported)}")
        print(f"Supported elements are: {', '.join(EMT_SUPPORTED_ELEMENTS)}")
        sys.exit(1)
