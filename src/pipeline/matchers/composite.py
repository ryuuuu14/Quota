from typing import Dict, Set, List, Optional
import logging

from ..models import MappingResult, Alternative, MatchType, MatchResult, DuplicateWarning, UnmatchedHeader, SuggestedAction
from ..synonym_registry import SynonymRegistry
from .base import MatcherStrategy, MatchCandidate
from .exact import ExactMatcher
from .synonym import SynonymMatcher
from .fuzzy import FuzzyMatcher

logger = logging.getLogger(__name__)


class CompositeMatcher:
    def __init__(self, registry: SynonymRegistry, config: Dict):
        self.registry = registry
        self.config = config
        self.matchers: List[MatcherStrategy] = []
        self._build_chain()

    def _build_chain(self) -> None:
        matcher_configs = self.config.get("matchers", {})
        if matcher_configs.get("exact", {}).get("enabled", True):
            self.matchers.append(ExactMatcher(self.registry, matcher_configs.get("exact", {})))
        if matcher_configs.get("synonym", {}).get("enabled", True):
            self.matchers.append(SynonymMatcher(self.registry, matcher_configs.get("synonym", {})))
        if matcher_configs.get("fuzzy", {}).get("enabled", True):
            self.matchers.append(FuzzyMatcher(self.registry, matcher_configs.get("fuzzy", {})))

    def match_all(
        self,
        excel_headers: List[str],
        expected_columns: List[str],
        required_columns: Optional[List[str]] = None,
        template_mapping: Optional[Dict[str, str]] = None,
        template_mode: str = "merge_confidence"
    ) -> MatchResult:
        required_set = set(required_columns or [])

        available_headers = {self.registry.normalize(h): h for h in excel_headers if h}
        used_headers: Set[str] = set()
        mappings: List[MappingResult] = []

        for expected in expected_columns:
            norm_expected = self.registry.normalize(expected)
            is_required = expected in required_set

            candidate = self._match_single(expected, norm_expected, available_headers, used_headers)

            if candidate and candidate.matched_header:
                used_headers.add(self.registry.normalize(candidate.matched_header))

            template_value = None
            if template_mapping and template_mode == "merge_confidence":
                template_value = template_mapping.get(expected)

            mapping = MappingResult(
                expected_column=expected,
                matched_header=candidate.matched_header if candidate else None,
                match_type=candidate.match_type if candidate else MatchType.NONE,
                confidence=candidate.confidence if candidate else 0,
                alternatives=candidate.alternatives if candidate else [],
                is_required=is_required,
                match_reason=candidate.reason if candidate else "no_match",
                template_value=template_value
            )
            mappings.append(mapping)

        duplicate_warnings = self._detect_duplicates(mappings)
        unmatched = self._find_unmatched(excel_headers, available_headers, used_headers, expected_columns)
        missing_required = [m.expected_column for m in mappings if m.is_required and m.matched_header is None]

        return MatchResult(
            mappings=mappings,
            unmatched_excel_headers=unmatched,
            duplicate_warnings=duplicate_warnings,
            missing_required=missing_required,
            synonym_config_hash=self.registry.config_hash
        )

    def _match_single(
        self,
        expected: str,
        norm_expected: str,
        available: Dict[str, str],
        used: Set[str]
    ) -> Optional[MatchCandidate]:
        for matcher in self.matchers:
            candidate = matcher.match(expected, norm_expected, available, used)
            if candidate:
                return candidate
        return None

    def _detect_duplicates(self, mappings: List[MappingResult]) -> List[DuplicateWarning]:
        header_to_expected: Dict[str, List[str]] = {}
        for m in mappings:
            if m.matched_header:
                header_to_expected.setdefault(m.matched_header, []).append(m.expected_column)

        warnings = []
        for header, expected_list in header_to_expected.items():
            if len(expected_list) > 1:
                warnings.append(DuplicateWarning(
                    excel_header=header,
                    expected_columns=expected_list
                ))
        return warnings

    def _find_unmatched(
        self,
        excel_headers: List[str],
        available: Dict[str, str],
        used: Set[str],
        expected_columns: List[str]
    ) -> List[UnmatchedHeader]:
        unmatched = []
        for h in excel_headers:
            norm_h = self.registry.normalize(h)
            if norm_h not in used:
                suggested = self._suggest_for_unmatched(norm_h, expected_columns)
                unmatched.append(UnmatchedHeader(
                    header=h,
                    suggested_matches=suggested,
                    suggested_action=SuggestedAction.REVIEW
                ))
        return unmatched

    def _suggest_for_unmatched(self, norm_header: str, expected_columns: List[str]) -> List[Alternative]:
        suggestions = []
        for expected in expected_columns:
            norm_expected = self.registry.normalize(expected)
            score = 0
            try:
                from rapidfuzz import fuzz
                score = fuzz.token_set_ratio(norm_header, norm_expected)
            except ImportError:
                import difflib
                score = int(difflib.SequenceMatcher(None, norm_header, norm_expected).ratio() * 100)

            if score >= 50:
                suggestions.append(Alternative(
                    header=expected,
                    confidence=score,
                    match_type=MatchType.FUZZY
                ))

        suggestions.sort(key=lambda a: a.confidence, reverse=True)
        return suggestions[:3]