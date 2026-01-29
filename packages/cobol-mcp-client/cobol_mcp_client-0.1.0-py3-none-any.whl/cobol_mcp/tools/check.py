from __future__ import annotations

from ..rules.models import Finding
from ..rules.parser import CobolParser
from ..rules.general import GeneralCobolChecker
from ..rules.ims import IMSCobolChecker, has_ims_context


def check(code: str | None) -> list[dict]:
    """
    Run COBOL blind-spot detection rules on source code.
    Returns a list of findings (rule_id, severity, message, line).

    Automatically detects IMS context (CBLTDLI/DFSLI000/DLITCBL calls)
    and runs IMS-specific rules in addition to general COBOL rules.
    """
    if not code or not code.strip():
        return []

    # Run general COBOL rules
    parser = CobolParser(code)
    general_checker = GeneralCobolChecker(parser)
    findings: list[Finding] = general_checker.analyze()

    # Run IMS rules if IMS context detected
    if has_ims_context(code):
        ims_checker = IMSCobolChecker(code)
        findings.extend(ims_checker.analyze())

    return [f.to_dict() for f in findings]
