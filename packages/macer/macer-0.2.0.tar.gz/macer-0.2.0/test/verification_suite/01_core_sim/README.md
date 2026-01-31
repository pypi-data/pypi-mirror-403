# Macer Verification: Core Simulation

This part covers iterative structure optimization, Equation of State (EOS) fitting, and Molecular Dynamics (NVT/NPT/Gibbs).

## Commands

### 1.1. Relaxation & Bulk Modulus
```bash
macer relax -p POSCAR --ff emt --fmax 0.1 --output-dir verif_relax
macer relax -p POSCAR --ff emt --bulk-modulus --strain 0.02 --n-points 5
```

### 1.2. Molecular Dynamics (MD)
```bash
macer md -p POSCAR --ff emt --ensemble nvt --temp 300 --nsteps 50 --save-every 10 --output-dir verif_md
macer md -p POSCAR --ff emt --ensemble npt --temp 300 --press 0.0 --nsteps 20 --output-dir verif_md_npt
```

### 1.3. Gibbs Free Energy
```bash
macer md -p POSCAR --ff emt --gibbs --temp 50 --temp-end 150 --temp-step 50 --nsteps 50 --equil-steps 10 --output-dir verif_gibbs
```

## Running the Verification
```bash
bash run_core_sim.sh
```
