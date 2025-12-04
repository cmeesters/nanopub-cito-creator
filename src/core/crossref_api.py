import requests
import logging

def get_cited_papers(doi):
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        message = data.get("message", {})
        cited_references = message.get("reference", [])

        cited_dict = {}
        for ref in cited_references:
            title = ref.get("article-title", ref.get("unstructured", "No Title"))
            cited_doi = ref.get("DOI")
            if cited_doi:
                cited_dict[cited_doi] = title
        return cited_dict
    else:
        logging.error(f"Failed to retrieve data: {response.status_code}")
        return {}