import hashlib
import logging
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

import yaml
from pydantic import BaseModel, ValidationError

from .models import MatcherConfig

logger = logging.getLogger(__name__)


class SynonymEntry(BaseModel):
    expected: str
    synonyms: List[str]


class SynonymsConfig(BaseModel):
    synonyms: List[SynonymEntry]


@dataclass
class LoadResult:
    success: bool
    registry: Optional["SynonymRegistry"] = None
    error: Optional[str] = None


class SynonymRegistry:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._synonyms: Dict[str, List[str]] = {}
        self._normalized_synonyms: Dict[str, List[Tuple[str, str]]] = {}
        self._expected_columns: Set[str] = set()
        self._config_hash: str = ""
        self._matcher_config: MatcherConfig = MatcherConfig()

    @classmethod
    def load(cls, config_path: str) -> LoadResult:
        try:
            registry = cls(config_path)
            registry._load()
            return LoadResult(success=True, registry=registry)
        except Exception as e:
            logger.error(f"Failed to load synonym registry: {e}")
            return LoadResult(success=False, error=str(e))

    def _load(self) -> None:
        with open(self.config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        config = SynonymsConfig.model_validate(raw)

        self._synonyms = {entry.expected: entry.synonyms for entry in config.synonyms}
        self._expected_columns = set(self._synonyms.keys())

        self._normalized_synonyms = {}
        for expected, synonyms in self._synonyms.items():
            norm_expected = self.normalize(expected)
            self._normalized_synonyms[norm_expected] = [(self.normalize(s), expected) for s in synonyms]

        canonical_yaml = yaml.dump(
            {entry.expected: entry.synonyms for entry in config.synonyms},
            sort_keys=True,
            allow_unicode=True
        )
        self._config_hash = hashlib.sha256(canonical_yaml.encode()).hexdigest()

        self._load_matcher_config()

        logger.info(f"Loaded {len(self._synonyms)} synonym groups, config hash: {self._config_hash[:8]}")

    def _load_matcher_config(self) -> None:
        config_dir = self.config_path.parent
        matcher_config_path = config_dir / "matcher_config.yaml"
        if matcher_config_path.exists():
            with open(matcher_config_path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
                if raw:
                    self._matcher_config = MatcherConfig.model_validate(raw)

    @property
    def synonyms(self) -> Dict[str, List[str]]:
        return self._synonyms

    @property
    def expected_columns(self) -> Set[str]:
        return self._expected_columns

    @property
    def config_hash(self) -> str:
        return self._config_hash

    @property
    def matcher_config(self) -> MatcherConfig:
        return self._matcher_config

    def normalize(self, s: str) -> str:
        if not s:
            return ""
        s = str(s).lower().strip()
        s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
        return s.replace("_", " ").replace("-", " ")

    def get_synonyms_for(self, expected: str) -> List[str]:
        return self._synonyms.get(expected, [])

    def get_normalized_synonyms_for(self, expected: str) -> List[Tuple[str, str]]:
        norm_expected = self.normalize(expected)
        return self._normalized_synonyms.get(norm_expected, [])

    def reload(self) -> LoadResult:
        return self.load(self.config_path)