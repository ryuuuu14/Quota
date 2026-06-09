from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel


class MatchType(str, Enum):
    EXACT = "exact"
    SYNONYM = "synonym"
    FUZZY = "fuzzy"
    SYNONYM_FUZZY = "synonym_fuzzy"
    NONE = "none"


class TemplateMode(str, Enum):
    OVERRIDE = "override"
    FILL_GAPS = "fill_gaps"
    MERGE_CONFIDENCE = "merge_confidence"
    SEPARATE = "separate"


class SuggestedAction(str, Enum):
    REVIEW = "review"
    IGNORE = "ignore"
    NEW_COLUMN = "new_column"


@dataclass
class Alternative:
    header: str
    confidence: int
    match_type: MatchType


@dataclass
class MappingResult:
    expected_column: str
    matched_header: Optional[str]
    match_type: MatchType
    confidence: int
    alternatives: List[Alternative]
    is_required: bool
    match_reason: str = ""
    template_value: Optional[str] = None


@dataclass
class UnmatchedHeader:
    header: str
    suggested_matches: List[Alternative]
    suggested_action: SuggestedAction = SuggestedAction.REVIEW


@dataclass
class DuplicateWarning:
    excel_header: str
    expected_columns: List[str]


@dataclass
class MatchResult:
    mappings: List[MappingResult]
    unmatched_excel_headers: List[UnmatchedHeader]
    duplicate_warnings: List[DuplicateWarning]
    missing_required: List[str]
    synonym_config_hash: str
    api_version: int = 1
    error: Optional[str] = None

    def to_legacy_dict(self) -> Dict[str, Optional[str]]:
        return {m.expected_column: m.matched_header for m in self.mappings}

    def to_ge_expectations(self) -> List[Dict[str, Any]]:
        expectations = []
        for m in self.mappings:
            if m.is_required:
                expectations.append({
                    "expectation_type": "expect_column_values_to_not_be_null",
                    "kwargs": {"column": m.expected_column}
                })
        return expectations


class MatcherConfig(BaseModel):
    exact: Dict[str, Any] = {"enabled": True}
    synonym: Dict[str, Any] = {"enabled": True}
    fuzzy: Dict[str, Any] = {
        "enabled": True,
        "engine": "rapidfuzz",
        "cutoff": 70,
        "fallback_cutoff": 50
    }
    features: Dict[str, Any] = {
        "template_merge": True,
        "confidence_scoring": True
    }