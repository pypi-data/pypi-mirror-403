# Example: Fine-tuning & Evaluation
Fine-tuning a model (MatterSim) and evaluating it.
## Command
```bash
# Generate small dataset
macer relax -p POSCAR --ff emt --fmax 0.1 --output-dir verif_relax
macer util ds build -i verif_relax/*.xml -o dataset.xyz
macer util ds split -i dataset.xyz --ratio 0.5 0.5 0.0

# Fine-tune (MatterSim)
macer util ft -d train.xyz --valid-data valid.xyz --epochs 1 --batch-size 2 --model-name finetuned.pth --device cpu --no-stresses

# Evaluate
macer util eval -d valid.xyz --ff mattersim --model mlff_results/finetuned.pth
```
