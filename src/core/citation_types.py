# File: /nanopub-cito-wx/nanopub-cito-wx/src/core/citation_types.py

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

CONFLICTING_COMBINATIONS = [
    ("agrees with", "disagrees with"),
    ("agrees with", "disputes"),
    ("cites as evidence", "disagrees with"),
]

def has_conflicts(selected_keys):
    for combo in CONFLICTING_COMBINATIONS:
        if combo[0] in selected_keys and combo[1] in selected_keys:
            return True
    return False