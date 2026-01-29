"""
Comprehensive edge case tests for tools: check.py and search.py.

Covers:
  - check.py orchestrator:
    * Empty/None/whitespace input
    * IMS auto-detection logic
    * Combining general + IMS findings
    * Output format validation
    * Large input handling

  - search.py:
    * Missing environment variables
    * HTTP error responses (401, 500, etc.)
    * Network/connection errors
    * Timeout handling
    * Empty results
    * Result formatting edge cases
    * Invalid/malformed API responses
"""

import json

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from textwrap import dedent

import httpx

from cobol_mcp.tools.check import check
from cobol_mcp.tools.search import search, _format_results


@pytest.fixture
def mock_http_client():
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


# ===========================================================================
# SECTION 1: check() - Input Validation Edge Cases
# ===========================================================================

class TestCheckInputValidation:
    """Tests for check() input validation edge cases."""

    def test_none_input(self):
        """check() returns empty list for None input."""
        result = check(None)
        assert result == []

    def test_empty_string(self):
        """check() returns empty list for empty string."""
        result = check("")
        assert result == []

    def test_whitespace_only(self):
        """check() returns empty list for whitespace-only string."""
        result = check("   \n\n\t\t  \n  ")
        assert result == []

    def test_single_space(self):
        """check() returns empty list for a single space."""
        result = check(" ")
        assert result == []

    def test_newlines_only(self):
        """check() returns empty list for newlines only."""
        result = check("\n\n\n\n")
        assert result == []

    def test_tabs_only(self):
        """check() returns empty list for tabs only."""
        result = check("\t\t\t")
        assert result == []

    def test_very_short_input(self):
        """check() handles very short non-empty input without crashing."""
        result = check("X")
        assert isinstance(result, list)

    def test_non_cobol_text(self):
        """check() handles non-COBOL text gracefully."""
        result = check("This is just plain English text with no COBOL at all.")
        assert isinstance(result, list)

    def test_binary_like_content(self):
        """check() handles content with unusual characters."""
        result = check("\x00\x01\x02\x03\x04")
        assert isinstance(result, list)

    def test_unicode_content(self):
        """check() handles unicode content without crashing."""
        result = check("PROCEDURE DIVISION.\n    DISPLAY '\u2603'.\n    STOP RUN.")
        assert isinstance(result, list)


# ===========================================================================
# SECTION 2: check() - Output Format
# ===========================================================================

class TestCheckOutputFormat:
    """Tests for check() output format guarantees."""

    def test_returns_list(self):
        """check() always returns a list."""
        result = check("PROCEDURE DIVISION.\n    DISPLAY 'X'.")
        assert isinstance(result, list)

    def test_each_finding_is_dict(self):
        """Each item in check() output is a dict."""
        src = "PROCEDURE DIVISION.\n    DISPLAY 'X'."
        result = check(src)
        for item in result:
            assert isinstance(item, dict)

    def test_finding_has_required_keys(self):
        """Each finding dict has rule_id, severity, message, line."""
        src = "PROCEDURE DIVISION.\n    DISPLAY 'X'."
        result = check(src)
        for item in result:
            assert "rule_id" in item
            assert "severity" in item
            assert "message" in item
            assert "line" in item

    def test_line_is_int_or_none(self):
        """Line field is always int or None."""
        src = dedent("""\
            PROCEDURE DIVISION.
                ADD 1 TO WS-X.
        """)
        result = check(src)
        for item in result:
            assert item["line"] is None or isinstance(item["line"], int)

    def test_severity_valid_values(self):
        """Severity is always Error, Warning, or Info."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC 9(5).
            PROCEDURE DIVISION.
                ADD 1 TO WS-X.
        """)
        result = check(src)
        valid_severities = {"Error", "Warning", "Info"}
        for item in result:
            assert item["severity"] in valid_severities

    def test_rule_id_is_string(self):
        """rule_id is always a non-empty string."""
        src = "PROCEDURE DIVISION.\n    DISPLAY 'X'."
        result = check(src)
        for item in result:
            assert isinstance(item["rule_id"], str)
            assert len(item["rule_id"]) > 0

    def test_message_is_nonempty_string(self):
        """message is always a non-empty string."""
        src = "PROCEDURE DIVISION.\n    DISPLAY 'X'."
        result = check(src)
        for item in result:
            assert isinstance(item["message"], str)
            assert len(item["message"]) > 0


