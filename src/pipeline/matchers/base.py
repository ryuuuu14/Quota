from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Set
from dataclasses import dataclass

from ..models import MappingResult, Alternative, MatchType
from ..synonym_registry import SynonymRegistry


@dataclass
class MatchCandidate:
    expected_column: str
    matched_header: Optional[str]
    match_type: MatchType
    confidence: int
    reason: str
    alternatives: List[Alternative]


class MatcherStrategy(ABC):
    def __init__(self, registry: SynonymRegistry, config: Dict):
        self.registry = registry
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def match(
        self,
        expected_column: str,
        norm_expected: str,
        available_headers: Dict[str, str],
        used_headers: Set[str]
    ) -> Optional[MatchCandidate]:
        pass

    def _make_alternative(self, header: str, confidence: int, match_type: MatchType) -> Alternative:
        return Alternative(header=header, confidence=confidence, match_type=match_type)

    def _make_candidate(
        self,
        expected: str,
        matched: Optional[str],
        mtype: MatchType,
        confidence: int,
        reason: str,
        alternatives: List[Alternative]
    ) -> Optional[MatchCandidate]:
        if matched is None:
            return None
        return MatchCandidate(
            expected_column=expected,
            matched_header=matched,
            match_type=mtype,
            confidence=confidence,
            reason=reason,
            alternatives=alternatives
        )