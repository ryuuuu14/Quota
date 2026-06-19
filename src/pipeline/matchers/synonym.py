from typing import Dict, Set, Optional
from ..models import MatchType
from .base import MatcherStrategy, MatchCandidate


class SynonymMatcher(MatcherStrategy):
    def match(
        self,
        expected_column: str,
        norm_expected: str,
        available_headers: Dict[str, str],
        used_headers: Set[str],
    ) -> Optional[MatchCandidate]:
        if not self.enabled:
            return None

        synonyms = self.registry.get_normalized_synonyms_for(expected_column)
        if not synonyms:
            return None

        for norm_syn, _ in synonyms:
            if norm_syn in available_headers and norm_syn not in used_headers:
                matched = available_headers[norm_syn]
                alternatives = [self._make_alternative(matched, 95, MatchType.SYNONYM)]
                return self._make_candidate(
                    expected=expected_column,
                    matched=matched,
                    mtype=MatchType.SYNONYM,
                    confidence=95,
                    reason=f"synonym: '{norm_syn}' in SYNONYMS['{expected_column}']",
                    alternatives=alternatives,
                )
        return None
