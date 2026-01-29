import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .rules.lookup import get_fix_hint, get_rule, list_rule_ids
from .tools.check import check as run_check
from .tools.search import search as run_search
from .tools.translate import lookup_translation

mcp = FastMCP("cobol-mcp")

ALLOWED_EXTENSIONS = {".cbl", ".cob", ".cpy", ".CBL", ".COB", ".CPY"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@mcp.tool()
def check(file_path: str) -> str:
    """
    Analyze a COBOL source file for common issues that LLMs typically miss.

    Pass the absolute path to a .cbl/.cob/.cpy COBOL file. The tool reads
    the file directly — do not paste file contents.

    Runs 30+ rules based on IBM research covering:
    - Missing FILE STATUS checks after I/O operations
    - Uninitialized variables used in arithmetic
    - Files used before OPEN statements
    - Missing STOP RUN / GOBACK
    - Arithmetic without ON SIZE ERROR
    - IMS DL/I issues (auto-detected): invalid function codes, missing PCB
      status checks, GSAM misuse, checkpoint/IOPCB errors

    Returns a list of findings with rule_id, severity, message, line number,
    and fix hint. For full rule docs with code examples, read cobol://rule/{rule_id}.
    """
    path = Path(file_path).expanduser().resolve()

    if path.suffix not in ALLOWED_EXTENSIONS:
        return json.dumps({
            "error": f"Invalid file type: {path.suffix}. Allowed: .cbl, .cob, .cpy",
            "code": "INVALID_EXTENSION"
        })

    if not path.is_file():
        return json.dumps({"error": f"File not found: {file_path}", "code": "FILE_NOT_FOUND"})

    try:
        if path.stat().st_size > MAX_FILE_SIZE:
            return json.dumps({
                "error": f"File too large (max {MAX_FILE_SIZE} bytes)",
                "code": "FILE_TOO_LARGE"
            })
    except OSError as e:
        return json.dumps({"error": f"Cannot access file: {e}", "code": "FILE_ACCESS_ERROR"})

    try:
        code = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return json.dumps({"error": f"Cannot read file: {e}", "code": "FILE_READ_ERROR"})

    findings = run_check(code)
    if not findings:
        return json.dumps({"findings": [], "message": "No issues detected."})

    for f in findings:
        f["fix"] = get_fix_hint(f["rule_id"])

    return json.dumps({"findings": findings}, indent=2)


@mcp.tool()
async def search(query: str, top_k: int = 8) -> str:
    """
    Search COBOL documentation for syntax, patterns, and concepts.

    Uses hybrid search (semantic + keyword) over:
    - GnuCOBOL Programmer's Guide
    - GnuCOBOL Quick Reference
    - GnuCOBOL Sample Programs
    - IBM Enterprise COBOL Language Reference
    - IBM CICS Application Programming Reference
    - Visual COBOL Developer's Guide
    - Visual COBOL Application Modernization Tools
    - Dialect comparison guides

    Examples:
    - "PERFORM VARYING syntax"
    - "how to read a sequential file"
    - "COMP-3 packed decimal byte size"
    - "EXEC CICS READ command"
    - "Visual COBOL managed COBOL .NET"

    Read cobol://context for dialect differences and effective query patterns.
    """
    return await run_search(query, top_k=top_k)


@mcp.resource("cobol://context")
def context() -> str:
    """Read before writing, reviewing, or searching COBOL code. Covers which dialects and documents the search tool indexes (GnuCOBOL, IBM Enterprise COBOL, IBM CICS, Visual COBOL), key dialect syntax differences, effective search query patterns, and PIC clause byte-size formulas."""
    path = Path(__file__).parent / "resources" / "context.md"
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        return f"Error loading context: {e}"


@mcp.resource("cobol://rule/{rule_id}")
def rule_detail(rule_id: str) -> str:
    """Fetch a single check rule by ID (e.g. COB-001, IMS-022). Returns severity, detection logic, and recommended fix."""
    content = get_rule(rule_id)
    if content is None:
        return f"Unknown rule_id: {rule_id}. Valid IDs: {', '.join(list_rule_ids())}"
    return content


@mcp.resource("cobol://rules")
def rules() -> str:
    """Read after running check() to understand findings, or before fixing COBOL/IMS issues. Complete reference of all rule IDs (COB-001 through COB-120, IMS-001 through IMS-170) with severity, detection logic, and recommended fixes."""
    path = Path(__file__).parent / "resources" / "rules.md"
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        return f"Error loading rules: {e}"


@mcp.tool()
def translate_reference(topic: str) -> str:
    """Get COBOL-to-Java translation patterns for a specific topic.

    Returns prescriptive guidance on how to translate COBOL constructs
    to idiomatic Java. Covers data types, control flow, file I/O,
    CICS, DB2 SQL, JCL/batch, and common anti-patterns.

    Example topics:
    - "PIC clause" or "data types"
    - "CICS" or "Spring"
    - "PERFORM" or "control flow"
    - "REDEFINES"
    - "88 level" or "condition names"
    - "GO TO elimination"
    - "JOBOL" or "anti-patterns"
    - "DB2" or "SQL"
    - "file handling" or "sequential"
    - "copybook"
    - "gnucobol" or "compiler"
    """
    return lookup_translation(topic)


@mcp.resource("cobol://gnucobol")
def gnucobol() -> str:
    """GnuCOBOL 3.2 compiler reference — compilation modes, dialect flags,
    debugging options, and environment variables for testing COBOL programs."""
    path = Path(__file__).parent / "resources" / "gnucobol.md"
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as e:
        return f"Error loading GnuCOBOL reference: {e}"


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ["setup", "list-ides", "--help", "-h"]:
        from .cli import main as cli_main
        cli_main()
    else:
        mcp.run()


if __name__ == "__main__":
    main()
