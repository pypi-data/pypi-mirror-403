# COBOL MCP Rule Reference

## General COBOL Rules

### COB-001 — Missing FILE STATUS
- **Severity:** Warning
- **Detects:** `SELECT <file>` without a `FILE STATUS IS <var>` clause
- **Why:** Without FILE STATUS, I/O errors (file-not-found, locked record, etc.) are silent — the program continues with stale data or unpredictable behavior
- **Fix:** Add `FILE STATUS IS WS-<file>-STATUS` to the SELECT clause; check the status variable after every I/O operation on that file

### COB-002 — File Not Opened
- **Severity:** Error
- **Detects:** `READ`, `WRITE`, `REWRITE`, or `DELETE` on a file that has no corresponding `OPEN` statement anywhere in the program
- **Why:** I/O on an unopened file causes a runtime abend (S013 on IBM, or file status 41)
- **Fix:** Add the appropriate `OPEN INPUT|OUTPUT|I-O|EXTEND <file>` before the I/O operation

### COB-003 — Missing STOP RUN / GOBACK
- **Severity:** Warning
- **Detects:** PROCEDURE DIVISION present but no `STOP RUN` or `GOBACK` found
- **Why:** Program may fall through the end of code without proper termination, causing unpredictable behavior or storage violations
- **Fix:** Add `STOP RUN` at the end of a main program, or `GOBACK` if it's a called subprogram

### COB-004 — Uninitialized Variable
- **Severity:** Warning
- **Detects:** WORKING-STORAGE variable used in arithmetic (`COMPUTE`, `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE`) without a prior `VALUE` clause, `INITIALIZE`, or `MOVE` target
- **Why:** Uninitialized WORKING-STORAGE contains unpredictable data (IBM initializes to LOW-VALUES; GnuCOBOL may zero-fill depending on options)
- **Fix:** Add a `VALUE 0` clause to the data definition, or `INITIALIZE` the variable before use

### COB-005 — Arithmetic Without ON SIZE ERROR
- **Severity:** Info
- **Detects:** Arithmetic statements (`COMPUTE`, `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE`) without an `ON SIZE ERROR` clause
- **Why:** Numeric overflow is silently truncated — the result wraps or loses high-order digits without warning
- **Fix:** Add `ON SIZE ERROR <error-handling>` to catch overflow conditions

## File I/O Rules

### COB-110 — WRITE Target Not a File Record
- **Severity:** Error
- **Detects:** `WRITE <target>` where the target is not a 01-level record defined under an FD in the FILE SECTION
- **Why:** WRITE requires a record name (the 01 under an FD), not a file name or working-storage variable
- **Fix:** Use the 01-level record name from the FD, e.g., `WRITE CUSTOMER-REC` not `WRITE CUSTOMER-FILE`

### COB-111 — WRITE Requires OUTPUT/EXTEND/I-O Mode
- **Severity:** Error
- **Detects:** `WRITE`, `REWRITE`, or `DELETE` on a record whose owning file is not opened in OUTPUT, EXTEND, or I-O mode
- **Why:** Writing to a file opened INPUT (or not opened at all) causes a runtime error (file status 49)
- **Fix:** Change the OPEN mode: use `OPEN OUTPUT` for sequential writes, `OPEN I-O` for REWRITE/DELETE, or `OPEN EXTEND` to append
- **Note:** Suppressed for GSAM-bound files (IMS manages GSAM open/close)

### COB-120 — File Used Without FILE STATUS Binding
- **Severity:** Error
- **Detects:** A file that is referenced by OPEN/READ/WRITE/REWRITE/DELETE/START/CLOSE but has no `FILE STATUS IS <var>` in its SELECT clause
- **Why:** Without a status variable, the program cannot detect or recover from I/O errors
- **Fix:** Add `FILE STATUS IS WS-<file>-STATUS` to the SELECT clause and check the variable after each I/O
- **Note:** Suppressed for GSAM-bound files (IMS-130/131/132 cover GSAM misuse)

