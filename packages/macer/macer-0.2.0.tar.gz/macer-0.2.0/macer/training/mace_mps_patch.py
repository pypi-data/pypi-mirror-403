import torch
import sys
import os

# --- MPS Compatibility Patch ---
# MACE internally calls .double() which fails on MPS.
# We monkey-patch torch.Tensor.double to return float32 if the tensor is on MPS.
orig_double = torch.Tensor.double

def mps_safe_double(self):
    if self.device.type == 'mps':
        # Return float32 instead of crashing on MPS
        return self.float()
    return orig_double(self)

torch.Tensor.double = mps_safe_double
# Also patch to() for explicit double conversions
orig_to = torch.Tensor.to
def mps_safe_to(self, *args, **kwargs):
    if 'dtype' in kwargs and kwargs['dtype'] == torch.float64 and self.device.type == 'mps':
        kwargs['dtype'] = torch.float32
    if len(args) > 0 and args[0] == torch.float64 and self.device.type == 'mps':
        args = (torch.float32,) + args[1:]
    return orig_to(self, *args, **kwargs)
torch.Tensor.to = mps_safe_to

print("INFO: Applied MPS float64 -> float32 monkey-patch for MACE.")

# --- Execute MACE ---
# We try to import from the path provided in the environment or fallback to standard
try:
    # Use the module name passed via arguments
    module_name = sys.argv[1]
    import importlib
    mace_cli = importlib.import_module(module_name)
    # Remove the wrapper-specific argument before passing to MACE
    sys.argv.pop(1)
    mace_cli.main()
except Exception as e:
    print(f"ERROR in MPS Wrapper: {e}")
    sys.exit(1)
