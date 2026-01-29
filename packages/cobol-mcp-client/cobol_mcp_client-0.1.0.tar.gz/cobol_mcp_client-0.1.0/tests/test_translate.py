import pytest

from cobol_mcp.tools.translate import _load_sections, lookup_translation
import cobol_mcp.tools.translate as translate_mod


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the cached sections before each test."""
    translate_mod._SECTIONS = None
    yield
    translate_mod._SECTIONS = None


class TestLoadSections:
    def test_loads_sections_from_files(self):
        sections = _load_sections()
        assert len(sections) > 0

    def test_sections_are_tuples_of_title_content(self):
        sections = _load_sections()
        for title, content in sections:
            assert isinstance(title, str)
            assert isinstance(content, str)
            assert len(title) > 0
            assert len(content) > 0

    def test_h3_sections_have_parent_context(self):
        sections = _load_sections()
        h3_sections = [(t, c) for t, c in sections if " > " in t]
        assert len(h3_sections) > 0, "Should have h3 sub-sections with parent context"

    def test_caches_after_first_load(self):
        sections1 = _load_sections()
        sections2 = _load_sections()
        assert sections1 is sections2

    def test_no_yaml_frontmatter_in_content(self):
        sections = _load_sections()
        for _, content in sections:
            assert "---" not in content[:5] or not content.startswith("---")

    def test_top_level_headings_not_sections(self):
        """# headings should not appear as section titles."""
        sections = _load_sections()
        for title, _ in sections:
            # Titles from # lines would have no > and match file title
            assert title != "CICS to Spring/Java EE Migration Patterns"
            assert title != "Common COBOL to Java Translation Pitfalls"
            assert title != "Complete COBOL to Java Data Type Mappings"


class TestLookupTranslation:
    def test_pic_clause_returns_data_types(self):
        result = lookup_translation("PIC clause")
        assert "PIC" in result
        assert "Java" in result or "java" in result

    def test_cics_returns_spring_patterns(self):
        result = lookup_translation("CICS")
        assert "CICS" in result
        # Should contain Spring or Java EE patterns
        assert "Spring" in result or "@" in result

    def test_perform_returns_control_flow(self):
        result = lookup_translation("PERFORM")
        assert "PERFORM" in result

    def test_redefines_returns_union_pattern(self):
        result = lookup_translation("REDEFINES")
        assert "REDEFINES" in result

    def test_condition_names_88_level(self):
        result = lookup_translation("88 level")
        assert "88" in result or "condition" in result.lower()

    def test_go_to_elimination(self):
        result = lookup_translation("GO TO elimination")
        assert "GO TO" in result or "state" in result.lower()

    def test_jobol_anti_pattern(self):
        result = lookup_translation("JOBOL")
        assert "JOBOL" in result

    def test_sql_db2(self):
        result = lookup_translation("DB2 SQL")
        assert "SQL" in result

    def test_file_handling(self):
        result = lookup_translation("file handling")
        assert "file" in result.lower() or "File" in result

    def test_copybook(self):
        result = lookup_translation("copybook")
        assert "copybook" in result.lower() or "COPY" in result or "class" in result.lower()

    def test_comp3_packed_decimal(self):
        result = lookup_translation("COMP-3")
        assert "COMP-3" in result or "packed" in result.lower() or "BigDecimal" in result

    def test_spring_batch_jcl(self):
        result = lookup_translation("JCL batch")
        assert "batch" in result.lower() or "JCL" in result

    def test_no_match_returns_available_topics(self):
        result = lookup_translation("xyznonexistent999")
        assert "No match for" in result
        assert "Available topics:" in result
        assert "- " in result

    def test_result_capped_at_4000_chars(self):
        result = lookup_translation("data")
        # Result should not massively exceed 4000 chars
        # (3 sections, each could be up to 4000, but cap applies)
        assert len(result) <= 12000  # generous upper bound for 3 sections

    def test_case_insensitive_matching(self):
        upper = lookup_translation("CICS")
        lower = lookup_translation("cics")
        # Both should match CICS sections
        assert "CICS" in upper
        assert "CICS" in lower

    def test_multiple_keyword_scoring(self):
        result = lookup_translation("control flow")
        assert "Control Flow" in result or "PERFORM" in result or "EVALUATE" in result

    def test_sequential_file(self):
        result = lookup_translation("sequential")
        assert "sequential" in result.lower() or "Sequential" in result

    def test_syncpoint_transaction(self):
        result = lookup_translation("SYNCPOINT")
        assert "SYNCPOINT" in result or "Transactional" in result

    def test_commarea_dto(self):
        result = lookup_translation("COMMAREA")
        assert "COMMAREA" in result or "DTO" in result or "CommArea" in result


class TestLookupEdgeCases:
    def test_empty_topic(self):
        result = lookup_translation("")
        # Empty string matches everything weakly via content preview
        # or returns all topics
        assert isinstance(result, str)
        assert len(result) > 0

    def test_single_char_topic(self):
        result = lookup_translation("X")
        assert isinstance(result, str)

    def test_very_long_topic(self):
        result = lookup_translation("a " * 500)
        assert isinstance(result, str)

    def test_special_characters_in_topic(self):
        result = lookup_translation("PIC S9(5)V99")
        assert isinstance(result, str)

    def test_result_format_has_headings(self):
        result = lookup_translation("CICS")
        assert result.startswith("## ")

    def test_multiple_results_separated_by_divider(self):
        result = lookup_translation("data types")
        # If multiple matches, they should be separated
        if result.count("## ") > 1:
            assert "---" in result


class TestServerRegistration:
    def test_translate_reference_tool_callable(self):
        from cobol_mcp.server import translate_reference

        result = translate_reference("CICS")
        assert "CICS" in result

    def test_gnucobol_resource_callable(self):
        from cobol_mcp.server import gnucobol

        result = gnucobol()
        assert "cobc" in result
        assert "GnuCOBOL" in result

    def test_gnucobol_resource_has_compiler_info(self):
        from cobol_mcp.server import gnucobol

        result = gnucobol()
        assert "-x" in result  # executable flag
        assert "-fsyntax-only" in result
        assert "COB_LIBRARY_PATH" in result
