@echo off
call conda activate meshEval
python mesh_eval_pipeline.py --gt gt.stl --rm mod.stl --out output