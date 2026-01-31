# Example: Gibbs Free Energy
Calculate Gibbs free energy via temperature integration.
## Command
```bash
macer md -p POSCAR --ff emt --dim 2 2 2 --gibbs --temp 50 --temp-end 150 --temp-step 50 --nsteps 50 --equil-steps 10 --output-dir output
```
