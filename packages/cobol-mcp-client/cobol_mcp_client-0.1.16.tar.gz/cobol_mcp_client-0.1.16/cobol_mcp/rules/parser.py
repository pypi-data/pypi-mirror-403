from __future__ import annotations
import re


class CobolParser:
    SIZE_ERROR_LOOKAHEAD = 3

    def __init__(self, text: str):
        self.text = text
        self.lines = [ln.rstrip('\n') for ln in text.splitlines()]

        self.ws_names: list[str] = []
        self.ws_has_value: dict[str, bool] = {}
        self.linkage_names: list[str] = []
        self.using_params: list[str] = []
        self.paragraphs: dict[str, int] = {}

        self.select_files: set[str] = set()
        self.file_to_status: dict[str, str | None] = {}
        self.rec_to_file: dict[str, str] = {}
        self.fd_record_names: set[str] = set()
        self.open_modes: dict[str, str] = {}

        self.io_operations: list[tuple[int, str, str]] = []
        self.arithmetic_ops: list[tuple[int, str, bool]] = []

        self.has_stop_run: bool = False
        self.has_goback: bool = False

        self._parse_working_storage()
        self._parse_linkage_section()
        self._parse_procedure_using()
        self._parse_file_control()
        self._parse_file_section()
        self._parse_procedure_body()

    def _parse_working_storage(self):
        in_ws = False
        for ln in self.lines:
            u = ln.upper()
            if 'WORKING-STORAGE SECTION' in u:
                in_ws = True
                continue
            if in_ws and any(x in u for x in ['LINKAGE SECTION', 'PROCEDURE DIVISION', 
                                               'LOCAL-STORAGE SECTION', 'FILE SECTION']):
                in_ws = False
            if not in_ws:
                continue

            m = re.search(r'^\s*(0?[1-9]|[1-4]\d|77)\s+([A-Z0-9-]+)\b', u)
            if m and m.group(2) != 'FILLER':
                name = m.group(2)
                self.ws_names.append(name)
                self.ws_has_value[name] = bool(re.search(r'\bVALUE\b', u))

    def _parse_linkage_section(self):
        in_ls = False
        for ln in self.lines:
            u = ln.upper()
            if 'LINKAGE SECTION' in u:
                in_ls = True
                continue
            if in_ls and any(x in u for x in ['PROCEDURE DIVISION', 'LOCAL-STORAGE SECTION',
                                               'WORKING-STORAGE SECTION']):
                in_ls = False
            if not in_ls:
                continue

            m = re.search(r'^\s*(0?[1-9]|[1-4]\d|77)\s+([A-Z0-9-]+)\b', u)
            if m and m.group(2) != 'FILLER':
                self.linkage_names.append(m.group(2))

    def _parse_procedure_using(self):
        for i, ln in enumerate(self.lines):
            if 'PROCEDURE DIVISION' in ln.upper():
                block = ln
                j = i + 1
                while '.' not in block and j < len(self.lines):
                    block += ' ' + self.lines[j]
                    j += 1
                if 'USING' in block.upper():
                    after = block.upper().split('USING', 1)[1]
                    names = re.findall(r'[A-Z0-9-]+', after.split('.')[0])
                    self.using_params = [n for n in names if n not in ('BY', 'REFERENCE', 'CONTENT', 'VALUE')]
                break

    def _parse_file_control(self):
        in_fc = False
        cur_file = None
        sel_re = re.compile(r'^\s*SELECT\s+([A-Z0-9-]+)\b', re.IGNORECASE)
        fs_re = re.compile(r'\bFILE\s+STATUS\s+(?:IS\s+)?([A-Z0-9-]+)\b', re.IGNORECASE)

        for ln in self.lines:
            u = ln.upper()
            if 'FILE-CONTROL' in u:
                in_fc = True
                continue
            if in_fc and ('DATA DIVISION' in u or 'FILE SECTION' in u):
                in_fc = False
            if not in_fc:
                continue

            msel = sel_re.search(ln)
            if msel:
                cur_file = msel.group(1).upper()
                self.select_files.add(cur_file)
                self.file_to_status.setdefault(cur_file, None)
                mfs = fs_re.search(ln)
                if mfs:
                    self.file_to_status[cur_file] = mfs.group(1).upper()
                continue

            mfs = fs_re.search(ln)
            if mfs and cur_file:
                self.file_to_status[cur_file] = mfs.group(1).upper()

    def _parse_file_section(self):
        file_sec_start = None
        for idx, ln in enumerate(self.lines):
            if re.search(r'^\s*FILE\s+SECTION\s*\.', ln, re.IGNORECASE):
                file_sec_start = idx
                break
        if file_sec_start is None:
            return

        boundary = re.compile(
            r'^\s*(WORKING-STORAGE|LINKAGE|LOCAL-STORAGE|REPORT|COMMUNICATION)\s+SECTION\s*\.'
            r'|^\s*[A-Z-]+\s+DIVISION\s*\.', re.IGNORECASE)
        
        i = file_sec_start + 1
        while i < len(self.lines) and not boundary.search(self.lines[i]):
            m_fd = re.match(r'^\s*(FD|SD)\s+([A-Z0-9-]+)\s*\.', self.lines[i], re.IGNORECASE)
            if not m_fd:
                i += 1
                continue

            current_fd = m_fd.group(2).upper()
            i += 1

            while i < len(self.lines) and not boundary.search(self.lines[i]):
                if re.match(r'^\s*(FD|SD)\s+[A-Z0-9-]+\s*\.', self.lines[i], re.IGNORECASE):
                    break
                m01 = re.match(r'^\s*01\s+([A-Z0-9-]+)\b', self.lines[i], re.IGNORECASE)
                if m01:
                    rec = m01.group(1).upper()
                    self.rec_to_file[rec] = current_fd
                    self.fd_record_names.add(rec)
                i += 1

    def _parse_procedure_body(self):
        in_proc = False
        open_re = re.compile(r'\bOPEN\s+(INPUT|OUTPUT|I-O|EXTEND)\s+([A-Z0-9-]+)', re.IGNORECASE)
        io_re = re.compile(r'\b(READ|WRITE|REWRITE|DELETE|CLOSE|START)\s+([A-Z0-9-]+)', re.IGNORECASE)
        arith_re = re.compile(r'\b(COMPUTE|ADD|SUBTRACT|MULTIPLY|DIVIDE)\b', re.IGNORECASE)
        size_error_re = re.compile(r'\bON\s+SIZE\s+ERROR\b', re.IGNORECASE)
        para_re = re.compile(r'^\s*([A-Z][A-Z0-9-]*)\s*\.\s*$', re.IGNORECASE)

        for i, ln in enumerate(self.lines):
            u = ln.upper()

            if 'PROCEDURE DIVISION' in u:
                in_proc = True
                continue
            if not in_proc:
                continue

            if re.search(r'\bSTOP\s+RUN\b', u):
                self.has_stop_run = True
            if re.search(r'\bGOBACK\b', u):
                self.has_goback = True

            for m in open_re.finditer(ln):
                self.open_modes[m.group(2).upper()] = m.group(1).upper()

            for m in io_re.finditer(ln):
                self.io_operations.append((i, m.group(1).upper(), m.group(2).upper()))

            verb_match = arith_re.search(ln)
            if verb_match:
                has_size = bool(size_error_re.search(ln))
                if not has_size:
                    for k in range(1, self.SIZE_ERROR_LOOKAHEAD + 1):
                        if i + k < len(self.lines):
                            if size_error_re.search(self.lines[i + k]):
                                has_size = True
                                break
                            if '.' in self.lines[i + k]:
                                break
                self.arithmetic_ops.append((i, verb_match.group(1).upper(), has_size))

            para_match = para_re.match(ln)
            if para_match:
                self.paragraphs[para_match.group(1).upper()] = i
