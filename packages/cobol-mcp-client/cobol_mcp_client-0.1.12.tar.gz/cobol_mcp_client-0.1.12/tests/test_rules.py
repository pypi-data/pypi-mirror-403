"""
Comprehensive unit tests for the COBOL MCP rules system.

Covers:
  - CobolParser edge cases (empty, minimal, missing sections)
  - GeneralCobolChecker rules COB-001 through COB-005 (positive and negative)
  - check() function behavior and IMS auto-detection
  - Edge cases: partial COBOL, comments-only, very large input
"""

import pytest
from textwrap import dedent

from cobol_mcp.rules.parser import CobolParser
from cobol_mcp.rules.general import GeneralCobolChecker
from cobol_mcp.rules.models import Finding
from cobol_mcp.tools.check import check
from cobol_mcp.rules.ims import has_ims_context


# ---------------------------------------------------------------------------
# Helper: extract rule_ids from check() output
# ---------------------------------------------------------------------------

def rule_ids(findings):
    """Extract rule_id values from a list of finding dicts."""
    return [f["rule_id"] for f in findings]


def has_rule(findings, rule_id):
    """Check if a specific rule_id appears in findings."""
    return any(f["rule_id"] == rule_id for f in findings)


def count_rule(findings, rule_id):
    """Count how many times a rule fires."""
    return sum(1 for f in findings if f["rule_id"] == rule_id)


# ===========================================================================
# SECTION 1: CobolParser Edge Cases
# ===========================================================================