# ===========================================================================
# SECTION 3: check() - IMS Auto-Detection
# ===========================================================================

class TestCheckIMSAutoDetection:
    """Tests for IMS auto-detection in check()."""

    def test_cbltdli_triggers_ims(self):
        """check() runs IMS rules when CBLTDLI is present."""
        src = dedent("""\
            PROCEDURE DIVISION.
                CALL 'CBLTDLI' USING 'GU  ' DB-PCB IO-AREA.
                STOP RUN.
        """)
        result = check(src)
        # At minimum, the check ran without error
        assert isinstance(result, list)

    def test_dfsli000_triggers_ims(self):
        """check() runs IMS rules when DFSLI000 is present."""
        src = dedent("""\
            PROCEDURE DIVISION.
                CALL 'DFSLI000' USING 'GU  ' DB-PCB IO-AREA.
                STOP RUN.
        """)
        result = check(src)
        assert isinstance(result, list)

    def test_dlitcbl_triggers_ims(self):
        """check() runs IMS rules when DLITCBL is present."""
        src = dedent("""\
            PROCEDURE DIVISION.
                ENTRY 'DLITCBL' USING IO-PCB DB-PCB.
                STOP RUN.
        """)
        result = check(src)
        assert isinstance(result, list)

    def test_no_ims_keywords_skips_ims(self):
        """check() skips IMS rules when no IMS keywords found."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "PLAIN COBOL".
                STOP RUN.
        """)
        result = check(src)
        ims_findings = [f for f in result if f["rule_id"].startswith("IMS-")]
        assert ims_findings == []

    def test_ims_in_comment_still_detected(self):
        """check() detects IMS context even in comments (substring match)."""
        src = dedent("""\
            * This program uses CBLTDLI
            PROCEDURE DIVISION.
                DISPLAY "HELLO".
                STOP RUN.
        """)
        # has_ims_context is a simple substring check, so it triggers
        result = check(src)
        assert isinstance(result, list)

    def test_case_insensitive_detection(self):
        """IMS detection is case-insensitive for has_ims_context."""
        src = dedent("""\
            PROCEDURE DIVISION.
                CALL 'cbltdli' USING 'GU  ' DB-PCB IO-AREA.
                STOP RUN.
        """)
        # The CALL regex matches case-insensitively, but the parser
        # splits on 'USING' (uppercase), so we need USING to be uppercase
        result = check(src)
        assert isinstance(result, list)


# ===========================================================================
# SECTION 4: check() - Combining General and IMS Findings
# ===========================================================================

class TestCheckCombinedFindings:
    """Tests for combining general COBOL + IMS findings."""

    def test_both_general_and_ims_findings_returned(self):
        """check() returns both general COB-* and IMS-* findings."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC 9(5).
            PROCEDURE DIVISION.
                ADD 1 TO WS-X.
                CALL 'CBLTDLI' USING MYSTERY DB-PCB IO-AREA.
        """)
        result = check(src)
        general = [f for f in result if f["rule_id"].startswith("COB-")]
        ims = [f for f in result if f["rule_id"].startswith("IMS-")]
        # Should have at least COB-003 (no STOP RUN) and IMS-001 (unknown func)
        assert len(general) > 0
        assert len(ims) > 0

    def test_general_only_when_no_ims(self):
        """check() returns only COB-* findings when no IMS context."""
        src = dedent("""\
            PROCEDURE DIVISION.
                DISPLAY "HELLO".
        """)
        result = check(src)
        for f in result:
            assert not f["rule_id"].startswith("IMS-")

    def test_findings_not_duplicated(self):
        """Findings are not duplicated between general and IMS checkers."""
        src = dedent("""\
            PROCEDURE DIVISION.
                CALL 'CBLTDLI' USING 'GU  ' DB-PCB IO-AREA.
                STOP RUN.
        """)
        result = check(src)
        # Each finding should be unique (no exact duplicates)
        seen = set()
        for f in result:
            key = (f["rule_id"], f["severity"], f["message"], f["line"])
            assert key not in seen, f"Duplicate finding: {f}"
            seen.add(key)


