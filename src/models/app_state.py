class AppState:
    """Centralized application state management."""

    def __init__(self, initial_doi=None, use_test_server=False, auto_publish=False):
        self.initial_doi = initial_doi
        self.use_test_server = use_test_server
        self.auto_publish = auto_publish

        self.current_doi = None
        self.cited_papers = {}
        self.selected_citations = {}

    def set_doi(self, doi: str):
        self.current_doi = doi

    def set_cited_papers(self, papers: dict):
        self.cited_papers = papers

    def add_citation(self, cited_doi: str, citation_types: list):
        self.selected_citations[cited_doi] = citation_types

    def clear_citations(self):
        self.selected_citations = {}

    def get_citations(self) -> dict:
        return self.selected_citations

    def reset(self):
        self.current_doi = None
        self.cited_papers = {}
        self.selected_citations = {}