## IMS Call Structure Rules

### IMS-001 — Invalid DL/I Function Code
- **Severity:** Error
- **Detects:** First USING argument in a `CALL 'CBLTDLI'`/`'DFSLI000'` is not a recognized DL/I function code (GU, GN, GNP, GHU, GHN, ISRT, REPL, DLET, CHKP, XRST) and cannot be resolved to a WORKING-STORAGE constant
- **Why:** An invalid function code causes an IMS DC status code or abend
- **Fix:** Use a valid function code literal (e.g., `'GU  '`) or define a WS constant like `05 DLI-GU PIC X(4) VALUE 'GU  '.`

### IMS-002 — Missing/Invalid PCB Argument
- **Severity:** Error
- **Detects:** Second USING argument in a DL/I call is missing or is not a declared LINKAGE PCB (exempt: CHKP/XRST which use IOPCB differently)
- **Why:** Passing the wrong PCB causes database operations on the wrong segment hierarchy or an abend
- **Fix:** Ensure the second argument matches a 01-level PCB declared in LINKAGE SECTION and listed in PROCEDURE DIVISION USING

### IMS-010 — PCB Not in PROCEDURE DIVISION USING
- **Severity:** Error
- **Detects:** LINKAGE SECTION contains PCB declarations but PROCEDURE DIVISION has no USING clause, or a specific PCB is in LINKAGE but not in USING
- **Why:** PCBs must be received via USING to be addressable; without this, the PCB pointer is uninitialized
- **Fix:** Add all PCB names to `PROCEDURE DIVISION USING <iopcb> <db-pcb-1> ...` in the order they appear in the PSB

### IMS-011 — Function Code Variable Not in WORKING-STORAGE
- **Severity:** Error
- **Detects:** A quoted token in the function-code position that doesn't resolve to a known DL/I function or a declared WS variable
- **Why:** Using an undeclared variable as a function code results in unpredictable content being passed to DL/I
- **Fix:** Declare the function code in WORKING-STORAGE: `05 DLI-GU PIC X(4) VALUE 'GU  '.`

### IMS-012 — Call PCB Not in USING List
- **Severity:** Error
- **Detects:** A PCB name used in a DL/I CALL that is not present in PROCEDURE DIVISION USING (only fires when LINKAGE PCBs exist)
- **Why:** The PCB address won't be initialized if it's not received through the USING interface
- **Fix:** Add the PCB to both LINKAGE SECTION (01 level) and PROCEDURE DIVISION USING

## IMS Status Handling Rules

### IMS-020 — No Status Check After DL/I Call
- **Severity:** Warning
- **Detects:** No IF or EVALUATE referencing a status variable within ~12 lines after a DL/I call (skips CHKP/XRST)
- **Why:** Ignoring the PCB status code after a DL/I call means the program won't detect "not found" (GE), "end of database" (GB), or error conditions
- **Fix:** Check the PCB status field immediately after the call:
  ```cobol
  CALL 'CBLTDLI' USING DLI-GU DB-PCB IO-AREA SSA1
  IF DB-PCB-STATUS NOT = SPACES
      PERFORM STATUS-ERROR-HANDLER
  END-IF
  ```

### IMS-021 — No GB Handling in Program
- **Severity:** Error
- **Detects:** Program uses sequential retrieval (GN/GHN/GNP) but never checks for status `'GB'` (end-of-database/segment) anywhere in the source
- **Why:** Sequential retrieval without GB handling causes an infinite loop or processes stale data past the end
- **Fix:** Add an EVALUATE or IF block that handles `'GB'`:
  ```cobol
  EVALUATE DB-PCB-STATUS
      WHEN SPACES  CONTINUE
      WHEN 'GB'    SET END-OF-DB TO TRUE
      WHEN OTHER   PERFORM STATUS-ERROR-HANDLER
  END-EVALUATE
  ```