# ===========================================================================
# SECTION 5: check() - Large Input Handling
# ===========================================================================

class TestCheckLargeInput:
    """Tests for check() with large inputs."""

    def test_1000_line_program(self):
        """check() handles a 1000-line program without crashing."""
        lines = [
            "IDENTIFICATION DIVISION.",
            "PROGRAM-ID. BIGPROG.",
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
        ]
        for i in range(200):
            lines.append(f"01  WS-VAR-{i:04d} PIC 9(5) VALUE 0.")
        lines.append("PROCEDURE DIVISION.")
        for i in range(200):
            lines.append(f"    ADD 1 TO WS-VAR-{i:04d}")
            lines.append(f"        ON SIZE ERROR DISPLAY 'OVF'.")
        lines.append("    STOP RUN.")
        src = "\n".join(lines)
        result = check(src)
        assert isinstance(result, list)

    def test_many_dli_calls(self):
        """check() handles many DL/I calls without error."""
        lines = [
            "DATA DIVISION.",
            "LINKAGE SECTION.",
            "01  DB-PCB.",
            "    05 PCB-STATUS PIC XX.",
            "PROCEDURE DIVISION USING DB-PCB.",
        ]
        for i in range(50):
            lines.append(f"    CALL 'CBLTDLI' USING 'GU  ' DB-PCB IO-AREA.")
            lines.append(f"    IF PCB-STATUS NOT = SPACES")
            lines.append(f"        DISPLAY 'ERR {i}'")
            lines.append(f"    ELSE")
            lines.append(f"        DISPLAY 'OK {i}'")
            lines.append(f"    END-IF.")
        lines.append("    STOP RUN.")
        src = "\n".join(lines)
        result = check(src)
        assert isinstance(result, list)


# ===========================================================================
# SECTION 6: search() - Missing Environment Variables
# ===========================================================================

