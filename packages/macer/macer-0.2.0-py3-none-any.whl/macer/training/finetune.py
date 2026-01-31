# -*- coding: utf-8 -*-
# Copyright (c) 2025 The Macer Package Authors
# Adapted from MatterSim (MIT License), Copyright (c) Microsoft Corporation.

import argparse
import os
import pickle as pkl
import random
import time
import sys

import numpy as np
import torch
import torch.distributed
import torch.nn as nn
from ase.units import GPa
from torch.utils.data import DataLoader
from torchmetrics import MeanMetric
from torch.optim.lr_scheduler import ReduceLROnPlateau

from mattersim.datasets.utils.build import build_dataloader
from mattersim.forcefield.m3gnet.scaling import AtomScaling
from mattersim.forcefield.potential import Potential, batch_to_dict
from mattersim.utils.atoms_utils import AtomsAdaptor
from mattersim.utils.logger_utils import get_logger

logger = get_logger()
try:
    local_rank = int(os.environ["LOCAL_RANK"])
except KeyError:
    local_rank = 0

def train_custom_loop(
    potential,
    dataloader,
    val_dataloader,
    loss_fn=torch.nn.HuberLoss(delta=0.01),
    include_energy=True,
    include_forces=False,
    include_stresses=False,
    force_loss_ratio=1.0,
    stress_loss_ratio=0.1,
    epochs=100,
    early_stop_patience=10,
    mae_energy_threshold=None,
    mae_force_threshold=None,
    mae_stress_threshold=None,
    metric_name="val_loss",
    wandb=None,
    save_checkpoint=False,
    save_path="./results/",
    ckpt_interval=10,
    is_distributed=False,
    need_to_load_data=False,
    **kwargs,
):
    """
    Custom training loop adapted from MatterSim Potential.train_model
    Adds support for absolute MAE threshold stopping.
    """
    device = potential.device
    potential.idx = ["val_loss", "val_mae_e", "val_mae_f", "val_mae_s"].index(metric_name)
    
    if is_distributed:
        potential.rank = torch.distributed.get_rank()
    
    logger.info(
        f"Number of trainable parameters: {sum(p.numel() for p in potential.model.parameters() if p.requires_grad):,}"
    )

    # Initialize best metric
    if potential.best_metric > 1000: # Reset if it's default initial high value
        potential.best_metric = float('inf')
        potential.best_metric_epoch = 0

    for epoch in range(potential.last_epoch + 1, epochs):
        logger.info(f"Epoch: {epoch} / {epochs}")
        
        # Training Phase
        if need_to_load_data:
            # Logic for loading data from pickle (omitted for simplicity as we use pre-loaded dataloader mostly)
             raise NotImplementedError("need_to_load_data=True is not fully implemented in custom loop yet.")
        else:
            metric = potential.train_one_epoch(
                dataloader,
                epoch,
                loss_fn,
                include_energy,
                include_forces,
                include_stresses,
                force_loss_ratio,
                stress_loss_ratio,
                wandb,
                is_distributed,
                mode="train",
                **kwargs,
            )
        
        # Validation Phase
        if val_dataloader is not None:
            metric_val = potential.train_one_epoch(
                val_dataloader,
                epoch,
                loss_fn,
                include_energy,
                include_forces,
                include_stresses,
                force_loss_ratio,
                stress_loss_ratio,
                wandb,
                is_distributed,
                mode="val",
                **kwargs,
            )
            # Use validation metrics for stopping/saving
            current_metrics = metric_val
        else:
            # Use training metrics if no validation set
            current_metrics = metric
        
        # Unpack metrics: (loss_avg, e_mae, f_mae, s_mae)
        curr_loss, curr_mae_e, curr_mae_f, curr_mae_s = current_metrics

        # Scheduler Step
        if isinstance(potential.scheduler, ReduceLROnPlateau):
            potential.scheduler.step(curr_loss)
        else:
            potential.scheduler.step()

        potential.last_epoch = epoch
        potential.validation_metrics = {
            "loss": curr_loss,
            "MAE_energy": curr_mae_e,
            "MAE_force": curr_mae_f,
            "MAE_stress": curr_mae_s,
        }

        # --- Custom Stopping Logic: Absolute Thresholds ---
        stop_by_threshold = False
        thresholds_met = []
        
        if mae_energy_threshold is not None:
            if curr_mae_e <= mae_energy_threshold:
                thresholds_met.append("Energy")
        
        if mae_force_threshold is not None and include_forces:
             if curr_mae_f <= mae_force_threshold:
                thresholds_met.append("Force")
        
        if mae_stress_threshold is not None and include_stresses:
             if curr_mae_s <= mae_stress_threshold:
                thresholds_met.append("Stress")

        # Check if ALL active thresholds are met
        # We only check conditions that were explicitly set by the user (not None)
        active_conditions = 0
        met_conditions = 0
        
        if mae_energy_threshold is not None:
            active_conditions += 1
            if curr_mae_e <= mae_energy_threshold: met_conditions += 1
            
        if mae_force_threshold is not None:
            active_conditions += 1
            if include_forces and curr_mae_f <= mae_force_threshold: met_conditions += 1
            elif not include_forces: met_conditions += 1 # Ignore force threshold if force training disabled? Or fail? Let's assume ignore or satisfied.

        if mae_stress_threshold is not None:
            active_conditions += 1
            if include_stresses and curr_mae_s <= mae_stress_threshold: met_conditions += 1

        if active_conditions > 0 and met_conditions == active_conditions:
             logger.info(f"Stopping early: Reached target thresholds! ({', '.join(thresholds_met)})")
             stop_by_threshold = True

        # Save Model Logic (Original)
        if is_distributed:
            # DDP Saving logic
             if potential.save_model_ddp(
                epoch,
                early_stop_patience,
                save_path,
                metric_name,
                save_checkpoint,
                current_metrics,
                ckpt_interval,
            ):
                logger.info("Early stopping (Patience)")
                break
        else:
            # Single GPU/CPU Saving logic
            if potential.save_model(
                epoch,
                early_stop_patience,
                save_path,
                metric_name,
                save_checkpoint,
                current_metrics,
                ckpt_interval,
            ):
                logger.info("Early stopping (Patience)")
                break

        if stop_by_threshold:
            # Save the final model as best_threshold_model just in case, or rely on save_model logic
            if save_checkpoint:
                 potential.save(os.path.join(save_path, "best_threshold_model.pth"))
            break

