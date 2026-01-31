from typing import Optional
import torch
import numpy as np
from scipy.spatial import KDTree

def radius_graph(
    x: torch.Tensor,
    r: float,
    batch: Optional[torch.Tensor] = None,
    loop: bool = False,
    max_num_neighbors: int = 32,
    flow: str = 'source_to_target',
    num_workers: int = 1,
    batch_size: Optional[int] = None,
) -> torch.Tensor:
    """
    Fallback implementation of torch_cluster.radius_graph using scipy.spatial.KDTree.
    This is used when torch_cluster is not installed (e.g., on some HPC systems).
    """
    try:
        import torch_cluster
        return torch_cluster.radius_graph(
            x=x, r=r, batch=batch, loop=loop, 
            max_num_neighbors=max_num_neighbors, 
            flow=flow, num_workers=num_workers, batch_size=batch_size
        )
    except ImportError:
        pass

    device = x.device
    x_np = x.detach().cpu().numpy()
    
    if batch is None:
        batch = torch.zeros(x.size(0), dtype=torch.long, device=device)
    
    batch_np = batch.detach().cpu().numpy()
    
    row, col = [], []
    for b in np.unique(batch_np):
        idx = np.where(batch_np == b)[0]
        if len(idx) == 0:
            continue
        
        # Build KDTree for the current batch
        tree = KDTree(x_np[idx])
        
        # query_ball_tree returns indices within the current batch slice
        indices = tree.query_ball_tree(tree, r)
        
        for i, neighbors in enumerate(indices):
            count = 0
            for j in neighbors:
                if not loop and i == j:
                    continue
                if count >= max_num_neighbors:
                    break
                
                # row is source, col is target
                if flow == 'source_to_target':
                    row.append(idx[j])
                    col.append(idx[i])
                else:
                    row.append(idx[i])
                    col.append(idx[j])
                count += 1
                
    if not row:
        return torch.empty((2, 0), dtype=torch.long, device=device)
        
    return torch.tensor([row, col], dtype=torch.long, device=device)


def radius(
    x: torch.Tensor,
    y: torch.Tensor,
    r: float,
    batch_x: Optional[torch.Tensor] = None,
    batch_y: Optional[torch.Tensor] = None,
    max_num_neighbors: int = 32,
    num_workers: int = 1,
) -> torch.Tensor:
    """
    Fallback implementation of torch_cluster.radius using scipy.spatial.KDTree.
    """
    try:
        import torch_cluster
        return torch_cluster.radius(
            x=x, y=y, r=r, batch_x=batch_x, batch_y=batch_y, 
            max_num_neighbors=max_num_neighbors, num_workers=num_workers
        )
    except ImportError:
        pass

    device = x.device
    x_np = x.detach().cpu().numpy()
    y_np = y.detach().cpu().numpy()
    
    if batch_x is None:
        batch_x = torch.zeros(x.size(0), dtype=torch.long, device=device)
    if batch_y is None:
        batch_y = torch.zeros(y.size(0), dtype=torch.long, device=device)
        
    batch_x_np = batch_x.detach().cpu().numpy()
    batch_y_np = batch_y.detach().cpu().numpy()
    
    row, col = [], []
    for b in np.unique(batch_y_np):
        idx_x = np.where(batch_x_np == b)[0]
        idx_y = np.where(batch_y_np == b)[0]
        
        if len(idx_x) == 0 or len(idx_y) == 0:
            continue
            
        tree_x = KDTree(x_np[idx_x])
        tree_y = KDTree(y_np[idx_y])
        
        # Find neighbors of y in x
        indices = tree_y.query_ball_tree(tree_x, r)
        
        for i, neighbors in enumerate(indices):
            count = 0
            for j in neighbors:
                if count >= max_num_neighbors:
                    break
                
                # row is index into x, col is index into y
                row.append(idx_x[j])
                col.append(idx_y[i])
                count += 1
                
    if not row:
        return torch.empty((2, 0), dtype=torch.long, device=device)
        
    return torch.tensor([row, col], dtype=torch.long, device=device)
