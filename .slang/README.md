# Slang Language Server

This folder holds my Slang setup for the editor. [`server.json`](server.json)
indexes the RTL and testbench folders and builds from [`uvm.f`](uvm.f), which
loads the RTL file list and the RegFile UVM testbench. The simulation runners
don't read anything in this folder.

The index explicitly includes `rtl/core/stages/`. Its five `.sv` files are
independent modules, each importing `core_types_pkg` and declaring its own
ports. They are ordinary sources in `rtl/filelist.f`, after the packages.
There are no stage `.svh` fragments or stage include paths to configure.

The flags set `--timescale=1ns/1ps` as the default for design elements without
an explicit time scale, matching the testbenches. This lets Slang analyze the
RTL together with the indexed testbenches without mixed/missing-time-scale
errors. It changes the editor's analysis configuration; simulation runners
and explicit testbench time scales are unchanged.

## UVM

The editor needs UVM 2020.3.1 in `tools/uvm-core-2020.3.1/`, set up as in
[tools/README.md](../tools/README.md#uvm). I keep it inside the workspace so
the bundled WASM runtime can read it.

Slang and the VS Code Verilator linter both read [`uvm_lib.f`](uvm_lib.f). It
defines `UVM_NO_DPI`, adds the UVM include path and loads `uvm_pkg`, then
`regfile_pkg`. The linter appends the open file after these packages, so a
testbench file can import them. `server.json` indexes only the top of the UVM
`src/` folder, so Slang can find `uvm_pkg` for a tab that is already open when
VS Code starts. The subfolders stay out of the index because `uvm_pkg.sv`
pulls them in through includes.

Paths in these lists start at the repository root. When I add a UVM file,
shared packages go into `uvm_lib.f` in dependency order, and testbench tops go
into the [RegFile file list](../tb/uvm/reg_file/filelist.f).
[`sim/run_reg_file_uvm.sh`](../sim/run_reg_file_uvm.sh) still names its own
files, so it needs the same change.

When I started the UVM testbench, VS Code showed more than 2000 warnings, some
inside the UVM library and some from Verilator lint.
[`uvm_warnings.toml`](uvm_warnings.toml) waives the Slang ones inside the
Accellera sources, since I don't edit upstream code. A second rule covers the
field and utils macros in `tb/uvm/`, whose expansion triggers warnings such as
unused typedefs and missing case defaults. It matches only the macro lines, so
my own code is still checked. For the same reason, `regfile_item.sv` turns
Verilator's width warnings off only around the field macros. After changing a
waiver, run **Verilog: Restart slang-server** and **Verilog: Rerun lint tool**.

## Recorded Local Editor Setup

- VS Code extension: **Verilog-HDL/SystemVerilog** (`mshr-h.veriloghdl`) **1.28.4**
- Selected runtime: `bundled-wasm` in [`.vscode/settings.json`](../.vscode/settings.json)
- WASI support extension: `ms-vscode.wasm-wasi-core` **1.0.2**

## How the WASM Runtime Works

The Verilog extension ships a compiled `slang-server.wasm` file. When VS Code opens Verilog or SystemVerilog source, the extension starts that bundled Slang language server through VS Code's WASI runtime and exchanges Language Server Protocol messages with it.

In practice, this gives the editor syntax and semantic diagnostics, symbol lookup, and go-to-definition support without requiring a separately installed native `slang-server` executable. The workspace explicitly selects this bundled runtime, so the editor does not depend on a machine-specific Slang path.

## Why Use Slang Alongside Verilator Lint?

This is not a choice between static lint and dynamic checking: Slang and Verilator are both static-analysis tools. The difference is when and how they are used.

Slang runs inside the editor and reacts to the file you are currently changing, including unsaved edits. It is useful for fast feedback and navigation while writing RTL. Verilator lint runs the project file list as an external command, so it is better for checking the assembled design and catching project-wide elaboration issues.

Neither tool executes the processor over clock cycles. That is dynamic simulation, and it still belongs to the directed tests and regression scripts under `sim/`.

When source folders or the build entry change, I update `server.json` or `uvm.f` and note it here. I keep Verilator lint on as well, because it reads the real RTL file list and is closer to the simulation build.

If the editor retains diagnostics for removed stage `.svh` files after a
checkout or refactor, close those obsolete tabs and run **Verilog: Restart
slang-server** from the Command Palette. Open the replacement modules under
`rtl/core/stages/` and inspect Problems again. A successful Verilator run alone
does not confirm that the language server has refreshed its diagnostics.