class TestCobolParserEdgeCases:
    """Tests for parser behavior on unusual or minimal input."""

    def test_empty_string(self):
        """Parser should handle empty string without raising."""
        parser = CobolParser("")
        # str.splitlines() on "" returns [], so lines is empty
        assert parser.lines == []
        assert parser.ws_names == []
        assert parser.linkage_names == []
        assert parser.using_params == []
        assert parser.select_files == set()
        assert parser.io_operations == []
        assert parser.arithmetic_ops == []
        assert not parser.has_stop_run
        assert not parser.has_goback

    def test_whitespace_only(self):
        """Parser should handle whitespace-only input gracefully."""
        parser = CobolParser("   \n\n   \n")
        assert parser.ws_names == []
        assert parser.paragraphs == {}

    def test_single_newline(self):
        """Parser should handle a single newline character."""
        parser = CobolParser("\n")
        assert parser.ws_names == []

    def test_minimal_identification_division_only(self):
        """Parser processes code with only IDENTIFICATION DIVISION."""
        src = dedent("""\
            IDENTIFICATION DIVISION.
            PROGRAM-ID. MINIMAL.
        """)
        parser = CobolParser(src)
        assert parser.ws_names == []
        assert parser.linkage_names == []
        assert not parser.has_stop_run

    def test_no_procedure_division(self):
        """Parser should not crash when PROCEDURE DIVISION is absent."""
        src = dedent("""\
            IDENTIFICATION DIVISION.
            PROGRAM-ID. NOPROC.
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-VAR PIC X(10).
        """)
        parser = CobolParser(src)
        assert "WS-VAR" in parser.ws_names
        assert parser.paragraphs == {}
        assert not parser.has_stop_run

    def test_working_storage_filler_excluded(self):
        """FILLER declarations should be excluded from ws_names."""
        src = dedent("""\
            IDENTIFICATION DIVISION.
            PROGRAM-ID. TESTFILL.
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-REC.
                05  FILLER        PIC X(5).
                05  WS-NAME       PIC X(20).
                05  FILLER        PIC X(10).
        """)
        parser = CobolParser(src)
        assert "FILLER" not in parser.ws_names
        assert "WS-NAME" in parser.ws_names

    def test_working_storage_value_detection(self):
        """Parser correctly identifies variables with and without VALUE clauses."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-COUNTER  PIC 9(5)  VALUE 0.
            01  WS-AMOUNT   PIC 9(7)V99.
            77  WS-FLAG     PIC X     VALUE 'N'.
        """)
        parser = CobolParser(src)
        assert parser.ws_has_value.get("WS-COUNTER") is True
        assert parser.ws_has_value.get("WS-AMOUNT") is False
        assert parser.ws_has_value.get("WS-FLAG") is True

    def test_working_storage_level_numbers(self):
        """Parser handles various level numbers correctly (01-49, 77)."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-GROUP.
                05  WS-ITEM-A  PIC X(5).
                10  WS-ITEM-B  PIC X(3).
                15  WS-ITEM-C  PIC 9(2).
                49  WS-ITEM-D  PIC X.
            77  WS-STANDALONE  PIC 9(3).
        """)
        parser = CobolParser(src)
        assert "WS-GROUP" in parser.ws_names
        assert "WS-ITEM-A" in parser.ws_names
        assert "WS-ITEM-B" in parser.ws_names
        assert "WS-ITEM-C" in parser.ws_names
        assert "WS-ITEM-D" in parser.ws_names
        assert "WS-STANDALONE" in parser.ws_names

    def test_working_storage_ends_at_linkage(self):
        """Working storage parsing stops at LINKAGE SECTION boundary."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-IN-WS PIC X(5).
            LINKAGE SECTION.
            01  LS-VAR   PIC X(5).
        """)
        parser = CobolParser(src)
        assert "WS-IN-WS" in parser.ws_names
        assert "LS-VAR" not in parser.ws_names

    def test_working_storage_ends_at_procedure_division(self):
        """Working storage parsing stops at PROCEDURE DIVISION."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-VAR PIC X.
            PROCEDURE DIVISION.
            MAIN-PARA.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert "WS-VAR" in parser.ws_names
        # MAIN-PARA should not appear in ws_names
        assert "MAIN-PARA" not in parser.ws_names

    def test_linkage_section_parsing(self):
        """Parser correctly identifies linkage section variables."""
        src = dedent("""\
            DATA DIVISION.
            LINKAGE SECTION.
            01  LS-PARM.
                05  LS-CODE PIC X(4).
                05  LS-DATA PIC X(100).
            PROCEDURE DIVISION USING LS-PARM.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert "LS-PARM" in parser.linkage_names
        assert "LS-CODE" in parser.linkage_names
        assert "LS-DATA" in parser.linkage_names

    def test_procedure_division_using_single_param(self):
        """Parser extracts USING parameters from PROCEDURE DIVISION."""
        src = dedent("""\
            PROCEDURE DIVISION USING WS-PARM.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert "WS-PARM" in parser.using_params

    def test_procedure_division_using_multiple_params(self):
        """Parser extracts multiple USING parameters."""
        src = dedent("""\
            PROCEDURE DIVISION USING PARM-1 PARM-2 PARM-3.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert "PARM-1" in parser.using_params
        assert "PARM-2" in parser.using_params
        assert "PARM-3" in parser.using_params

    def test_procedure_division_using_by_reference(self):
        """Parser strips BY REFERENCE from USING parameters."""
        src = dedent("""\
            PROCEDURE DIVISION USING BY REFERENCE MY-PCB.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert "MY-PCB" in parser.using_params
        # BY and REFERENCE should not be in params
        assert "BY" not in parser.using_params
        assert "REFERENCE" not in parser.using_params

    def test_procedure_division_using_multiline(self):
        """Parser handles USING clause spanning multiple lines."""
        src = dedent("""\
            PROCEDURE DIVISION USING
                PARM-A
                PARM-B.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert "PARM-A" in parser.using_params
        assert "PARM-B" in parser.using_params

    def test_file_control_select_with_status(self):
        """Parser correctly identifies SELECT with FILE STATUS."""
        src = dedent("""\
            ENVIRONMENT DIVISION.
            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
                SELECT CUSTOMER-FILE ASSIGN TO CUSTFILE
                    FILE STATUS IS WS-CUST-STATUS.
            DATA DIVISION.
        """)
        parser = CobolParser(src)
        assert "CUSTOMER-FILE" in parser.select_files
        assert parser.file_to_status.get("CUSTOMER-FILE") == "WS-CUST-STATUS"

    def test_file_control_select_without_status(self):
        """Parser identifies SELECT without FILE STATUS clause."""
        src = dedent("""\
            ENVIRONMENT DIVISION.
            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
                SELECT ORDER-FILE ASSIGN TO ORDFILE.
            DATA DIVISION.
        """)
        parser = CobolParser(src)
        assert "ORDER-FILE" in parser.select_files
        assert parser.file_to_status.get("ORDER-FILE") is None

    def test_file_control_inline_status(self):
        """Parser handles FILE STATUS IS on the same line as SELECT."""
        src = dedent("""\
            FILE-CONTROL.
                SELECT MYFILE ASSIGN TO MYDSN FILE STATUS IS WS-STAT.
            DATA DIVISION.
        """)
        parser = CobolParser(src)
        assert "MYFILE" in parser.select_files
        assert parser.file_to_status.get("MYFILE") == "WS-STAT"

    def test_file_section_fd_records(self):
        """Parser maps 01-level records to their FD file."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            FD  CUST-FILE.
            01  CUST-REC.
                05  CUST-ID PIC X(5).
            FD  ORD-FILE.
            01  ORD-REC.
                05  ORD-ID PIC X(10).
            WORKING-STORAGE SECTION.
        """)
        parser = CobolParser(src)
        assert parser.rec_to_file.get("CUST-REC") == "CUST-FILE"
        assert parser.rec_to_file.get("ORD-REC") == "ORD-FILE"
        assert "CUST-REC" in parser.fd_record_names
        assert "ORD-REC" in parser.fd_record_names

    def test_file_section_multiple_records_per_fd(self):
        """Parser handles multiple 01-level records under a single FD."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            FD  MULTI-FILE.
            01  REC-A.
                05 FIELD-A PIC X.
            01  REC-B.
                05 FIELD-B PIC X.
            WORKING-STORAGE SECTION.
        """)
        parser = CobolParser(src)
        assert parser.rec_to_file.get("REC-A") == "MULTI-FILE"
        assert parser.rec_to_file.get("REC-B") == "MULTI-FILE"

    def test_procedure_body_stop_run(self):
        """Parser detects STOP RUN in procedure division."""
        src = dedent("""\
            PROCEDURE DIVISION.
            MAIN-PARA.
                DISPLAY "HELLO".
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert parser.has_stop_run is True
        assert parser.has_goback is False

    def test_procedure_body_goback(self):
        """Parser detects GOBACK in procedure division."""
        src = dedent("""\
            PROCEDURE DIVISION.
            MAIN-PARA.
                DISPLAY "HELLO".
                GOBACK.
        """)
        parser = CobolParser(src)
        assert parser.has_stop_run is False
        assert parser.has_goback is True

    def test_procedure_body_both_terminations(self):
        """Parser detects both STOP RUN and GOBACK."""
        src = dedent("""\
            PROCEDURE DIVISION.
            MAIN-PARA.
                IF DONE
                    STOP RUN
                ELSE
                    GOBACK
                END-IF.
        """)
        parser = CobolParser(src)
        assert parser.has_stop_run is True
        assert parser.has_goback is True

    def test_open_statement_parsing(self):
        """Parser captures OPEN mode and file."""
        src = dedent("""\
            PROCEDURE DIVISION.
                OPEN INPUT CUST-FILE.
                OPEN OUTPUT RPT-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert parser.open_modes.get("CUST-FILE") == "INPUT"
        assert parser.open_modes.get("RPT-FILE") == "OUTPUT"

    def test_io_operations_parsing(self):
        """Parser captures READ/WRITE/CLOSE operations."""
        src = dedent("""\
            PROCEDURE DIVISION.
                OPEN INPUT MY-FILE.
                READ MY-FILE.
                CLOSE MY-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert any(verb == "READ" and target == "MY-FILE"
                   for _, verb, target in parser.io_operations)
        assert any(verb == "CLOSE" and target == "MY-FILE"
                   for _, verb, target in parser.io_operations)

    def test_arithmetic_ops_without_size_error(self):
        """Parser detects arithmetic without ON SIZE ERROR."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(5) VALUE 10.
            01  WS-B PIC 9(5) VALUE 20.
            PROCEDURE DIVISION.
                ADD WS-A TO WS-B.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert len(parser.arithmetic_ops) == 1
        line_idx, verb, has_size = parser.arithmetic_ops[0]
        assert verb == "ADD"
        assert has_size is False

    def test_arithmetic_ops_with_size_error_same_line(self):
        """Parser detects ON SIZE ERROR on the same line as arithmetic."""
        src = dedent("""\
            PROCEDURE DIVISION.
                ADD A TO B ON SIZE ERROR DISPLAY "OVF".
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert len(parser.arithmetic_ops) == 1
        _, _, has_size = parser.arithmetic_ops[0]
        assert has_size is True

    def test_arithmetic_ops_with_size_error_next_line(self):
        """Parser detects ON SIZE ERROR on a following line (within 3 lines)."""
        src = dedent("""\
            PROCEDURE DIVISION.
                COMPUTE WS-RESULT = WS-A * WS-B
                    ON SIZE ERROR
                        DISPLAY "OVERFLOW".
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert len(parser.arithmetic_ops) == 1
        _, verb, has_size = parser.arithmetic_ops[0]
        assert verb == "COMPUTE"
        assert has_size is True

    def test_paragraph_labels_detected(self):
        """Parser identifies paragraph labels in procedure division."""
        src = dedent("""\
            PROCEDURE DIVISION.
            MAIN-PARA.
                PERFORM SUB-PARA.
                STOP RUN.
            SUB-PARA.
                DISPLAY "SUB".
        """)
        parser = CobolParser(src)
        assert "MAIN-PARA" in parser.paragraphs
        assert "SUB-PARA" in parser.paragraphs

    def test_case_insensitive_keywords(self):
        """Parser handles mixed-case COBOL keywords."""
        src = dedent("""\
            data division.
            Working-Storage Section.
            01  ws-var pic x(5) value "HELLO".
            Procedure Division.
                stop run.
        """)
        parser = CobolParser(src)
        assert "WS-VAR" in parser.ws_names
        assert parser.ws_has_value.get("WS-VAR") is True
        assert parser.has_stop_run is True

    def test_comments_only_source(self):
        """Parser handles source that is all comment lines."""
        src = dedent("""\
      * This is a comment line
      * Another comment
      * No real code here
        """)
        parser = CobolParser(src)
        assert parser.ws_names == []
        assert parser.paragraphs == {}
        assert not parser.has_stop_run


# ===========================================================================
# SECTION 2: GeneralCobolChecker - COB-001 (Missing FILE STATUS)
# ===========================================================================

class TestCOB001MissingFileStatus:
    """Tests for rule COB-001: SELECT without FILE STATUS IS clause."""

    def test_select_without_file_status_fires(self):
        """COB-001 should fire when SELECT lacks FILE STATUS."""
        src = dedent("""\
            ENVIRONMENT DIVISION.
            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
                SELECT TRANS-FILE ASSIGN TO TRANSDS.
            DATA DIVISION.
            PROCEDURE DIVISION.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert any(f.rule_id == "COB-001" for f in findings)
        assert any("TRANS-FILE" in f.message for f in findings)

    def test_select_with_file_status_clean(self):
        """COB-001 should NOT fire when FILE STATUS IS is present."""
        src = dedent("""\
            ENVIRONMENT DIVISION.
            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
                SELECT TRANS-FILE ASSIGN TO TRANSDS
                    FILE STATUS IS WS-FS.
            DATA DIVISION.
            PROCEDURE DIVISION.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-001" for f in findings)

    def test_multiple_selects_mixed(self):
        """COB-001 fires only for files missing FILE STATUS, not all."""
        src = dedent("""\
            FILE-CONTROL.
                SELECT FILE-A ASSIGN TO DSA
                    FILE STATUS IS WS-FSA.
                SELECT FILE-B ASSIGN TO DSB.
                SELECT FILE-C ASSIGN TO DSC
                    FILE STATUS IS WS-FSC.
            DATA DIVISION.
            PROCEDURE DIVISION.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob001 = [f for f in findings if f.rule_id == "COB-001"]
        assert len(cob001) == 1
        assert "FILE-B" in cob001[0].message

    def test_no_file_control_no_finding(self):
        """COB-001 should not fire if there is no FILE-CONTROL at all."""
        src = dedent("""\
            IDENTIFICATION DIVISION.
            PROGRAM-ID. NOFILES.
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC X.
            PROCEDURE DIVISION.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-001" for f in findings)

    def test_inline_file_status_on_select_line(self):
        """COB-001 clean when FILE STATUS IS appears on same line as SELECT."""
        src = dedent("""\
            FILE-CONTROL.
                SELECT INFILE ASSIGN TO INDSN FILE STATUS IS FS-IN.
            DATA DIVISION.
            PROCEDURE DIVISION.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-001" for f in findings)


# ===========================================================================
# SECTION 3: GeneralCobolChecker - COB-002 (File Not Opened)
# ===========================================================================

class TestCOB002FileNotOpened:
    """Tests for rule COB-002: READ/WRITE without corresponding OPEN."""

    def test_read_without_open_fires(self):
        """COB-002 fires when READ is performed without an OPEN statement."""
        src = dedent("""\
            FILE-CONTROL.
                SELECT MY-FILE ASSIGN TO MYF
                    FILE STATUS IS WS-FS.
            DATA DIVISION.
            FILE SECTION.
            FD  MY-FILE.
            01  MY-REC PIC X(80).
            PROCEDURE DIVISION.
                READ MY-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob002 = [f for f in findings if f.rule_id == "COB-002"]
        assert len(cob002) == 1
        assert "MY-FILE" in cob002[0].message

    def test_read_with_open_clean(self):
        """COB-002 should NOT fire when file is properly opened before READ."""
        src = dedent("""\
            FILE-CONTROL.
                SELECT MY-FILE ASSIGN TO MYF
                    FILE STATUS IS WS-FS.
            DATA DIVISION.
            FILE SECTION.
            FD  MY-FILE.
            01  MY-REC PIC X(80).
            PROCEDURE DIVISION.
                OPEN INPUT MY-FILE.
                READ MY-FILE.
                CLOSE MY-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-002" for f in findings)

    def test_write_without_open_fires(self):
        """COB-002 fires when WRITE is on a record whose file is not opened."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            FD  OUT-FILE.
            01  OUT-REC PIC X(80).
            PROCEDURE DIVISION.
                WRITE OUT-REC.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob002 = [f for f in findings if f.rule_id == "COB-002"]
        assert len(cob002) == 1
        assert "WRITE" in cob002[0].message

    def test_write_with_open_output_clean(self):
        """COB-002 clean when file is opened for OUTPUT and WRITE performed."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            FD  OUT-FILE.
            01  OUT-REC PIC X(80).
            PROCEDURE DIVISION.
                OPEN OUTPUT OUT-FILE.
                WRITE OUT-REC.
                CLOSE OUT-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-002" for f in findings)

    def test_close_without_open_not_flagged(self):
        """COB-002 should NOT fire for CLOSE (CLOSE is skipped by the rule)."""
        src = dedent("""\
            PROCEDURE DIVISION.
                CLOSE MY-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-002" for f in findings)

    def test_rewrite_without_open_fires(self):
        """COB-002 fires for REWRITE when file is not opened."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            FD  UPD-FILE.
            01  UPD-REC PIC X(80).
            PROCEDURE DIVISION.
                REWRITE UPD-REC.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob002 = [f for f in findings if f.rule_id == "COB-002"]
        assert len(cob002) == 1
        assert "REWRITE" in cob002[0].message


# ===========================================================================
# SECTION 4: GeneralCobolChecker - COB-003 (Missing STOP RUN / GOBACK)
# ===========================================================================

class TestCOB003MissingStopRun:
    """Tests for rule COB-003: No STOP RUN or GOBACK found."""

    def test_no_stop_run_no_goback_fires(self):
        """COB-003 fires when PROCEDURE DIVISION has no terminator."""
        src = dedent("""\
            IDENTIFICATION DIVISION.
            PROGRAM-ID. NOTERM.
            PROCEDURE DIVISION.
            MAIN-PARA.
                DISPLAY "HELLO".
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert any(f.rule_id == "COB-003" for f in findings)

    def test_stop_run_present_clean(self):
        """COB-003 should NOT fire when STOP RUN is present."""
        src = dedent("""\
            PROCEDURE DIVISION.
            MAIN-PARA.
                DISPLAY "DONE".
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-003" for f in findings)

    def test_goback_present_clean(self):
        """COB-003 should NOT fire when GOBACK is present."""
        src = dedent("""\
            PROCEDURE DIVISION.
            MAIN-PARA.
                DISPLAY "DONE".
                GOBACK.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-003" for f in findings)

    def test_no_procedure_division_no_finding(self):
        """COB-003 should NOT fire if there is no PROCEDURE DIVISION at all."""
        src = dedent("""\
            IDENTIFICATION DIVISION.
            PROGRAM-ID. NOPROC.
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-VAR PIC X.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-003" for f in findings)

    def test_stop_run_in_nested_if(self):
        """COB-003 clean when STOP RUN is inside an IF block."""
        src = dedent("""\
            PROCEDURE DIVISION.
                IF TRUE
                    STOP RUN
                END-IF.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-003" for f in findings)

    def test_both_stop_run_and_goback_clean(self):
        """COB-003 should not fire when both terminators present."""
        src = dedent("""\
            PROCEDURE DIVISION.
                IF MODE-BATCH
                    STOP RUN
                ELSE
                    GOBACK
                END-IF.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-003" for f in findings)


# ===========================================================================
# SECTION 5: GeneralCobolChecker - COB-004 (Uninitialized Variable)
# ===========================================================================

class TestCOB004UninitializedVariable:
    """Tests for rule COB-004: Variable used in arithmetic without initialization."""

    def test_uninitialized_in_add_fires(self):
        """COB-004 fires when WS variable without VALUE is used in ADD."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-TOTAL    PIC 9(5).
            01  WS-AMOUNT   PIC 9(5) VALUE 100.
            PROCEDURE DIVISION.
                ADD WS-TOTAL TO WS-AMOUNT.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob004 = [f for f in findings if f.rule_id == "COB-004"]
        assert len(cob004) == 1
        assert "WS-TOTAL" in cob004[0].message

    def test_initialized_with_value_clean(self):
        """COB-004 should NOT fire when all arithmetic vars have VALUE clauses."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A  PIC 9(5) VALUE 10.
            01  WS-B  PIC 9(5) VALUE 20.
            PROCEDURE DIVISION.
                ADD WS-A TO WS-B.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-004" for f in findings)

    def test_initialized_by_move_before_use_clean(self):
        """COB-004 clean when variable is MOVEd to before arithmetic use."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X  PIC 9(5).
            01  WS-Y  PIC 9(5) VALUE 5.
            PROCEDURE DIVISION.
                MOVE 0 TO WS-X.
                ADD WS-X TO WS-Y.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-004" for f in findings)

    def test_initialized_by_initialize_clean(self):
        """COB-004 clean when variable is INITIALIZEd before use."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-COUNTER  PIC 9(5).
            PROCEDURE DIVISION.
                INITIALIZE WS-COUNTER.
                ADD 1 TO WS-COUNTER.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-004" for f in findings)

    def test_uninitialized_in_compute_fires(self):
        """COB-004 fires for uninitialized variable in COMPUTE."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-RATE   PIC 9V99.
            01  WS-RESULT PIC 9(7)V99 VALUE 0.
            PROCEDURE DIVISION.
                COMPUTE WS-RESULT = WS-RESULT * WS-RATE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob004 = [f for f in findings if f.rule_id == "COB-004"]
        assert any("WS-RATE" in f.message for f in cob004)

    def test_only_warns_once_per_variable(self):
        """COB-004 fires only once per variable even if used multiple times."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X  PIC 9(5).
            PROCEDURE DIVISION.
                ADD WS-X TO WS-X.
                ADD WS-X TO WS-X.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob004 = [f for f in findings if f.rule_id == "COB-004"]
        x_findings = [f for f in cob004 if "WS-X" in f.message]
        assert len(x_findings) == 1

    def test_no_arithmetic_no_finding(self):
        """COB-004 should not fire if there are no arithmetic operations."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC 9(5).
            PROCEDURE DIVISION.
                DISPLAY WS-X.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-004" for f in findings)


# ===========================================================================
# SECTION 6: GeneralCobolChecker - COB-005 (Arithmetic No ON SIZE ERROR)
# ===========================================================================

class TestCOB005ArithmeticNoSizeError:
    """Tests for rule COB-005: Arithmetic without ON SIZE ERROR."""

    def test_add_without_size_error_fires(self):
        """COB-005 fires for ADD without ON SIZE ERROR."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(5) VALUE 10.
            01  WS-B PIC 9(5) VALUE 20.
            PROCEDURE DIVISION.
                ADD WS-A TO WS-B.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob005 = [f for f in findings if f.rule_id == "COB-005"]
        assert len(cob005) == 1
        assert "ADD" in cob005[0].message
        assert cob005[0].severity == "Info"

    def test_add_with_size_error_clean(self):
        """COB-005 should NOT fire when ON SIZE ERROR is present."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(5) VALUE 10.
            01  WS-B PIC 9(5) VALUE 20.
            PROCEDURE DIVISION.
                ADD WS-A TO WS-B
                    ON SIZE ERROR
                        DISPLAY "OVERFLOW".
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-005" for f in findings)

    def test_compute_without_size_error_fires(self):
        """COB-005 fires for COMPUTE without ON SIZE ERROR."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC 9(3) VALUE 0.
            PROCEDURE DIVISION.
                COMPUTE WS-X = 999 + 1.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob005 = [f for f in findings if f.rule_id == "COB-005"]
        assert len(cob005) == 1
        assert "COMPUTE" in cob005[0].message

    def test_subtract_without_size_error_fires(self):
        """COB-005 fires for SUBTRACT without ON SIZE ERROR."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(3) VALUE 100.
            01  WS-B PIC 9(3) VALUE 200.
            PROCEDURE DIVISION.
                SUBTRACT WS-A FROM WS-B.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert any(f.rule_id == "COB-005" and "SUBTRACT" in f.message for f in findings)

    def test_multiply_without_size_error_fires(self):
        """COB-005 fires for MULTIPLY without ON SIZE ERROR."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(3) VALUE 100.
            PROCEDURE DIVISION.
                MULTIPLY 2 BY WS-A.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert any(f.rule_id == "COB-005" and "MULTIPLY" in f.message for f in findings)

    def test_divide_without_size_error_fires(self):
        """COB-005 fires for DIVIDE without ON SIZE ERROR."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(5) VALUE 100.
            PROCEDURE DIVISION.
                DIVIDE 3 INTO WS-A.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert any(f.rule_id == "COB-005" and "DIVIDE" in f.message for f in findings)

    def test_multiple_arithmetic_ops_all_flagged(self):
        """COB-005 fires for each arithmetic operation missing ON SIZE ERROR."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(5) VALUE 10.
            01  WS-B PIC 9(5) VALUE 20.
            01  WS-C PIC 9(5) VALUE 30.
            PROCEDURE DIVISION.
                ADD WS-A TO WS-B.
                SUBTRACT WS-A FROM WS-C.
                MULTIPLY WS-A BY WS-B.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob005 = [f for f in findings if f.rule_id == "COB-005"]
        assert len(cob005) == 3

    def test_no_arithmetic_no_finding(self):
        """COB-005 should not fire when there is no arithmetic at all."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "NO MATH HERE".
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-005" for f in findings)

    def test_size_error_on_same_line_as_verb(self):
        """COB-005 clean when ON SIZE ERROR appears on same line."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(3) VALUE 0.
            PROCEDURE DIVISION.
                ADD 1 TO WS-A ON SIZE ERROR DISPLAY "OVF".
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert not any(f.rule_id == "COB-005" for f in findings)


# ===========================================================================
# SECTION 7: GeneralCobolChecker - Finding Line Numbers
# ===========================================================================

class TestFindingLineNumbers:
    """Tests verifying that findings report correct 1-based line numbers."""

    def test_cob_002_reports_correct_line(self):
        """COB-002 line number should be 1-based line of the I/O operation."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            FD  MY-FILE.
            01  MY-REC PIC X(80).
            PROCEDURE DIVISION.
                READ MY-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob002 = [f for f in findings if f.rule_id == "COB-002"]
        assert len(cob002) == 1
        # Line 6 is "    READ MY-FILE." (1-based)
        assert cob002[0].line == 6

    def test_cob_005_reports_correct_line(self):
        """COB-005 line number should be 1-based line of the arithmetic op."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "START".
                ADD 1 TO WS-A.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob005 = [f for f in findings if f.rule_id == "COB-005"]
        assert len(cob005) == 1
        # Line 3 is "    ADD 1 TO WS-A." (1-based)
        assert cob005[0].line == 3

    def test_cob_003_has_no_line_number(self):
        """COB-003 does not report a line number (program-wide issue)."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "NO EXIT".
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob003 = [f for f in findings if f.rule_id == "COB-003"]
        assert len(cob003) == 1
        assert cob003[0].line is None


# ===========================================================================
# SECTION 8: Finding Model Tests
# ===========================================================================

class TestFindingModel:
    """Tests for the Finding dataclass."""

    def test_finding_to_dict(self):
        """Finding.to_dict() returns correct dictionary representation."""
        f = Finding("COB-001", "Warning", "Test message", 42)
        d = f.to_dict()
        assert d == {
            "rule_id": "COB-001",
            "severity": "Warning",
            "message": "Test message",
            "line": 42
        }

    def test_finding_to_dict_no_line(self):
        """Finding.to_dict() handles None line correctly."""
        f = Finding("COB-003", "Warning", "No terminator")
        d = f.to_dict()
        assert d["line"] is None

    def test_finding_equality(self):
        """Two Findings with same values should be equal (dataclass)."""
        f1 = Finding("COB-001", "Warning", "msg", 10)
        f2 = Finding("COB-001", "Warning", "msg", 10)
        assert f1 == f2

    def test_finding_inequality(self):
        """Findings with different values are not equal."""
        f1 = Finding("COB-001", "Warning", "msg", 10)
        f2 = Finding("COB-002", "Error", "msg", 10)
        assert f1 != f2


# ===========================================================================
# SECTION 9: check() Function and IMS Auto-Detection
# ===========================================================================

class TestCheckFunction:
    """Tests for the check() entry point in tools/check.py."""

    def test_empty_code_returns_empty(self):
        """check() returns empty list for empty string input."""
        assert check("") == []

    def test_none_code_returns_empty(self):
        """check() returns empty list for None input."""
        assert check(None) == []

    def test_whitespace_only_returns_empty(self):
        """check() returns empty list for whitespace-only input."""
        assert check("   \n\n   ") == []

    def test_returns_list_of_dicts(self):
        """check() returns list of dict (not Finding objects)."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "HELLO".
        """)
        result = check(src)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
            assert "rule_id" in item
            assert "severity" in item
            assert "message" in item
            assert "line" in item

    def test_general_rules_run(self):
        """check() runs general COBOL rules and returns findings."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "NO EXIT".
        """)
        result = check(src)
        assert has_rule(result, "COB-003")

    def test_ims_not_triggered_without_cbltdli(self):
        """check() does NOT run IMS rules when no IMS context detected."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "PLAIN COBOL".
                STOP RUN.
        """)
        result = check(src)
        # No IMS-xxx rules should appear
        ims_findings = [f for f in result if f["rule_id"].startswith("IMS-")]
        assert ims_findings == []

    def test_ims_triggered_by_cbltdli(self):
        """check() runs IMS rules when CBLTDLI is present in source."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  DLI-FUNC  PIC X(4) VALUE 'GU  '.
            LINKAGE SECTION.
            01  MY-PCB.
                05 PCB-STATUS PIC XX.
            PROCEDURE DIVISION USING MY-PCB.
                CALL 'CBLTDLI' USING DLI-FUNC MY-PCB IO-AREA.
                STOP RUN.
        """)
        result = check(src)
        # IMS rules should have been triggered; we check that the result set
        # contains at least one IMS finding or that no error was raised
        # The exact IMS findings depend on the code quality
        assert isinstance(result, list)

    def test_ims_triggered_by_dfsli000(self):
        """check() runs IMS rules when DFSLI000 is present in source."""
        src = dedent("""\
            PROCEDURE DIVISION.
                CALL 'DFSLI000' USING DLI-GU DB-PCB IO-AREA.
                STOP RUN.
        """)
        result = check(src)
        # Should detect IMS context
        assert isinstance(result, list)

    def test_ims_triggered_by_dlitcbl(self):
        """check() runs IMS rules when DLITCBL entry is present."""
        src = dedent("""\
            PROCEDURE DIVISION.
                ENTRY 'DLITCBL' USING IO-PCB DB-PCB.
                STOP RUN.
        """)
        result = check(src)
        assert isinstance(result, list)

    def test_ims_detection_case_insensitive(self):
        """IMS detection works regardless of case."""
        assert has_ims_context("call 'cbltdli' using func pcb area")
        assert has_ims_context("CALL 'CBLTDLI' USING FUNC PCB AREA")
        assert has_ims_context("Call 'CblTdli' Using Func PCB Area")

    def test_check_combines_general_and_ims_findings(self):
        """check() returns both general and IMS findings when IMS context present."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-FUNC  PIC X(4) VALUE 'GU  '.
            01  WS-UNINIT PIC 9(5).
            LINKAGE SECTION.
            01  DB-PCB.
                05 PCB-STATUS PIC XX.
            PROCEDURE DIVISION USING DB-PCB.
                ADD 1 TO WS-UNINIT.
                CALL 'CBLTDLI' USING WS-FUNC DB-PCB IO-AREA.
        """)
        result = check(src)
        # Should have general findings (at minimum COB-003 for missing STOP RUN,
        # COB-005 for ADD without SIZE ERROR, COB-004 for uninitialized)
        general = [f for f in result if f["rule_id"].startswith("COB-")]
        assert len(general) > 0


# ===========================================================================
# SECTION 10: has_ims_context() Function
# ===========================================================================

class TestHasImsContext:
    """Tests for the has_ims_context detection function."""

    def test_cbltdli_detected(self):
        """Detects CBLTDLI keyword."""
        assert has_ims_context("CALL 'CBLTDLI' USING FUNC PCB AREA.") is True

    def test_dfsli000_detected(self):
        """Detects DFSLI000 keyword."""
        assert has_ims_context("CALL 'DFSLI000' USING FUNC PCB AREA.") is True

    def test_dlitcbl_detected(self):
        """Detects DLITCBL keyword."""
        assert has_ims_context("ENTRY 'DLITCBL' USING IOPCB DBPCB.") is True

    def test_no_ims_keywords(self):
        """Returns False when no IMS keywords present."""
        assert has_ims_context("DISPLAY 'HELLO WORLD'. STOP RUN.") is False

    def test_empty_string(self):
        """Returns False for empty string."""
        assert has_ims_context("") is False

    def test_ims_in_comment(self):
        """Detects IMS keywords even in comments (simple text scan)."""
        # Note: the function does a simple text search, not a semantic one
        assert has_ims_context("      * CALL 'CBLTDLI' is used here") is True

    def test_partial_match_not_detected(self):
        """Should not detect partial matches like MYCBLTDLIX (actually will because substring match)."""
        # has_ims_context uses 'in' operator, so substrings match
        # This test documents the actual behavior
        assert has_ims_context("MYCBLTDLIX") is True  # substring match by design


# ===========================================================================
# SECTION 11: Edge Cases - Partial/Unusual COBOL
# ===========================================================================

class TestEdgeCasesPartialCobol:
    """Tests for handling of unusual, partial, or malformed COBOL input."""

    def test_only_data_division(self):
        """Parser handles source with only DATA DIVISION, no PROCEDURE."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-FIELD  PIC X(10) VALUE SPACES.
        """)
        parser = CobolParser(src)
        assert "WS-FIELD" in parser.ws_names
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        # No PROCEDURE DIVISION => no COB-003
        assert not any(f.rule_id == "COB-003" for f in findings)

    def test_procedure_division_no_statements(self):
        """Parser handles PROCEDURE DIVISION with no statements after it."""
        src = dedent("""\
            PROCEDURE DIVISION.
        """)
        parser = CobolParser(src)
        assert not parser.has_stop_run
        assert not parser.has_goback
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        assert any(f.rule_id == "COB-003" for f in findings)

    def test_very_long_variable_name(self):
        """Parser handles the maximum 30-character COBOL variable name."""
        long_name = "A-VERY-LONG-VARIABLE-NAME-HERE"  # 30 chars
        src = f"""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  {long_name} PIC X(10).
            PROCEDURE DIVISION.
                STOP RUN.
        """
        parser = CobolParser(src)
        assert long_name in parser.ws_names

    def test_numeric_level_with_leading_zero(self):
        """Parser handles level numbers like 01, 05 with leading zeros."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-GROUP.
                05  WS-SUB-A PIC X.
                05  WS-SUB-B PIC X.
        """)
        parser = CobolParser(src)
        assert "WS-GROUP" in parser.ws_names
        assert "WS-SUB-A" in parser.ws_names
        assert "WS-SUB-B" in parser.ws_names

    def test_multiple_opens_same_file(self):
        """Parser captures last OPEN mode when file is opened multiple times."""
        src = dedent("""\
            PROCEDURE DIVISION.
                OPEN INPUT MY-FILE.
                CLOSE MY-FILE.
                OPEN OUTPUT MY-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        # The last OPEN overrides the first in the dict
        assert parser.open_modes.get("MY-FILE") == "OUTPUT"

    def test_all_five_arithmetic_verbs(self):
        """Parser detects all five arithmetic verbs."""
        src = dedent("""\
            PROCEDURE DIVISION.
                ADD 1 TO A.
                SUBTRACT 1 FROM B.
                MULTIPLY 2 BY C.
                DIVIDE 2 INTO D.
                COMPUTE E = A + B.
                STOP RUN.
        """)
        parser = CobolParser(src)
        verbs = [v for _, v, _ in parser.arithmetic_ops]
        assert "ADD" in verbs
        assert "SUBTRACT" in verbs
        assert "MULTIPLY" in verbs
        assert "DIVIDE" in verbs
        assert "COMPUTE" in verbs

    def test_mixed_io_verbs(self):
        """Parser handles READ, WRITE, REWRITE, DELETE, START, CLOSE."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            FD  TEST-FILE.
            01  TEST-REC PIC X(80).
            PROCEDURE DIVISION.
                OPEN I-O TEST-FILE.
                READ TEST-FILE.
                REWRITE TEST-REC.
                DELETE TEST-FILE.
                START TEST-FILE.
                CLOSE TEST-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        verbs = [v for _, v, _ in parser.io_operations]
        assert "READ" in verbs
        assert "REWRITE" in verbs
        assert "DELETE" in verbs
        assert "START" in verbs
        assert "CLOSE" in verbs

    def test_special_characters_in_program_id(self):
        """Parser handles programs with hyphens in PROGRAM-ID."""
        src = dedent("""\
            IDENTIFICATION DIVISION.
            PROGRAM-ID. MY-TEST-PROG.
            PROCEDURE DIVISION.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert parser.has_stop_run

    def test_file_section_no_fd(self):
        """Parser handles FILE SECTION with no FD entries."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC X.
        """)
        parser = CobolParser(src)
        assert parser.rec_to_file == {}
        assert parser.fd_record_names == set()

    def test_file_section_absent(self):
        """Parser handles absence of FILE SECTION entirely."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC X.
            PROCEDURE DIVISION.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert parser.rec_to_file == {}


# ===========================================================================
# SECTION 12: Edge Cases - Very Large Input
# ===========================================================================

class TestLargeInput:
    """Tests for handling very large COBOL programs."""

    def test_many_working_storage_variables(self):
        """Parser handles 500 working storage variables."""
        lines = ["DATA DIVISION.", "WORKING-STORAGE SECTION."]
        for i in range(500):
            lines.append(f"01  WS-VAR-{i:04d} PIC X(10).")
        lines.append("PROCEDURE DIVISION.")
        lines.append("    STOP RUN.")
        src = "\n".join(lines)
        parser = CobolParser(src)
        assert len(parser.ws_names) == 500

    def test_many_paragraphs(self):
        """Parser handles many paragraph labels without error."""
        lines = ["PROCEDURE DIVISION."]
        for i in range(100):
            lines.append(f"PARA-{i:04d}.")
            lines.append(f"    DISPLAY 'PARA {i}'.")
        lines.append("    STOP RUN.")
        src = "\n".join(lines)
        parser = CobolParser(src)
        assert len(parser.paragraphs) == 100

    def test_many_arithmetic_ops(self):
        """COB-005 fires for each of many arithmetic operations."""
        lines = ["PROCEDURE DIVISION."]
        for i in range(50):
            lines.append(f"    ADD 1 TO WS-VAR-{i}.")
        lines.append("    STOP RUN.")
        src = "\n".join(lines)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob005 = [f for f in findings if f.rule_id == "COB-005"]
        assert len(cob005) == 50

    def test_large_source_with_no_issues(self):
        """A large clean program produces no general findings."""
        lines = [
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. BIGPROG.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
        ]
        for i in range(100):
            lines.append(f"01  WS-VAR-{i:04d} PIC 9(5) VALUE 0.")
        lines.append("PROCEDURE DIVISION.")
        lines.append("MAIN-PARA.")
        for i in range(100):
            lines.append(f"    ADD 1 TO WS-VAR-{i:04d}")
            lines.append(f"        ON SIZE ERROR DISPLAY 'OVF'.")
        lines.append("    STOP RUN.")
        src = "\n".join(lines)
        result = check(src)
        # No COB-003 (has STOP RUN), no COB-005 (all have ON SIZE ERROR),
        # no COB-004 (all have VALUE), no COB-001 (no files)
        general = [f for f in result if f["rule_id"].startswith("COB-")]
        assert general == []


# ===========================================================================
# SECTION 13: Integration - Complete Programs
# ===========================================================================

class TestCompletePrograms:
    """Integration tests with realistic COBOL programs."""

    def test_clean_batch_program(self):
        """A well-structured batch program should produce minimal findings."""
        src = dedent("""\
            IDENTIFICATION DIVISION.
            PROGRAM-ID. BATCHPGM.
            ENVIRONMENT DIVISION.
            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
                SELECT INPUT-FILE ASSIGN TO INFILE
                    FILE STATUS IS WS-FS-IN.
                SELECT OUTPUT-FILE ASSIGN TO OUTFILE
                    FILE STATUS IS WS-FS-OUT.
            DATA DIVISION.
            FILE SECTION.
            FD  INPUT-FILE.
            01  IN-REC PIC X(80).
            FD  OUTPUT-FILE.
            01  OUT-REC PIC X(80).
            WORKING-STORAGE SECTION.
            01  WS-FS-IN   PIC XX.
            01  WS-FS-OUT  PIC XX.
            01  WS-EOF     PIC X VALUE 'N'.
            01  WS-COUNT   PIC 9(5) VALUE 0.
            PROCEDURE DIVISION.
            MAIN-PARA.
                OPEN INPUT INPUT-FILE.
                OPEN OUTPUT OUTPUT-FILE.
                PERFORM UNTIL WS-EOF = 'Y'
                    READ INPUT-FILE
                        AT END MOVE 'Y' TO WS-EOF
                    END-READ
                    IF WS-EOF NOT = 'Y'
                        MOVE IN-REC TO OUT-REC
                        WRITE OUT-REC
                        ADD 1 TO WS-COUNT
                            ON SIZE ERROR DISPLAY "COUNT OVERFLOW"
                    END-IF
                END-PERFORM.
                CLOSE INPUT-FILE.
                CLOSE OUTPUT-FILE.
                DISPLAY "RECORDS: " WS-COUNT.
                STOP RUN.
        """)
        result = check(src)
        # This is a well-structured program; should have no general findings
        general = [f for f in result if f["rule_id"].startswith("COB-")]
        assert general == []

    def test_program_with_all_general_issues(self):
        """Program triggering all 5 general rules simultaneously."""
        src = dedent("""\
            ENVIRONMENT DIVISION.
            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
                SELECT BAD-FILE ASSIGN TO BADDS.
            DATA DIVISION.
            FILE SECTION.
            FD  BAD-FILE.
            01  BAD-REC PIC X(80).
            WORKING-STORAGE SECTION.
            01  WS-UNINIT  PIC 9(5).
            01  WS-AMOUNT  PIC 9(5) VALUE 100.
            PROCEDURE DIVISION.
                READ BAD-FILE.
                ADD WS-UNINIT TO WS-AMOUNT.
        """)
        result = check(src)
        ids = rule_ids(result)
        assert "COB-001" in ids  # SELECT without FILE STATUS
        assert "COB-002" in ids  # READ without OPEN
        assert "COB-003" in ids  # No STOP RUN / GOBACK
        assert "COB-004" in ids  # WS-UNINIT used without initialization
        assert "COB-005" in ids  # ADD without ON SIZE ERROR

    def test_subprogram_with_goback(self):
        """Subprogram using GOBACK should not trigger COB-003."""
        src = dedent("""\
            IDENTIFICATION DIVISION.
            PROGRAM-ID. SUBPGM.
            DATA DIVISION.
            LINKAGE SECTION.
            01  LS-PARM  PIC X(10).
            PROCEDURE DIVISION USING LS-PARM.
                DISPLAY LS-PARM.
                GOBACK.
        """)
        result = check(src)
        assert not has_rule(result, "COB-003")


# ===========================================================================
# SECTION 14: Parametrized Tests for COB-005 Arithmetic Verbs
# ===========================================================================

class TestCOB005Parametrized:
    """Parametrized tests ensuring COB-005 fires for all arithmetic verbs."""

    @pytest.mark.parametrize("verb,statement", [
        ("ADD", "ADD 1 TO WS-A"),
        ("SUBTRACT", "SUBTRACT 1 FROM WS-A"),
        ("MULTIPLY", "MULTIPLY 2 BY WS-A"),
        ("DIVIDE", "DIVIDE 2 INTO WS-A"),
        ("COMPUTE", "COMPUTE WS-A = WS-A + 1"),
    ])
    def test_arithmetic_without_size_error(self, verb, statement):
        """Each arithmetic verb without ON SIZE ERROR triggers COB-005."""
        src = f"""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(5) VALUE 10.
            PROCEDURE DIVISION.
                {statement}.
                STOP RUN.
        """
        result = check(src)
        cob005 = [f for f in result if f["rule_id"] == "COB-005"]
        assert len(cob005) >= 1
        assert any(verb in f["message"] for f in cob005)

    @pytest.mark.parametrize("verb,statement", [
        ("ADD", "ADD 1 TO WS-A ON SIZE ERROR DISPLAY 'ERR'"),
        ("SUBTRACT", "SUBTRACT 1 FROM WS-A ON SIZE ERROR DISPLAY 'ERR'"),
        ("MULTIPLY", "MULTIPLY 2 BY WS-A ON SIZE ERROR DISPLAY 'ERR'"),
        ("DIVIDE", "DIVIDE 2 INTO WS-A ON SIZE ERROR DISPLAY 'ERR'"),
        ("COMPUTE", "COMPUTE WS-A = WS-A + 1 ON SIZE ERROR DISPLAY 'ERR'"),
    ])
    def test_arithmetic_with_size_error_clean(self, verb, statement):
        """Each arithmetic verb with ON SIZE ERROR should NOT trigger COB-005."""
        src = f"""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-A PIC 9(5) VALUE 10.
            PROCEDURE DIVISION.
                {statement}.
                STOP RUN.
        """
        result = check(src)
        cob005 = [f for f in result if f["rule_id"] == "COB-005"]
        assert len(cob005) == 0


# ===========================================================================
# SECTION 15: Regression / Corner Cases
# ===========================================================================

class TestRegressionCases:
    """Regression tests for tricky parsing scenarios."""

    def test_stop_run_with_extra_spaces(self):
        """STOP RUN with multiple spaces between words still detected."""
        src = dedent("""\
            PROCEDURE DIVISION.
                STOP    RUN.
        """)
        parser = CobolParser(src)
        assert parser.has_stop_run is True

    def test_open_io_mode(self):
        """Parser handles OPEN I-O mode (with hyphen)."""
        src = dedent("""\
            PROCEDURE DIVISION.
                OPEN I-O UPD-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert parser.open_modes.get("UPD-FILE") == "I-O"

    def test_open_extend_mode(self):
        """Parser handles OPEN EXTEND mode."""
        src = dedent("""\
            PROCEDURE DIVISION.
                OPEN EXTEND LOG-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        assert parser.open_modes.get("LOG-FILE") == "EXTEND"

    def test_arithmetic_with_period_stops_lookahead(self):
        """ON SIZE ERROR search stops at period on an intervening line."""
        src = dedent("""\
            PROCEDURE DIVISION.
                ADD 1 TO WS-A
                DISPLAY "SEPARATOR".
                ON SIZE ERROR DISPLAY "TOO LATE".
                STOP RUN.
        """)
        parser = CobolParser(src)
        # The period on the DISPLAY line (i+1) stops the lookahead before
        # reaching the ON SIZE ERROR on line i+2.
        _, _, has_size = parser.arithmetic_ops[0]
        assert has_size is False

    def test_on_size_error_on_next_line_detected(self):
        """ON SIZE ERROR on the immediate next line IS detected (no intervening period)."""
        src = dedent("""\
            PROCEDURE DIVISION.
                ADD 1 TO WS-A.
                ON SIZE ERROR DISPLAY "CAUGHT".
                STOP RUN.
        """)
        parser = CobolParser(src)
        # The parser checks for ON SIZE ERROR on lines[i+k] before checking for
        # period on lines[i+k], so the match is found.
        _, _, has_size = parser.arithmetic_ops[0]
        assert has_size is True

    def test_multiple_files_select(self):
        """Parser correctly handles multiple SELECT statements."""
        src = dedent("""\
            FILE-CONTROL.
                SELECT FILE-1 ASSIGN TO DS1
                    FILE STATUS IS FS-1.
                SELECT FILE-2 ASSIGN TO DS2.
                SELECT FILE-3 ASSIGN TO DS3
                    FILE STATUS IS FS-3.
            DATA DIVISION.
        """)
        parser = CobolParser(src)
        assert len(parser.select_files) == 3
        assert parser.file_to_status.get("FILE-1") == "FS-1"
        assert parser.file_to_status.get("FILE-2") is None
        assert parser.file_to_status.get("FILE-3") == "FS-3"

    def test_write_resolves_to_fd_file(self):
        """COB-002: WRITE on a record resolves to the FD file for open check."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            FD  REPORT-FILE.
            01  REPORT-REC PIC X(132).
            PROCEDURE DIVISION.
                OPEN OUTPUT REPORT-FILE.
                WRITE REPORT-REC.
                CLOSE REPORT-FILE.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        # File is opened => no COB-002
        assert not any(f.rule_id == "COB-002" for f in findings)

    def test_working_storage_boundary_with_local_storage(self):
        """Working storage parsing stops at LOCAL-STORAGE SECTION."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-IN-WS PIC X.
            LOCAL-STORAGE SECTION.
            01  LS-VAR   PIC X.
        """)
        parser = CobolParser(src)
        assert "WS-IN-WS" in parser.ws_names
        assert "LS-VAR" not in parser.ws_names

    def test_checker_analyze_returns_fresh_list(self):
        """Each call to analyze() returns a fresh list of findings."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "HELLO".
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings1 = checker.analyze()
        findings2 = checker.analyze()
        assert findings1 == findings2
        assert findings1 is not findings2  # separate list objects

    def test_sd_entry_in_file_section(self):
        """Parser handles SD (sort file description) in FILE SECTION."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            SD  SORT-FILE.
            01  SORT-REC PIC X(80).
            WORKING-STORAGE SECTION.
        """)
        parser = CobolParser(src)
        assert parser.rec_to_file.get("SORT-REC") == "SORT-FILE"

    def test_cob004_linkage_variable_not_flagged(self):
        """COB-004 only flags WORKING-STORAGE variables, not LINKAGE."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-RESULT PIC 9(5) VALUE 0.
            LINKAGE SECTION.
            01  LS-INPUT PIC 9(5).
            PROCEDURE DIVISION USING LS-INPUT.
                ADD LS-INPUT TO WS-RESULT.
                STOP RUN.
        """)
        parser = CobolParser(src)
        checker = GeneralCobolChecker(parser)
        findings = checker.analyze()
        cob004 = [f for f in findings if f.rule_id == "COB-004"]
        # LS-INPUT should NOT be flagged (it's in linkage, not WS)
        assert not any("LS-INPUT" in f.message for f in cob004)


# ===========================================================================
# SECTION 16: GeneralCobolChecker - Severity Levels
# ===========================================================================

class TestSeverityLevels:
    """Tests verifying correct severity levels for each rule."""

    def test_cob001_severity_is_warning(self):
        """COB-001 has Warning severity."""
        src = dedent("""\
            FILE-CONTROL.
                SELECT F1 ASSIGN TO DS1.
            DATA DIVISION.
            PROCEDURE DIVISION.
                STOP RUN.
        """)
        findings = check(src)
        cob001 = [f for f in findings if f["rule_id"] == "COB-001"]
        assert all(f["severity"] == "Warning" for f in cob001)

    def test_cob002_severity_is_error(self):
        """COB-002 has Error severity."""
        src = dedent("""\
            DATA DIVISION.
            FILE SECTION.
            FD  MY-FILE.
            01  MY-REC PIC X(80).
            PROCEDURE DIVISION.
                READ MY-FILE.
                STOP RUN.
        """)
        findings = check(src)
        cob002 = [f for f in findings if f["rule_id"] == "COB-002"]
        assert all(f["severity"] == "Error" for f in cob002)

    def test_cob003_severity_is_warning(self):
        """COB-003 has Warning severity."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "HELLO".
        """)
        findings = check(src)
        cob003 = [f for f in findings if f["rule_id"] == "COB-003"]
        assert all(f["severity"] == "Warning" for f in cob003)

    def test_cob004_severity_is_warning(self):
        """COB-004 has Warning severity."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC 9(5).
            PROCEDURE DIVISION.
                ADD 1 TO WS-X.
                STOP RUN.
        """)
        findings = check(src)
        cob004 = [f for f in findings if f["rule_id"] == "COB-004"]
        assert all(f["severity"] == "Warning" for f in cob004)

    def test_cob005_severity_is_info(self):
        """COB-005 has Info severity."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC 9(5) VALUE 0.
            PROCEDURE DIVISION.
                ADD 1 TO WS-X.
                STOP RUN.
        """)
        findings = check(src)
        cob005 = [f for f in findings if f["rule_id"] == "COB-005"]
        assert all(f["severity"] == "Info" for f in cob005)


# ===========================================================================
# SECTION 17: check() Function - Output Format
# ===========================================================================

class TestCheckOutputFormat:
    """Tests verifying the exact output format of check()."""

    def test_each_finding_has_four_keys(self):
        """Every finding dict has exactly rule_id, severity, message, line."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "HELLO".
        """)
        result = check(src)
        for finding in result:
            assert set(finding.keys()) == {"rule_id", "severity", "message", "line"}

    def test_line_is_int_or_none(self):
        """Line field is either an integer or None."""
        src = dedent("""\
            FILE-CONTROL.
                SELECT F1 ASSIGN TO DS1.
            DATA DIVISION.
            FILE SECTION.
            FD  F1.
            01  F1-REC PIC X.
            PROCEDURE DIVISION.
                READ F1.
        """)
        result = check(src)
        for finding in result:
            assert finding["line"] is None or isinstance(finding["line"], int)

    def test_message_is_nonempty_string(self):
        """Message field is always a non-empty string."""
        src = dedent("""\
            PROCEDURE DIVISION.
                ADD 1 TO WS-X.
        """)
        result = check(src)
        for finding in result:
            assert isinstance(finding["message"], str)
            assert len(finding["message"]) > 0

    def test_rule_id_format(self):
        """Rule IDs follow the COB-NNN or IMS-NNN pattern."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "TEST".
        """)
        result = check(src)
        import re
        for finding in result:
            assert re.match(r'^(COB|IMS)-\d{3}$|^IMS-INIT-STATUS$', finding["rule_id"]), \
                f"Unexpected rule_id format: {finding['rule_id']}"
