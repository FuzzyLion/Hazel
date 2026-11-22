# GCC Notes

## Role in This Project

`riscv64-elf-gcc` is used as a driver for the RISC-V assembler and linker. The
current project builds assembly programs directly; GCC is not compiling C code
in this flow.

```text
Assembly source
  -> GCC driver
  -> assembler
  -> linker
  -> ELF executable
```

GCC does not simulate the processor and does not generate the final Verilog
memory image.

## Current Command Shape

The local smoke build uses the following options:

```bash
riscv64-elf-gcc \
  -march=rv32i_zicsr \
  -mabi=ilp32 \
  -nostdlib \
  -nostartfiles \
  -Wl,-T,"$LINKER_SCRIPT" \
  -Wl,-e,"$ENTRY_POINT" \
  -Wl,-Map,"$MAP_FILE" \
  -Wl,--no-relax \
  -o "$ELF_FILE" \
  "${PREPROCESSED_FILES[@]}"
```

## Options Used

### `-march=rv32i_zicsr`

Allows RV32I instructions and the CSR instruction subset. The toolchain rejects
instructions such as `csrw` when `zicsr` is not enabled.

### `-mabi=ilp32`

Selects the 32-bit integer ABI used by RV32 programs.

### `-nostdlib`

Prevents the standard C library from being linked. The processor does not yet
provide the runtime environment expected by that library.

### `-nostartfiles`

Prevents GCC from adding its default startup files. This project provides its
own `_start` code.

### `-Wl,...`

Passes options to the linker. For example:

```text
-Wl,-T,software/linker/core.ld
```

means that GCC passes `-T software/linker/core.ld` to `ld`.

### `-o <file>`

Sets the output ELF filename.

## ISA-Lite Differences

`software/scripts/build_riscv_lite_test.sh` differs from the local smoke build
in four options:

```bash
-x assembler-with-cpp
-march=rv32i
-I<include-directory>
-Wl,-Ttext=0
```

`-x assembler-with-cpp` runs the C preprocessor before assembly. `-march=rv32i`
leaves out `zicsr`, because neither the upstream user-level tests nor my local
environment use CSR instructions. `-I` adds the directories with the test
macros and the local environment header. `-Wl,-Ttext=0` places `.text` at
address 0 without the project linker script, so there is no `.trap` section
and no map file.

## Inputs and Output

```text
Input:  .s or .S assembly sources
Output: .elf executable
```

The ELF is inspected with `objdump` and converted to a memory image with
`objcopy`.
