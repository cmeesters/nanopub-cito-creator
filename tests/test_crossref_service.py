"""Test suite for services.crossref_service module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from src.services.crossref_service import get_cited_papers


class TestGetCitedPapersSuccess:
    """Test successful retrieval of cited papers."""

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_with_valid_response(self, mock_get):
        """Test getting cited papers with valid API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "article-title": "Paper 1 Title",
                        "author": "Smith, J., Jones, K.",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert isinstance(result, dict)
        assert "10.1111/paper1" in result
        assert result["10.1111/paper1"]["title"] == "Paper 1 Title"

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_extracts_authors(self, mock_get):
        """Test that authors are extracted from the API response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "article-title": "Paper 1 Title",
                        "author": "Smith, J., Jones, K., Williams, M.",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert "10.1111/paper1" in result
        paper = result["10.1111/paper1"]
        assert "authors" in paper
        assert "Smith, J." in paper["authors"]

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_handles_multiple_references(self, mock_get):
        """Test handling of multiple references."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "article-title": "Paper 1",
                        "author": "Author A",
                    },
                    {
                        "DOI": "10.2222/paper2",
                        "article-title": "Paper 2",
                        "author": "Author B",
                    },
                    {
                        "DOI": "10.3333/paper3",
                        "article-title": "Paper 3",
                        "author": "Author C",
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert len(result) == 3
        assert "10.1111/paper1" in result
        assert "10.2222/paper2" in result
        assert "10.3333/paper3" in result

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_handles_unstructured_title(self, mock_get):
        """Test handling of unstructured title when article-title is missing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "unstructured": "Smith, J. et al. (2020). Some paper title. Journal.",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert "10.1111/paper1" in result
        paper = result["10.1111/paper1"]
        assert paper["title"] is not None

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_extracts_authors_from_unstructured(self, mock_get):
        """Test extracting authors from unstructured field."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "unstructured": "Smith, J., Jones, K., Williams, M. (2020). Paper Title.",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert "10.1111/paper1" in result
        paper = result["10.1111/paper1"]
        assert len(paper["authors"]) > 0

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_filters_references_without_doi(self, mock_get):
        """Test that references without DOI are filtered out."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "article-title": "Paper 1",
                        "author": "Author A",
                    },
                    {
                        "article-title": "Paper without DOI",
                        "author": "Author B",
                    },
                    {
                        "DOI": "10.3333/paper3",
                        "article-title": "Paper 3",
                        "author": "Author C",
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert len(result) == 2
        assert "10.1111/paper1" in result
        assert "10.3333/paper3" in result

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_returns_untitled_for_missing_title(self, mock_get):
        """Test that 'Untitled' is used when title is not available."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "author": "Author A",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert result["10.1111/paper1"]["title"] == "Untitled"


class TestGetCitedPapersErrors:
    """Test error handling in get_cited_papers."""

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_handles_connection_error(self, mock_get):
        """Test handling of connection errors."""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        result = get_cited_papers("10.1234/example")

        assert result == {}

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_handles_timeout(self, mock_get):
        """Test handling of request timeouts."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        result = get_cited_papers("10.1234/example")

        assert result == {}

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_handles_generic_exception(self, mock_get):
        """Test handling of generic exceptions."""
        mock_get.side_effect = Exception("Generic error")

        result = get_cited_papers("10.1234/example")

        assert result == {}

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_handles_non_200_status(self, mock_get):
        """Test handling of non-200 HTTP status codes."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert result == {}

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_handles_500_error(self, mock_get):
        """Test handling of 500 server error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert result == {}

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_handles_missing_reference_key(self, mock_get):
        """Test handling of missing 'reference' key in response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {}}
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert result == {}

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_handles_missing_message_key(self, mock_get):
        """Test handling of missing 'message' key in response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        assert result == {}


class TestGetCitedPapersApiCall:
    """Test API call behavior."""

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_calls_correct_url(self, mock_get):
        """Test that the correct CrossRef URL is called."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"reference": []}}
        mock_get.return_value = mock_response

        get_cited_papers("10.1234/example")

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://api.crossref.org/works/10.1234/example" in call_args[0]

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_uses_timeout(self, mock_get):
        """Test that request timeout is set."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"reference": []}}
        mock_get.return_value = mock_response

        get_cited_papers("10.1234/example")

        call_kwargs = mock_get.call_args[1]
        assert "timeout" in call_kwargs
        assert call_kwargs["timeout"] == 15

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_with_various_doi_formats(self, mock_get):
        """Test with various DOI formats."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"reference": []}}
        mock_get.return_value = mock_response

        test_dois = [
            "10.1234/example",
            "10.1234/example.with.dots",
            "10.1234/example-with-dashes",
        ]

        for doi in test_dois:
            get_cited_papers(doi)
            assert f"10.1234" in mock_get.call_args[0][0]


class TestGetCitedPapersAuthorsHandling:
    """Test various author handling scenarios."""

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_limits_authors_to_three_plus_et_al(self, mock_get):
        """Test that more than 3 authors gets truncated with 'et al.'"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "article-title": "Paper 1",
                        "author": "Smith, J., Jones, K., Williams, M., Brown, R.",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        paper = result["10.1111/paper1"]
        assert "et al." in paper["authors"]

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_empty_author_field(self, mock_get):
        """Test handling of empty author field."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "article-title": "Paper 1",
                        "author": "",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        paper = result["10.1111/paper1"]
        assert paper["authors"] == ""

    @patch("src.services.crossref_service.requests.get")
    def test_get_cited_papers_missing_author_field(self, mock_get):
        """Test handling of missing author field."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "reference": [
                    {
                        "DOI": "10.1111/paper1",
                        "article-title": "Paper 1",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = get_cited_papers("10.1234/example")

        paper = result["10.1111/paper1"]
        assert paper["authors"] == ""