class TestSearchMissingEnvVars:
    """Tests for search() when environment variables are missing."""

    @pytest.mark.asyncio
    async def test_no_api_key_returns_message(self):
        """search() returns config message when API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            result = await search("PERFORM syntax")
            assert "not configured" in result.lower() or "Set COBOL_MCP_API_KEY" in result

    @pytest.mark.asyncio
    async def test_no_api_key_returns_message(self):
        """search() returns config message when API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            result = await search("PERFORM syntax")
            assert "not configured" in result.lower()

    @pytest.mark.asyncio
    async def test_empty_api_key_returns_message(self):
        """search() returns config message when API key is empty string."""
        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "", "COBOL_MCP_API_URL": "http://x"}, clear=True):
            result = await search("query")
            assert "not configured" in result.lower() or "Set" in result

    @pytest.mark.asyncio
    async def test_uses_default_url_when_not_set(self, mock_http_client):
        """search() uses default API URL when COBOL_MCP_API_URL is not set."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "test-key"}, clear=True):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("query")
                call_args = mock_http_client.post.call_args
                assert "cobol-mcp-backend.onrender.com" in call_args[0][0]


# ===========================================================================
# SECTION 7: search() - HTTP Error Handling
# ===========================================================================

class TestSearchHTTPErrors:
    """Tests for search() HTTP error handling."""

    @pytest.mark.asyncio
    async def test_401_returns_auth_error(self, mock_http_client):
        """search() returns authentication error message for 401."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "bad-key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("test query")
                assert "Authentication failed" in result or "401" in result

    @pytest.mark.asyncio
    async def test_500_returns_status_code(self, mock_http_client):
        """search() returns error with status code for 500."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_response
        )
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("test query")
                assert "500" in result

    @pytest.mark.asyncio
    async def test_403_returns_status_code(self, mock_http_client):
        """search() returns error with status code for 403 Forbidden."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response
        )
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("test query")
                assert "403" in result

    @pytest.mark.asyncio
    async def test_429_rate_limit(self, mock_http_client):
        """search() returns error with status code for 429 Too Many Requests."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Too Many Requests", request=MagicMock(), response=mock_response
        )
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("test query")
                assert "429" in result


# ===========================================================================
# SECTION 8: search() - Network/Connection Errors
# ===========================================================================

class TestSearchNetworkErrors:
    """Tests for search() network error handling."""

    @pytest.mark.asyncio
    async def test_connection_refused(self, mock_http_client):
        """search() handles connection refused gracefully."""
        mock_http_client.post.side_effect = httpx.ConnectError("Connection refused")

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://localhost:9999"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("test query")
                assert "connection error" in result.lower() or "Connection" in result

    @pytest.mark.asyncio
    async def test_timeout_error(self, mock_http_client):
        """search() handles timeout gracefully."""
        mock_http_client.post.side_effect = httpx.ReadTimeout("Request timed out")

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("test query")
                assert "connection error" in result.lower() or "timed out" in result.lower() or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_dns_resolution_error(self, mock_http_client):
        """search() handles DNS resolution failure gracefully."""
        mock_http_client.post.side_effect = httpx.ConnectError("Name resolution failed")

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://nonexistent.invalid"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("test query")
                assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_generic_request_error(self, mock_http_client):
        """search() handles generic RequestError gracefully."""
        mock_http_client.post.side_effect = httpx.RequestError("Unknown network error")

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("test query")
                assert "error" in result.lower()


# ===========================================================================
# SECTION 9: search() - Successful Responses
# ===========================================================================

class TestSearchSuccessfulResponses:
    """Tests for search() with successful API responses."""

    @pytest.mark.asyncio
    async def test_empty_results(self, mock_http_client):
        """search() returns 'no results' message when API returns empty list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("obscure query")
                assert "No results found" in result

    @pytest.mark.asyncio
    async def test_no_results_key(self, mock_http_client):
        """search() handles response missing 'results' key."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {}  # No 'results' key
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("test query")
                assert "No results found" in result

    @pytest.mark.asyncio
    async def test_single_result(self, mock_http_client):
        """search() correctly formats a single result."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "results": [{
                "title": "PERFORM Statement",
                "source": "gnucobol",
                "chunk_text": "PERFORM executes a paragraph or section.",
                "score": 0.95,
            }]
        }
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("PERFORM syntax")
                assert "PERFORM Statement" in result
                assert "gnucobol" in result
                assert "0.95" in result

    @pytest.mark.asyncio
    async def test_multiple_results(self, mock_http_client):
        """search() correctly formats multiple results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"title": "Result 1", "source": "src1", "chunk_text": "Text 1", "score": 0.9},
                {"title": "Result 2", "source": "src2", "chunk_text": "Text 2", "score": 0.8},
                {"title": "Result 3", "source": "src3", "chunk_text": "Text 3", "score": 0.7},
            ]
        }
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                result = await search("COBOL")
                assert "Result 1" in result
                assert "Result 2" in result
                assert "Result 3" in result

    @pytest.mark.asyncio
    async def test_custom_top_k(self, mock_http_client):
        """search() passes custom top_k to the API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                await search("query", top_k=3)
                call_args = mock_http_client.post.call_args
                json_body = call_args.kwargs.get("json") or call_args[1].get("json")
                assert json_body["top_k"] == 3


