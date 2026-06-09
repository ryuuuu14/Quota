from typing import Dict, Set, Optional, List
import logging

from ..models import Alternative, MatchType
from ..synonym_registry import SynonymRegistry
from .base import MatcherStrategy, MatchCandidate

logger = logging.getLogger(__name__)

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    import difflib


class FuzzyMatcher(MatcherStrategy):
    def __init__(self, registry: SynonymRegistry, config: Dict):
        super().__init__(registry, config)
        self.engine = config.get("engine", "rapidfuzz")
        self.cutoff = config.get("cutoff", 70)
        self.fallback_cutoff = config.get("fallback_cutoff", 50)

    def match(
        self,
        expected_column: str,
        norm_expected: str,
        available_headers: Dict[str, str],
        used_headers: Set[str]
    ) -> Optional[MatchCandidate]:
        if not self.enabled:
            return None

        candidates = [
            (h, norm_h) for norm_h, h in available_headers.items()
            if norm_h not in used_headers
        ]
        if not candidates:
            return None

        best_match = self._find_best(norm_expected, candidates)
        if best_match:
            matched_header, score, match_type = best_match
            alternatives = [
                self._make_alternative(matched_header, score, match_type)
            ]
            return self._make_candidate(
                expected=expected_column,
                matched=matched_header,
                mtype=match_type,
                confidence=score,
                reason=f"fuzzy: {match_type.value} score {score}% for '{norm_expected}'",
                alternatives=alternatives
            )

        synonym_fuzzy = self._try_synonym_fuzzy(expected_column, candidates, used_headers)
        return synonym_fuzzy

    def _find_best(self, norm_expected: str, candidates: List[tuple]) -> Optional[tuple]:
        if self.engine == "rapidfuzz" and RAPIDFUZZ_AVAILABLE:
            return self._rapidfuzz_match(norm_expected, candidates)
        return self._difflib_match(norm_expected, candidates)

    def _rapidfuzz_match(self, norm_expected: str, candidates: List[tuple]) -> Optional[tuple]:
        from rapidfuzz import fuzz
        best_score = 0
        best_header = None
        for header, norm_h in candidates:
            score = fuzz.token_set_ratio(norm_expected, norm_h)
            if score >= self.cutoff and score > best_score:
                best_score = score
                best_header = header
        if best_header:
            return (best_header, best_score, MatchType.FUZZY)
        return None

    def _difflib_match(self, norm_expected: str, candidates: List[tuple]) -> Optional[tuple]:
        import difflib
        norm_headers = [norm_h for _, norm_h in candidates]
        matches = difflib.get_close_matches(
            norm_expected, norm_headers, n=1, cutoff=self.fallback_cutoff / 100
        )
        if matches:
            idx = norm_headers.index(matches[0])
            header = candidates[idx][0]
            score = int(difflib.SequenceMatcher(None, norm_expected, matches[0]).ratio() * 100)
            return (header, score, MatchType.FUZZY)
        return None

    def _try_synonym_fuzzy(
        self,
        expected_column: str,
        candidates: List[tuple],
        used_headers: Set[str]
    ) -> Optional[MatchCandidate]:
        synonyms = self.registry.get_normalized_synonyms_for(expected_column)
        if not synonyms:
            return None

        available = [(h, n) for n, h in candidates if n not in used_headers]
        if not available:
            return None

        for norm_syn, _ in synonyms:
            best = self._find_best(norm_syn, available)
            if best:
                matched_header, score, _ = best
                return self._make_candidate(
                    expected=expected_column,
                    matched=matched_header,
                    mtype=MatchType.SYNONYM_FUZZY,
                    confidence=score,
                    reason=f"synonym_fuzzy: '{norm_syn}' token_set_ratio {score}%",
                    alternatives=[self._make_alternative(matched_header, score, MatchType.SYNONYM_FUZZY)]
                )
        return None