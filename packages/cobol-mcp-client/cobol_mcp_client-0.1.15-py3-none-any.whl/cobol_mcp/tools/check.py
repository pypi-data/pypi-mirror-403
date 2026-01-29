from __future__ import annotations

from ..rules.models import Finding
from ..rules.parser import CobolParser
from ..rules.general import GeneralCobolChecker
from ..rules.ims import IMSCobolChecker, has_ims_context


def check(code: str | None) -> list[dict]:
    if not code or not code.strip():
        return []

    parser = CobolParser(code)
    general_checker = GeneralCobolChecker(parser)
    findings: list[Finding] = general_checker.analyze()

    if has_ims_context(code):
        ims_checker = IMSCobolChecker(code)
        findings.extend(ims_checker.analyze())

    return [f.to_dict() for f in findings]
