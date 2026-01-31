#!/bin/bash
set -e

echo ">>> [02_phonopy] Starting Phonopy Workflow Verification..."

# 2.1. Phonon Band (PB)
echo "  [2.1] Phonon Band (PB)..."
macer phonopy pb -p POSCAR --ff emt --dim 2 2 2 --dos --write-arrow --output-dir verif_pb

# 2.2. Symmetry Refine (SR)
echo "  [2.2] Symmetry Refine (SR)..."
macer phonopy sr -p POSCAR --ff emt --tolerance 0.01 --output-dir verif_sr

# 2.3. QHA
echo "  [2.3] QHA..."
macer phonopy qha -p POSCAR --ff emt --dim 2 2 2 --num-volumes 4 --tmax 500 --output-dir verif_qha

# 2.4. SSCHA
echo "  [2.4] SSCHA..."
macer phonopy sscha -p POSCAR --ff emt --dim 2 2 2 -T 300 --max-iter 2 --output-dir verif_sscha

# 2.5. Thermal Conductivity (TC)
echo "  [2.5] Thermal Conductivity (TC)..."
if command -v phono3py &> /dev/null; then
    macer phonopy tc -p POSCAR --ff emt --dim 2 2 2 --mesh 3 3 3 --no-save-hdf5 --output-dir verif_tc
else
    echo "  [2.5] Skip TC (phono3py not found)"
fi

# 2.6. Finite Temperature (FT)
echo "  [2.6] Finite Temperature (FT)..."
macer phonopy ft -p POSCAR --ff emt -T 300 --dim 2 2 2 --md-steps 50 --output-dir verif_ft

echo ">>> [02_phonopy] Verification Complete."