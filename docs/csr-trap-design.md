# CSRs, Traps and the Timer

[Phase 4](plans/system/phase-4-csr-exception-interrupt.md) gave Hazel a
working machine-mode trap loop. Software can read and write the CSRs I
implemented, a trap jumps to `mtvec`, the handler reads `mcause` to see what
happened, and `mret` goes back to the program. A one-shot timer interrupt
works too, programmed through a real MMIO store.

I built only what the SoC phase needs, so this covers a small part of the
privileged spec.

## What's There

The core decodes all six Zicsr instructions (`csrrw`, `csrrs`, `csrrc`,
`csrrwi`, `csrrsi` and `csrrci`) plus `ecall`, `ebreak` and `mret`. It has
eight CSRs:

| CSR | Address | What software can write |
| --- | --- | --- |
| `mstatus` | `0x300` | Only `MIE` (bit 3) and `MPIE` (bit 7). `MPP` stays at machine mode |
| `mie` | `0x304` | Only `MTIE` (bit 7) |
| `mtvec` | `0x305` | Bits 31:2. The mode bits are forced to 0, so only Direct mode exists |
| `mscratch` | `0x340` | All bits |
| `mepc` | `0x341` | Bits 31:2. Bits 1:0 always read as 0 |
| `mcause` | `0x342` | All bits |
| `mtval` | `0x343` | All bits |
| `mip` | `0x344` | Nothing. Writes are ignored, and `MTIP` (bit 7) shows the timer request |

All CSRs reset to 0 except `mstatus`, which resets to `0x1800` so that `MPP`
reads as machine mode. A CSR instruction with any other address is an illegal
instruction, even a pure read. I made only the implemented bits writable, so
software can't set up interrupt state the hardware doesn't have.

CSR instructions put the old CSR value in `rd`. `csrrw` and `csrrwi` always
write. `csrrs` and `csrrc` skip the write when `rs1` is `x0`, and `csrrsi` and
`csrrci` skip it when the immediate is 0.

## How the Work Is Split

I split trap handling into four jobs: finding the fault, picking the trap that
wins, updating CSR state and redirecting the PC. Finding the fault happens in
whichever block can see it. The other three jobs have one module each.

| Module | Its job | What it leaves to others |
| --- | --- | --- |
| [control_unit.sv](../rtl/core/control/control_unit.sv) | Decodes CSR and system instructions and flags illegal encodings, `ecall` and `ebreak` | Trap priority and CSR state |
| [pc_target_gen.sv](../rtl/core/datapath/pc_target_gen.sv) | Flags misaligned branch and jump targets | Trap priority and `mepc` |
| [alu_op.sv](../rtl/core/datapath/alu_op.sv) | Flags misaligned loads and stores | Flushing and CSR updates |
| [trap_ctrl.sv](../rtl/core/csr/trap_ctrl.sv) | Picks the winning trap, builds `mcause`, `mtval` and `mepc`, requests the flush | Storing any CSR |
| [csr_file.sv](../rtl/core/csr/csr_file.sv) | Holds CSR state, runs CSR instructions, applies trap entry and `mret`, flags unsupported CSR addresses | Choosing the PC |
| [pc_mux.sv](../rtl/core/datapath/pc_mux.sv) | Puts `mtvec` ahead of branch, jump and `mret` targets | Detecting traps |
| [hazard_unit.sv](../rtl/core/control/hazard_unit.sv) and the pipeline registers | Turn trap and redirect decisions into flushes and bubbles | Trap data |
| [machine_timer.sv](../rtl/peripherals/machine_timer.sv) | Holds `mtime` and `mtimecmp` and raises a level-sensitive timer request | Interrupt enables |
| [mmio_decoder.sv](../rtl/soc/mmio_decoder.sv) | Routes timer stores away from data RAM | Timer state and trap priority |

The main rule is that `trap_ctrl` only reads CSRs and only `csr_file` writes
them. That keeps `csr_file.sv` from becoming a second control unit and
`trap_ctrl.sv` from becoming a hidden CSR bank.

```text
detection in ID and EX
        |
        v
trap_ctrl: cause, trap data, priority
        |
        +--> hazard unit: flush D and E
        +--> EX_MEM: drop the EX instruction
        +--> csr_file: save mepc, mcause, mtval, update mstatus
        +--> pc_mux: PC <- mtvec

handler
        +--> maybe change mepc or acknowledge the timer
        +--> mret: restore mstatus, PC <- mepc
```

