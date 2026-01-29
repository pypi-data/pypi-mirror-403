"""Tests for cobol_mcp.rules.lookup module."""

from cobol_mcp.rules.lookup import get_rule, get_fix_hint, list_rule_ids


class TestGetRule:
    """Tests for get_rule()."""

    def test_known_rule_returns_block(self):
        """get_rule returns a non-empty string for a known rule ID."""
        block = get_rule("COB-001")
        assert block is not None
        assert "COB-001" in block

    def test_unknown_rule_returns_none(self):
        """get_rule returns None for an unknown rule ID."""
        assert get_rule("INVALID-999") is None

    def test_case_insensitive(self):
        """get_rule normalizes to uppercase."""
        assert get_rule("cob-001") is not None
        assert get_rule("ims-020") is not None

    def test_block_contains_severity(self):
        """Rule block contains severity information."""
        block = get_rule("COB-001")
        assert "Severity" in block

    def test_block_contains_fix(self):
        """Rule block contains fix guidance."""
        block = get_rule("COB-001")
        assert "Fix:" in block

    def test_ims_rule(self):
        """get_rule works for IMS rules."""
        block = get_rule("IMS-022")
        assert block is not None
        assert "IMS-022" in block

    def test_block_does_not_bleed_into_next_rule(self):
        """Rule block stops before the next ### heading."""
        block = get_rule("COB-001")
        assert "COB-002" not in block

    def test_block_does_not_bleed_into_next_section(self):
        """Rule block stops before the next ## section heading."""
        block = get_rule("COB-005")
        # COB-005 is the last rule in "General COBOL Rules" section
        # It should not contain content from "File I/O Rules"
        assert "COB-110" not in block


class TestGetFixHint:
    """Tests for get_fix_hint()."""

    def test_known_rule_returns_nonempty(self):
        """get_fix_hint returns a non-empty string for a known rule."""
        hint = get_fix_hint("COB-001")
        assert len(hint) > 0

    def test_unknown_rule_returns_empty(self):
        """get_fix_hint returns empty string for unknown rule."""
        assert get_fix_hint("INVALID-999") == ""

    def test_hint_does_not_include_prefix(self):
        """Fix hint does not include the **Fix:** prefix."""
        hint = get_fix_hint("COB-001")
        assert "**Fix:**" not in hint

    def test_ims_rule_fix_hint(self):
        """get_fix_hint works for IMS rules."""
        hint = get_fix_hint("IMS-022")
        assert len(hint) > 0
        assert "GB" in hint

    def test_case_insensitive(self):
        """get_fix_hint normalizes case."""
        assert get_fix_hint("cob-001") == get_fix_hint("COB-001")

    def test_multiline_fix_returns_first_line(self):
        """For rules with multi-line fix sections, returns just the first line."""
        # IMS-020 has a fix with code block after the first line
        hint = get_fix_hint("IMS-020")
        assert len(hint) > 0
        assert "```" not in hint


class TestListRuleIds:
    """Tests for list_rule_ids()."""

    def test_returns_list(self):
        """list_rule_ids returns a list."""
        ids = list_rule_ids()
        assert isinstance(ids, list)

    def test_contains_cob_rules(self):
        """list_rule_ids includes COB rules."""
        ids = list_rule_ids()
        cob_ids = [r for r in ids if r.startswith("COB-")]
        assert len(cob_ids) > 0

    def test_contains_ims_rules(self):
        """list_rule_ids includes IMS rules."""
        ids = list_rule_ids()
        ims_ids = [r for r in ids if r.startswith("IMS-")]
        assert len(ims_ids) > 0

    def test_all_ids_nonempty_strings(self):
        """All rule IDs are non-empty strings."""
        for rule_id in list_rule_ids():
            assert isinstance(rule_id, str)
            assert len(rule_id) > 0

    def test_known_rules_present(self):
        """Spot-check that specific known rules are present."""
        ids = list_rule_ids()
        assert "COB-001" in ids
        assert "IMS-022" in ids
        assert "IMS-170" in ids
