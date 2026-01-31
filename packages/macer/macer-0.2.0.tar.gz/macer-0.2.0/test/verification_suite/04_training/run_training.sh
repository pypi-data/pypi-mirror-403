#!/bin/bash
set -e

echo ">>> [04_training] Starting MLFF Training Verification..."

# Generate data for training
echo "  Generating test data via relaxation and QHA..."
macer relax -p POSCAR --ff emt --fmax 0.1 --output-dir verif_relax
macer phonopy qha -p POSCAR --ff emt --dim 2 2 2 --num-volumes 3 --tmax 300 --output-dir verif_qha

# 4.1. Dataset Build & Split
echo "  [4.1] Dataset Build & Split..."
rm -rf dataset.xyz train.xyz valid.xyz test.xyz
macer util ds build -i verif_relax/*.xml verif_qha/vasprun*.xml -o dataset.xyz
macer util ds split -i dataset.xyz --ratio 0.4 0.3 0.3

# 4.2. Fine-tuning
echo "  [4.2] Fine-tuning (1 epoch)..."
if macer util model list | grep -q "mattersim"; then
    macer util ft -d train.xyz --valid-data valid.xyz --epochs 1 --batch-size 2 --model-name finetuned_test.pth --device cpu --no-stresses
else
    echo "  [4.2] Skip Fine-tuning (mattersim not found for training test)"
fi

# 4.3. Evaluation
echo "  [4.3] Evaluation..."
if [ -f "mlff_results/finetuned_test.pth" ]; then
    macer util eval -d test.xyz --ff mattersim --model mlff_results/finetuned_test.pth
else
    echo "  [4.3] Skip Evaluation (no trained model found)"
fi

echo ">>> [04_training] Verification Complete."