def main(args):
    # Set default dtype
    if args.dtype == "float32":
        torch.set_default_dtype(torch.float32)
        logger.info("Set default dtype to torch.float32")
    elif args.dtype == "float64":
        torch.set_default_dtype(torch.float64)
        logger.info("Set default dtype to torch.float64")

    # DDP Setup
    if args.device == "cuda":
        if not torch.distributed.is_initialized():
             torch.distributed.init_process_group(backend="nccl")
    else:
        if not torch.distributed.is_initialized():
             torch.distributed.init_process_group(backend="gloo")
             
    args_dict = vars(args)
    
    # WandB Setup
    if args.wandb and local_rank == 0:
        wandb_api_key = (
            args.wandb_api_key
            if args.wandb_api_key is not None
            else os.getenv("WANDB_API_KEY")
        )
        wandb.login(key=wandb_api_key)
        wandb.init(
            project=args.wandb_project,
            name=args.run_name,
            config=args,
        )

    if args.wandb:
        args_dict["wandb"] = wandb

    torch.distributed.barrier()

    # Random Seed
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    if args.device == "cuda":
        torch.cuda.set_device(local_rank)

    # Load Training Data
    if args.train_data_path.endswith(".pkl"):
        with open(args.train_data_path, "rb") as f:
            atoms_train = pkl.load(f)
    else:
        atoms_train = AtomsAdaptor.from_file(filename=args.train_data_path)
    
    energies = []
    forces = [] if args.include_forces else None
    stresses = [] if args.include_stresses else None
    
    logger.info("Processing training datasets...")
    for atoms in atoms_train:
        energies.append(atoms.get_potential_energy())
        if args.include_forces:
            forces.append(atoms.get_forces())
        if args.include_stresses:
            stresses.append(atoms.get_stress(voigt=False) / GPa)

    dataloader = build_dataloader(
        atoms_train,
        energies,
        forces,
        stresses,
        shuffle=True,
        pin_memory=(args.device == "cuda"),
        is_distributed=True,
        **args_dict,
    )

    device = args.device
    
    # Normalization
    if args.re_normalize:
        scale = AtomScaling(
            atoms=atoms_train,
            total_energy=energies,
            forces=forces,
            verbose=True,
            **args_dict,
        ).to(device)

    # Load Validation Data
    val_dataloader = None
    if args.valid_data_path is not None:
        if args.valid_data_path.endswith(".pkl"):
            with open(args.valid_data_path, "rb") as f:
                atoms_val = pkl.load(f)
        else:
            atoms_val = AtomsAdaptor.from_file(filename=args.valid_data_path)
        
        val_energies = []
        val_forces = [] if args.include_forces else None
        val_stresses = [] if args.include_stresses else None
        
        logger.info("Processing validation datasets...")
        for atoms in atoms_val:
            val_energies.append(atoms.get_potential_energy())
            if args.include_forces:
                val_forces.append(atoms.get_forces())
            if args.include_stresses:
                val_stresses.append(atoms.get_stress(voigt=False) / GPa)
                
        val_dataloader = build_dataloader(
            atoms_val,
            val_energies,
            val_forces,
            val_stresses,
            pin_memory=(args.device == "cuda"),
            is_distributed=True,
            **args_dict,
        )

    # Load Model
    potential = Potential.from_checkpoint(
        load_path=args.load_model_path,
        load_training_state=False,
        **args_dict,
    )

    # Custom Fine-tuning Logic (MatterSim Approach)
    if args.reset_head:
        reset_predictive_head(potential.model)
    
    if args.reset_head or args.head_lr is not None or args.backbone_lr is not None:
        configure_custom_optimizer(potential, args)

    if args.re_normalize:
        potential.model.set_normalizer(scale)

    if args.device == "cuda":
        potential.model = torch.nn.parallel.DistributedDataParallel(potential.model)
    torch.distributed.barrier()

    # Use Custom Training Loop
    train_custom_loop(
        potential=potential,
        dataloader=dataloader,
        val_dataloader=val_dataloader,
        loss_fn=torch.nn.HuberLoss(delta=0.01),
        is_distributed=True,
        **args_dict,
    )

    if local_rank == 0 and args.save_checkpoint and args.wandb:
        wandb.save(os.path.join(args.save_path, "best_model.pth"))