### IMS-022 — No Local GB Handling Near GN/GHN
- **Severity:** Warning
- **Detects:** A specific GN/GHN call with no visible `'GB'` check in IF/EVALUATE blocks within ~60 lines forward (requires loop context or multiple sequential reads on same PCB)
- **Why:** Even if GB is handled elsewhere, each retrieval loop should have its own exit condition check
- **Fix:** Add a GB check immediately after the GN/GHN call within the retrieval loop

### IMS-024 — Status Check Missing Default Branch
- **Severity:** Error
- **Detects:** An IF or EVALUATE that tests a harvested status variable but lacks an ELSE or WHEN OTHER branch
- **Why:** Unexpected status codes (like 'AI', 'AJ') slip through without handling, causing silent data corruption
- **Fix:** Add `ELSE PERFORM UNEXPECTED-STATUS-HANDLER` or `WHEN OTHER PERFORM UNEXPECTED-STATUS-HANDLER`

### IMS-INIT-STATUS — Loop Tests Uninitialized Status
- **Severity:** Warning
- **Detects:** `PERFORM ... UNTIL <status-var>` where the status variable has no prior initialization (MOVE, VALUE, or a preceding DL/I call with status check)
- **Why:** On first iteration, the status variable contains garbage, so the UNTIL condition may immediately be true (skipping the loop) or never true (infinite loop)
- **Fix:** Either:
  - Initialize the status: `MOVE SPACES TO DB-PCB-STATUS`
  - Use `PERFORM WITH TEST AFTER` (checks condition after first iteration)
  - Issue a priming DL/I call before the loop

## IMS GSAM Rules

### IMS-130 — COBOL WRITE on GSAM File
- **Severity:** Error
- **Detects:** Standard COBOL `WRITE` on a record whose owning file is assigned to a GSAM dataset
- **Why:** GSAM files must be written via DL/I ISRT calls through the GSAM PCB; COBOL WRITE bypasses IMS control
- **Fix:** Replace `WRITE <rec>` with `CALL 'CBLTDLI' USING DLI-ISRT GSAM-PCB IO-AREA`

### IMS-131 — COBOL READ/REWRITE/DELETE on GSAM File
- **Severity:** Error
- **Detects:** Standard COBOL `READ`, `REWRITE`, or `DELETE` on a GSAM-assigned file or record
- **Why:** All GSAM I/O must go through DL/I calls; COBOL verbs don't work with IMS-managed GSAM datasets
- **Fix:** Use `CALL 'CBLTDLI' USING DLI-GN GSAM-PCB IO-AREA` for reads, ISRT for writes

### IMS-132 — Explicit OPEN/CLOSE on GSAM File
- **Severity:** Warning
- **Detects:** `OPEN` or `CLOSE` statement referencing a GSAM-assigned file
- **Why:** IMS automatically manages GSAM dataset open/close; explicit OPEN/CLOSE is unnecessary and may conflict with IMS resource management
- **Fix:** Remove the OPEN/CLOSE statements for GSAM files; IMS handles the lifecycle

## IMS Checkpointing Rules

### IMS-140 — CHKP/XRST Not Using IOPCB
- **Severity:** Error
- **Detects:** A `CHKP` or `XRST` call passes a database PCB instead of the IOPCB as the second argument
- **Why:** Checkpoint and restart calls must use the I/O PCB (IOPCB); using a DB PCB causes an abend or corrupted checkpoint
- **Fix:** Change the PCB argument to the IOPCB: `CALL 'CBLTDLI' USING DLI-CHKP IOPCB ...`

### IMS-141 — IOPCB Not Declared/Received
- **Severity:** Error
- **Detects:** CHKP or XRST calls exist but no IOPCB is declared in LINKAGE SECTION or listed in PROCEDURE DIVISION USING
- **Why:** The IOPCB must be the first PCB in the PSB and must be received via USING to be addressable
- **Fix:** Add IOPCB to LINKAGE (01 IOPCB with standard PCB mask) and as the first entry in PROCEDURE DIVISION USING

