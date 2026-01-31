#!/bin/bash
macer md -p POSCAR --ff emt --dim 2 2 2 --temp 300 --nsteps 100 --output-dir md_output
macer util md traj2xdatcar -i md_output/md.traj -o md_output/XDATCAR
macer dynaphopy POSCAR md_output/XDATCAR -q 0 0 0 -pd --silent
