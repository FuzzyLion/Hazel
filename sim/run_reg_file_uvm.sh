#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$SCRIPT_DIR/trace.sh"
SIM_BUILD_DIR="$SCRIPT_DIR/build/reg_file_uvm"

cd "$REPO_ROOT"

mkdir -p "$SIM_BUILD_DIR"

uvm_src="$PWD/tools/uvm-core-2020.3.1/src"

run_verilator --binary --timing -j 2 -Wno-fatal \
  -Wno-DECLFILENAME -Wno-TIMESCALEMOD -Wno-UNUSEDSIGNAL -Wno-UNUSEDPARAM \
  --timescale-override 1ns/1ps \
  --top-module regfile_top \
  --Mdir "$SIM_BUILD_DIR/obj_dir" \
  -o regfile_top \
  -f tb/uvm/reg_file/filelist.f

sim_bin="$SIM_BUILD_DIR/obj_dir/regfile_top"

run_simulation "$SIM_BUILD_DIR/regfile_top.vcd" "$sim_bin"

# for seed in 1 42 2026; do
#    printf '\n=== seed %s ===\n' "$seed"
#    "$sim_bin" "+verilator+seed+$seed"
# done
