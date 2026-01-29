# GnuCOBOL Commands Reference

This system has GnuCOBOL 3.2.0 installed at `/opt/homebrew/bin/cobc`.

## Compiler Command (cobc)

The primary tool is `cobc`, the GnuCOBOL compiler.

```bash
cobc [options] file [file ...]
```

### Information Commands

```bash
cobc --version          # Show compiler version
cobc --info             # Display build/configuration info
cobc --help             # Display available options
cobc --list-reserved    # Display reserved words
cobc --list-intrinsics  # Show intrinsic functions
cobc --list-mnemonics   # List mnemonic names
cobc --list-system      # List system routines
```

## Compilation Modes

| Flag | Output | Purpose |
|------|--------|---------|
| `-x` | Executable | Create standalone program with main() |
| `-m` | `.so`/`.dylib` | Build dynamically loadable module (default) |
| `-c` | `.o` | Compile and assemble only |
| `-C` | `.c` | Translation to C only |
| `-S` | `.s` | Generate assembly |
| `-E` | `.i` | Preprocess only |
| `-fsyntax-only` | None | Syntax check without compiling |

## Common Compilation Examples

### Create Executable
```bash
cobc -x -o program program.cob
./program
```

### Create Module (for CALL statements)
```bash
cobc -m subprogram.cob
# Creates subprogram.so (or .dylib on macOS)
```

### Compile Multiple Files
```bash
# All at once
cobc -x -o main main.cob sub1.cob sub2.cob

# Or separately
cobc -c sub1.cob sub2.cob
cobc -x -o main main.cob sub1.o sub2.o
```

### Syntax Check Only
```bash
cobc -fsyntax-only program.cob
```

## Source Format Options

| Flag | Format |
|------|--------|
| `-free` or `-F` | Free format (modern, recommended) |
| `-fixed` | Fixed format (traditional columns 1-80) |
| `-fformat=variable` | Micro Focus variable format |
| `-fformat=cobol85` | Strict COBOL-85 fixed format |

```bash
# Free format source
cobc -x -free program.cob

# Fixed format (legacy)
cobc -x -fixed program.cob
```

## Dialect/Standard Selection

Emulate specific COBOL implementations:

```bash
cobc -std=ibm program.cob      # IBM Enterprise COBOL
cobc -std=mf program.cob       # Micro Focus
cobc -std=acu program.cob      # ACUCOBOL-GT
cobc -std=cobol85 program.cob  # COBOL-85 standard
cobc -std=cobol2014 program.cob # COBOL 2014 standard
cobc -std=default program.cob  # GnuCOBOL default (permissive)
```

## Include and Library Paths

```bash
# Add COPY file search path
cobc -I /path/to/copybooks program.cob

# Add library search path
cobc -L /path/to/libs -l mylib program.cob

# Output to specific file
cobc -x -o bin/myprogram program.cob
```

## Debugging Options

```bash
# Enable all runtime checks
cobc -x --debug program.cob

# Generate debug info for gdb/lldb
cobc -x -g program.cob

# Trace execution
cobc -x -ftrace program.cob      # Trace procedures
cobc -x -ftraceall program.cob   # Trace all statements

# Stack checking for PERFORM
cobc -x -fstack-check program.cob

# Combined debug build
cobc -x -g --debug -ftraceall program.cob
```

## Optimization

```bash
cobc -x -O program.cob     # Standard optimization
cobc -x -O2 program.cob    # More optimization
cobc -x -O3 program.cob    # Aggressive optimization
cobc -x -Os program.cob    # Optimize for size
cobc -x -O0 program.cob    # No optimization (debugging)
```

## Warning Control

```bash
cobc -Wall program.cob        # Enable most warnings
cobc -Wextra program.cob      # Additional warnings
cobc -w program.cob           # Suppress all warnings
cobc -Werror program.cob      # Treat warnings as errors
cobc -fmax-errors=5 program.cob  # Stop after 5 errors
```

## Running Programs

### Executables
```bash
./program
./program arg1 arg2
```

### Modules with cobcrun
```bash
cobcrun module_name
cobcrun module_name arg1 arg2
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `COB_LIBRARY_PATH` | Search path for loadable modules |
| `COB_PRE_LOAD` | Modules to load before execution |
| `COB_RUNTIME_CONFIG` | Path to runtime config file |
| `COB_SCREEN_ESC` | Enable ESC key in SCREEN SECTION |
| `COB_SCREEN_EXCEPTIONS` | Enable function keys in ACCEPT |

```bash
# Set module search path
export COB_LIBRARY_PATH=/path/to/modules:.

# Run with environment
COB_LIBRARY_PATH=./lib cobcrun mymodule
```

## Useful for Translation Testing

When validating COBOL-to-Java translations, use GnuCOBOL to:

### 1. Verify Original COBOL Behavior
```bash
# Compile and run original COBOL
cobc -x -free -std=ibm -o original program.cob
./original < test_input.txt > cobol_output.txt
```

### 2. Check Syntax Before Translation
```bash
cobc -fsyntax-only -std=ibm -Wall program.cob
```

### 3. Generate C for Reference
```bash
# See how GnuCOBOL translates to C
cobc -C -free program.cob
# Creates program.c - useful for understanding semantics
```

### 4. Debug Specific Sections
```bash
# Trace to understand control flow
cobc -x -free -ftraceall program.cob 2>&1 | tee trace.log
./program
```

### 5. Test with Different Dialects
```bash
# If source was IBM mainframe
cobc -x -std=ibm program.cob

# If source was Micro Focus
cobc -x -std=mf program.cob
```

## Quick Reference Card

```bash
# Compile executable (free format)
cobc -x -free -o prog prog.cob

# Compile module
cobc -m -free module.cob

# Syntax check
cobc -fsyntax-only prog.cob

# Debug build
cobc -x -g --debug prog.cob

# IBM dialect
cobc -x -std=ibm prog.cob

# See generated C
cobc -C prog.cob
```
