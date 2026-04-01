"""Test suite for services.ontology_database module."""
import pytest
import tempfile
import json
from pathlib import Path
from src.services.ontology_database import OntologyDatabase


class TestOntologyDatabaseInitialization:
    """Test OntologyDatabase initialization."""

    def test_database_initialization(self):
        """Test database can be initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = OntologyDatabase(str(db_path))
            assert db.connection is not None
            db.close()

    def test_database_file_created(self):
        """Test that database file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = OntologyDatabase(str(db_path))
            db.close()
            assert db_path.exists()

    def test_context_manager_usage(self):
        """Test database can be used as context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                assert db.connection is not None


class TestSaveOntology:
    """Test saving ontologies."""

    def test_save_ontology_basic(self):
        """Test saving a basic ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                citations_data = {
                    "10.1111/paper1": ["cites", "supports"],
                    "10.2222/paper2": ["discusses"]
                }
                ontology_id = db.save_ontology("10.1234/example", citations_data)
                assert ontology_id > 0

    def test_save_ontology_with_metadata(self):
        """Test saving ontology with metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                citations_data = {"10.1111/paper1": ["cites"]}
                ontology_id = db.save_ontology(
                    "10.1234/example",
                    citations_data,
                    original_title="Example Paper",
                    status="in_progress"
                )
                assert ontology_id > 0

    def test_save_ontology_update_existing(self):
        """Test that saving with same DOI updates existing record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                citations_data1 = {"10.1111/paper1": ["cites"]}
                id1 = db.save_ontology("10.1234/example", citations_data1)

                citations_data2 = {"10.1111/paper1": ["cites"], "10.2222/paper2": ["supports"]}
                id2 = db.save_ontology("10.1234/example", citations_data2)

                assert id1 == id2


class TestGetOntology:
    """Test retrieving ontologies."""

    def test_get_ontology_existing(self):
        """Test retrieving an existing ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                citations_data = {
                    "10.1111/paper1": ["cites", "supports"],
                    "10.2222/paper2": ["discusses"]
                }
                db.save_ontology("10.1234/example", citations_data, "Example Paper")
                
                ontology = db.get_ontology("10.1234/example")
                assert ontology is not None
                assert ontology['doi'] == "10.1234/example"
                assert ontology['original_title'] == "Example Paper"
                assert ontology['citations_data'] == citations_data

    def test_get_ontology_nonexistent(self):
        """Test retrieving a non-existent ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                ontology = db.get_ontology("10.9999/nonexistent")
                assert ontology is None

    def test_get_ontology_preserves_citations_data(self):
        """Test that citations data is preserved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                citations_data = {
                    "10.1111/paper1": ["cites", "supports"],
                    "10.2222/paper2": ["discusses"],
                    "10.3333/paper3": ["refutes", "disagrees with"]
                }
                db.save_ontology("10.1234/example", citations_data)
                
                retrieved = db.get_ontology("10.1234/example")
                assert retrieved['citations_data'] == citations_data


class TestOntologyExists:
    """Test checking ontology existence."""

    def test_ontology_exists_true(self):
        """Test ontology_exists returns True for existing ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                db.save_ontology("10.1234/example", {"10.1111/paper1": ["cites"]})
                assert db.ontology_exists("10.1234/example") is True

    def test_ontology_exists_false(self):
        """Test ontology_exists returns False for non-existent ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                assert db.ontology_exists("10.9999/nonexistent") is False

    def test_ontology_exists_after_delete(self):
        """Test ontology_exists returns False after deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                db.save_ontology("10.1234/example", {"10.1111/paper1": ["cites"]})
                db.delete_ontology("10.1234/example")
                assert db.ontology_exists("10.1234/example") is False


class TestGetAllOntologies:
    """Test retrieving all ontologies."""

    def test_get_all_ontologies_empty(self):
        """Test getting all ontologies from empty database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                ontologies = db.get_all_ontologies()
                assert ontologies == []

    def test_get_all_ontologies_multiple(self):
        """Test retrieving multiple ontologies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                db.save_ontology("10.1111/example1", {"10.1111/paper1": ["cites"]})
                db.save_ontology("10.2222/example2", {"10.2222/paper2": ["supports"]})
                db.save_ontology("10.3333/example3", {"10.3333/paper3": ["discusses"]})

                ontologies = db.get_all_ontologies()
                assert len(ontologies) == 3
                dois = [o['doi'] for o in ontologies]
                assert "10.1111/example1" in dois
                assert "10.2222/example2" in dois
                assert "10.3333/example3" in dois


class TestDeleteOntology:
    """Test deleting ontologies."""

    def test_delete_ontology_existing(self):
        """Test deleting an existing ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                db.save_ontology("10.1234/example", {"10.1111/paper1": ["cites"]})
                result = db.delete_ontology("10.1234/example")
                assert result is True
                assert db.ontology_exists("10.1234/example") is False

    def test_delete_ontology_nonexistent(self):
        """Test deleting a non-existent ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                result = db.delete_ontology("10.9999/nonexistent")
                assert result is False


class TestUpdateStatus:
    """Test updating ontology status."""

    def test_update_status_existing(self):
        """Test updating status of existing ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                db.save_ontology("10.1234/example", {"10.1111/paper1": ["cites"]}, status="in_progress")
                result = db.update_status("10.1234/example", "completed")
                assert result is True

                ontology = db.get_ontology("10.1234/example")
                assert ontology['status'] == "completed"

    def test_update_status_nonexistent(self):
        """Test updating status of non-existent ontology."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                result = db.update_status("10.9999/nonexistent", "completed")
                assert result is False

    def test_update_status_various_statuses(self):
        """Test updating to various status values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            with OntologyDatabase(str(db_path)) as db:
                db.save_ontology("10.1234/example", {"10.1111/paper1": ["cites"]})

                statuses = ["in_progress", "completed", "published", "draft"]
                for status in statuses:
                    db.update_status("10.1234/example", status)
                    ontology = db.get_ontology("10.1234/example")
                    assert ontology['status'] == status


class TestDatabasePersistence:
    """Test that data persists across connections."""

    def test_data_persists_across_connections(self):
        """Test that data saved in one connection is available in another."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            # Save data in first connection
            with OntologyDatabase(str(db_path)) as db:
                citations_data = {"10.1111/paper1": ["cites"]}
                db.save_ontology("10.1234/example", citations_data, "Test Paper")

            # Retrieve data in second connection
            with OntologyDatabase(str(db_path)) as db:
                ontology = db.get_ontology("10.1234/example")
                assert ontology is not None
                assert ontology['doi'] == "10.1234/example"
                assert ontology['original_title'] == "Test Paper"
