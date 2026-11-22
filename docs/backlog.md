# Backlog

## Traps and the Timer

- Make `mtime` readable through MMIO, with a safe way to read the 64-bit value
  on RV32, then add a test for repeated ticks. For a slower tick I'd use a
  clock enable or a prescaler instead of a second clock.
- Add software and external interrupts to `mip` and `mie`, with a clear
  priority between sources. Exceptions still go ahead of every interrupt.
- Decide when an interrupt counts as accepted during stalls, memory waits,
  cache misses and `wfi`. For `wfi` the boundary can't depend on a valid
  instruction in EX.
- Add vectored `mtvec` once something needs it. Direct mode is enough for my
  handler.
- Define a real trap frame (stack, saved registers, nested traps, recovery
  rules) before the trap handler turns into a general runtime.

## Verification

- Load ELF data sections, or a separate data-memory image, so the upstream
  load/store tests can run.
- Make instruction memory bigger or configurable per testbench, or write small
  local programs for the upstream R-type tests that don't fit yet.
- Broaden trap coverage: unsupported CSR access through the other CSR forms,
  more exception and timer collisions, and more older side effects in flight.

## Extensions

- RISC-V cryptographic accelerator
