from __future__ import annotations
import re
from .models import Finding
from .parser import CobolParser


class GeneralCobolChecker:
    def __init__(self, parser: CobolParser):
        self.parser = parser
        self.findings: list[Finding] = []

    def analyze(self) -> list[Finding]:
        self.findings = []
        self._rule_cob_001_missing_file_status()
        self._rule_cob_002_file_not_opened()
        self._rule_cob_003_missing_stop_run()
        self._rule_cob_004_uninitialized_variable()
        self._rule_cob_005_arithmetic_no_size_error()
        return self.findings

    def _add(self, rule_id: str, severity: str, message: str, line: int = None):
        self.findings.append(Finding(rule_id, severity, message, None if line is None else line + 1))

    def _rule_cob_001_missing_file_status(self):
        for fname in self.parser.select_files:
            if self.parser.file_to_status.get(fname) is None:
                self._add("COB-001", "Warning",
                    f"SELECT {fname} has no FILE STATUS IS clause. I/O errors will be silent.")

    def _rule_cob_002_file_not_opened(self):
        opened_files = set(self.parser.open_modes.keys())

        for line_idx, verb, target in self.parser.io_operations:
            if verb == 'CLOSE':
                continue

            if verb == 'WRITE':
                file_name = self.parser.rec_to_file.get(target)
                if file_name is None:
                    continue
            elif verb == 'READ':
                file_name = target
            else:
                file_name = self.parser.rec_to_file.get(target, target)

            if file_name not in opened_files:
                self._add("COB-002", "Error",
                    f"{verb} on {target} but no OPEN statement found for file {file_name}.", line_idx)

    def _rule_cob_003_missing_stop_run(self):
        if not self.parser.has_stop_run and not self.parser.has_goback:
            has_proc = any('PROCEDURE DIVISION' in ln.upper() for ln in self.parser.lines)
            if has_proc:
                self._add("COB-003", "Warning", "No STOP RUN or GOBACK found. Program may not terminate properly.")

    def _rule_cob_004_uninitialized_variable(self):
        initialized = {name for name, has_value in self.parser.ws_has_value.items() if has_value}
        in_proc = False

        for i, ln in enumerate(self.parser.lines):
            u = ln.upper()
            if 'PROCEDURE DIVISION' in u:
                in_proc = True
                continue
            if not in_proc:
                continue

            m = re.search(r'\bMOVE\b.*\bTO\s+([A-Z0-9-]+)', u)
            if m:
                initialized.add(m.group(1))

            m = re.search(r'\bINITIALIZE\s+([A-Z0-9-]+)', u)
            if m:
                initialized.add(m.group(1))

            if re.search(r'\b(COMPUTE|ADD|SUBTRACT|MULTIPLY|DIVIDE)\b', u):
                for name in self.parser.ws_names:
                    if name in initialized:
                        continue
                    if re.search(rf'\b{re.escape(name)}\b', u):
                        self._add("COB-004", "Warning",
                            f"Variable {name} used in arithmetic without VALUE clause or prior INITIALIZE/MOVE.", i)
                        initialized.add(name)

    def _rule_cob_005_arithmetic_no_size_error(self):
        for line_idx, verb, has_size_error in self.parser.arithmetic_ops:
            if not has_size_error:
                self._add("COB-005", "Info",
                    f"{verb} at line {line_idx + 1} has no ON SIZE ERROR clause. Overflow will be truncated.", line_idx)
