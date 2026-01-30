"""Google Natural Language API integration for word relevance scoring."""

from __future__ import annotations

import os
import typing
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class EntityInfo:
    """Information about an entity extracted from text."""

    name: str
    entity_type: str
    salience: float
    mentions: list[str] = field(default_factory=list)


@dataclass
class ScoredWord:
    """A word with its relevance score."""

    word: str
    count: int
    score: float
    is_related: bool
    entity_type: str | None = None


class NLPError(Exception):
    """Error from Google Natural Language API."""

    pass


class RelevanceScorer:
    """Score words by relevance to a search query using Google NLP API.

    Uses the Google Cloud Natural Language API to:
    1. Extract entities from the search query
    2. Analyze each word's semantic relationship to query entities
    3. Score and classify words as related or unrelated
    """

    def __init__(self, threshold: float = 0.5) -> None:
        """Initialize the relevance scorer.

        Args:
            threshold: Score threshold for classifying words as related.
                Words with score >= threshold are considered related.
        """
        self._threshold = threshold
        self._client: typing.Any = None
        self._query_entities: list[EntityInfo] = []
        self._query_text: str = ""

    @property
    def is_available(self) -> bool:
        """Check if the NLP API is available."""
        # Check for credentials
        return bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

    def _get_client(self) -> typing.Any:
        """Get or create the NLP API client."""
        if self._client is None:
            try:
                from google.cloud import language_v1

                self._client = language_v1.LanguageServiceClient()
            except ImportError as e:
                raise NLPError(
                    "google-cloud-language package not installed. "
                    "Install with: pip install google-cloud-language"
                ) from e
            except Exception as e:
                raise NLPError(f"Failed to initialize NLP client: {e}") from e

        return self._client

    def analyze_query(self, query: str) -> list[EntityInfo]:
        """Analyze the search query to extract entities.

        Args:
            query: The search query text.

        Returns:
            List of EntityInfo objects for entities found in query.
        """
        self._query_text = query.lower()

        try:
            from google.cloud import language_v1
        except ImportError as e:
            raise NLPError(
                "google-cloud-language package not installed. "
                "Install with: pip install google-cloud-language"
            ) from e

        client = self._get_client()

        document = language_v1.Document(
            content=query,
            type_=language_v1.Document.Type.PLAIN_TEXT,
        )

        try:
            response = client.analyze_entities(document=document)
        except Exception as e:
            raise NLPError(f"Entity analysis failed: {e}") from e

        entities: list[EntityInfo] = []
        for entity in response.entities:
            entity_info = EntityInfo(
                name=entity.name,
                entity_type=language_v1.Entity.Type(entity.type_).name,
                salience=entity.salience,
                mentions=[m.text.content for m in entity.mentions],
            )
            entities.append(entity_info)

        self._query_entities = entities
        return entities

    def _calculate_word_score(self, word: str) -> tuple[float, str | None]:
        """Calculate relevance score for a single word.

        Args:
            word: The word to score.

        Returns:
            Tuple of (score, entity_type or None).
        """
        word_lower = word.lower()

        # Direct match with query text
        if word_lower in self._query_text.split():
            return 1.0, "QUERY_TERM"

        # Check against extracted entities
        best_score = 0.0
        best_type: str | None = None

        for entity in self._query_entities:
            entity_name_lower = entity.name.lower()

            # Exact match with entity
            if word_lower == entity_name_lower:
                score = 0.9 + (entity.salience * 0.1)
                if score > best_score:
                    best_score = score
                    best_type = entity.entity_type

            # Word is part of entity name
            elif word_lower in entity_name_lower.split():
                score = 0.7 + (entity.salience * 0.2)
                if score > best_score:
                    best_score = score
                    best_type = entity.entity_type

            # Entity name contains word
            elif word_lower in entity_name_lower:
                score = 0.5 + (entity.salience * 0.3)
                if score > best_score:
                    best_score = score
                    best_type = entity.entity_type

            # Check mentions
            for mention in entity.mentions:
                mention_lower = mention.lower()
                if word_lower in mention_lower.split():
                    score = 0.6 + (entity.salience * 0.2)
                    if score > best_score:
                        best_score = score
                        best_type = entity.entity_type

        return best_score, best_type

    def score_words(
        self,
        words: Sequence[tuple[str, int]],
    ) -> list[ScoredWord]:
        """Score a list of words for relevance to the query.

        Args:
            words: List of (word, count) tuples.

        Returns:
            List of ScoredWord objects with scores and classifications.
        """
        if not self._query_entities and not self._query_text:
            raise NLPError("Must call analyze_query() before score_words()")

        scored: list[ScoredWord] = []

        for word, count in words:
            score, entity_type = self._calculate_word_score(word)

            scored.append(
                ScoredWord(
                    word=word,
                    count=count,
                    score=score,
                    is_related=score >= self._threshold,
                    entity_type=entity_type,
                )
            )

        return scored

    def classify_words(
        self,
        words: Sequence[tuple[str, int]],
    ) -> tuple[list[ScoredWord], list[ScoredWord]]:
        """Classify words into related and unrelated groups.

        Args:
            words: List of (word, count) tuples.

        Returns:
            Tuple of (related_words, unrelated_words).
        """
        scored = self.score_words(words)

        related = [w for w in scored if w.is_related]
        unrelated = [w for w in scored if not w.is_related]

        # Sort each group by count descending
        related.sort(key=lambda w: w.count, reverse=True)
        unrelated.sort(key=lambda w: w.count, reverse=True)

        return related, unrelated


async def score_words_with_nlp(
    query: str,
    words: Sequence[tuple[str, int]],
    threshold: float = 0.5,
) -> tuple[list[ScoredWord], list[ScoredWord]]:
    """Convenience function to score words against a query.

    Args:
        query: The search query.
        words: List of (word, count) tuples.
        threshold: Score threshold for related classification.

    Returns:
        Tuple of (related_words, unrelated_words).
    """
    scorer = RelevanceScorer(threshold=threshold)
    scorer.analyze_query(query)
    return scorer.classify_words(words)
