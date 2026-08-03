#!/bin/bash
set -e

cd /Users/madanibezoui/Documents/Projects/ALUR/code

echo "Wiping old chunks..."
rm -f ../results/protocol/tmp_v2/bench_*.npz

echo "Running chunks..."
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage benchmark --csize 100 --new-run-id
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage benchmark --csize 300
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage benchmark --csize 1000 --crit 3,5,8
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage benchmark --csize 1000 --crit 10,15,20

echo "Finalizing benchmark..."
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage bfinalize

echo "Running other stages..."
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage redundancy
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage probes
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage gates
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage direct
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage stochastic
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage multistakeholder

echo "Generating final report..."
.venv/bin/python run_protocol.py --config configs/full_config.yaml --stage report

echo "Done!"
