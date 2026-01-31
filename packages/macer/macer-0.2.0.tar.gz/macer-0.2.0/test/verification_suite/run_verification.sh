#!/bin/bash
# Macer Verification Runner
# This script executes all verification steps described in README.md

# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================================"
echo "   Macer (v0.1.14) Verification Suite"
echo "========================================================"

# Check for POSCAR
if [ ! -f "POSCAR" ]; then
    echo "Error: POSCAR not found in current directory."
    exit 1
fi

echo -e "\n>>> 1. Core Simulation"
echo "  [1.1] Relaxation & Bulk Modulus..."
macer relax -p POSCAR --ff mattersim --fmax 0.1 --output-dir verif_relax
macer relax -p POSCAR --ff mattersim --bulk-modulus --strain 0.02 --n-points 5

echo "  [1.2] Molecular Dynamics (NVT/NPT)..."
macer md -p POSCAR --ff mattersim --ensemble nvt --temp 300 --nsteps 50 --save-every 10 --output-dir verif_md
macer md -p POSCAR --ff mattersim --ensemble npt --temp 300 --press 0.0 --nsteps 20 --output-dir verif_md_npt

echo "  [1.3] Gibbs Free Energy..."
macer md -p POSCAR --ff mattersim --gibbs --temp 50 --temp-end 150 --temp-step 50 --nsteps 50 --equil-steps 10 --output-dir verif_gibbs

echo -e "\n>>> 2. Phonopy Workflows"
echo "  [2.1] Phonon Band (PB)..."
macer phonopy pb -p POSCAR --ff mattersim --dim 2 2 2 --dos --write-arrow --output-dir verif_pb

echo "  [2.2] Symmetry Refine (SR)..."
macer phonopy sr -p POSCAR --ff mattersim --tolerance 0.01 --output-dir verif_sr

echo "  [2.3] QHA..."
macer phonopy qha -p POSCAR --ff mattersim --dim 2 2 2 --num-volumes 4 --tmax 500 --output-dir verif_qha

echo "  [2.4] SSCHA..."
macer phonopy sscha -p POSCAR --ff mattersim --dim 2 2 2 -T 300 --max-iter 2 --output-dir verif_sscha

echo "  [2.5] Thermal Conductivity (TC)..."
macer phonopy tc -p POSCAR --ff mattersim --dim 2 2 2 --mesh 3 3 3 --no-save-hdf5 --output-dir verif_tc

echo "  [2.6] Finite Temperature (FT)..."
macer phonopy ft -p POSCAR --ff mattersim -T 300 --dim 2 2 2 --md-steps 50 --output-dir verif_ft

echo -e "\n>>> 3. Utilities"
echo "  [3.1] MD Utils..."
macer util md summary -i verif_md/md.csv
macer util md traj2xdatcar -i verif_md/md.traj -o verif_md/XDATCAR_util
macer util md plot -i verif_md/md.csv -o verif_md/plot_util
macer util md cell -i verif_md/md.traj -o verif_md/cell_util
macer util md rdf -i verif_md/md.traj -o verif_md/rdf_util --rmax 1.9

echo "  [3.2] Struct & Model..."
macer util struct vasp4to5 -i POSCAR -o POSCAR_v5
macer util model list

# Dynaphopy Wrapper...
macer dynaphopy POSCAR verif_md/XDATCAR -q 0 0 0 -pd --silent

echo -e "\n>>> 4. MLFF Training & Dataset"
echo "  [4.1] Dataset Build & Split..."
# Clean up previous results
rm -rf mlff_results dataset.xyz train.xyz valid.xyz test.xyz

# Use vasprun.xml from relax and qha steps (using wildcards)
macer util ds build -i verif_relax/*.xml verif_qha/*.xml -o dataset.xyz
macer util ds split -i dataset.xyz --ratio 0.4 0.3 0.3

echo "  [4.2] Fine-tuning (1 epoch)..."
macer util ft -d train.xyz --valid-data valid.xyz --epochs 1 --batch-size 2 --model-name finetuned_test.pth --device cpu --no-stresses

echo "  [4.3] Evaluation..."
macer util eval -d test.xyz --ff mattersim --model mlff_results/finetuned_test.pth

echo -e "\n========================================================"
echo "   Verification Complete! All tests passed."
echo "========================================================"
