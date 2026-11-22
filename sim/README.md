# Simulation Scripts

These scripts build and run my tests in Verilator: the module testbenches, the
Cocotb register-file test, the smoke programs and the ISA-lite tests. What each
test checks is in [verification](../docs/verification.md).

## Common Commands

```bash
bash sim/run_regression.sh      # module tests, smoke programs and the Cocotb runner
bash sim/run_isa_lite.sh        # the 19 default rv32ui tests
bash sim/run_isa_lite.sh ori    # one rv32ui test
```

The regression needs the [Cocotb environment](#cocotb-regfile) active, and it
stops at the first runner that fails.

## Script Groups

| Scripts | What they run |
| --- | --- |
| `run_control_unit.sh`, `run_imm_ext.sh`, `run_alu_op.sh` | Decode and datapath module tests |
| `run_pc_target_gen.sh`, `run_hazard_unit.sh` | Redirect and hazard-control module tests |
| `run_reg_file.sh`, `run_data_mem.sh` | Storage module tests |
| `run_reg_file_cocotb.sh` | The Cocotb register-file test, once per stimulus seed |
| `run_basic_smoke.sh`, `run_smoke_*.sh` | Smoke programs on the whole core |
| `run_isa_lite.sh` | The selected upstream `rv32ui` tests |
| `run_regression.sh` | Everything above except ISA-lite |

Integrated processor tests compile the RTL through
[`rtl/filelist.f`](../rtl/filelist.f), whose paths start at the repository
root. Module tests list only the files they need. When I move a source file, I
update both the filelist and any module test that names it directly.

## Cocotb Regfile

Besides Verilator and a C++ compiler, the test needs GNU Make and Cocotb 2.x.
I run it with Cocotb 2.1.0 and Verilator 5.046. The Makefile asks
`cocotb-config` where Cocotb's makefiles are, so activate the Python
environment first. With a virtual environment in `.venv/`, which Git ignores:

```bash
source .venv/bin/activate
bash sim/run_reg_file_cocotb.sh
```

The runner calls `make sim` once per stimulus seed, in the order `1`, `42`,
`2026`, and stops at the first failure. To replay one seed from the
repository root:

```bash
RF_SEED=42 make -C tb/cocotb/reg_file sim
```

Only `RF_SEED` affects this test. It seeds the test's own `random.Random`,
defaults to `2026` and shows up in the log as `Stimulus seed=...`. The
`Seeding Python random module with ...` line comes from Cocotb, which takes
that seed from the current time unless `COCOTB_RANDOM_SEED` is set. The test
never draws from the global `random` module. Assertion messages in the random
loops start with `seed=... cycle=...`, so a failure already names the seed to
replay.

Build output and `results.xml` go to `sim/build/cocotb_reg_file/`. Each
`make sim` rewrites `results.xml`, so after a full batch it only describes the
seed `2026` run. Its `random_seed` property is Cocotb's seed, not `RF_SEED`.

Cocotb only rebuilds the Verilator model when a listed source is newer than
the build. If you point `VERILOG_SOURCES` at another file, such as a mutated
RTL copy, run `make -C tb/cocotb/reg_file clean` after switching back.

## Waveforms

Tracing is off by default. `TRACE=1` turns on Verilator tracing and the
testbench's `$dumpfile`/`$dumpvars` block, `TRACE=0` turns it off, and any
other value is rejected.

```bash
TRACE=1 bash sim/run_data_mem.sh
gtkwave sim/build/data_mem/data_mem_tb.vcd
```

Each runner prints the VCD path and saves the file in its own
`sim/build/<test>/` folder next to `obj_dir/`. The basic and hazard smokes
write `sim/build/basic_smoke/basic_smoke.vcd` and
`sim/build/smoke_hazard/hazard_smoke.vcd`.

The same switch works for the whole regression, where the Cocotb step ignores
it, and for ISA-lite. ISA-lite writes one VCD per case, so trace only the case
you're debugging.

```bash
TRACE=1 bash sim/run_regression.sh
TRACE=1 bash sim/run_isa_lite.sh ori
gtkwave sim/build/riscv_lite/verilator/ori/rv32ui_ori.vcd
```

A run without tracing leaves old VCD files in place, so a VCD on disk doesn't
mean the last run wrote it.

[`trace.sh`](trace.sh) adds the compile flag and passes the output path as
`+trace=<path>`. Each testbench has a `waveform_dump` block inside
`` `ifdef TRACE_VCD ``. A new test should follow the same pattern and call
`run_verilator` and `run_simulation` from its runner.

## Building Programs

```bash
bash sim/build_hex.sh programs/asm/smoke_basic.s programs/hex/smoke_basic.hex
bash sim/build_hex.sh <main.s> <output.hex> <extra.s> ...   # several sources, one image
```

Without an output argument, `build_hex.sh` writes
`programs/hex/<source-name>.hex`. My assembly sources live in `programs/asm/`,
and the shared trap handler stays in `software/runtime/`.

```text
assembly sources
  -> riscv64-elf-gcc (rv32i_zicsr, my linker script)
  -> ELF, plus dump and map files
  -> objcopy writes Verilog hex for .text and .trap
  -> $readmemh loads instr_mem
```

[`core.ld`](../software/linker/core.ld) puts `.text` at `0x00000000` and
`.trap` at the next aligned address after it. My notes on GCC, ld, the linker
script, objcopy, objdump and Verilator are in
[docs/tool-chain-notes](../docs/tool-chain-notes/).

## Generated Files

| Path | Contents |
| --- | --- |
| `programs/asm/` | My hand-written assembly sources |
| `programs/hex/` | Instruction images of those programs, tracked in Git |
| `programs/hex/riscv_lite/` | Generated ISA-lite images, ignored by Git |
| `sim/build/programs/` | Preprocessed assembly, ELF, dump and map files for my programs |
| `sim/build/<test>/obj_dir/` | Verilator's C++ and the simulation executables |
| `sim/build/<test>/*.vcd` | Waveforms from `TRACE=1` |
| `sim/build/cocotb_reg_file/` | The Cocotb Verilator build and the last run's `results.xml` |
| `sim/build/riscv_lite/` | ISA-lite ELF, dump and Verilator output |
| `sim/build/riscv_lite/verilator/<case>/rv32ui_<case>.vcd` | Per-case ISA-lite waveforms from `TRACE=1` |

Everything under `sim/build/` is ignored and can be regenerated. Edit the
assembly sources, never the generated images.

## Two Build Paths

- `sim/build_hex.sh` builds my smoke and trap programs. It uses my linker
  script and keeps `.text` and `.trap` at separate addresses.
- `software/scripts/build_riscv_lite_test.sh` builds the ISA-lite tests. It
  links at address 0 and copies one continuous run of instruction words out of
  the dump, with no trap or data sections.

A change to one of them doesn't carry over to the other.