`trap_ctrl` and `csr_file` are both inside `ex_stage1`, and `pc_mux` is inside
`if_stage1`. `core.sv` carries the redirect, `mtvec`, `mepc` and the D/E flush
requests between the stages and the hazard unit. The EX-to-MEM kill stays
inside `ex_stage1`, next to `EX_MEM`.

## Where a Trap Is Taken

### EX is the precise boundary

I decide traps in EX, where forwarding, the data address and the branch target
are all ready. On trap entry the instructions in IF and ID are flushed, and
`trap_flush_M` stops the EX instruction from entering MEM. The older
instruction already in MEM isn't touched and finishes normally.

For an exception, the EX instruction is the one that faulted, and it must not
commit. For the timer, the EX instruction is fine but gets squashed anyway.
Its PC goes into `mepc`, and `mret` runs it again. Both cases end the same
way:

```text
older instructions     -> complete once
current EX instruction -> doesn't commit
younger instructions   -> flushed
```

A CSR instruction in EX that traps, or that the timer squashes, also loses its
CSR write, because trap entry has priority inside `csr_file`.

The cost is that an interrupt can only be taken while EX holds a valid
instruction. That's fine while a program runs. A `wfi` or a core that sleeps
would need a boundary that doesn't depend on `valid_E`.

### Exceptions beat the timer

The timer request only counts when `mip.MTIP`, `mie.MTIE` and `mstatus.MIE`
are all set. An exception belongs to the instruction in EX, and the timer has
nothing to do with that instruction. So when both show up in the same cycle,
the exception wins, and the timer request stays pending. The order in
`trap_ctrl.sv` is:

| Priority | Event | `mcause` | `mtval` |
| ---: | --- | --- | --- |
| 1 | Illegal instruction or unsupported CSR | `2` | Instruction bits |
| 2 | `ecall` from machine mode | `11` | `0` |
| 3 | `ebreak` | `3` | `0` |
| 4 | Misaligned branch or jump target | `0` | Target address |
| 5 | Misaligned load | `4` | Load address |
| 6 | Misaligned store | `6` | Store address |
| 7 | Machine-timer interrupt | `0x8000_0007` | `0` |

I ordered the exceptions by asking three questions in turn. Is the instruction
itself legal? If it's a legal branch or jump, is its target legal? If it's a
legal load or store, is its address legal? The timer only gets a turn when
none of them fire.

### A trap beats a redirect

In `pc_mux.sv`, `mtvec` wins over any branch, jump or `mret` target. The
redirect is part of the EX instruction committing, and a trapped instruction
doesn't commit. If the timer is taken while a taken branch sits in EX, the
branch is squashed. After `mret` it runs again from `mepc` and takes the
branch that time.

### Trap entry and flush stay separate signals

Right now one accepted trap drives `trap_entry_E`, `trap_flush_D`,
`trap_flush_E` and `trap_flush_M` together. I could merge them into one wire,
but they mean different things.

- `trap_entry_E` tells the CSRs to record a trap.
- `trap_flush_D` and `trap_flush_E` remove younger work.
- `trap_flush_M` drops the EX instruction before it can do anything in MEM.

Keeping them apart should make memory waits, more execution units and new
interrupt boundaries easier to reason about later.

## CSR Details

### CSR operands use the forwarded value

A CSR instruction can depend on the instruction right before it, just like an
ALU instruction. If I took `rs1` straight from the register file read in ID, I
would skip forwarding and could write a stale value into the CSR. So the CSR
write data comes from the forwarded EX operand.

CSR read results also have their own MEM-to-EX forwarding path. Code after a
CSR read needs no NOPs, and CSRs fit into the hazard rules I already had.

### `mip` is built from hardware

I pass the full 32-bit `mstatus`, `mie` and `mip` into `trap_ctrl.sv`, even
though it only uses three of those bits today. The unused bits are a little
noise, but software, the timer and later interrupt sources all see one
interface.

Software never writes `mip`. `csr_file.sv` builds it from the pending hardware
sources:

```text
mip[3]  <- software interrupt (not yet)
mip[7]  <- timer request
mip[11] <- external interrupt (not yet)
```

### JALR clears bit 0 before the alignment check

RISC-V says JALR clears bit 0 of its target. I do that first and then check
4-byte alignment on the result:

```text
target = (forwarded_rs1 + sign_extended_imm) & 0xFFFF_FFFE
```

A raw sum of `0x101` becomes the legal target `0x100`. A final target of
`0x102` is still misaligned and traps. Clearing bit 0 is part of the JALR
definition and never counts as a fault. The alignment check only runs when a
branch or jump actually redirects. A branch that falls through never traps on
its target.

