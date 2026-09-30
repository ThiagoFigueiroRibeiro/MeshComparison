@echo off
call conda activate esim
python percept_eval_pipeline.py --gt gt.stl --rm mod.stl --out output