# Phase 1: Five-Stage Pipeline Core

## Time Limit

Recommended: 1 to 2 weeks
Hard limit: 2.5 weeks

## Goal

I want the main pipeline to run simple, hazard-free programs before the full hazard unit exists.

## Key Constraints

1. This phase does not need to solve every hazard.
2. The priority is to get the main datapath and cross-stage control flow right.
3. The completed Phase 1 baseline uses internal memories. The request/response interface originally targeted in Phase 0 is deferred to Phase 5.

## Detailed Tasks

### Task 1: Implement the Basic Modules

1. Implement the `pc`, `regfile`, `alu`, immediate generator, and basic controller.
2. Give every module a clear input and output interface.

### Task 2: Build the Five-Stage Pipeline Skeleton

1. Implement the IF, ID, EX, MEM, and WB stages.
2. Connect the PC, register file, ALU, immediate generator, and basic controller.
3. Add the pipeline registers between stages.
4. Make sure control signals move through the pipeline in step with their instruction.

### Task 3: Implement Basic Control-Flow Behavior

1. Resolve branches and generate branch targets in `EX`.
2. Implement the basic jump paths for `jal` and `jalr`.
3. Support flush and redirect in the simplest cases.

### Task 4: Close the Minimum Program-Execution Loop

1. Fetch instructions from an initialized image.
2. Run sequential programs without complex dependencies.
3. Verify basic Load/Store behavior.

## First-Priority Instruction Support

1. Basic integer arithmetic
2. Load/Store
3. `jal` and `jalr`
4. Basic branches

## Deliverables

1. First version of the CPU top-level RTL
2. RTL for the basic modules
3. Simple smoke-test programs
4. Initial waveform captures
5. Current definitions for every pipeline register

## Verification Requirements

1. Run basic programs without complex data dependencies.
2. Check register writeback results and PC updates.
3. Verify that branch redirects from `EX` behave as expected.
4. Verify instruction fetch and program execution with the current internal instruction memory. Request/response and wait-state checks belong to Phase 5.
5. The first RV32I-only version assumes `pc_F[1:0] == 2'b00`. Instruction memory only converts the byte address into a word-array index by using `pc_F[MEM_ADDR_WIDTH + 1:2]`; misaligned fetches are not handled inside instruction memory in this phase.

## Risks and Notes

1. Do not make every stall path complicated in this phase.
2. First make instructions flow correctly. Handle complex dependencies afterward.
3. Preserve the current internal-memory contract during this baseline. Introduce a shared request/response interface and its adapter deliberately in Phase 5.

## Exit Conditions

1. The CPU can run simple programs reliably.
2. The main datapath and cross-stage controls are not visibly out of step.
3. The project is ready to move into hazard-control closure.

## Understanding Check

I should be able to answer these from my own RTL and test results.

1. Can I walk one instruction from `IF` to `WB` through my actual RTL?
2. Which control signals are generated in decode and where are they consumed later?
3. How do I know my pipeline registers carry enough information?
4. What would break first if a branch target were calculated incorrectly?
5. What am I still assuming because the hazard unit isn't complete yet?
