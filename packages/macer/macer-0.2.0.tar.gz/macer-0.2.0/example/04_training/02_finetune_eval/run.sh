#!/bin/bash
macer util ds split -i converted-from-ML_AB.xyz --ratio 0.5 0.5 0.0
macer util ft -d train.xyz --valid-data valid.xyz --epochs 1 --batch-size 2 --model-name finetuned.pth --device cpu --no-stresses
macer util eval -d valid.xyz --ff mattersim --model mlff_results/finetuned.pth
