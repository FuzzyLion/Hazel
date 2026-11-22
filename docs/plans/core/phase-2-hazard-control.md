# Phase 2: Hazard Unit and Control Closure

## Time Limit

Recommended: 1 to 1.5 weeks
Hard limit: 2 weeks

## Goal

I want the pipeline to handle common data and control hazards correctly, with one stable set of priority rules.

## Key Decisions

1. Branches are resolved in `EX`, so the flush range follows that choice.
2. The baseline keeps the internal memories with fixed timing. Variable-latency memory waits and pipeline holds wait for Phase 5.
3. The first load-use implementation follows the textbook approach: hold Fetch and Decode, clear the Execute pipeline register, and insert one bubble into EX.

## Detailed Tasks

### Task 1: Handle Data Hazards

1. Implement the forwarding paths.
2. Implement the load-use stall.

### Task 2: Handle Control Hazards

1. Implement flushes caused by branches and jumps.
2. Align the flush rules with redirect behavior in `EX`.

### Task 3: Memory-Wait Stalls (Moved to Phase 5)

1. Add pipeline hold control for memory waits.
2. Keep a data-hazard stall distinct from a memory-wait stall.

### Task 4: Unify the Priority Rules

1. Define one priority order for redirects and load-use stalls. Traps joined it in Phase 4, and memory waits join it in Phase 5.
2. Keep hazard control in its own module.

## Current Rules

The rules as they're implemented now, including the trap case that Phase 4 added, are in [core architecture](../../core-architecture.md#hazards-and-redirects).

## Tests to Add Early

1. Focused, hand-written tests for RAW hazards, load-use hazards, and branches
2. Basic `RV32I` cases from `riscv-tests`
3. Branch cases that prove wrong-path instructions are flushed

## Deliverables

1. Hazard Unit RTL
2. Hazard-control rule table
3. Focused test suite
4. Basic `riscv-tests` integration notes
5. Control-priority timing notes

## Verification Requirements

1. Forwarding selections are correct.
2. Bubble insertion and stall behavior are correct.
3. Wrong-path instructions are flushed correctly.
4. Pipeline holds and exactly-once memory side effects under request/response waits get proven in Phase 5.

## Risks and Notes

1. Many bugs come from priority conflicts, not forwarding itself.
2. If `memory_wait` semantics are unclear now, Cache integration will expose the same problems again.
3. Start replacing some hand-written examples with `riscv-tests` during this phase.

## Exit Conditions

1. Common hazard scenarios have a stable, complete control path.
2. The CPU passes a useful set of basic programs and selected `riscv-tests`.
3. The project is ready for structured verification.

## Rule Table

This is the rule table from Phase 2. Phase 4 later added CSR forwarding from MEM and the trap flush.

| Situation | `stall_F` | `stall_D` | `flush_D` | `flush_E` | Forwarding |
| --- | :---: | :---: | :---: | :---: | --- |
| No hazard | 0 | 0 | 0 | 0 | Normal |
| RAW on the ALU result in MEM | 0 | 0 | 0 | 0 | MEM when `rs` matches |
| RAW on the WB result | 0 | 0 | 0 | 0 | WB when `rs` matches |
| Load in EX feeds the instruction in ID | 1 | 1 | 0 | 1 | Normal this cycle |
| Taken branch or jump in EX | 0 | 0 | 1 | 1 | Computed normally |

## Understanding Check

I should be able to answer these from my own RTL and test results.

1. What is the priority order between stall, flush, redirect and memory wait in my design?
2. Why is that priority order correct?
3. How do I tell a load-use hazard from a normal RAW hazard?
4. Which forwarding paths does my RTL have, and why are they enough?
5. What failure would appear if one forwarding path were missing?
