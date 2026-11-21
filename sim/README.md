# Simulation Scripts

This directory contains the build and execution scripts for directed
SystemVerilog tests, the Cocotb Regfile test, processor smoke programs, and
the selected ISA-lite test flow.

## Documentation

Use the following documents as the source of truth for each topic:

- [Project overview and current status](../README.md)
- [Core architecture](../docs/core-architecture.md)
- [Verification strategy and test boundaries](../docs/verification.md)
- [GCC notes](../docs/tool-chain-notes/gcc.md)
- [GNU ld notes](../docs/tool-chain-notes/ld.md)
- [Linker script notes](../docs/tool-chain-notes/linker.md)
- [objcopy notes](../docs/tool-chain-notes/objcopy.md)
- [objdump notes](../docs/tool-chain-notes/objdump.md)
- [Verilator notes](../docs/tool-chain-notes/verilator.md)
- [ISA-lite test environment](../software/tests/riscv_lite/README.md)

This README is only an operational entry point. Detailed tool options,
verification rationale, failure analysis, and architectural claims belong in
the linked documents.

## Common Commands

Run the complete regression with the [Cocotb environment](#cocotb-regfile)
active:

```bash
bash sim/run_regression.sh
```

Run the selected ISA-lite tests:

```bash
bash sim/run_isa_lite.sh
```

Run one ISA-lite test:

```bash
bash sim/run_isa_lite.sh ori
```

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
`2026`, and stops at the first failure. `run_regression.sh` calls the same
runner. To replay one seed from the repository root:

```bash
RF_SEED=42 make -C tb/cocotb/reg_file sim
```

Each log shows two seeds, and only `RF_SEED` affects this test. It seeds the
test's own `random.Random` instance, defaults to `2026`, and appears as
`Stimulus seed=...`. The startup line
`Seeding Python random module with ...` comes from Cocotb. Cocotb takes that
seed from the current time unless `COCOTB_RANDOM_SEED` is set, and the test
never draws from the global `random` module. Assertion messages in the random
loops start with `seed=... cycle=...`, so a failure already names the seed to
replay.

Build output and `results.xml` go to `sim/build/cocotb_reg_file/`. `make sim`
deletes and rewrites `results.xml` on every run, so after a full batch it only
describes the seed `2026` run. Its `random_seed` property is Cocotb's seed,
not `RF_SEED`.

Cocotb rebuilds the Verilator model only when a listed source is newer than
the build. If you point `VERILOG_SOURCES` at another file, such as a mutated
RTL copy, run `make -C tb/cocotb/reg_file clean` after switching back.
Otherwise the model built from that file can stay in use.

## Waveforms

The directed SystemVerilog testbenches support optional VCD output. By default,
their runners compile and run without tracing. Set `TRACE=1` to enable both
Verilator tracing and the testbench's `$dumpfile` / `$dumpvars` block:

```bash
TRACE=1 bash sim/run_data_mem.sh
gtkwave sim/build/data_mem/data_mem_tb.vcd
```

The runner prints the absolute VCD path and saves the file in its own
`sim/build/<test>/` directory, alongside `obj_dir/`. In particular, Basic and
Hazard smoke waveforms are `sim/build/basic_smoke/basic_smoke.vcd` and
`sim/build/smoke_hazard/hazard_smoke.vcd`.

The same switch applies to the complete regression, where the Cocotb step
ignores it, and to selected ISA-lite cases:

```bash
TRACE=1 bash sim/run_regression.sh
TRACE=1 bash sim/run_isa_lite.sh ori
gtkwave sim/build/riscv_lite/verilator/ori/rv32ui_ori.vcd
```

ISA-lite saves a separate VCD for each case. Prefer selecting the case being
debugged rather than exporting the entire batch. `TRACE=0` explicitly disables
tracing; other values are rejected. A run without tracing leaves existing VCD
files untouched, so their presence alone does not prove the latest run exported
a waveform.

The shared [`trace.sh`](trace.sh) helper controls compilation and passes the
output path as `+trace=<absolute-path>`. Each testbench keeps an explicit
`waveform_dump` block guarded by `TRACE_VCD`, which is defined only for tracing
builds. When adding a test, follow this pattern and call `run_verilator` and
`run_simulation` from its runner.

## Building Programs

Build one local assembly program:

```bash
bash sim/build_hex.sh \
  programs/asm/smoke_basic.s \
  programs/hex/smoke_basic.hex
```

If the output argument is omitted, `build_hex.sh` writes
`programs/hex/<source-basename>.hex`. Keep local assembly sources in
`programs/asm/`; the shared trap handler remains in `software/runtime/`.

Build an image from multiple assembly sources:

```bash
bash sim/build_hex.sh \
  <primary-source.s> \
  <output.hex> \
  <additional-source.s> ...
```

## Script Groups

| Scripts | Purpose |
| --- | --- |
| `run_control_unit.sh`, `run_imm_ext.sh`, `run_alu_op.sh` | Focused combinational control and datapath tests |
| `run_pc_target_gen.sh`, `run_hazard_unit.sh` | Redirect and hazard-control tests |
| `run_reg_file.sh`, `run_data_mem.sh` | Focused sequential storage tests |
| `run_reg_file_cocotb.sh` | Cocotb Regfile test, once per stimulus seed |
| `run_basic_smoke.sh`, `run_smoke_*.sh` | Integrated processor smoke programs |
| `run_isa_lite.sh` | Selected upstream RV32UI tests |
| `run_regression.sh` | Unified regression entry point, including the Cocotb runner |

Integrated processor tests compile the RTL through
[`rtl/filelist.f`](../rtl/filelist.f), whose paths are relative to the repository
root. Module tests list only the packages and modules they need. When moving a
source file, update both the RTL filelist and any direct module-test references.

## Program Build Flow

`build_hex.sh` converts local assembly sources into an instruction-memory
image:

```text
assembly sources
  -> RISC-V GCC, assembler, and linker
  -> ELF
  -> dump and map reports
  -> objcopy Verilog hex
  -> $readmemh
  -> instr_mem
```

The local build uses [`software/linker/core.ld`](../software/linker/core.ld) to
place `.text` at byte address `0x00000000` and `.trap` at the next aligned
address after `.text`. See the linker, `ld`, `objcopy`, and `objdump` notes
above for the details of this flow.

## Generated Files

Instruction images are grouped under `programs/hex/`; intermediate compiler
and simulator output stays under the ignored `sim/build/` directory:

| Path | Contents |
| --- | --- |
| `programs/asm/` | Local hand-written assembly sources |
| `programs/hex/` | Local program instruction images |
| `programs/hex/riscv_lite/` | Generated upstream ISA-lite instruction images, ignored by Git |
| `sim/build/programs/` | Preprocessed assembly, ELF, dump, and map files for local programs |
| `sim/build/<test>/obj_dir/` | Verilator-generated C++ and simulation executables |
| `sim/build/<test>/*.vcd` | Directed-test waveforms generated with `TRACE=1` |
| `sim/build/cocotb_reg_file/` | Cocotb Verilator build and the last run's `results.xml` |
| `sim/build/riscv_lite/` | ISA-lite ELF, dump, and Verilator output |
| `sim/build/riscv_lite/verilator/<case>/rv32ui_<case>.vcd` | Per-case ISA-lite waveforms generated with `TRACE=1` |

HEX images and intermediate output can be regenerated from the assembly
sources. Edit assembly sources, not generated instruction images. The local
HEX images remain tracked; ISA-lite images and intermediate output are ignored.

## Build-Path Boundary

The repository currently has two related but separate program build paths:

- `sim/build_hex.sh` builds local smoke and Phase 4 trap programs. It uses the
  project linker script and preserves non-contiguous `.text` and `.trap`
  addresses.
- `software/scripts/build_riscv_lite_test.sh` builds the selected ISA-lite
  tests introduced in Phase 3. It currently handles a continuous executable instruction
  stream and does not load trap or data sections.

Changes to one build path do not automatically apply to the other.
