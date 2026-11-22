# Phase Plans

I split Hazel into ten phases, from freezing the first architecture to an RTOS
on the full system. Each phase has its own plan with tasks, exit conditions and
an Understanding Check, the questions I should be able to answer before I call
the phase done.

## What I Want This Project to Show

Saying "I built a CPU" isn't worth much on its own. What matters is whether I
can explain the design, show how I verified it and defend my tradeoffs. Before
I use Hazel as my main internship project, I want to be able to do all of
these:

1. Explain the whole architecture in 3 to 5 minutes: `RV32I`, the five-stage
   pipeline, branches resolved in `EX`, the current internal-memory timing and
   the hazard unit. The planned Phase 5 request/response interface gets
   explained separately from what is implemented.
2. Walk one instruction from `IF` to `WB` through my own RTL.
3. Explain what forwarding, stalls and flushes each solve.
4. Show a structured verification flow, not just waveforms that look about
   right.
5. Walk through at least two real bugs that I found and fixed myself.
6. Explain why the first version is a solid in-order pipeline without
   out-of-order execution, register renaming or a branch predictor.

These would make it stronger:

1. Passing a meaningful set of basic `riscv-tests`
2. A minimal CSR, exception and interrupt loop
3. A minimal SoC
4. Running on a NEXYS Artix-7 board
5. A cache, added later
6. An FPU, added later

These look impressive but add little, so I'm staying away from them:

1. Advanced terms I can't back up with the control logic or timing
2. Code without tests or a regression
3. Passing cases without knowing why they pass
4. A predictor, register renaming or a complex bus added so early that the
   project loses its main thread

## How I Ordered the Work

I make Phases 1 to 3 solid first, then close the system loop in Phases 4 to 6,
and only then move on to the cache, the FPU and the RTOS. The foundation is the
five-stage pipeline, the hazard unit with its control priorities, and a
complete verification loop.

## Phase List

The status describes what's in the repository now. A phase whose baseline or
minimum milestone is done can still have follow-up work in its own file.

| Phase | Plan | Status |
| --- | --- | --- |
| 0 | [First-version architecture boundary](foundation/phase-0-architecture-boundary.md) | Baseline done |
| 1 prep | [Phase 1 preparation sheet](foundation/phase-1-preparation-sheet.md) | Baseline done |
| 1 | [Five-stage pipeline core](core/phase-1-pipeline-core.md) | Baseline done |
| 2 | [Hazard unit and control closure](core/phase-2-hazard-control.md) | Baseline done |
| 3 | [Structured verification environment](core/phase-3-verification.md) | Baseline done |
| 4 | [CSRs, exceptions and interrupts](system/phase-4-csr-exception-interrupt.md) | Minimum milestone done |
| 5 | [SoC integration and FPGA bring-up](system/phase-5-soc-fpga.md) | Next |
| 6 | [System-level validation and software baseline](system/phase-6-system-validation.md) | Planned |
| 7 | [Cache design and integration](extensions/phase-7-cache.md) | Planned |
| 8 | [FPU design and integration](extensions/phase-8-fpu.md) | Planned |
| 9 | [RTOS and final system integration](extensions/phase-9-rtos-final-integration.md) | Planned |

## Project-Wide Principles

1. The first version stays at `RV32I`.
2. Branches resolve in `EX` in the first version.
3. Phase 5 replaces the fixed-latency internal memory with a minimal
   request/response interface, before the SoC and the cache build on it.
4. `riscv-tests` come in early, during Phases 2 and 3.
5. The cache and the FPU are required milestones, but they only come after the
   main pipeline is stable.
6. Verification moves forward together with the implementation.

## What Every Phase Ends With

1. The phase goal
2. Its time limit
3. The modules or design work it finished
4. The tests I ran
5. Open issues or risks
6. The entry conditions for the next phase

## When Hazel Is Complete

I'll call Hazel complete when:

1. The five-stage RV32I core, the hazard unit and the control priorities are
   stable under a repeatable regression.
2. CSR access, precise traps, return and at least one interrupt source form a
   tested machine-mode loop.
3. A minimal SoC with UART and timer runs in simulation and on the NEXYS
   Artix-7 board.
4. A known-good software and verification baseline exists before the big
   extensions.
5. The cache and the FPU keep the integer and system regression passing.
6. The final hardware and runtime give a clear, tested path to a lightweight
   RTOS.
