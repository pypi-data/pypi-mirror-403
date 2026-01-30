"""Tests for Google NLP relevance scoring."""

from __future__ import annotations

import pytest

from pycewl.google.nlp import EntityInfo, RelevanceScorer, ScoredWord


class TestEntityInfo:
    """Tests for EntityInfo dataclass."""

    def test_creation(self) -> None:
        """Test EntityInfo creation."""
        entity = EntityInfo(
            name="Star Trek",
            entity_type="WORK_OF_ART",
            salience=0.8,
            mentions=["Star Trek", "the show"],
        )

        assert entity.name == "Star Trek"
        assert entity.entity_type == "WORK_OF_ART"
        assert entity.salience == 0.8
        assert len(entity.mentions) == 2


class TestScoredWord:
    """Tests for ScoredWord dataclass."""

    def test_creation(self) -> None:
        """Test ScoredWord creation."""
        word = ScoredWord(
            word="enterprise",
            count=42,
            score=0.85,
            is_related=True,
            entity_type="ORGANIZATION",
        )

        assert word.word == "enterprise"
        assert word.count == 42
        assert word.score == 0.85
        assert word.is_related is True
        assert word.entity_type == "ORGANIZATION"

    def test_creation_unrelated(self) -> None:
        """Test ScoredWord creation for unrelated word."""
        word = ScoredWord(
            word="welcome",
            count=10,
            score=0.1,
            is_related=False,
        )

        assert word.is_related is False
        assert word.entity_type is None


class TestRelevanceScorer:
    """Tests for RelevanceScorer class."""

    def test_not_available_without_credentials(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test is_available returns False without credentials."""
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

        scorer = RelevanceScorer()

        assert scorer.is_available is False

    def test_available_with_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test is_available returns True with credentials."""
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/to/creds.json")

        scorer = RelevanceScorer()

        assert scorer.is_available is True

    def test_threshold_configuration(self) -> None:
        """Test threshold is configurable."""
        scorer = RelevanceScorer(threshold=0.7)

        assert scorer._threshold == 0.7

    def test_default_threshold(self) -> None:
        """Test default threshold is 0.5."""
        scorer = RelevanceScorer()

        assert scorer._threshold == 0.5


class TestRelevanceScorerMocked:
    """Tests for RelevanceScorer with mocked entities."""

    def test_score_words_direct_match(self) -> None:
        """Test scoring with direct query match."""
        scorer = RelevanceScorer(threshold=0.5)

        # Manually set query text and entities
        scorer._query_text = "star trek"
        scorer._query_entities = [
            EntityInfo(
                name="Star Trek",
                entity_type="WORK_OF_ART",
                salience=0.9,
                mentions=["Star Trek"],
            ),
        ]

        words = [("star", 10), ("trek", 8), ("welcome", 5)]
        scored = scorer.score_words(words)

        # Direct query words should have high scores
        star_word = next(w for w in scored if w.word == "star")
        assert star_word.score >= 0.9
        assert star_word.is_related is True

    def test_score_words_entity_match(self) -> None:
        """Test scoring with entity name match."""
        scorer = RelevanceScorer(threshold=0.5)

        scorer._query_text = "star trek"
        scorer._query_entities = [
            EntityInfo(
                name="Enterprise",
                entity_type="ORGANIZATION",
                salience=0.7,
                mentions=["Enterprise", "the Enterprise"],
            ),
        ]

        words = [("Enterprise", 15), ("ship", 5)]
        scored = scorer.score_words(words)

        enterprise_word = next(w for w in scored if w.word == "Enterprise")
        assert enterprise_word.score >= 0.5
        assert enterprise_word.entity_type == "ORGANIZATION"

    def test_classify_words(self) -> None:
        """Test word classification into related/unrelated."""
        scorer = RelevanceScorer(threshold=0.5)

        scorer._query_text = "star trek"
        scorer._query_entities = [
            EntityInfo(
                name="Star Trek",
                entity_type="WORK_OF_ART",
                salience=0.9,
                mentions=["Star Trek"],
            ),
        ]

        words = [("star", 10), ("welcome", 5), ("page", 3)]
        related, unrelated = scorer.classify_words(words)

        # "star" should be related
        related_words = [w.word for w in related]
        unrelated_words = [w.word for w in unrelated]

        assert "star" in related_words
        # "welcome" and "page" should be unrelated
        assert "welcome" in unrelated_words or "page" in unrelated_words

    def test_classify_sorted_by_count(self) -> None:
        """Test that classified words are sorted by count."""
        scorer = RelevanceScorer(threshold=0.5)

        scorer._query_text = "test"
        scorer._query_entities = []

        words = [("aaa", 5), ("bbb", 20), ("ccc", 10)]
        _, unrelated = scorer.classify_words(words)

        counts = [w.count for w in unrelated]
        assert counts == sorted(counts, reverse=True)
