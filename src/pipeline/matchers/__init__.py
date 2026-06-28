from .base import MatcherStrategy, MatchCandidate
from .exact import ExactMatcher
from .synonym import SynonymMatcher
from .fuzzy import FuzzyMatcher
from .composite import CompositeMatcher

__all__ = [
    "MatcherStrategy",
    "MatchCandidate",
    "ExactMatcher",
    "SynonymMatcher",
    "FuzzyMatcher",
    "CompositeMatcher",
]
