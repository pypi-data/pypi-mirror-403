"""
Macer: Machine-learning accelerated Atomic Computational Environment for automated Research workflows
Copyright (c) 2025 The Macer Package Authors
Author: Soungmin Bae <soungminbae@gmail.com>
License: MIT
"""

__version__ = "0.2.0"
__author__ = "Soungmin Bae"
__email__ = "soungminbae@gmail.com"

# Apply runtime patches for external dependencies
try:
    from macer.utils.fix_dynaphopy import apply_dynaphopy_patch
    apply_dynaphopy_patch()
except ImportError:
    pass