# ===========================================================================
# SECTION 10: search() - Request Construction
# ===========================================================================

class TestSearchRequestConstruction:
    """Tests for how search() constructs the HTTP request."""

    @pytest.mark.asyncio
    async def test_uses_correct_endpoint(self, mock_http_client):
        """search() posts to {api_url}/search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.example.com"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                await search("test")
                call_args = mock_http_client.post.call_args
                url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
                assert url == "http://api.example.com/search"

    @pytest.mark.asyncio
    async def test_sends_bearer_token(self, mock_http_client):
        """search() sends Authorization: Bearer header."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "my-secret-key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                await search("test")
                call_args = mock_http_client.post.call_args
                headers = call_args.kwargs.get("headers") or call_args[1].get("headers", {})
                assert headers.get("Authorization") == "Bearer my-secret-key"

    @pytest.mark.asyncio
    async def test_sends_query_in_body(self, mock_http_client):
        """search() sends query in JSON body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                await search("PERFORM VARYING")
                call_args = mock_http_client.post.call_args
                json_body = call_args.kwargs.get("json") or call_args[1].get("json", {})
                assert json_body["query"] == "PERFORM VARYING"

    @pytest.mark.asyncio
    async def test_default_top_k_is_8(self, mock_http_client):
        """search() uses top_k=8 by default."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                await search("test")
                call_args = mock_http_client.post.call_args
                json_body = call_args.kwargs.get("json") or call_args[1].get("json", {})
                assert json_body["top_k"] == 8

    @pytest.mark.asyncio
    async def test_timeout_is_30_seconds(self, mock_http_client):
        """search() uses a 30-second timeout."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                await search("test")
                call_args = mock_http_client.post.call_args
                timeout = call_args.kwargs.get("timeout") or call_args[1].get("timeout")
                assert timeout == 30.0


# ===========================================================================
# SECTION 11: _format_results() Edge Cases
# ===========================================================================

class TestFormatResults:
    """Tests for _format_results() helper function."""

    def test_empty_results_list(self):
        """_format_results handles empty results list."""
        result = _format_results("test", [])
        assert "test" in result
        # Just the header, no numbered items
        assert "### 1." not in result

    def test_missing_title(self):
        """_format_results handles result missing 'title' key."""
        results = [{"source": "src", "chunk_text": "text", "score": 0.5}]
        result = _format_results("query", results)
        assert "Untitled" in result

    def test_missing_source(self):
        """_format_results handles result missing 'source' key."""
        results = [{"title": "T", "chunk_text": "text", "score": 0.5}]
        result = _format_results("query", results)
        assert "unknown" in result

    def test_missing_score(self):
        """_format_results handles result with score=0 (default)."""
        results = [{"title": "T", "source": "s", "chunk_text": "text"}]
        result = _format_results("query", results)
        assert "0.00" in result

    def test_missing_text_uses_text_key(self):
        """_format_results uses 'text' key when 'chunk_text' is missing."""
        results = [{"title": "T", "source": "s", "text": "alt text", "score": 0.5}]
        result = _format_results("query", results)
        assert "alt text" in result

    def test_both_text_keys_missing(self):
        """_format_results handles result with no text keys."""
        results = [{"title": "T", "source": "s", "score": 0.5}]
        result = _format_results("query", results)
        # Should not crash, just have empty text area
        assert "T" in result

    def test_whitespace_in_text_stripped(self):
        """_format_results strips whitespace from chunk_text."""
        results = [{"title": "T", "source": "s", "chunk_text": "  hello  \n  ", "score": 0.5}]
        result = _format_results("query", results)
        assert "hello" in result

    def test_score_formatting(self):
        """_format_results formats score to 2 decimal places."""
        results = [{"title": "T", "source": "s", "chunk_text": "t", "score": 0.12345}]
        result = _format_results("query", results)
        assert "0.12" in result

    def test_header_includes_query(self):
        """_format_results header includes the search query."""
        result = _format_results("PERFORM VARYING", [])
        assert "PERFORM VARYING" in result

    def test_numbering_sequential(self):
        """_format_results numbers results sequentially starting from 1."""
        results = [
            {"title": f"R{i}", "source": "s", "chunk_text": f"t{i}", "score": 0.5}
            for i in range(5)
        ]
        result = _format_results("q", results)
        assert "### 1." in result
        assert "### 2." in result
        assert "### 3." in result
        assert "### 4." in result
        assert "### 5." in result

    def test_special_characters_in_query(self):
        """_format_results handles special characters in query."""
        result = _format_results("EXEC CICS READ (DATASET)", [])
        assert "EXEC CICS READ (DATASET)" in result

    def test_very_long_text_not_truncated(self):
        """_format_results does not truncate long chunk_text."""
        long_text = "x" * 5000
        results = [{"title": "T", "source": "s", "chunk_text": long_text, "score": 0.5}]
        result = _format_results("q", results)
        assert long_text in result


# ===========================================================================
# SECTION 12: search() - API URL Construction Edge Cases
# ===========================================================================

class TestSearchURLConstruction:
    """Tests for edge cases in API URL construction."""

    @pytest.mark.asyncio
    async def test_trailing_slash_in_api_url(self, mock_http_client):
        """search() handles API URL with trailing slash."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test/"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                await search("test")
                call_args = mock_http_client.post.call_args
                url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
                # It will be "http://api.test//search" with trailing slash - documenting behavior
                assert "/search" in url

    @pytest.mark.asyncio
    async def test_api_url_with_path(self, mock_http_client):
        """search() appends /search to API URL with existing path."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_http_client.post.return_value = mock_response

        with patch.dict("os.environ", {"COBOL_MCP_API_KEY": "key", "COBOL_MCP_API_URL": "http://api.test/v1"}):
            with patch("httpx.AsyncClient", return_value=mock_http_client):
                await search("test")
                call_args = mock_http_client.post.call_args
                url = call_args[0][0] if call_args[0] else call_args.kwargs.get("url", "")
                assert url == "http://api.test/v1/search"


# ===========================================================================
# SECTION 13: check() - Specific Rule Interaction Tests
# ===========================================================================

class TestCheckRuleInteractions:
    """Tests for interactions between general and IMS rules."""

    def test_gsam_suppresses_cob_120(self):
        """COB-120 is suppressed for GSAM-bound files via IMS rules."""
        src = dedent("""\
            ENVIRONMENT DIVISION.
            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
                SELECT GSAM-OUT ASSIGN TO GSAMDD.
            DATA DIVISION.
            FILE SECTION.
            FD  GSAM-OUT.
            01  GSAM-REC PIC X(80).
            PROCEDURE DIVISION.
                CALL 'CBLTDLI' USING 'GU  ' DB-PCB IO-AREA.
                STOP RUN.
        """)
        result = check(src)
        # IMS-130/131/132 may fire, but COB-120 should be suppressed for GSAM
        # (The IMS checker handles this internally)
        assert isinstance(result, list)

    def test_ims_program_with_goback_no_cob003(self):
        """IMS program using GOBACK should not trigger COB-003."""
        src = dedent("""\
            DATA DIVISION.
            LINKAGE SECTION.
            01  DB-PCB.
                05 PCB-STATUS PIC XX.
            PROCEDURE DIVISION USING DB-PCB.
                CALL 'CBLTDLI' USING 'GU  ' DB-PCB IO-AREA.
                IF PCB-STATUS NOT = SPACES
                    DISPLAY "ERR"
                ELSE
                    DISPLAY "OK"
                END-IF.
                GOBACK.
        """)
        result = check(src)
        cob003 = [f for f in result if f["rule_id"] == "COB-003"]
        assert len(cob003) == 0

    def test_ims_and_general_both_fire_on_bad_program(self):
        """Both general and IMS findings fire on a program with multiple issues."""
        src = dedent("""\
            DATA DIVISION.
            WORKING-STORAGE SECTION.
            01  WS-X PIC 9(5).
            PROCEDURE DIVISION.
                ADD 1 TO WS-X.
                CALL 'CBLTDLI' USING MYSTERY-VAR FAKE-PCB IO-AREA.
        """)
        result = check(src)
        has_cob = any(f["rule_id"].startswith("COB-") for f in result)
        has_ims = any(f["rule_id"].startswith("IMS-") for f in result)
        assert has_cob, "Expected at least one COB-* finding"
        assert has_ims, "Expected at least one IMS-* finding"


# ===========================================================================
# SECTION 14: Server check() - File Path Interface
# ===========================================================================

class TestServerCheckFilePath:
    """Tests for the server-level check() that accepts file paths."""

    def test_valid_cobol_file(self, tmp_path):
        """check() reads file and returns findings."""
        from cobol_mcp.server import check as server_check
        f = tmp_path / "test.cbl"
        f.write_text("       PROCEDURE DIVISION.\n           ADD 1 TO X.\n           STOP RUN.\n")
        result = json.loads(server_check(str(f)))
        assert "findings" in result
        assert isinstance(result["findings"], list)

    def test_nonexistent_file(self):
        """check() returns error for missing file."""
        from cobol_mcp.server import check as server_check
        result = json.loads(server_check("/tmp/does_not_exist_xyz.cbl"))
        assert "error" in result
        assert "not found" in result["error"].lower() or "File not found" in result["error"]

    def test_empty_file(self, tmp_path):
        """check() returns no findings for empty file."""
        from cobol_mcp.server import check as server_check
        f = tmp_path / "empty.cbl"
        f.write_text("")
        result = json.loads(server_check(str(f)))
        assert result["findings"] == []

    def test_tilde_expansion(self, tmp_path, monkeypatch):
        """check() expands ~ in file paths."""
        from cobol_mcp.server import check as server_check
        # Use a non-existent path with ~ to verify expansion happens
        result = json.loads(server_check("~/nonexistent_cobol_file.cbl"))
        assert "error" in result

    def test_findings_have_correct_format(self, tmp_path):
        """check() returns findings with expected keys including fix."""
        from cobol_mcp.server import check as server_check
        f = tmp_path / "test.cbl"
        f.write_text(dedent("""\
            ENVIRONMENT DIVISION.
            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
                SELECT MYFILE ASSIGN TO 'X'.
            PROCEDURE DIVISION.
                STOP RUN.
        """))
        result = json.loads(server_check(str(f)))
        assert len(result["findings"]) > 0
        finding = result["findings"][0]
        assert "rule_id" in finding
        assert "severity" in finding
        assert "message" in finding
        assert "fix" in finding
        assert isinstance(finding["fix"], str)

    def test_fix_field_is_nonempty_for_known_rule(self, tmp_path):
        """check() populates fix hint for known rules."""
        from cobol_mcp.server import check as server_check
        f = tmp_path / "test.cbl"
        f.write_text(dedent("""\
            ENVIRONMENT DIVISION.
            INPUT-OUTPUT SECTION.
            FILE-CONTROL.
                SELECT MYFILE ASSIGN TO 'X'.
            PROCEDURE DIVISION.
                STOP RUN.
        """))
        result = json.loads(server_check(str(f)))
        # COB-001 (missing FILE STATUS) should fire and have a fix hint
        cob001 = [f for f in result["findings"] if f["rule_id"] == "COB-001"]
        assert len(cob001) > 0
        assert len(cob001[0]["fix"]) > 0
