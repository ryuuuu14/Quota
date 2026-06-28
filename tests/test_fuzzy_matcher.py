import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from pipeline.synonym_registry import SynonymRegistry
from pipeline.matchers import CompositeMatcher, ExactMatcher, SynonymMatcher
from pipeline.models import MatchType, MatchResult


@pytest.fixture
def sample_synonyms_yaml(tmp_path):
    data = {
        "synonyms": [
            {"expected": "ma_gv", "synonyms": ["msgv", "magv", "ma giang vien"]},
            {"expected": "ho_ten", "synonyms": ["hoten", "fullname", "name"]},
            {"expected": "ngay_thuc_hien", "synonyms": ["ngay", "date", "log date"]},
            {"expected": "so_luong", "synonyms": ["qty", "quantity", "so luong"]},
        ]
    }
    path = tmp_path / "synonyms.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
    return str(path)


@pytest.fixture
def registry(sample_synonyms_yaml):
    result = SynonymRegistry.load(sample_synonyms_yaml)
    assert result.success
    return result.registry


class TestExactMatcher:
    def test_exact_match(self, registry):
        config = {"enabled": True}
        matcher = ExactMatcher(registry, config)
        available = {"ma_gv": "ma_gv", "hoten": "hoten"}
        result = matcher.match("ma_gv", "ma_gv", available, set())
        assert result is not None
        assert result.matched_header == "ma_gv"
        assert result.match_type == MatchType.EXACT
        assert result.confidence == 100

    def test_exact_match_no_match(self, registry):
        matcher = ExactMatcher(registry, {"enabled": True})
        result = matcher.match("ma_gv", "ma_gv", {"other": "other"}, set())
        assert result is None

    def test_disabled(self, registry):
        matcher = ExactMatcher(registry, {"enabled": False})
        result = matcher.match("ma_gv", "ma_gv", {"ma_gv": "ma_gv"}, set())
        assert result is None


class TestSynonymMatcher:
    def test_synonym_match(self, registry):
        config = {"enabled": True}
        matcher = SynonymMatcher(registry, config)
        available = {"msgv": "msgv"}
        result = matcher.match("ma_gv", "ma_gv", available, set())
        assert result is not None
        assert result.matched_header == "msgv"
        assert result.match_type == MatchType.SYNONYM
        assert result.confidence == 95

    def test_synonym_no_match(self, registry):
        matcher = SynonymMatcher(registry, {"enabled": True})
        result = matcher.match("ma_gv", "ma_gv", {"unknown": "unknown"}, set())
        assert result is None


class TestCompositeMatcher:
    def test_full_pipeline(self, registry):
        matcher = CompositeMatcher(registry, {
            "matchers": {
                "exact": {"enabled": True},
                "synonym": {"enabled": True},
                "fuzzy": {"enabled": True, "engine": "difflib", "fallback_cutoff": 50}
            }
        })

        excel_headers = ["msgv", "fullname", "ngay", "qty"]
        expected = ["ma_gv", "ho_ten", "ngay_thuc_hien", "so_luong"]
        required = ["ma_gv", "ho_ten"]

        result = matcher.match_all(excel_headers, expected, required)

        assert len(result.mappings) == 4
        assert result.mappings[0].matched_header == "msgv"
        assert result.mappings[1].matched_header == "fullname"
        assert len(result.missing_required) == 0

    def test_missing_required(self, registry):
        matcher = CompositeMatcher(registry, {
            "matchers": {
                "exact": {"enabled": True},
                "synonym": {"enabled": True},
                "fuzzy": {"enabled": False}
            }
        })

        excel_headers = ["msgv"]
        expected = ["ma_gv", "ho_ten", "so_luong"]
        required = ["ma_gv", "ho_ten", "so_luong"]

        result = matcher.match_all(excel_headers, expected, required)

        assert len(result.missing_required) == 2
        assert "ho_ten" in result.missing_required
        assert "so_luong" in result.missing_required

    def test_unmatched_headers(self, registry):
        matcher = CompositeMatcher(registry, {
            "matchers": {
                "exact": {"enabled": True},
                "synonym": {"enabled": True},
                "fuzzy": {"enabled": False}
            }
        })

        excel_headers = ["msgv", "random_col_1", "random_col_2"]
        expected = ["ma_gv"]
        required = ["ma_gv"]

        result = matcher.match_all(excel_headers, expected, required)

        assert len(result.unmatched_excel_headers) == 2
        assert all(u.suggested_action.value == "review" for u in result.unmatched_excel_headers)

    def test_duplicate_detection(self, registry):
        matcher = CompositeMatcher(registry, {
            "matchers": {
                "exact": {"enabled": True},
                "synonym": {"enabled": True},
                "fuzzy": {"enabled": False}
            }
        })

        excel_headers = ["msgv"]
        expected = ["ma_gv", "ho_ten"]
        required = ["ma_gv"]

        result = matcher.match_all(excel_headers, expected, required)
        assert len(result.duplicate_warnings) == 0

    def test_to_legacy_dict(self, registry):
        matcher = CompositeMatcher(registry, {
            "matchers": {
                "exact": {"enabled": True},
                "synonym": {"enabled": True},
                "fuzzy": {"enabled": False}
            }
        })

        excel_headers = ["msgv", "fullname"]
        expected = ["ma_gv", "ho_ten"]

        result = matcher.match_all(excel_headers, expected)
        legacy = result.to_legacy_dict()

        assert isinstance(legacy, dict)
        assert legacy["ma_gv"] == "msgv"
        assert legacy["ho_ten"] == "fullname"


