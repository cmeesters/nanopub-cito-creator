"""Test suite for core.citation_types module."""
import pytest
from src.models.citation_types import (
    CITATION_TYPES,
    CONFLICTING_COMBINATIONS,
    POSITIVE_CITATIONS,
    NEGATIVE_CITATIONS,
    get_citation_sentiment,
)


class TestCitationTypesData:
    """Test citation types data structures."""

    def test_citation_types_dict_not_empty(self):
        """Test that CITATION_TYPES dictionary is populated."""
        assert len(CITATION_TYPES) > 0
        assert isinstance(CITATION_TYPES, dict)

    def test_citation_types_have_valid_urls(self):
        """Test that all citation types have valid URLs."""
        for label, url in CITATION_TYPES.items():
            assert isinstance(label, str)
            assert isinstance(url, str)
            assert url.startswith("http://purl.org/spar/cito/")

    def test_conflicting_combinations_valid(self):
        """Test that conflicting combinations are valid tuples."""
        assert len(CONFLICTING_COMBINATIONS) > 0
        for combo in CONFLICTING_COMBINATIONS:
            assert isinstance(combo, tuple)
            assert len(combo) == 2
            assert combo[0] in CITATION_TYPES
            assert combo[1] in CITATION_TYPES

    def test_positive_citations_valid(self):
        """Test that positive citations are in CITATION_TYPES."""
        for citation in POSITIVE_CITATIONS:
            assert citation in CITATION_TYPES

    def test_negative_citations_valid(self):
        """Test that negative citations are in CITATION_TYPES."""
        for citation in NEGATIVE_CITATIONS:
            assert citation in CITATION_TYPES

    def test_positive_and_negative_no_overlap(self):
        """Test that positive and negative citations don't overlap."""
        overlap = POSITIVE_CITATIONS & NEGATIVE_CITATIONS
        assert len(overlap) == 0


class TestGetCitationSentiment:
    """Test get_citation_sentiment function."""

    def test_positive_sentiment(self):
        """Test detection of positive citations."""
        for citation in ["agrees with", "confirms", "supports"]:
            assert get_citation_sentiment(citation) == "positive"

    def test_negative_sentiment(self):
        """Test detection of negative citations."""
        for citation in ["disagrees with", "disputes", "refutes"]:
            assert get_citation_sentiment(citation) == "negative"

    def test_neutral_sentiment(self):
        """Test detection of neutral citations."""
        for citation in ["cites", "discusses", "describes"]:
            assert get_citation_sentiment(citation) == "neutral"

    def test_unknown_citation_type(self):
        """Test handling of unknown citation types."""
        # Unknown citations should default to neutral
        result = get_citation_sentiment("unknown_citation_type")
        assert result == "neutral"

    def test_all_known_citations_have_sentiment(self):
        """Test that all known citations return a valid sentiment."""
        valid_sentiments = {"positive", "negative", "neutral"}
        for citation in CITATION_TYPES.keys():
            sentiment = get_citation_sentiment(citation)
            assert sentiment in valid_sentiments
