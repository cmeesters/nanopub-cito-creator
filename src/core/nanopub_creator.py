import argparse
import requests
from nanopub import Nanopub, NanopubConf, load_profile
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF
import logging

# Define namespaces
SCHOLARLY = URIRef("http://purl.org/spar/fabio/ScholarlyWork")

# Predefined dictionary of citation types
CITATION_TYPES = {
    "agrees with": "http://purl.org/spar/cito/agreesWith",
    "cites": "http://purl.org/spar/cito/cites",
    "cites as authority": "http://purl.org/spar/cito/citesAsAuthority",
    "cites as data source": "http://purl.org/spar/cito/citesAsDataSource",
    "cites as evidence": "http://purl.org/spar/cito/citesAsEvidence",
    "cites as metadata Document": "http://purl.org/spar/cito/citesAsMetadataDocument",
    "cites as potential solution": "http://purl.org/spar/cito/citesAsPotentialSolution",
    "cites as recommended reading": "http://purl.org/spar/cito/citesAsRecommendedReading",
    "cites as related": "http://purl.org/spar/cito/citesAsRelated",
    "cites as source document": "http://purl.org/spar/cito/citesAsSourceDocument",
    "cites for information": "http://purl.org/spar/cito/citesForInformation",
    "compiles": "http://purl.org/spar/cito/compiles",
    "confirms": "http://purl.org/spar/cito/confirms",
    "contains assertion from": "http://purl.org/spar/cito/containsAssertionFrom",
    "corrects": "http://purl.org/spar/cito/corrects",
    "credits": "http://purl.org/spar/cito/credits",
    "critics": "http://purl.org/spar/cito/criticizes",
    "derides": "http://purl.org/spar/cito/derides",
    "describes": "http://purl.org/spar/cito/describes",
    "disagrees with": "http://purl.org/spar/cito/disagreesWith",
    "discusses": "http://purl.org/spar/cito/discusses",
    "disputes": "http://purl.org/spar/cito/disputes",
    "documents": "http://purl.org/spar/cito/documents",
    "extends": "http://purl.org/spar/cito/extends",
    "includes excerpt from": "http://purl.org/spar/cito/includesExcerptFrom",
    "includes quotation from": "http://purl.org/spar/cito/includesQuotationFrom",
    "links to": "http://purl.org/spar/cito/linksTo",
    "obtains background information from": "http://purl.org/spar/cito/obtainsBackgroundFrom",
    "obtains support from": "http://purl.org/spar/cito/obtainsSupportFrom",
    "parodies": "http://purl.org/spar/cito/parodies",
    "plagiarizes": "http://purl.org/spar/cito/plagiarizes",
    "qualifies": "http://purl.org/spar/cito/qualifies",
    "refutes": "http://purl.org/spar/cito/refutes",
    "replies to": "http://purl.org/spar/cito/repliesTo",
    "retracts": "http://purl.org/spar/cito/retracts",
    "reviews": "http://purl.org/spar/cito/reviews",
    "ridicules": "http://purl.org/spar/cito/ridicules",
    "speculates on": "http://purl.org/spar/cito/speculatesOn",
    "supports": "http://purl.org/spar/cito/supports",
    "updates": "http://purl.org/spar/cito/updates",
    "uses conclusions from": "http://purl.org/spar/cito/usesConclusionsFrom",
    "uses data from": "http://purl.org/spar/cito/usesDataFrom",
    "uses method in": "http://purl.org/spar/cito/usesMethodIn",
}

# Define conflicting combinations
CONFLICTING_COMBINATIONS = [
    ("agrees with", "disagrees with"),
    ("agrees with", "disputes"),
    ("cites as evidence", "disagrees with"),
]

# Configure logging
logging.basicConfig(
    filename="create_nanopub.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


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


def create_nanopub(original_doi, cited_dois_with_types, conf):
    g = Graph()
    original_uri = URIRef(f"https://doi.org/{original_doi}")
    g.add((original_uri, RDF.type, SCHOLARLY))

    for cited_doi, citation_types in cited_dois_with_types.items():
        cited_uri = URIRef(f"https://doi.org/{cited_doi}")
        for citation_type in citation_types:
            g.add((original_uri, URIRef(CITATION_TYPES[citation_type]), cited_uri))
    logging.info(f'serialized graph: {g.serialize(format="turtle")}')
    
    logging.info(f"creating nanopub with conf: {conf}")
    np = Nanopub(conf=conf, assertion=g)

    try:
        npub = np.publish()
        logging.info(f"Nanopub created: {npub.uri}")
        print(f"Nanopub created: {npub.uri}")
    except Exception as e:
        logging.error(f"Failed to publish nanopub: {e}")
        print(f"Failed to publish nanopub: {e}")