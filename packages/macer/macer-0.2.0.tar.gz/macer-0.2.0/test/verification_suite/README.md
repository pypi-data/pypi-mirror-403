# Macer Verification Suite

This directory contains a complete verification suite for `macer` (v0.1.14). It covers Core Simulations, Phonopy Workflows, and Utility commands using the `mattersim` force field (or others if specified).

## Prerequisites
- **Macer installed**: Ensure `macer` is in your PATH.
- **Force Field**: The examples use `mattersim`. Ensure it is installed or replace with another supported FF (e.g. `mace`, `sevennet`).
- **Input**: A `POSCAR` file is required (provided in this directory).

## How to Run
You can run the provided script to execute all verification steps sequentially:
```bash
bash run_verification.sh
```
Or run individual commands as detailed below.

---

## 1. Core Simulation

### 1.1. Relaxation & Bulk Modulus
Iterative structure optimization and Equation of State (EOS) fitting.

**Command:**
```bash
macer relax -p POSCAR --ff mattersim --fmax 0.1 --output-dir verif_relax
macer relax -p POSCAR --ff mattersim --bulk-modulus --strain 0.02 --n-points 5
```
**Expected Output:**
- `verif_relax/CONTCAR-final`: Relaxed structure.
- `bulk_modulus-POSCAR.log`: Calculated Bulk Modulus (e.g., ~82 GPa).
- `eos_fit_birchmurnaghan.pdf`: EOS plot.

### 1.2. Molecular Dynamics (MD)
NVT and NPT simulations.

**Command:**
```bash
macer md -p POSCAR --ff mattersim --ensemble nvt --temp 300 --nsteps 50 --save-every 10 --output-dir verif_md
macer md -p POSCAR --ff mattersim --ensemble npt --temp 300 --press 0.0 --nsteps 20 --output-dir verif_md_npt
```
**Expected Output:**
- `verif_md/md.traj`, `verif_md/md.csv`: Trajectory and log data.
- `md_thermo.pdf`, `md_rdf.pdf`: Auto-generated analysis plots.
- `verif_md_npt/XDATCAR`: Variable cell trajectory.

### 1.3. Gibbs Free Energy
Thermodynamic integration workflow.

**Command:**
```bash
macer md -p POSCAR --ff mattersim --gibbs --temp 50 --temp-end 150 --temp-step 50 --nsteps 50 --equil-steps 10 --output-dir verif_gibbs
```
**Expected Output:**
- `verif_gibbs/gibbs_results.csv`: Free energy values (G_abs, Delta_G).
- `gibbs.log`: Integration details.

---

## 2. Phonopy Workflows

### 2.1. Phonon Band (PB)
Phonon dispersion and DOS.

**Command:**
```bash
macer phonopy pb -p POSCAR --ff mattersim --dim 2 2 2 --dos --write-arrow --output-dir verif_pb
```
**Expected Output:**
- `verif_pb/band.pdf`: Phonon band structure.
- `verif_pb/phonon_dos.pdf`: Phonon DOS.
- `verif_pb/ARROW-POSCAR/`: VESTA files for visualization.

### 2.2. Symmetry Refine (SR)
Iterative symmetrization.

**Command:**
```bash
macer phonopy sr -p POSCAR --ff mattersim --tolerance 0.01 --output-dir verif_sr
```
**Expected Output:**
- `verif_sr/CONTCAR-symmetrized`: Symmetrized structure.

### 2.3. Quasi-Harmonic Approximation (QHA)
Thermal expansion calculation.

**Command:**
```bash
macer phonopy qha -p POSCAR --ff mattersim --dim 2 2 2 --num-volumes 4 --tmax 500 --output-dir verif_qha
```
**Expected Output:**
- `verif_qha/helmholtz-volume.pdf`: Free energy vs Volume curves.
- `verif_qha/thermal_expansion-temperature.dat`: CTE data.

### 2.4. SSCHA (Anharmonicity)
Self-consistent phonon calculation.

**Command:**
```bash
macer phonopy sscha -p POSCAR --ff mattersim --dim 2 2 2 -T 300 --max-iter 2 --output-dir verif_sscha
```
**Expected Output:**
- `verif_sscha/sscha_convergence.pdf`: Convergence plot.
- `verif_sscha/FORCE_CONSTANTS_SSCHA_final`: Renormalized force constants.

### 2.5. Thermal Conductivity (TC)
Phono3py workflow (requires phono3py installed).

**Command:**
```bash
macer phonopy tc -p POSCAR --ff mattersim --dim 2 2 2 --mesh 3 3 3 --no-save-hdf5 --output-dir verif_tc
```
**Expected Output:**
- `verif_tc/kappa_vs_temperature.pdf`: Thermal conductivity plot.

### 2.6. Finite Temperature (FT - Dynaphopy)
Dynaphopy integration for temperature-dependent phonons.

**Command:**
```bash
macer phonopy ft -p POSCAR --ff mattersim -T 300 --dim 2 2 2 --md-steps 50 --output-dir verif_ft
```
**Expected Output:**
- `verif_ft/band_comparison.pdf`: Comparison of 0K vs 300K bands.
- `verif_ft/power_spectrum_comparison.pdf`: Power spectrum visualization.

---

## 3. Utilities

**Command:**
```bash
# MD Analysis
macer util md summary -i verif_md/md.csv
macer util md traj2xdatcar -i verif_md/md.traj -o verif_md/XDATCAR_util
macer util md plot -i verif_md/md.csv -o verif_md/plot_util
macer util md cell -i verif_md/md.traj -o verif_md/cell_util
macer util md rdf -i verif_md/md.traj -o verif_md/rdf_util --rmax 1.9

# Structure & Model
macer util struct vasp4to5 -i POSCAR -o POSCAR_v5
macer util model list

# Dynaphopy Wrapper
macer dynaphopy POSCAR verif_md/XDATCAR -q 0 0 0 -pd --silent

---

## 4. MLFF Training & Dataset Utilities

These tests verify the machine learning workflow: creating datasets from simulation outputs and fine-tuning models.

### 4.1. Dataset Management
Builds an Extended XYZ dataset from VASP outputs (generated in previous steps).

**Command:**
```bash
# Build dataset from relaxation outputs
macer util ds build -i verif_relax/*.xml verif_qha/vasprun*.xml -o dataset.xyz

# Split into train/valid/test
macer util ds split -i dataset.xyz --ratio 0.8 0.1 0.1
```
**Expected Output:**
- `dataset.xyz`: Merged dataset.
- `train.xyz`, `valid.xyz`, `test.xyz`: Split datasets.

### 4.2. Fine-tuning (MatterSim)
Runs a minimal fine-tuning session (1 epoch) to verify the training loop.

**Command:**
```bash
macer util ft -d train.xyz --valid-data valid.xyz --epochs 1 --batch-size 2 --model-name finetuned_test.pth --device cpu
```
**Expected Output:**
- `mlff_results/finetuned_test.pth`: Trained model checkpoint.
- Training logs printed to stdout.

### 4.3. Evaluation
Evaluates the fine-tuned model.

**Command:**
```bash
macer util eval -d test.xyz --ff mattersim --model mlff_results/finetuned_test.pth
```
**Expected Output:**
- MAE metrics and parity plots (if data sufficient).
```
