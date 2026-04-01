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
    
    # Log the RDF being created
    logging.info(f"Creating nanopub for DOI: {original_doi}")
    logging.info(f"Number of citations: {len(cited_map)}")
    
    for cited_doi, types in cited_map.items():
        cited_uri = URIRef(f"https://doi.org/{cited_doi}")
        logging.info(f"  Citation: {cited_doi} with {len(types)} type(s): {types}")
        for t in types:
            if t not in CITATION_TYPES:
                logging.warning(f"Unknown citation type: {t}")
                continue
            pred_uri = URIRef(CITATION_TYPES[t])
            g.add((original_uri, pred_uri, cited_uri))
    
    # Log the RDF
    rdf_ttl = g.serialize(format="turtle")
    logging.info(f"RDF Graph:\n{rdf_ttl}")
    
    try:
        np = Nanopub(conf=conf, assertion=g)
        published = np.publish()

        # Log the published nanopub URI
        logging.info(f"Published nanopub object: {published}")
        
        # Handle different return types from nanopub library
        if isinstance(published, tuple):
            # If it's a tuple, the first element is likely the nanopub object
            published_np = published[0]
            if hasattr(published_np, 'uri'):
                uri = published_np.uri
            else:
                # Fallback: try to get URI from source_uri attribute
                uri = getattr(published_np, 'source_uri', str(published))
        elif hasattr(published, 'uri'):
            uri = published.uri
        else:
            # Fallback for unexpected return type
            uri = str(published)
        
        logging.info(f"Published nanopub: {uri}")
        return uri
    except Exception as e:
        logging.error(f"Error publishing nanopub: {e}")
        logging.error(f"Error type: {type(e).__name__}")
        
        # Try to get more details from HTTP error
        if hasattr(e, 'response'):
            logging.error(f"Response status code: {e.response.status_code}")
            logging.error(f"Response headers: {e.response.headers}")
            logging.error(f"Response text: {e.response.text}")
        
        # Log the nanopub that failed
        if 'np' in locals():
            try:
                logging.error(f"Failed nanopub RDF:\n{np.rdf.serialize(format='turtle')}")
            except:
                logging.error("Could not serialize failed nanopub")
        
        raise