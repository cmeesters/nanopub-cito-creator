import requests
import logging

def get_cited_papers(doi: str):
    """Fetch cited papers from CrossRef API."""
    url = f"https://api.crossref.org/works/{doi}"
    try:
        r = requests.get(url, timeout=15)
    except Exception as e:
        logging.error(f"Request error: {e}")
        return {}
    if r.status_code != 200:
        logging.error(f"CrossRef status {r.status_code}")
        return {}
    data = r.json().get("message", {})
    refs = data.get("reference", [])
    cited = {}
    for ref in refs:
        ref_doi = ref.get("DOI")
        if not ref_doi:
            continue
        
        title = ref.get("article-title") or ref.get("unstructured") or "Untitled"
        
        # Extract authors from unstructured field if available
        authors_str = ""
        if "author" in ref and ref["author"]:
            # Sometimes author is a string like "Smith, J., Jones, K."
            authors_str = ref["author"]
            authors_list = [a.strip() for a in authors_str.split(",")]
            if len(authors_list) > 3:
                authors_str = ", ".join(authors_list[:3]) + " et al."
        elif "unstructured" in ref:
            # Try to extract from unstructured citation
            # This is imperfect but better than nothing
            unstructured = ref["unstructured"]
            # Look for patterns like "Author A, Author B (Year)"
            if "(" in unstructured:
                before_year = unstructured.split("(")[0].strip()
                # Take first part before any dots or semicolons
                potential_authors = before_year.split(".")[0].split(";")[0]
                if len(potential_authors) < 100:  # Sanity check
                    authors_str = potential_authors
        
        if not authors_str:
            authors_str = ""
        
        cited[ref_doi] = {
            'title': title,
            'authors': authors_str
        }
    return cited