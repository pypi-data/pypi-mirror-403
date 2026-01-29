from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path

RULES_PATH = Path(__file__).parent.parent / "resources" / "rules.md"
_RULE_HEADING = re.compile(r"^### ((?:COB|IMS)\S+)\s", re.MULTILINE)


@lru_cache(maxsize=1)
def _parse_rules() -> dict[str, str]:
    text = RULES_PATH.read_text(encoding="utf-8")
    rules: dict[str, str] = {}
    matches = list(_RULE_HEADING.finditer(text))
    for i, m in enumerate(matches):
        rule_id = m.group(1)
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_match = re.search(r"^## ", text[m.end():end], re.MULTILINE)
        if section_match:
            end = m.end() + section_match.start()
        rules[rule_id] = text[start:end].strip()
    return rules


def get_rule(rule_id: str) -> str | None:
    return _parse_rules().get(rule_id.upper())


def get_fix_hint(rule_id: str) -> str:
    block = get_rule(rule_id)
    if not block:
        return ""
    m = re.search(r"\*\*Fix:\*\*\s*(.+)", block)
    return m.group(1).strip() if m else ""


def list_rule_ids() -> list[str]:
    return list(_parse_rules().keys())
