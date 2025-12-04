"""Test suite for models.app_state module."""
import pytest
from src.models.app_state import AppState


class TestAppStateInitialization:
    """Test AppState initialization."""

    def test_app_state_default_initialization(self):
        """Test AppState with default parameters."""
        app_state = AppState()
        assert app_state.initial_doi is None
        assert app_state.use_test_server is False
        assert app_state.auto_publish is False
        assert app_state.current_doi is None
        assert app_state.cited_papers == {}
        assert app_state.selected_citations == {}

    def test_app_state_with_doi(self):
        """Test AppState initialization with DOI."""
        app_state = AppState(initial_doi="10.1234/example")
        assert app_state.initial_doi == "10.1234/example"
        assert app_state.current_doi is None  # Initial DOI doesn't set current_doi

    def test_app_state_with_test_server(self):
        """Test AppState initialization with test server flag."""
        app_state = AppState(use_test_server=True)
        assert app_state.use_test_server is True

    def test_app_state_with_auto_publish(self):
        """Test AppState initialization with auto_publish flag."""
        app_state = AppState(auto_publish=True)
        assert app_state.auto_publish is True

    def test_app_state_with_all_parameters(self):
        """Test AppState initialization with all parameters."""
        app_state = AppState(
            initial_doi="10.1234/example",
            use_test_server=True,
            auto_publish=True,
        )
        assert app_state.initial_doi == "10.1234/example"
        assert app_state.use_test_server is True
        assert app_state.auto_publish is True


class TestAppStateSetDoi:
    """Test AppState.set_doi method."""

    def test_set_doi_valid(self):
        """Test setting a valid DOI."""
        app_state = AppState()
        app_state.set_doi("10.1234/example")
        assert app_state.current_doi == "10.1234/example"

    def test_set_doi_overwrites_previous(self):
        """Test that setting DOI overwrites the previous one."""
        app_state = AppState()
        app_state.set_doi("10.1111/first")
        app_state.set_doi("10.2222/second")
        assert app_state.current_doi == "10.2222/second"

    def test_set_doi_with_string_types(self):
        """Test setting DOI with various string types."""
        app_state = AppState()
        test_dois = [
            "10.1234/example",
            "10.1234/example.with.dots",
            "10.1234/example-with-dashes",
        ]
        for doi in test_dois:
            app_state.set_doi(doi)
            assert app_state.current_doi == doi


class TestAppStateSetCitedPapers:
    """Test AppState.set_cited_papers method."""

    def test_set_cited_papers_empty(self):
        """Test setting empty cited papers."""
        app_state = AppState()
        app_state.set_cited_papers({})
        assert app_state.cited_papers == {}

    def test_set_cited_papers_with_data(self):
        """Test setting cited papers with data."""
        app_state = AppState()
        papers = {
            "10.1234/paper1": "Paper 1 Title",
            "10.1234/paper2": "Paper 2 Title",
        }
        app_state.set_cited_papers(papers)
        assert app_state.cited_papers == papers

    def test_set_cited_papers_with_dict_objects(self):
        """Test setting cited papers with nested dict objects."""
        app_state = AppState()
        papers = {
            "10.1234/paper1": {"title": "Paper 1", "authors": "Author A"},
            "10.1234/paper2": {"title": "Paper 2", "authors": "Author B"},
        }
        app_state.set_cited_papers(papers)
        assert app_state.cited_papers == papers
        assert app_state.cited_papers["10.1234/paper1"]["title"] == "Paper 1"

    def test_set_cited_papers_overwrites_previous(self):
        """Test that setting cited papers overwrites the previous ones."""
        app_state = AppState()
        app_state.set_cited_papers({"10.1111/old": "Old Paper"})
        app_state.set_cited_papers({"10.2222/new": "New Paper"})
        assert app_state.cited_papers == {"10.2222/new": "New Paper"}


