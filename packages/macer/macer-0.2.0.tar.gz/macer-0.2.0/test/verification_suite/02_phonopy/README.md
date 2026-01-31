# Macer Verification: Phonopy Workflows

This part covers Phonon Band (PB), Symmetry Refine (SR), Quasi-Harmonic Approximation (QHA), SSCHA, Thermal Conductivity (TC), and Finite Temperature (FT).

## Commands

### 2.1. Phonon Band (PB)
```bash
macer phonopy pb -p POSCAR --ff emt --dim 2 2 2 --dos --write-arrow --output-dir verif_pb
```

### 2.2. Symmetry Refine (SR)
```bash
macer phonopy sr -p POSCAR --ff emt --tolerance 0.01 --output-dir verif_sr
```

### 2.3. QHA
```bash
macer phonopy qha -p POSCAR --ff emt --dim 2 2 2 --num-volumes 4 --tmax 500 --output-dir verif_qha
```

### 2.4. SSCHA
```bash
macer phonopy sscha -p POSCAR --ff emt --dim 2 2 2 -T 300 --max-iter 2 --output-dir verif_sscha
```

### 2.5. Thermal Conductivity (TC)
```bash
macer phonopy tc -p POSCAR --ff emt --dim 2 2 2 --mesh 3 3 3 --no-save-hdf5 --output-dir verif_tc
```

### 2.6. Finite Temperature (FT)
```bash
macer phonopy ft -p POSCAR --ff emt -T 300 --dim 2 2 2 --md-steps 50 --output-dir verif_ft
```

## Running the Verification
```bash
bash run_phonopy.sh
```
