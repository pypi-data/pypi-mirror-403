from copy import deepcopy

DEFAULT_PAYLOAD_TEMPLATE = {
    "baseUri": "",
    "idType": "INCREMENTAL",
    "idPrefix": "",
    "idStartNumber": 1,
    "idNumberDigits": 3,
    "shortDisplayName": "",
    "longDisplayName": "",
    "version": "1",
    "annotationProperties": [],
    "relationalProperties": [],
    "ontologyMetadataProperties": [],
    "description": "",
    "ontologyFileWebLocation": "",
    "inferred": False,
    "allowReverseMappings": False,
    "validateOntology": False,
    "importCustomDatatypes": False,
    "ontologyInstances": False,
    "keywords": [],
    "propertiesToHide": [],
    "synonymProperties": ["http://www.geneontology.org/formats/oboInOwl#hasExactSynonym"],
    "mappingProperties": ["http://www.geneontology.org/formats/oboInOwl#hasDbXref"],
    "allLabelProperties": ["http://www.w3.org/2000/01/rdf-schema#label"],
    "partonomyProperties": ["http://purl.obolibrary.org/obo/BFO_0000050"],
    "derivesFromProperties": ["http://purl.obolibrary.org/obo/RO_0001000"],
    "developsFromProperties": ["http://purl.obolibrary.org/obo/RO_0002202"],
    "obsoleteSubClassProperties": [],
    "textualDefinitionProperties": ["http://purl.obolibrary.org/obo/IAO_0000115"],
    "obsoleteAnnotationPropertyKeyValue": [
        {
            "obsoleteAnnotationPropertyIRI": "http://www.w3.org/2002/07/owl#deprecated",
            "obsoleteWhenHasValue": "true"
        }
    ],
    "hierarchicalProperties": [
        "http://purl.obolibrary.org/obo/BFO_0000050",
        "http://purl.obolibrary.org/obo/RO_0002202"
    ],
    "defaultLangTag": "en",
    "useLang": False,
    "idStrategies": [],
    "provenanceSettings": {
        "enabled": False,
        "entityProperties": {
            "enabled": False,
            "createdBy": "http://purl.org/pav/createdBy",
            "createdTimestamp": "http://purl.org/pav/createdOn",
            "lastUpdatedBy": "http://purl.org/pav/curatedBy",
            "lastUpdatedTimestamp": "http://purl.org/pav/lastUpdateOn",
            "allAnnotationProperties": False
        },
        "valueProperties": {
            "enabled": False,
            "createdBy": "http://purl.org/pav/createdBy",
            "createdTimestamp": "http://purl.org/pav/createdOn",
            "lastUpdatedBy": "http://purl.org/pav/curatedBy",
            "lastUpdatedTimestamp": "http://purl.org/pav/lastUpdateOn",
            "allAnnotationProperties": False
        },
        "dateFormat": "yyyy-MM-dd HH:mm:ss"
    },
    "populateMetadataPropertiesOnImport": False,
    "allowDeletes": True,
    "ontologyUri": "",
    "ontologyId": "",
    "extractSuperclassesFromClassExpression": True,
    "sourceOntologySet": [],
    "designPatterns": {
        "ontologyId": "",
        "userLogin": None,
        "timestamp": None,
        "ontologyDesignPatternsJSON": {
            "ontologyDesignPatternList": []
        },
        "validation": None,
        "allLabelsUnique": {
            "type": "ALL_LABELS_UNIQUE",
            "severity": "WARNING",
            "enabled": False,
            "ignoreCase": False
        },
        "allSynonymsUnique": {
            "type": "ALL_SYNONYMS_UNIQUE",
            "severity": "WARNING",
            "enabled": False,
            "ignoreCase": False
        },
        "noOverlapBetweenLabelsAndSynonyms": {
            "type": "NO_OVERLAP_BETWEEN_LABELS_AND_SYNONYMS",
            "severity": "WARNING",
            "enabled": False,
            "ignoreCase": False
        }
    }
}


def build_ontology_payload(
    *,
    ontology_id: str,
    base_uri: str,
    ontology_uri: str,
    id_prefix: str,
    id_start_number: int = 1,
    id_number_digits: int = 3,
    short_display_name: str,
    long_display_name: str,
    ontology_file_web_location: str,
    validate_ontology: bool = False,
    keywords: list[str] = None,
    populate_metadata_properties_on_import: bool = True,
    allow_deletes: bool = True,
    all_labels_unique: dict = None,
    all_synonyms_unique: dict = None
) -> dict:
    payload = deepcopy(DEFAULT_PAYLOAD_TEMPLATE)

    payload["ontologyId"] = ontology_id
    payload["ontologyUri"] = ontology_uri
    payload["baseUri"] = base_uri
    payload["idPrefix"] = id_prefix
    payload["idStartNumber"] = id_start_number
    payload["idNumberDigits"] = id_number_digits
    payload["shortDisplayName"] = short_display_name
    payload["longDisplayName"] = long_display_name
    payload["ontologyFileWebLocation"] = ontology_file_web_location
    payload["validateOntology"] = validate_ontology
    payload["keywords"] = keywords or [short_display_name.split()[0]]
    payload["populateMetadataPropertiesOnImport"] = populate_metadata_properties_on_import
    payload["allowDeletes"] = allow_deletes

    payload["designPatterns"]["ontologyId"] = ontology_id

    if all_labels_unique:
        pattern = payload["designPatterns"]["allLabelsUnique"]
        pattern.update({
            "enabled": all_labels_unique.get("enabled", pattern["enabled"]),
            "ignoreCase": all_labels_unique.get("ignore_case", pattern["ignoreCase"]),
            "severity": all_labels_unique.get("severity", pattern["severity"])
        })

    if all_synonyms_unique:
        pattern = payload["designPatterns"]["allSynonymsUnique"]
        pattern.update({
            "enabled": all_synonyms_unique.get("enabled", pattern["enabled"]),
            "ignoreCase": all_synonyms_unique.get("ignore_case", pattern["ignoreCase"]),
            "severity": all_synonyms_unique.get("severity", pattern["severity"])
        })

    return payload

def make_source_ontology_set(ontology_ids: list[str]) -> list[dict]:
    """
    Create a properly structured 'sourceOntologySet' for application ontology builds.

    Args:
        ontology_ids (list): List of ontology IDs.

    Returns:
        list: A list of dictionaries formatted for sourceOntologySet.
    """
    return [
        {
            "ontologyId": oid,
            "includeAll": True,
            "copySourceMetadata": False,
            "includeRootClassSet": [],
            "excludeRootClassSet": [],
            "includeAncestorsSet": [],
            "excludeAncestorsSet": [],
            "advancedQueriesSet": [],
            "sparqlQueriesSet": [],
            "ontologyFakeRootId": None,
            "snapshotName": None,
            "ord": None
        }
        for oid in ontology_ids
    ]

def ontology_exists(client, ontology_id: str) -> bool:
    """
    Check if an ontology exists in CENtree.

    Args:
        client: An instance of CENtreeClient or subclass.
        ontology_id (str): Ontology ID to check.

    Returns:
        bool: True if it exists, False otherwise.
    """
    try:
        resp = client.request("GET", "/api/search/ontologies/exact", params={"q": ontology_id},
                              suppress_warning=True)
        return resp.status_code == 200 and bool(resp.json().get("content"))
    except Exception:
        return False