class TestSynonymRegistry:
    def test_normalize(self, registry):
        assert registry.normalize("  ABC  ") == "abc"
        assert registry.normalize("Mã GV") == "ma gv"
        assert registry.normalize("ngày_thực_hiện") == "ngay thuc hien"

    def test_config_hash_stable(self, sample_synonyms_yaml):
        r1 = SynonymRegistry.load(sample_synonyms_yaml)
        r2 = SynonymRegistry.load(sample_synonyms_yaml)
        assert r1.registry.config_hash == r2.registry.config_hash

    def test_invalid_yaml(self, tmp_path):
        path = tmp_path / "bad.yaml"
        with open(path, "w") as f:
            f.write("not: valid: yaml: [")
        result = SynonymRegistry.load(str(path))
        assert not result.success
        assert result.error is not None

    def test_missing_file(self):
        result = SynonymRegistry.load("/nonexistent/file.yaml")
        assert not result.success


class TestMatchResult:
    def test_to_legacy_dict(self):
        from pipeline.models import MappingResult, MatchResult, MatchType, Alternative

        mappings = [
            MappingResult(
                expected_column="col_a", matched_header="header_a",
                match_type=MatchType.EXACT, confidence=100,
                alternatives=[Alternative(header="header_a", confidence=100, match_type=MatchType.EXACT)],
                is_required=True
            ),
            MappingResult(
                expected_column="col_b", matched_header=None,
                match_type=MatchType.NONE, confidence=0,
                alternatives=[], is_required=True
            ),
        ]

        result = MatchResult(
            mappings=mappings,
            unmatched_excel_headers=[],
            duplicate_warnings=[],
            missing_required=["col_b"],
            synonym_config_hash="abc123"
        )

        legacy = result.to_legacy_dict()
        assert legacy["col_a"] == "header_a"
        assert legacy["col_b"] is None

    def test_to_ge_expectations(self):
        from pipeline.models import MappingResult, MatchResult, MatchType, Alternative

        mappings = [
            MappingResult(expected_column="req_col", matched_header="h",
                          match_type=MatchType.EXACT, confidence=100,
                          alternatives=[], is_required=True),
            MappingResult(expected_column="opt_col", matched_header="h",
                          match_type=MatchType.EXACT, confidence=100,
                          alternatives=[], is_required=False),
        ]

        result = MatchResult(
            mappings=mappings, unmatched_excel_headers=[],
            duplicate_warnings=[], missing_required=[],
            synonym_config_hash="abc123"
        )

        ge = result.to_ge_expectations()
        assert len(ge) == 1
        assert ge[0]["expectation_type"] == "expect_column_values_to_not_be_null"
        assert ge[0]["kwargs"]["column"] == "req_col"