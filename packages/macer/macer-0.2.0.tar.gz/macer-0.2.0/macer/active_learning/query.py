
import os
import glob
import numpy as np
from typing import List, Tuple
from ase.io import read, write
from ase import Atoms
import torch
import logging

from mattersim.forcefield.potential import Potential, batch_to_dict
from mattersim.datasets.utils.build import build_dataloader

logger = logging.getLogger(__name__)

class EnsembleCalculator:
    """
    Calculates properties using an ensemble of MatterSim models to estimate uncertainty.
    """
    def __init__(self, model_paths: List[str], device: str = "cpu"):
        self.device = device
        self.models = []
        logger.info(f"Loading {len(model_paths)} ensemble models...")
        for path in model_paths:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Model not found: {path}")
            
            # Load model in eval mode
            # Using load_training_state=False to speed up loading (we only need weights)
            model = Potential.from_checkpoint(
                load_path=path, 
                device=device, 
                load_training_state=False
            )
            model.eval()
            self.models.append(model)
        
    def predict(self, atoms_list: List[Atoms], batch_size: int = 4) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predicts forces for a list of atoms and returns the ensemble mean and standard deviation.
        
        Returns:
            mean_forces: (N_structures, N_atoms_max, 3) - Average force
            std_forces: (N_structures, N_atoms_max, 3) - Standard deviation of forces (Uncertainty)
            
        Note: Handling variable atom numbers in a batch is complex for simple array return.
        Here we assume the list contains structures from the same MD trajectory (same N_atoms).
        If N_atoms varies, we process one by one or handle ragging. 
        For MD active learning, usually N_atoms is constant.
        """
        
        # Use one model's args to build dataloader (assuming all models compatible)
        ref_model = self.models[0]
        cutoff = ref_model.model.model_args["cutoff"]
        threebody_cutoff = ref_model.model.model_args["threebody_cutoff"]
        
        # Build dataloader
        # We assume atoms_list fits in memory or batching is handled by caller if huge.
        dataloader = build_dataloader(
            atoms_list,
            model_type=ref_model.model_name,
            cutoff=cutoff,
            threebody_cutoff=threebody_cutoff,
            batch_size=batch_size,
            shuffle=False,
            only_inference=True
        )
        
        all_structure_uncertainties = []
        
        # Iterate over batches
        for batch_idx, graph_batch in enumerate(dataloader):
            graph_batch = graph_batch.to(self.device)
            input_dict = batch_to_dict(graph_batch)
            
            # Collect predictions from all models
            batch_forces_ensemble = [] # Shape: (n_models, n_atoms_in_batch, 3)
            
            # MatterSim forces require gradients w.r.t atom_pos
            input_dict["atom_pos"].requires_grad_(True)
            
            for model in self.models:
                result = model.forward(input_dict, include_forces=True, include_stresses=False)
                batch_forces_ensemble.append(result["forces"].detach().cpu().numpy())
            
            batch_forces_ensemble = np.array(batch_forces_ensemble)
            
            # Calculate STD across models (Axis 0)
            # Shape: (n_atoms_in_batch, 3)
            force_std_per_atom = np.std(batch_forces_ensemble, axis=0)
            
            # Now we need to split back to per-structure
            # num_atoms is a tensor of number of atoms per graph in batch
            num_atoms_list = graph_batch.num_atoms.cpu().tolist()
            
            start_idx = 0
            for n_atoms in num_atoms_list:
                # Get STD for this structure's atoms
                struct_std = force_std_per_atom[start_idx : start_idx + n_atoms]
                
                # Metric: Maximum force deviation on any atom in the structure
                # This is a robust metric for "danger": if any atom is uncertain, the structure is risky.
                # Shape: (n_atoms, 3) -> Norm -> (n_atoms,) -> Max
                atom_std_norms = np.linalg.norm(struct_std, axis=1)
                max_dev = np.max(atom_std_norms)
                
                all_structure_uncertainties.append(max_dev)
                start_idx += n_atoms
                
        return np.array(all_structure_uncertainties)

def query_uncertain_structures(
    traj_path: str,
    model_paths: List[str],
    top_k: int = 10,
    threshold: float = 0.05,
    output_dir: str = "active_learning_selection",
    device: str = "cpu",
    step_interval: int = 1
):
    """
    Selects the most uncertain structures from a trajectory.
    """
    logger.info(f"Reading trajectory: {traj_path}")
    traj = read(traj_path, index=f"::{step_interval}")
    if not isinstance(traj, list):
        traj = [traj]
    
    logger.info(f"Loaded {len(traj)} frames (step interval: {step_interval}).")
    
    ensemble = EnsembleCalculator(model_paths, device=device)
    
    logger.info("Calculating uncertainty (Max Force STD)...")
    uncertainties = ensemble.predict(traj)
    
    # Selection Logic
    # 1. Filter by threshold
    candidates_indices = np.where(uncertainties >= threshold)[0]
    
    if len(candidates_indices) == 0:
        logger.info(f"No structures found with uncertainty > {threshold} eV/A. Model is confident.")
        return
    
    logger.info(f"Found {len(candidates_indices)} structures exceeding threshold {threshold}.")
    
    # 2. Sort by uncertainty (descending)
    sorted_indices = candidates_indices[np.argsort(uncertainties[candidates_indices])[::-1]]
    
    # 3. Select Top-K
    # TODO: Implement 'spacing' logic to avoid picking neighbor frames?
    # For now, simple top-k.
    selected_indices = sorted_indices[:top_k]
    
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Saving top {len(selected_indices)} uncertain structures to {output_dir}...")
    
    for i, idx in enumerate(selected_indices):
        atoms = traj[idx]
        unc_val = uncertainties[idx]
        # Filename includes original index and uncertainty value for reference
        filename = f"POSCAR_frame_{idx:05d}_unc_{unc_val:.4f}.vasp"
        write(os.path.join(output_dir, filename), atoms, format="vasp")
        
    logger.info("Selection complete.")
