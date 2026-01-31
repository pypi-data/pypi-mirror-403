# Macer Verification: Training & Dataset

This part covers dataset construction from simulation outputs and the machine learning fine-tuning workflow.

## Commands

### 4.1. Dataset Management
```bash
macer util ds build -i verif_relax/*.xml verif_qha/vasprun*.xml -o dataset.xyz
macer util ds split -i dataset.xyz --ratio 0.4 0.3 0.3
```

### 4.2. Fine-tuning
```bash
macer util ft -d train.xyz --valid-data valid.xyz --epochs 1 --batch-size 2 --model-name finetuned_test.pth --device cpu --no-stresses
```

### 4.3. Evaluation
```bash
macer util eval -d test.xyz --ff mattersim --model mlff_results/finetuned_test.pth
```

## Running the Verification
```bash
bash run_training.sh
```
