# Phase 5: SoC Integration and FPGA Bring-up

## Time Limit

Recommended: 1.5 to 2.5 weeks
Hard limit: 3 weeks

## Goal

I want to go from a core that works in simulation to a minimal system that runs a program on the board.

## Detailed Tasks

### Task 1: Build the SoC Top Level

1. Design the minimum SoC top level.
2. Define one shared address map.

### Task 2: Add the Basic Peripherals

1. Integrate ROM, RAM, UART, and Timer.
2. Connect the CPU's handshake interfaces to SoC memory and peripherals.

### Task 3: Prepare the Board-Level Project

1. Prepare the Vivado project, constraints, and board-level clock and reset handling.
2. Add a minimal observable debug path, such as serial output or LED status.

### Task 4: Complete the First Bring-up

1. Run a minimal program on the board.
2. Record the board behavior, serial output, and known issues.

## Design Questions

1. How does a slow peripheral feed a stall back to the CPU?
2. How do peripheral and main-memory addresses fit into one address map?
3. During board bring-up, how do I quickly tell whether a problem is in the CPU, the SoC integration or a peripheral?
4. Which pipeline registers hold during a memory wait? Freezing only Fetch and Decode isn't enough once MEM can wait.
5. Does a memory wait or a branch redirect win?
6. Who inserts the bubble when a memory wait and a load-use stall happen together?
7. How does a held load or store avoid committing twice or losing its response?

## Deliverables

1. SoC top-level RTL
2. Address-map document
3. FPGA project and constraints
4. Board bring-up notes
5. Peripheral-handshake integration notes

## Verification Requirements

1. A SoC-level program runs successfully in simulation.
2. The FPGA runs a minimal program and produces observable output.
3. Slow peripherals do not break pipeline control.

## Risks and Notes

1. Many problems will appear here for the first time as system-integration issues rather than CPU-internal logic bugs.
2. Slow UART and Timer behavior must fit the handshake-based stall mechanism.
3. Do not fold Cache integration into this phase.

## Exit Conditions

1. The minimal system runs on the board.
2. Key peripherals such as UART and Timer work.
3. The project is ready for system-level testing and the software baseline.

## Understanding Check

I should be able to answer these from my own RTL and test results.

1. What is my address map, and why did I choose it?
2. How does a slow peripheral stall or delay the CPU safely?
3. If the board misbehaves, how do I tell whether the fault is in the CPU, the SoC glue, the memory map or a peripheral?
4. What assumptions changed when moving from simulation to FPGA?
5. Why does my SoC structure still fit the later cache work?