def reset_predictive_head(model):
    """
    Resets the weights of the 'final' layer in the M3GNet model.
    This corresponds to the 'Predictive Head' mentioned in the MatterSim paper.
    """
    # Handle DDP wrapped model
    if hasattr(model, "module"):
        _model = model.module
    else:
        _model = model

    if hasattr(_model, "final"):
        logger.info("Resetting predictive head (model.final) parameters...")
        for layer in _model.final.modules():
            if hasattr(layer, "reset_parameters"):
                layer.reset_parameters()
    else:
        logger.warning("Could not find 'final' layer to reset. Skipping head reset.")

def configure_custom_optimizer(potential, args):
    """
    Configures optimizer with differential learning rates for Head vs Backbone.
    """
    # Handle DDP wrapped model
    if hasattr(potential.model, "module"):
        _model = potential.model.module
    else:
        _model = potential.model

    if not hasattr(_model, "final"):
        logger.warning("Model does not have 'final' attribute. Falling back to single LR.")
        return

    head_params = list(_model.final.parameters())
    head_ids = list(map(id, head_params))
    backbone_params = [p for p in _model.parameters() if id(p) not in head_ids]
    
    # Defaults based on MatterSim paper if not provided
    head_lr = args.head_lr if args.head_lr is not None else 2e-3
    backbone_lr = args.backbone_lr if args.backbone_lr is not None else 1e-4

    logger.info(f"Configuring Differential LR: Head={head_lr}, Backbone={backbone_lr}")

    optimizer = torch.optim.Adam([
        {'params': backbone_params, 'lr': backbone_lr},
        {'params': head_params, 'lr': head_lr}
    ]) # Note: weight_decay is 0.0 by default in PyTorch, which matches paper's finetuning often

    potential.optimizer = optimizer
    
    # Re-initialize scheduler attached to new optimizer
    # Using ReduceLROnPlateau as it is robust for fine-tuning
    potential.scheduler = ReduceLROnPlateau(
        optimizer, 
        mode='min', 
        factor=0.5, 
        patience=5
    )
    logger.info("Re-initialized Optimizer and Scheduler (ReduceLROnPlateau) for differential learning rates.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    # Path parameters
    parser.add_argument("--run_name", type=str, default="macer_run")
    parser.add_argument("--train_data_path", type=str, required=True)
    parser.add_argument("--valid_data_path", type=str, default=None)
    parser.add_argument("--load_model_path", type=str, default="mattersim-v1.0.0-1m")
    parser.add_argument("--save_path", type=str, default="./results")
    parser.add_argument("--save_checkpoint", action="store_true", default=True)
    parser.add_argument("--ckpt_interval", type=int, default=10)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--dtype", type=str, default="float64", choices=["float32", "float64"])

    # Model parameters
    parser.add_argument("--cutoff", type=float, default=5.0)
    parser.add_argument("--threebody_cutoff", type=float, default=4.0)

    # Training parameters
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--step_size", type=int, default=10)
    parser.add_argument("--include_forces", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include_stresses", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--force_loss_ratio", type=float, default=1.0)
    parser.add_argument("--stress_loss_ratio", type=float, default=0.1)
    parser.add_argument("--early_stop_patience", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)

    # MAE Thresholds (New)
    parser.add_argument("--mae_energy_threshold", type=float, default=None)
    parser.add_argument("--mae_force_threshold", type=float, default=None)
    parser.add_argument("--mae_stress_threshold", type=float, default=None)
    
    # Advanced Fine-tuning (New)
    parser.add_argument("--reset_head", action="store_true", help="Reset predictive head weights")
    parser.add_argument("--head_lr", type=float, default=None, help="Learning rate for predictive head")
    parser.add_argument("--backbone_lr", type=float, default=None, help="Learning rate for backbone")

    # Scaling
    parser.add_argument("--re_normalize", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--scale_key", type=str, default="per_species_forces_rms")
    parser.add_argument("--shift_key", type=str, default="per_species_energy_mean_linear_reg")
    parser.add_argument("--init_scale", type=float, default=None)
    parser.add_argument("--init_shift", type=float, default=None)
    parser.add_argument("--trainable_scale", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--trainable_shift", action=argparse.BooleanOptionalAction, default=False)

    # WandB
    parser.add_argument("--wandb", action="store_true")
    parser.add_argument("--wandb_api_key", type=str, default=None)
    parser.add_argument("--wandb_project", type=str, default="wandb_test")

    args = parser.parse_args()
    main(args)

