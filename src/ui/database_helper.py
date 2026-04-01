"""UI helper for managing database state and button actions."""
from typing import Optional, Dict

try:
    # Try relative import (for package use)
    from ..services.ontology_database import OntologyDatabase
    from ..models.app_state import AppState
except ImportError:
    # Fall back to absolute import (for direct script execution)
    from services.ontology_database import OntologyDatabase
    from models.app_state import AppState


class DatabaseUIHelper:
    """Helper class for managing database interactions in the UI."""

    def __init__(self, db_path: str = "ontologies.db"):
        """Initialize the database helper.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db = OntologyDatabase(db_path)

    def check_doi_in_database(self, doi: str) -> bool:
        """Check if a DOI has a saved ontology in the database.
        
        Args:
            doi: DOI to check
            
        Returns:
            True if ontology exists, False otherwise
        """
        return self.db.ontology_exists(doi)

    def load_ontology_for_redo(self, doi: str, app_state: AppState) -> bool:
        """Load a saved ontology for re-annotation.
        
        Args:
            doi: DOI of the ontology to load
            app_state: Application state to populate
            
        Returns:
            True if successfully loaded, False otherwise
        """
        ontology = self.db.get_ontology(doi)
        if not ontology:
            return False

        # Populate app state with saved data
        app_state.set_doi(doi)
        app_state.set_cited_papers({})  # Will be repopulated from citations_data
        
        # Convert citations_data format back to app_state format
        citations = {}
        for cited_doi, citation_types in ontology['citations_data'].items():
            citations[cited_doi] = citation_types
            app_state.add_citation(cited_doi, citation_types)
        
        return True

    def load_ontology_for_continuation(self, doi: str, app_state: AppState) -> bool:
        """Load a saved ontology to continue annotation.
        
        Args:
            doi: DOI of the ontology to load
            app_state: Application state to populate
            
        Returns:
            True if successfully loaded, False otherwise
        """
        # Same as load_ontology_for_redo, but could have different behavior
        return self.load_ontology_for_redo(doi, app_state)

    def save_ontology_state(
        self,
        doi: str,
        citations: Dict[str, list],
        original_title: str = None,
        status: str = "in_progress"
    ) -> int:
        """Save the current ontology state to database.
        
        Args:
            doi: DOI of the original paper
            citations: Dictionary of citations with their types
            original_title: Title of the original paper
            status: Status of the ontology
            
        Returns:
            ID of the saved record
        """
        return self.db.save_ontology(doi, citations, original_title, status)

    def update_ontology_status(self, doi: str, status: str) -> bool:
        """Update the status of a saved ontology.
        
        Args:
            doi: DOI of the ontology
            status: New status value
            
        Returns:
            True if updated, False if not found
        """
        return self.db.update_status(doi, status)

    def get_all_saved_ontologies(self) -> list:
        """Get all saved ontologies from the database.
        
        Returns:
            List of ontology records
        """
        return self.db.get_all_ontologies()

    def delete_ontology(self, doi: str) -> bool:
        """Delete a saved ontology.
        
        Args:
            doi: DOI of the ontology to delete
            
        Returns:
            True if deleted, False if not found
        """
        return self.db.delete_ontology(doi)
    
    def mark_real_publication(self, doi: str, nanopub_uri: str) -> bool:
        """Mark that a real (non-test) nanopub has been published.
        
        Args:
            doi: DOI of the ontology
            nanopub_uri: URI of the published nanopub
            
        Returns:
            True if updated, False if not found
        """
        return self.db.mark_real_publication(doi, nanopub_uri)
    
    def has_real_publication(self, doi: str) -> bool:
        """Check if a real (non-test) nanopub has been published for this DOI.
        
        Args:
            doi: DOI to check
            
        Returns:
            True if a real nanopub has been published
        """
        return self.db.has_real_publication(doi)

    def close(self):
        """Close the database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
