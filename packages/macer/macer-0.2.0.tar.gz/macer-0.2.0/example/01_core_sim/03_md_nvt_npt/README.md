# Example: Molecular Dynamics (NVT/NPT)
Perform NVT and NPT simulations.
## Command
```bash
macer md -p POSCAR --ff emt --dim 2 2 2 --ensemble nvt --temp 300 --nsteps 50 --output-dir nvt_output
macer md -p POSCAR --ff emt --dim 2 2 2 --ensemble npt --temp 300 --press 0.0 --nsteps 50 --output-dir npt_output
```