## Trap Entry and `mret`

Trap entry does this:

```text
mstatus.MPIE <- mstatus.MIE
mstatus.MIE  <- 0
mepc         <- PC of the EX instruction
mcause       <- selected cause
mtval        <- cause-specific value
PC           <- mtvec
```

`mret` does this:

```text
mstatus.MIE  <- mstatus.MPIE
mstatus.MPIE <- 1
PC           <- mepc
```

`mret` leaves `mie` and `mip` alone. `mie` is software's setting, and
`mip.MTIP` shows whether the timer is still asking. The handler has to clear
the request itself by moving `mtimecmp` into the future.

## The Timer

`machine_timer.sv` is a 64-bit counter and a comparator on the core clock:

```text
every clock       -> mtime + 1
mtime >= mtimecmp -> timer_irq is high
```

Reset sets `mtime` to 0 and `mtimecmp` to all ones. The timer stays quiet
until software programs it, using `sw` to two addresses:

```text
0x1000_0000 -> mtimecmp[31:0]
0x1000_0004 -> mtimecmp[63:32]
```

The MMIO decoder keeps those stores out of data RAM.

On RV32 the 64-bit compare value takes three stores: all ones to the low half,
then the new high half, then the new low half. With a plain two-store update,
the comparator could see a half-old, half-new deadline for a cycle and fire
early.

After moving `mtimecmp`, my handler also clears `mie.MTIE`, so the timer fires
only once. I left periodic ticks out because software can't read `mtime` yet.
A periodic handler needs a readable `mtime`, a deadline that software keeps
track of, or a hardware reload. That work belongs with the SoC and the
runtime.

## The Handler

[trap_handler.s](../software/runtime/trap_handler.s) is a small teaching
runtime. It swaps `t0` with `mscratch` to get the scratch area that the
program set up in data memory, saves `t1`, `t2` and `t3`, and dispatches on
`mcause` with one branch per supported cause. Anything else goes to
`fatal_trap`. It isn't ABI-safe, and it can't survive a trap inside itself.

Hardware always saves the PC of the EX instruction. What the handler does
with it depends on the cause.

- For `ecall` and `ebreak`, it adds 4 to `mepc`, so `mret` continues after the
  trap instruction.
- For the timer, it leaves `mepc` alone, so the squashed instruction runs
  again.
- Illegal instructions and misaligned accesses go to `fatal_trap`, which sets
  `x31` to 2 and stops. I don't pretend to recover from them.

`ecall` and `ebreak` keep different causes, even though my handler resumes
both the same way. This isn't debugger support. There's no Debug Module,
`dpc`, `dcsr` or `dret`.

The `.trap` section has no fixed address. The linker places it after `.text`,
and each program's startup code loads the `trap_handler` address into `mtvec`.

`x31` is only a signal between my test programs and their testbenches, and
each pair agrees on what a nonzero value means. The real trap record is
`mcause`, `mepc` and `mtval`.

## How I Tested It

The trap tests run as part of `sim/run_regression.sh`. Module tests check the
local rules, and smoke programs run the whole loop through real instructions.

| What | Where |
| --- | --- |
| CSR decode | All six CSR forms, `ecall`, `ebreak`, `mret` and illegal system encodings in `control_unit_tb.sv` |
| Hazards | CSR result forwarding, trap flush priority, load-use stalls and redirects in `hazard_unit_tb.sv` |
| JALR and target alignment | Bit-0 clearing and taken-target alignment in `pc_target_gen_tb.sv` |
| CSR and trap flow | Old-value writeback, pure reads, two `ebreak` sites, one `ecall`, handler register preservation, `mepc` and `mret` in [smoke_csr_trap.s](../programs/asm/smoke_csr_trap.s) |
| Precise exceptions | One smoke each for an illegal instruction and a misaligned target, load and store |
| Unsupported CSR and priority | A `csrrw` to an unsupported CSR, once alone and once with a pending, enabled timer |
| Timer | MMIO programming, enable gating, cause `0x8000_0007`, flushing, one-shot acknowledgement and `mret` re-execution in [smoke_timer_interrupt.s](../programs/asm/smoke_timer_interrupt.s) |

The precise-exception smokes check more than `mcause`. Each one also checks
that a younger instruction was flushed and that the faulting instruction had
no side effect. The `jal` doesn't write `ra`, the load doesn't overwrite `a0`,
and the store doesn't change memory. [Verification](verification.md) has the
details and the gaps.