class TestAppStateAddCitation:
    """Test AppState.add_citation method."""

    def test_add_single_citation_type(self):
        """Test adding a citation with a single type."""
        app_state = AppState()
        app_state.add_citation("10.1234/cited", ["cites"])
        assert "10.1234/cited" in app_state.selected_citations
        assert app_state.selected_citations["10.1234/cited"] == ["cites"]

    def test_add_multiple_citation_types(self):
        """Test adding a citation with multiple types."""
        app_state = AppState()
        app_state.add_citation("10.1234/cited", ["cites", "supports"])
        assert app_state.selected_citations["10.1234/cited"] == ["cites", "supports"]

    def test_add_multiple_citations(self):
        """Test adding multiple citations."""
        app_state = AppState()
        app_state.add_citation("10.1111/first", ["cites"])
        app_state.add_citation("10.2222/second", ["supports"])
        assert len(app_state.selected_citations) == 2
        assert app_state.selected_citations["10.1111/first"] == ["cites"]
        assert app_state.selected_citations["10.2222/second"] == ["supports"]

    def test_add_citation_overwrites_existing(self):
        """Test that adding citation with same DOI overwrites previous."""
        app_state = AppState()
        app_state.add_citation("10.1234/cited", ["cites"])
        app_state.add_citation("10.1234/cited", ["supports", "agrees with"])
        assert app_state.selected_citations["10.1234/cited"] == ["supports", "agrees with"]


class TestAppStateClearCitations:
    """Test AppState.clear_citations method."""

    def test_clear_citations_empty_state(self):
        """Test clearing citations from empty state."""
        app_state = AppState()
        app_state.clear_citations()
        assert app_state.selected_citations == {}

    def test_clear_citations_with_data(self):
        """Test clearing citations with data."""
        app_state = AppState()
        app_state.add_citation("10.1111/first", ["cites"])
        app_state.add_citation("10.2222/second", ["supports"])
        app_state.clear_citations()
        assert app_state.selected_citations == {}

    def test_clear_citations_does_not_affect_other_state(self):
        """Test that clearing citations doesn't affect other state."""
        app_state = AppState()
        app_state.set_doi("10.1234/example")
        app_state.set_cited_papers({"10.1234/paper": "Title"})
        app_state.add_citation("10.1111/first", ["cites"])
        app_state.clear_citations()
        assert app_state.current_doi == "10.1234/example"
        assert app_state.cited_papers == {"10.1234/paper": "Title"}


class TestAppStateGetCitations:
    """Test AppState.get_citations method."""

    def test_get_citations_empty(self):
        """Test getting citations when empty."""
        app_state = AppState()
        assert app_state.get_citations() == {}

    def test_get_citations_returns_dict(self):
        """Test that get_citations returns a dictionary."""
        app_state = AppState()
        app_state.add_citation("10.1111/first", ["cites"])
        result = app_state.get_citations()
        assert isinstance(result, dict)

    def test_get_citations_reflects_changes(self):
        """Test that get_citations reflects current state."""
        app_state = AppState()
        assert app_state.get_citations() == {}
        app_state.add_citation("10.1111/first", ["cites"])
        assert len(app_state.get_citations()) == 1
        app_state.add_citation("10.2222/second", ["supports"])
        assert len(app_state.get_citations()) == 2


class TestAppStateReset:
    """Test AppState.reset method."""

    def test_reset_clears_all_state(self):
        """Test that reset clears all state."""
        app_state = AppState(initial_doi="10.1234/example", use_test_server=True)
        app_state.set_doi("10.1234/current")
        app_state.set_cited_papers({"10.1111/paper": "Title"})
        app_state.add_citation("10.2222/cited", ["cites"])

        app_state.reset()

        assert app_state.current_doi is None
        assert app_state.cited_papers == {}
        assert app_state.selected_citations == {}

    def test_reset_preserves_initial_settings(self):
        """Test that reset preserves initial settings."""
        app_state = AppState(
            initial_doi="10.1234/example", use_test_server=True, auto_publish=True
        )
        app_state.set_doi("10.1234/current")
        app_state.reset()

        assert app_state.initial_doi == "10.1234/example"
        assert app_state.use_test_server is True
        assert app_state.auto_publish is True

    def test_reset_allows_reuse(self):
        """Test that reset allows the app_state to be reused."""
        app_state = AppState()

        # First use
        app_state.set_doi("10.1111/first")
        app_state.add_citation("10.2222/cited", ["cites"])
        assert len(app_state.get_citations()) == 1

        # Reset and reuse
        app_state.reset()
        app_state.set_doi("10.3333/second")
        app_state.add_citation("10.4444/cited", ["supports"])
        assert app_state.current_doi == "10.3333/second"
        assert len(app_state.get_citations()) == 1
