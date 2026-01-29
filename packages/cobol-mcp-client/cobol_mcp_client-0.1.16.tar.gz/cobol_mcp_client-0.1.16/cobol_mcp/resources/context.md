# COBOL MCP Context

## Documentation Indexed by `search`

| Source Document | Dialect | Best For |
|----------------|---------|----------|
| GnuCOBOL Programmer's Guide | GnuCOBOL 3.x | Open-source COBOL syntax, compiler options, extensions |
| GnuCOBOL Quick Reference | GnuCOBOL 3.x | Compact syntax lookup |
| GnuCOBOL Sample Programs | GnuCOBOL 3.x | Working code examples |
| IBM Enterprise COBOL Language Reference | IBM Enterprise COBOL 6.x | Mainframe COBOL syntax, COMP-5, XML/JSON, UTF-8 |
| IBM CICS Application Programming Reference | IBM CICS TS | EXEC CICS commands, transaction processing |
| Visual COBOL Developer's Guide | Micro Focus Visual COBOL | Managed COBOL, .NET/JVM integration, IDE features |
| Visual COBOL Application Modernization Tools | Micro Focus Visual COBOL | Legacy migration, code analysis, modernization |
| Dialect comparison guides | Cross-dialect | Differences between GnuCOBOL, IBM, Micro Focus |

## Effective Search Queries

Prefix queries with dialect context when targeting a specific platform:

- `"IBM EXEC CICS READ command"` — CICS-specific syntax
- `"GnuCOBOL SCREEN SECTION ACCEPT"` — GnuCOBOL screen I/O
- `"Visual COBOL managed COBOL .NET"` — Micro Focus managed code
- `"COMP-3 packed decimal byte size"` — cross-dialect numeric storage
- `"DL/I CALL CBLTDLI USING"` — IMS DL/I call patterns

For CICS patterns, use `EXEC CICS` as the prefix:
- `"EXEC CICS READ FILE INTO"` — file control
- `"EXEC CICS SEND MAP"` — BMS map I/O
- `"EXEC CICS SYNCPOINT"` — transaction control

For DL/I patterns, reference the call interface:
- `"CALL CBLTDLI GU GN GHN"` — retrieval calls
- `"CALL CBLTDLI ISRT REPL DLET"` — update calls
- `"PCB status codes GB GE"` — status code meanings

## Key Dialect Differences

| Feature | GnuCOBOL | IBM Enterprise COBOL | Micro Focus Visual COBOL |
|---------|----------|---------------------|--------------------------|
| Binary storage (`COMP`) | Big-endian, truncated to PIC digits | Big-endian, truncated to PIC digits | Native-endian, full binary range |
| `COMP-5` | Same as COMP (no difference) | Native binary, full range of storage bytes | Native binary, full range |
| Screen I/O | `SCREEN SECTION` + `ACCEPT`/`DISPLAY` | Not supported (use CICS BMS) | `SCREEN SECTION` or managed UI |
| Program exit | `STOP RUN` or `GOBACK` | `GOBACK` preferred (CICS: `EXEC CICS RETURN`) | `STOP RUN` or `GOBACK` |
| XML GENERATE | Not supported | Built-in statement | Supported |
| JSON GENERATE | Not supported | Built-in statement (v6.2+) | Supported via library |
| File I/O | Standard COBOL I/O verbs | Standard + VSAM/QSAM | Standard + managed file classes |
| Debugging | `-fdebugging-line`, `-g` flags | CEDF (CICS), Language Environment | IDE debugger, managed debugging |
| Copybook path | `-I` flag or `COB_COPY_DIR` env | `SYSLIB` DD, `LIB` compiler option | `COBCPY` env, project settings |

## GnuCOBOL Syntax Validation

Use the GnuCOBOL compiler for ground-truth syntax checking:

```bash
cobc -fsyntax-only program.cbl          # fixed-format, default dialect
cobc -fsyntax-only -free program.cbl    # free-format
cobc -fsyntax-only -std=ibm program.cbl # IBM compatibility dialect
cobc -fsyntax-only -std=mf program.cbl  # Micro Focus compatibility dialect
```

Useful flags:
- `-Wall` — enable all warnings
- `-Wextra` — additional warnings
- `-std=ibm-strict` — strict IBM compatibility (errors on GnuCOBOL extensions)

## PIC Clause Byte Sizes

| PIC Clause | Type | Byte Size | Notes |
|------------|------|-----------|-------|
| `X(n)` | Alphanumeric | n | One byte per character |
| `9(n)` | Unsigned numeric (display) | n | One byte per digit |
| `S9(n)` | Signed numeric (display) | n | Sign embedded in last byte (or +1 for SIGN SEPARATE) |
| `9(n)V9(m)` | Implied decimal | n+m | Decimal point not stored |
| `S9(n)V9(m) COMP-3` | Packed decimal | floor((n+m+1)/2)+1 | Half-byte per digit + sign nibble |
| `S9(n) COMP` / `COMP-4` | Binary | 2 (1-4 digits), 4 (5-9), 8 (10-18) | Big-endian on IBM/GnuCOBOL |
| `S9(n) COMP-5` | Native binary | Same sizes as COMP | Full range of storage bytes (IBM/MF); same as COMP on GnuCOBOL |
| `XX` or `X(2)` | 2-char alphanumeric | 2 | Common for status codes |

## IMS Auto-Detection

The `check` tool automatically applies IMS rules when it detects DL/I calls in the source:
- `CALL 'CBLTDLI'` or `CALL 'DFSLI000'`
- `ENTRY 'DLITCBL'`

When IMS is detected, additional rules (IMS-001 through IMS-170) are applied. See `cobol://rules` for the complete rule reference with detection logic and fixes.
