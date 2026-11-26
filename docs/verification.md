# Verification

I verify Hazel in Verilator with directed SystemVerilog testbenches at two
levels: module tests that drive one block, and smoke programs that run through
the whole pipeline. On top of that, 19 upstream `rv32ui` tests run in a small
local environment I call ISA-lite, and the register file has one Cocotb test
that I wrote to learn Cocotb. Together they show that the cases I wrote behave
as intended. They don't prove full RV32I or privileged-spec compliance, and
[Known Gaps](#known-gaps) lists what I know is missing.

## Two Levels of Tests

Module tests drive one block through its ports, so a failure points at one
signal or rule. Smoke programs run real instruction streams through the
integrated core and check registers and memory at the end. They find what
module tests can't see, such as forwarding, pipeline-register fields, redirect
flushing, writeback selection and how neighboring instructions interact.

When a smoke failure exposes a local bug, I also add a module check for it.
The register-file bypass bug went that way. The hazard smoke caught it, and
afterwards `reg_file_tb` got `test_bypass`.

## What the Regression Runs

`sim/run_regression.sh` runs 20 entries: seven module tests, twelve smoke
programs and one Cocotb runner. The [simulation guide](../sim/README.md) has
the commands and output paths.

### Module Tests

| Testbench | What it checks |
| --- | --- |
| `control_unit_tb.sv` | The control bundle for every implemented instruction, `uses_rs1_D` and `uses_rs2_D`, `ecall`, `ebreak`, `mret`, all six CSR forms, and unsupported encodings such as a bad funct3, a bad funct7 or a malformed `mret` |
| `imm_ext_tb.sv` | I, S, B, J and U immediates and the default case |
| `alu_op_tb.sv` | Every ALU operation with edge cases, both outcomes of all six branches, and the load/store alignment flags |
| `pc_target_gen_tb.sv` | PC-relative and JALR targets, JALR bit-0 clearing, redirect decisions, `mret`, and misaligned targets, which only trap when taken |
| `reg_file_tb.sv` | Reset, synchronous write, combinational reads, x0 and the WB bypass |
| `data_mem_tb.sv` | Synchronous write, combinational read, write disable, byte lanes and word indexing |
| `hazard_unit_tb.sv` | Forwarding sources and their priority, CSR forwarding, load-use stalls, ignored source fields, redirect and trap flushes, and that invalid stages never forward or stall |

### Smoke Programs

| Program | What it checks |
| --- | --- |
| `smoke_basic` | `addi`, `add`, `sw`, `lw` and `auipc` with NOPs between them, so no hazards |
| `smoke_branch` | A taken `beq` flushes the two wrong-path instructions |
| `smoke_alu` | Immediate ALU instructions and both outcomes of all six branches, with a completion code in `x31` |
| `smoke_hazard` | MEM and WB forwarding, the register-file bypass, a store, and a `lw` straight into `jalr` |
| `smoke_csr_trap` | All six CSR forms with old-value writeback and pure reads, two `ebreak` sites, one `ecall`, handler register preservation, `mepc` and `mret` |
| `smoke_illegal_trap`, `smoke_instr_misaligned_trap`, `smoke_load_misaligned_trap`, `smoke_store_misaligned_trap` | One precise exception each |
| `smoke_unsupported_csr_trap` | `csrrw` to the unsupported CSR `0x7c0`, with interrupts on and no timer request |
| `smoke_sync_exception_timer_priority` | The same fault while the timer is pending and enabled |
| `smoke_timer_interrupt` | Timer programming through MMIO, enable gating, delivery, one-shot acknowledgement and `mret` re-execution |

The `lw` into `jalr` case in `smoke_hazard` loads a code address from data RAM
and jumps to it right away. Its testbench requires exactly one load-use stall
with IF and ID held and a bubble in EX, the loaded target, the link address,
an untouched wrong-path marker and a reached target marker. That checks
decode, the stall, WB forwarding of the load result and the JALR redirect
together for this one sequence.

### How the Trap Smokes Check Precision

The four precise-exception smokes share one pattern. A marker before the
faulting instruction must commit, the faulting instruction must have no side
effect, and a marker after it must be flushed. The testbenches also check the
trap data in `mcause`, `mepc` and `mtval`.

`smoke_unsupported_csr_trap` and `smoke_sync_exception_timer_priority` both
fault on `csrrw s3, 0x7c0, t4`. Both require cause 2, the faulting PC in
`mepc`, the instruction bits in `mtval`, the trap redirect, D/E/M flushing, an
unchanged `s3`, an older committed marker, a flushed younger marker and the
fatal handler's signature.

The priority test builds a real collision. It programs a deadline of 80
through MMIO, waits for `mip.MTIP` with global interrupts off, enables
`mie.MTIE`, and puts the `mstatus.MIE` write right before the faulting
`csrrw`. Since CSRs update in EX, MIE turns on just as the `csrrw` enters EX. A
monitor on the rising edge requires MTIP, MTIE and MIE to be set when the trap
is accepted, and it records that MTIP was pending before the enables. The test
also checks the selected and latched trap data, which shows the exception
winning over the pending timer. The timer stays pending, with its deadline
unchanged in the fatal handler. Neither test forces internal signals. If CSR
writes ever move out of EX, the priority test needs a new setup.

### Cocotb Regfile Checks

I used the register file to learn Cocotb, and that exercise is complete.
[`test_reg_file.py`](../tb/cocotb/reg_file/test_reg_file.py) has a directed
part and a model-based part.

The directed part checks reset, synchronous write, both combinational read
ports, the read-side WB bypass with write enable on and off, and that x0 reads
0 while a write to x0 is active. The reset-priority case asserts reset and a
write to x7 in the same cycle. Before the edge, a read of x7 already returns
the WB value, because the bypass path does not look at reset. After the edge,
with writes off, x7 reads 0, so reset won over the write.

The model-based part checks the read ports against
[`RegFileModel`](../tb/cocotb/reg_file/reg_file_model.py), first with a few
fixed values and then with seeded random stimulus. Like the RTL, the model
keeps the storage update (`on_rising_edge`) apart from the combinational read
with x0 masking and bypass (`read`). A uniform loop randomizes write enable,
`rd`, both read addresses, and 32-bit data for 100 cycles. A biased loop keeps
writes on with `rd` between 1 and 31 for another 100 cycles and picks one of
four modes per cycle, so that neither port, only rs1, only rs2, or both ports
read the register being written. In every random cycle, both ports are checked
against `read` after the inputs settle, and the model is updated only at the
rising edge. After each loop, writes go off and both ports read back all 32
registers.

The biased loop also prints how often each mode was picked. No check reads
that count. It only shows what the generator chose and isn't an independent
functional-coverage check.

To make sure the test can fail, I pointed the Makefile at a temporary copy of
`reg_file.sv` with the x0 mask removed from both read ports. The directed x0
check failed with expected 0, actual 50. In that check `rd` is 0 and write
enable is high, so without the mask the bypass forwards the WB value 50 to x0.
This was a one-off manual check on 2026-11-20. The copy is not in the
repository, and the Makefile points at the original RTL again.

I'll only bring Cocotb to other modules when randomized memory latency, large
test matrices or a golden-memory model for the cache make the extra Python
flow worth it. Commands, dependencies, seed replay and output paths are in the
[simulation guide](../sim/README.md#cocotb-regfile).

### Stage Hierarchy and Observation Paths

Processor testbenches instantiate `top` as `dut`, and `top` instantiates
`core` as `core_processor`. The stage modules add one level below `core`.
These are the paths I use most:

| What I look at | Path from `dut.core_processor` |
| --- | --- |
| Register file, including the ISA-lite `x31` result | `id_stage1.reg_file1.regs[...]` |
| Data RAM | `mem_stage1.data_mem1.mem[...]` |
| Timer deadline | `mem_stage1.machine_timer1.mtimecmp` |
| Saved trap CSRs | `ex_stage1.csr_file1.mcause_reg`, `.mepc_reg`, `.mtval_reg` |
| Trap selection and the E-to-M kill | `ex_stage1.trap_entry_E`, `.trap_mcause_E`, `.trap_flush_M` |
| Fetch PC | `if_stage1.pc_F_out` |

Cross-stage bundles and controls such as `data_E_idex`, `ctrl_E`,
`hazard_stallflush_ctrl`, `trap_flush_D/E` and `timer_irq` are still visible
in `core`. I pick the stage port or internal path that matches the block I'm
checking. A deeper path doesn't make a test prove more.

When I split the core into stage modules on 2026-10-28, the leaf modules and
all test stimulus, assertions and expected values stayed the same. Thirteen
processor testbenches only changed their observation paths.

## ISA-Lite

`sim/run_isa_lite.sh` runs 19 upstream `rv32ui` tests: `addi`, `slti`,
`sltiu`, `andi`, `ori`, `xori`, `slli`, `srli`, `srai`, `lui`, `auipc`, `jal`,
`jalr`, `beq`, `bne`, `blt`, `bge`, `bltu` and `bgeu`. The upstream
environment expects trap vectors, `ecall` and `tohost`, which my core doesn't
fully support. So I wrote a small replacement in
`software/tests/riscv_lite/env/riscv_test.h` that keeps the upstream macro
names and reports the result in `x31`. The
[riscv_lite README](../software/tests/riscv_lite/README.md) explains the
macros and the `x31` codes.

```text
upstream rv32ui/*.S
  + local riscv_lite/riscv_test.h
  + upstream scalar macros
  -> riscv64-elf-gcc (assemble and link)
  -> ELF
  -> riscv64-elf-objdump
  -> awk pulls out the instruction words
  -> programs/hex/riscv_lite/*.hex
  -> $readmemh loads instr_mem
  -> the pipeline runs the program
  -> x31 reports pass or fail
```

Most `rv32ui` tests are thin wrappers around shared `rv64ui` bodies. That's
how upstream organizes them, and `-march=rv32i -mabi=ilp32` makes the macros
pick RV32 behavior.

A test goes into the default set only if it builds with my environment, fits
in the 256-word instruction memory, needs no initialized data memory or
official privileged environment, and I've seen it pass on the current
pipeline. The runner stops with an error when a test needs more than 256
instruction words. A test can't pass just because part of it was cut off.

## Debugging an ISA-Lite Failure

When `bash sim/run_isa_lite.sh ori` fails, the problem isn't automatically in
ORI decode or the ALU. An integrated test can fail anywhere from decode to
writeback, or because of the program image or the test environment. Work
through it in this order.

1. Read `x31`. If it's odd and greater than 1, the failing test number is
   `(x31 - 1) / 2`.
2. Open the dump under `sim/build/riscv_lite/` and the source under
   `tools/riscv-tests/isa/rv32ui/`.
3. Find the macro or instruction sequence for that test number.
4. Cut it down to the smallest local smoke program that still fails.
5. Match the symptom to a layer.
   - A wrong value from an isolated `ori` with stable operands points at
     `control_unit`, `imm_ext`, `alu_op` or writeback selection.
   - A failure only when a source was written by one of the previous two
     instructions points at forwarding or the load-use stall.
   - If a branch decides the failure path, check the branch compare, target
     generation and redirect flushing.
   - If `x31` never changes and the test times out, check program loading,
     reset and the PC, and jump loops.
   - An impossible test number means something overwrote `x3`. The
     environment keeps `TESTNUM` in `gp` (`x3`), an ordinary register, so a
     test that writes `x3` or a CPU bug that writes the wrong destination
     corrupts the reported number.
   - If the source needs data memory, traps, CSRs or `ecall`, count it as an
     environment mismatch. The core may be fine.
6. After the fix, run the focused test and the full regression.

The dump shows the failing instruction stream, not the root cause. For signal
timing, rerun with `TRACE=1 bash sim/run_isa_lite.sh ori`, which writes
`sim/build/riscv_lite/verilator/ori/rv32ui_ori.vcd`.

## Directed Testbench Style

I write directed SystemVerilog tests for readability, even when a
parameterized version would be shorter. Each task covers one instruction or
one behavior:

```systemverilog
task automatic test_example_instr();
    apply_instr_defaults();

    instr_D = 32'hXXXXXXXX; // assembly instruction
    #1;

    check_ctrl_bundle("example control bundle", EXPECTED_CTRL);
    check_imm_src("example immediate source", EXPECTED_IMM);
endtask
```

Reusable check tasks go at the bottom of the testbench. I don't hide stimulus
inside generic helpers. Each test shows its default step, its inputs, the
propagation delay and its checks. A failed check stops with `$fatal(1, ...)`,
and a passing test ends with `$finish`. Waveforms from `TRACE=1` are only for
looking at timing. Pass or fail always comes from the checks.

## Run Log

The last runs I recorded:

| Date | What I ran | Result |
| --- | --- | --- |
| 2026-10-28 | After the stage split: integrated Verilator lint, the 19 directed tests and the 19 default ISA-lite tests | All passed, with no Verilator warnings or errors |
| 2026-11-20 | The Cocotb regfile test with seeds 1, 42 and 2026, then the full regression | Both passed |
| 2026-11-21 | The 19 default ISA-lite tests | All passed |
| 2026-11-26 | The full regression after upgrading Verilator from 5.046 to 5.054 and deleting `sim/build` | All passed |

## Known Gaps

- The upstream load/store tests (`lb`, `lw`, `sb`, `sw` and the rest) don't
  run, because the flow loads only instruction words and skips the ELF data
  sections.
- `add` and the other upstream R-type tests don't fit in 256 instruction
  words. My programs only run `add`, `sub`, `and` and `or` in register form,
  so `sll`, `srl`, `sra`, `slt`, `sltu` and `xor` only have module-level
  checks.
- The upstream misaligned-access tests need the official trap environment,
  and `fence_i` only matters once there's an instruction cache.
- Trap coverage is directed. Unsupported CSR access is only tested through
  `csrrw`, there is one exception and timer collision, and older instructions
  with side effects in flight are only covered by the cases above.
- There is no memory wait yet, and no test covers stalls from slow memory.
- There is no periodic timer test, since software can't read `mtime` yet.
- The Cocotb test only covers the register file through its ports. Its three
  seeds with 200 random cycles each are only a sample of the input space.
- The check after the stage split reran the existing tests through the new
  hierarchy. It isn't a formal equivalence check.