### IMS-142 — Basic CHKP When Symbolic Expected
- **Severity:** Warning
- **Detects:** A CHKP call appears to be the basic form (<=2 args, no length token) while XRST or restart/token context exists in the program
- **Why:** When using XRST for restart, the corresponding CHKP should be the symbolic form (with checkpoint ID length and area arguments) to enable proper restart
- **Fix:** Use symbolic CHKP form: `CALL 'CBLTDLI' USING DLI-CHKP IOPCB CHKP-ID-LEN CHKP-ID AREA-LEN AREA`

### IMS-143 — CHKP/XRST Passed Wrong PCB
- **Severity:** Error
- **Detects:** CHKP or XRST passes a PCB that isn't the IOPCB, while an IOPCB symbol exists in the program
- **Why:** Even though an IOPCB is declared, the call uses a different PCB — likely a copy-paste error
- **Fix:** Change the second USING argument to the IOPCB name

## IMS SSA & Argument Rules

### IMS-160 — SSA Operator Field Malformed
- **Severity:** Error
- **Detects:** An SSA-related data item with `PIC X(3)` for the operator field (should be `PIC X(2)`)
- **Why:** IMS SSA operators (EQ, GE, GT, LE, LT, NE) are exactly 2 characters; PIC X(3) causes misalignment of the SSA structure
- **Fix:** Change the operator field to `PIC X(2)` and ensure the value is a valid 2-character operator

### IMS-161 — Suspicious MOVE Into SSA
- **Severity:** Error
- **Detects:** `MOVE ... TO ... IN <name>-SSA` pattern — moving data into SSA fields
- **Why:** SSA qualification values should be set from program logic, not copied from I/O area fields (which may contain stale or wrong-segment data)
- **Fix:** Set SSA qualification values from WORKING-STORAGE variables or literals, not from the I/O area returned by a previous call

### IMS-162 — DL/I Argument Order Wrong
- **Severity:** Error
- **Detects:** In GU/GN/GHU/GHN/ISRT calls: arg3 looks like an SSA (contains "SSA" or has parenthesized qualifier) while arg4 looks like a buffer/IO-area
- **Why:** Expected order is func, PCB, IO-AREA, SSA1, SSA2... — swapping IO-area and SSA causes the segment to be written into the SSA structure
- **Fix:** Correct the order: `CALL 'CBLTDLI' USING func PCB IO-AREA SSA1 [SSA2...]`

### IMS-163 — ISRT Without SSA
- **Severity:** Warning
- **Detects:** An ISRT call has no SSA arguments while the program defines/uses SSAs elsewhere
- **Why:** ISRT without an SSA relies on current position, which may be wrong after navigation; an unqualified ISRT can insert into the wrong segment type
- **Fix:** Add at least one SSA to specify the target segment: `CALL 'CBLTDLI' USING DLI-ISRT DB-PCB IO-AREA SEG-SSA`

## IMS GSAM Audit Rule

### IMS-170 — No ISRT After GN/GHN (GSAM Present)
- **Severity:** Warning
- **Detects:** When GSAM is present in FILE-CONTROL, a GN/GHN call has no nearby ISRT within ~14 lines or in the immediately PERFORMed paragraph
- **Why:** Common audit pattern: read from DB (GN/GHN) then write audit record to GSAM (ISRT). Missing ISRT may indicate a forgotten audit trail
- **Fix:** Add an ISRT call to the GSAM PCB after processing the retrieved segment, or document why no audit record is needed

## Severity Guide

| Severity | Meaning | Action |
|----------|---------|--------|
| Error | Likely causes runtime failure, data corruption, or abend | Must fix before deployment |
| Warning | May cause incorrect behavior depending on data/timing | Should fix; document if intentionally accepted |
| Info | Style or defensive-coding suggestion | Consider fixing for robustness |
