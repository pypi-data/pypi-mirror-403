# Example: Dataset Management
Building and splitting datasets from simulation outputs.
## Command
```bash
# Generate data first
macer relax -p POSCAR --ff emt --fmax 0.1 --output-dir verif_relax
macer phonopy qha -p POSCAR --ff emt --dim 2 2 2 --num-volumes 3 --tmax 300 --output-dir verif_qha

# Run dataset utils
macer util ds build -i verif_relax/*.xml verif_qha/vasprun*.xml -o dataset.xyz
macer util ds split -i dataset.xyz --ratio 0.8 0.1 0.1
```
