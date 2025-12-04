import logging
from nanopub import Nanopub
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from models.citation_types import CITATION_TYPES

SCHOLARLY = URIRef("http://purl.org/spar/fabio/ScholarlyWork")

def create_nanopub(original_doi, cited_map, conf):
    g = Graph()
    original_uri = URIRef(f"https://doi.org/{original_doi}")
    g.add((original_uri, RDF.type, SCHOLARLY))
    for cited_doi, types in cited_map.items():
        cited_uri = URIRef(f"https://doi.org/{cited_doi}")
        for t in types:
            g.add((original_uri, URIRef(CITATION_TYPES[t]), cited_uri))
    logging.info(g.serialize(format="turtle"))
    np = Nanopub(conf=conf, assertion=g)
    published = np.publish()
    logging.info(f"Published nanopub: {published.uri}")
    return published.uri