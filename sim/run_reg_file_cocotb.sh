#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT/tb/cocotb/reg_file"

for rf_seed in 1 42 2026; do
    RF_SEED="$rf_seed" make sim
done
