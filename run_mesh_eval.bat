@echo off
call conda activate esim
python mesh_eval_pipeline.py --gt gt.stl --rm mod.stl --out output