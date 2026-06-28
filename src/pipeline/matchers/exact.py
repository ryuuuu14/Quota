from typing import Dict, Set, Optional
from ..models import MatchType
from .base import MatcherStrategy, MatchCandidate


class ExactMatcher(MatcherStrategy):
    def match(
        self,
        expected_column: str,
        norm_expected: str,
        available_headers: Dict[str, str],
        used_headers: Set[str],
    ) -> Optional[MatchCandidate]:
        if not self.enabled:
            return None

        if norm_expected in available_headers and norm_expected not in used_headers:
            matched = available_headers[norm_expected]
            return self._make_candidate(
                expected=expected_column,
                matched=matched,
                mtype=MatchType.EXACT,
                confidence=100,
                reason=f"exact: '{norm_expected}' == '{norm_expected}'",
                alternatives=[self._make_alternative(matched, 100, MatchType.EXACT)],
            )
        return None
