# Macer Verification: Utilities

This part covers MD analysis utilities, structure management, and the Dynaphopy wrapper.

## Commands

### 3.1. MD Utils
```bash
macer util md summary -i verif_md/md.csv
macer util md traj2xdatcar -i verif_md/md.traj -o verif_md/XDATCAR_util
macer util md plot -i verif_md/md.csv -o verif_md/plot_util
macer util md cell -i verif_md/md.traj -o verif_md/cell_util
macer util md rdf -i verif_md/md.traj -o verif_md/rdf_util --rmax 1.9
```

### 3.2. Struct & Model
```bash
macer util struct vasp4to5 -i POSCAR -o POSCAR_v5
macer util model list
```

### 3.3. Dynaphopy Wrapper
```bash
macer dynaphopy POSCAR verif_md/XDATCAR -q 0 0 0 -pd --silent
```

## Running the Verification
```bash
bash run_utils.sh
```
