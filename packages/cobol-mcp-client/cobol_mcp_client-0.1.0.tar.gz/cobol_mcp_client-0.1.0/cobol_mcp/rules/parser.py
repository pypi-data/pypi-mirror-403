from __future__ import annotations

import re


class CobolParser:
    """
    Shared COBOL source parser. Extracts structural information from COBOL source
    text for use by both general and IMS-specific rule checkers.
    """

    SIZE_ERROR_LOOKAHEAD = 3  # lines to scan forward for ON SIZE ERROR

    def __init__(self, text: str):
        self.text = text
        self.lines = [ln.rstrip('\n') for ln in text.splitlines()]

        # Working Storage
        self.ws_names: list[str] = []
        self.ws_has_value: dict[str, bool] = {}  # name -> whether it has a VALUE clause

        # Linkage Section
        self.linkage_names: list[str] = []

        # Procedure Division
        self.using_params: list[str] = []
        self.paragraphs: dict[str, int] = {}  # paragraph name -> line index

        # File handling
        self.select_files: set[str] = set()  # file names from SELECT
        self.file_to_status: dict[str, str | None] = {}  # file -> status var (or None)
        self.rec_to_file: dict[str, str] = {}  # record 01 name -> FD name
        self.fd_record_names: set[str] = set()
        self.open_modes: dict[str, str] = {}  # file -> mode (INPUT/OUTPUT/I-O/EXTEND)

        # I/O operations found: (line_index, verb, target)
        self.io_operations: list[tuple[int, str, str]] = []

        # Arithmetic operations: (line_index, verb)
        self.arithmetic_ops: list[tuple[int, str, bool]] = []  # (line, verb, has_size_error)

        # Control flow
        self.has_stop_run: bool = False
        self.has_goback: bool = False

        # Run all parse methods
        self._parse_working_storage()
        self._parse_linkage_section()
        self._parse_procedure_using()
        self._parse_file_control()
        self._parse_file_section()
        self._parse_procedure_body()

    def _parse_working_storage(self):
        """Parse WORKING-STORAGE SECTION for variable declarations."""
        in_ws = False
        for i, ln in enumerate(self.lines):
            u = ln.upper()
            if 'WORKING-STORAGE SECTION' in u:
                in_ws = True
                continue
            if in_ws and ('LINKAGE SECTION' in u or 'PROCEDURE DIVISION' in u
                          or 'LOCAL-STORAGE SECTION' in u or 'FILE SECTION' in u):
                in_ws = False
            if not in_ws:
                continue

            # Match level numbers 01-49 and 77
            m = re.search(r'^\s*(0?[1-9]|[1-4]\d|77)\s+([A-Z0-9-]+)\b', u)
            if m:
                name = m.group(2)
                if name == 'FILLER':
                    continue
                self.ws_names.append(name)
                self.ws_has_value[name] = bool(re.search(r'\bVALUE\b', u))

    def _parse_linkage_section(self):
        """Parse LINKAGE SECTION for variable declarations."""
        in_ls = False
        for i, ln in enumerate(self.lines):
            u = ln.upper()
            if 'LINKAGE SECTION' in u:
                in_ls = True
                continue
            if in_ls and ('PROCEDURE DIVISION' in u or 'LOCAL-STORAGE SECTION' in u
                          or 'WORKING-STORAGE SECTION' in u):
                in_ls = False
            if not in_ls:
                continue

            m = re.search(r'^\s*(0?[1-9]|[1-4]\d|77)\s+([A-Z0-9-]+)\b', u)
            if m:
                name = m.group(2)
                if name == 'FILLER':
                    continue
                self.linkage_names.append(name)

    def _parse_procedure_using(self):
        """Parse PROCEDURE DIVISION USING and ENTRY 'DLITCBL' USING."""
        for i, ln in enumerate(self.lines):
            if 'PROCEDURE DIVISION' in ln.upper():
                block = ln
                j = i + 1
                while '.' not in block and j < len(self.lines):
                    block += ' ' + self.lines[j]
                    j += 1
                uu = block.upper()
                if 'USING' in uu:
                    after = uu.split('USING', 1)[1]
                    names = re.findall(r'[A-Z0-9-]+', after.split('.')[0])
                    self.using_params = [n for n in names if n not in ('BY', 'REFERENCE', 'CONTENT', 'VALUE')]
                break

    def _parse_file_control(self):
        """Parse FILE-CONTROL for SELECT and FILE STATUS clauses."""
        in_fc = False
        cur_file = None
        sel_re = re.compile(r'^\s*SELECT\s+([A-Z0-9-]+)\b', re.IGNORECASE)
        fs_re = re.compile(r'\bFILE\s+STATUS\s+(?:IS\s+)?([A-Z0-9-]+)\b', re.IGNORECASE)

        for i, ln in enumerate(self.lines):
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

                # Check for FILE STATUS on same line
                mfs = fs_re.search(ln)
                if mfs:
                    self.file_to_status[cur_file] = mfs.group(1).upper()
                continue

            mfs = fs_re.search(ln)
            if mfs and cur_file:
                self.file_to_status[cur_file] = mfs.group(1).upper()

    def _parse_file_section(self):
        """Parse FILE SECTION for FD records and 01-level record names."""
        file_sec_start = None
        for idx, ln in enumerate(self.lines):
            if re.search(r'^\s*FILE\s+SECTION\s*\.', ln, re.IGNORECASE):
                file_sec_start = idx
                break
        if file_sec_start is None:
            return

        boundary = re.compile(
            r'^\s*(WORKING-STORAGE|LINKAGE|LOCAL-STORAGE|REPORT|COMMUNICATION)\s+SECTION\s*\.'
            r'|^\s*[A-Z-]+\s+DIVISION\s*\.',
            re.IGNORECASE,
        )
        n = len(self.lines)
        i = file_sec_start + 1
        while i < n and not boundary.search(self.lines[i]):
            m_fd = re.match(r'^\s*(FD|SD)\s+([A-Z0-9-]+)\s*\.', self.lines[i], re.IGNORECASE)
            if not m_fd:
                i += 1
                continue

            current_fd = m_fd.group(2).upper()
            i += 1

            while i < n and not boundary.search(self.lines[i]):
                if re.match(r'^\s*(FD|SD)\s+[A-Z0-9-]+\s*\.', self.lines[i], re.IGNORECASE):
                    break
                m01 = re.match(r'^\s*01\s+([A-Z0-9-]+)\b', self.lines[i], re.IGNORECASE)
                if m01:
                    rec = m01.group(1).upper()
                    self.rec_to_file[rec] = current_fd
                    self.fd_record_names.add(rec)
                i += 1

    def _parse_procedure_body(self):
        """Parse PROCEDURE DIVISION body for I/O, arithmetic, control flow, and paragraphs."""
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

            # STOP RUN / GOBACK
            if re.search(r'\bSTOP\s+RUN\b', u):
                self.has_stop_run = True
            if re.search(r'\bGOBACK\b', u):
                self.has_goback = True

            # OPEN statements
            for m in open_re.finditer(ln):
                mode = m.group(1).upper()
                fname = m.group(2).upper()
                self.open_modes[fname] = mode

            # I/O operations
            for m in io_re.finditer(ln):
                verb = m.group(1).upper()
                target = m.group(2).upper()
                self.io_operations.append((i, verb, target))

            # Arithmetic operations
            verb_match = arith_re.search(ln)
            if verb_match:
                # Check if ON SIZE ERROR is on same line or next few lines
                has_size = bool(size_error_re.search(ln))
                if not has_size:
                    # Look ahead up to 3 lines for ON SIZE ERROR
                    for k in range(1, self.SIZE_ERROR_LOOKAHEAD + 1):
                        if i + k < len(self.lines):
                            if size_error_re.search(self.lines[i + k]):
                                has_size = True
                                break
                            # Stop if we hit a period (end of statement)
                            if '.' in self.lines[i + k]:
                                break
                self.arithmetic_ops.append((i, verb_match.group(1).upper(), has_size))

            # Paragraph names (standard COBOL format: starts at column 8, ends with period)
            para_match = para_re.match(ln)
            if para_match:
                para_name = para_match.group(1).upper()
                self.paragraphs[para_name] = i
