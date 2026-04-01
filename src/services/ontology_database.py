"""SQLite database service for storing and retrieving ontologies."""
import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class OntologyDatabase:
    """Service for managing ontology storage in SQLite."""

    def __init__(self, db_path: str = "ontologies.db"):
        """Initialize the database connection and create tables if needed.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection = None
        self._init_db()

    def _init_db(self):
        """Initialize database connection and create tables if needed."""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            self._create_tables()
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            raise

    def _create_tables(self):
        """Create necessary database tables if they don't exist."""
        cursor = self.connection.cursor()
        
        # Table for storing ontologies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ontologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doi TEXT UNIQUE NOT NULL,
                original_title TEXT,
                citations_data TEXT NOT NULL,
                status TEXT DEFAULT 'in_progress',
                published_real_nanopub INTEGER DEFAULT 0,
                nanopub_uri TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add column to existing tables if it doesn't exist (for migration)
        cursor.execute("PRAGMA table_info(ontologies)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'published_real_nanopub' not in columns:
            cursor.execute("ALTER TABLE ontologies ADD COLUMN published_real_nanopub INTEGER DEFAULT 0")
        if 'nanopub_uri' not in columns:
            cursor.execute("ALTER TABLE ontologies ADD COLUMN nanopub_uri TEXT")
        
        # Table for tracking citation metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ontology_id INTEGER NOT NULL,
                cited_doi TEXT NOT NULL,
                title TEXT,
                authors TEXT,
                citation_types TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ontology_id) REFERENCES ontologies(id) ON DELETE CASCADE
            )
        """)
        
        self.connection.commit()

    def save_ontology(self, doi: str, citations_data: Dict, original_title: str = None, status: str = "in_progress") -> int:
        """Save or update an ontology record.
        
        Args:
            doi: DOI of the original paper
            citations_data: Dictionary of citations with their types
            original_title: Title of the original paper
            status: Status of the ontology ('in_progress', 'completed', 'published')
            
        Returns:
            ID of the saved/updated record
        """
        try:
            cursor = self.connection.cursor()
            citations_json = json.dumps(citations_data)
            
            cursor.execute("""
                INSERT INTO ontologies (doi, original_title, citations_data, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(doi) DO UPDATE SET
                    citations_data = ?,
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (doi, original_title, citations_json, status, citations_json, status))
            
            result = cursor.fetchone()
            ontology_id = result[0]
            self.connection.commit()
            logging.info(f"Saved ontology for DOI {doi} with ID {ontology_id}")
            return ontology_id
            
        except sqlite3.Error as e:
            logging.error(f"Error saving ontology: {e}")
            raise

    def get_ontology(self, doi: str) -> Optional[Dict]:
        """Retrieve an ontology by DOI.
        
        Args:
            doi: DOI of the original paper
            
        Returns:
            Dictionary containing ontology data, or None if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, doi, original_title, citations_data, status, created_at, updated_at
                FROM ontologies
                WHERE doi = ?
            """, (doi,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'doi': row['doi'],
                    'original_title': row['original_title'],
                    'citations_data': json.loads(row['citations_data']),
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
            
        except sqlite3.Error as e:
            logging.error(f"Error retrieving ontology: {e}")
            raise

    def ontology_exists(self, doi: str) -> bool:
        """Check if an ontology exists for a given DOI.
        
        Args:
            doi: DOI to check
            
        Returns:
            True if ontology exists, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 FROM ontologies WHERE doi = ? LIMIT 1", (doi,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logging.error(f"Error checking ontology existence: {e}")
            return False

    def get_all_ontologies(self) -> List[Dict]:
        """Retrieve all stored ontologies.
        
        Returns:
            List of ontology dictionaries
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, doi, original_title, status, created_at, updated_at
                FROM ontologies
                ORDER BY updated_at DESC
            """)
            
            ontologies = []
            for row in cursor.fetchall():
                ontologies.append({
                    'id': row['id'],
                    'doi': row['doi'],
                    'original_title': row['original_title'],
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            return ontologies
            
        except sqlite3.Error as e:
            logging.error(f"Error retrieving ontologies: {e}")
            return []

    def delete_ontology(self, doi: str) -> bool:
        """Delete an ontology by DOI.
        
        Args:
            doi: DOI of the ontology to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM ontologies WHERE doi = ?", (doi,))
            self.connection.commit()
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            logging.error(f"Error deleting ontology: {e}")
            raise

    def update_status(self, doi: str, status: str) -> bool:
        """Update the status of an ontology.
        
        Args:
            doi: DOI of the ontology
            status: New status value
            
        Returns:
            True if updated, False if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE ontologies
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE doi = ?
            """, (status, doi))
            self.connection.commit()
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            logging.error(f"Error updating status: {e}")
            raise
    
    def mark_real_publication(self, doi: str, nanopub_uri: str) -> bool:
        """Mark that a real (non-test) nanopub has been published.
        
        Args:
            doi: DOI of the ontology
            nanopub_uri: URI of the published nanopub
            
        Returns:
            True if updated, False if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE ontologies
                SET published_real_nanopub = 1, nanopub_uri = ?, status = 'published', updated_at = CURRENT_TIMESTAMP
                WHERE doi = ?
            """, (nanopub_uri, doi))
            self.connection.commit()
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            logging.error(f"Error marking publication: {e}")
            raise
    
    def has_real_publication(self, doi: str) -> bool:
        """Check if a real (non-test) nanopub has been published for this DOI.
        
        Args:
            doi: DOI to check
            
        Returns:
            True if a real nanopub has been published
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT published_real_nanopub FROM ontologies WHERE doi = ?", (doi,))
            row = cursor.fetchone()
            return row and row[0] == 1
        except sqlite3.Error as e:
            logging.error(f"Error checking publication status: {e}")
            return False

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
