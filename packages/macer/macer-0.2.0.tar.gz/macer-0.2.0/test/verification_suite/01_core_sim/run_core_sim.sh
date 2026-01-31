#!/bin/bash
set -e

echo ">>> [01_core_sim] Starting Core Simulation Verification..."

# 1.1. Relaxation & Bulk Modulus
echo "  [1.1] Relaxation & Bulk Modulus..."
macer relax -p POSCAR --ff emt --fmax 0.1 --output-dir verif_relax
macer relax -p POSCAR --ff emt --bulk-modulus --strain 0.02 --n-points 5

# 1.2. Molecular Dynamics (NVT/NPT)
echo "  [1.2] Molecular Dynamics (NVT/NPT)..."
macer md -p POSCAR --ff emt --dim 2 2 2 --ensemble nvt --temp 300 --nsteps 50 --save-every 10 --output-dir verif_md
macer md -p POSCAR --ff emt --dim 2 2 2 --ensemble npt --temp 300 --press 0.0 --nsteps 20 --output-dir verif_md_npt

# 1.3. Gibbs Free Energy
echo "  [1.3] Gibbs Free Energy..."
macer md -p POSCAR --ff emt --dim 2 2 2 --gibbs --temp 50 --temp-end 150 --temp-step 50 --nsteps 50 --equil-steps 10 --output-dir verif_gibbs

echo ">>> [01_core_sim] Verification Complete."