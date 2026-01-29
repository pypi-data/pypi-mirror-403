from __future__ import annotations
from dataclasses import dataclass, asdict


@dataclass
class Finding:
    rule_id: str
    severity: str
    message: str
    line: int | None = None

    def to_dict(self):
        return asdict(self)
