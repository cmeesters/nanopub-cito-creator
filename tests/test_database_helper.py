"""Test suite for ui.database_helper module."""
import pytest
import tempfile
from pathlib import Path
from src.ui.database_helper import DatabaseUIHelper
from src.models.app_state import AppState


class TestDatabaseUIHelperInitialization:
    """Test DatabaseUIHelper initialization."""

    def test_helper_initialization(self):
        """Test helper can be initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            helper = DatabaseUIHelper(str(db_path))
            assert helper.db is not None
            helper.close()

    def test_helper_context_manager(self):
        """Test helper can be used as context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                assert helper.db is not None


class TestCheckDoiInDatabase:
    """Test checking if DOI exists in database."""

    def test_check_doi_exists(self):
        """Test checking for existing DOI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                citations = {"10.1111/paper1": ["cites"]}
                helper.save_ontology_state("10.1234/example", citations)
                
                assert helper.check_doi_in_database("10.1234/example") is True

    def test_check_doi_not_exists(self):
        """Test checking for non-existent DOI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                assert helper.check_doi_in_database("10.9999/nonexistent") is False


class TestLoadOntologyForRedo:
    """Test loading ontology for re-annotation."""

    def test_load_ontology_for_redo_success(self):
        """Test successfully loading ontology for redo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                # Save an ontology first
                citations = {
                    "10.1111/paper1": ["cites", "supports"],
                    "10.2222/paper2": ["discusses"]
                }
                helper.save_ontology_state("10.1234/example", citations, "Example Paper")

                # Load it into app state
                app_state = AppState()
                result = helper.load_ontology_for_redo("10.1234/example", app_state)

                assert result is True
                assert app_state.current_doi == "10.1234/example"
                assert len(app_state.get_citations()) == 2

    def test_load_ontology_for_redo_nonexistent(self):
        """Test loading non-existent ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                app_state = AppState()
                result = helper.load_ontology_for_redo("10.9999/nonexistent", app_state)

                assert result is False

    def test_load_ontology_populates_citations(self):
        """Test that loading populates all citations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                citations = {
                    "10.1111/paper1": ["cites"],
                    "10.2222/paper2": ["supports", "agrees with"],
                    "10.3333/paper3": ["refutes"]
                }
                helper.save_ontology_state("10.1234/example", citations)

                app_state = AppState()
                helper.load_ontology_for_redo("10.1234/example", app_state)

                loaded_citations = app_state.get_citations()
                assert loaded_citations == citations


class TestLoadOntologyForContinuation:
    """Test loading ontology for continuation."""

    def test_load_ontology_for_continuation_success(self):
        """Test successfully loading ontology for continuation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                citations = {"10.1111/paper1": ["cites"]}
                helper.save_ontology_state("10.1234/example", citations)

                app_state = AppState()
                result = helper.load_ontology_for_continuation("10.1234/example", app_state)

                assert result is True
                assert app_state.current_doi == "10.1234/example"

    def test_load_ontology_for_continuation_nonexistent(self):
        """Test loading non-existent ontology for continuation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                app_state = AppState()
                result = helper.load_ontology_for_continuation("10.9999/nonexistent", app_state)

                assert result is False


class TestSaveOntologyState:
    """Test saving ontology state."""

    def test_save_ontology_state_basic(self):
        """Test saving basic ontology state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                citations = {"10.1111/paper1": ["cites"]}
                ontology_id = helper.save_ontology_state("10.1234/example", citations)

                assert ontology_id > 0
                assert helper.check_doi_in_database("10.1234/example") is True

    def test_save_ontology_state_with_metadata(self):
        """Test saving ontology with metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                citations = {"10.1111/paper1": ["cites"]}
                ontology_id = helper.save_ontology_state(
                    "10.1234/example",
                    citations,
                    original_title="Example Paper",
                    status="in_progress"
                )

                assert ontology_id > 0


class TestUpdateOntologyStatus:
    """Test updating ontology status."""

    def test_update_ontology_status(self):
        """Test updating ontology status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                citations = {"10.1111/paper1": ["cites"]}
                helper.save_ontology_state("10.1234/example", citations, status="in_progress")

                result = helper.update_ontology_status("10.1234/example", "completed")
                assert result is True

    def test_update_status_nonexistent(self):
        """Test updating status of non-existent ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                result = helper.update_ontology_status("10.9999/nonexistent", "completed")
                assert result is False


class TestGetAllSavedOntologies:
    """Test retrieving all saved ontologies."""

    def test_get_all_saved_ontologies_empty(self):
        """Test getting all ontologies from empty database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                ontologies = helper.get_all_saved_ontologies()
                assert ontologies == []

    def test_get_all_saved_ontologies_multiple(self):
        """Test getting multiple saved ontologies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                helper.save_ontology_state("10.1111/example1", {"10.1111/paper1": ["cites"]})
                helper.save_ontology_state("10.2222/example2", {"10.2222/paper2": ["supports"]})

                ontologies = helper.get_all_saved_ontologies()
                assert len(ontologies) == 2


class TestDeleteOntology:
    """Test deleting ontology."""

    def test_delete_ontology(self):
        """Test deleting an ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                helper.save_ontology_state("10.1234/example", {"10.1111/paper1": ["cites"]})
                
                result = helper.delete_ontology("10.1234/example")
                assert result is True
                assert helper.check_doi_in_database("10.1234/example") is False

    def test_delete_nonexistent_ontology(self):
        """Test deleting non-existent ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with DatabaseUIHelper(str(db_path)) as helper:
                result = helper.delete_ontology("10.9999/nonexistent")
                assert result is False
