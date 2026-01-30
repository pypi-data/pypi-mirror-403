"""Create Ontology from pydantic models"""

from importlib.metadata import version
from types import UnionType
from typing import Any, get_args, get_origin

from pydantic import BaseModel, HttpUrl
from pydantic._internal._model_construction import ModelMetaclass
from pydantic.fields import FieldInfo
from rdflib import XSD, Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, VANN

from eccenca_marketplace_client.models.files import AbstractFileSpec, GraphFileSpec, ProjectFileSpec
from eccenca_marketplace_client.models.manifests import (
    AbstractPackageManifest,
    ProjectPackageManifest,
    VocabularyPackageManifest,
)
from eccenca_marketplace_client.models.metadata import Metadata

NS_IRI = "https://marketplace.eccenca.com/schema/"
NS_PREFIX = "eccm"
NS_LABEL = "eccenca Marketplace Ontology and Shapes"
NS_COMMENT = "Vocabulary to describe eccenca Marketplace Packages."
NS_VERSION = "v" + version("eccenca-marketplace-client")
NS_CLASSES = [
    AbstractPackageManifest,
    VocabularyPackageManifest,
    ProjectPackageManifest,
    Metadata,
    AbstractFileSpec,
    GraphFileSpec,
    ProjectFileSpec,
]

TYPE_TO_XSD = {
    str: XSD.string,
    int: XSD.integer,
    float: XSD.double,
    bool: XSD.boolean,
    HttpUrl: XSD.anyURI,
}


def normalize_type(annotation: type[Any] | None) -> type:
    """Normalize type by unwrapping Annotated, Union, and list wrappers"""
    if annotation is None:
        raise TypeError("Cannot normalize None")

    if isinstance(annotation, str):
        return str

    origin = get_origin(annotation)
    args = get_args(annotation)

    if hasattr(annotation, "__metadata__") and args:
        return normalize_type(args[0])

    if origin is type(None) or (origin and str(origin).startswith("typing.Union")):
        non_none_args = [arg for arg in args if arg is not type(None)]
        if not non_none_args:
            msg = f"Cannot normalize Union type with only None: {annotation}"
            raise ValueError(msg)
        return normalize_type(non_none_args[0])

    if origin is list:
        return normalize_type(args[0]) if args else str

    return annotation


def get_ontology_graph() -> Graph:
    """Get Ontology Graph"""
    graph = Graph(identifier=NS_IRI)
    graph += get_ontology_description()
    for model in NS_CLASSES:
        graph += get_class_description(model)
    for model in NS_CLASSES:
        graph += get_property_descriptions(model)
    graph += get_subclass_relationships()
    graph += get_manifest_json_property()
    return graph


def get_manifest_json_property() -> Graph:
    """Add manifest_json property to ontology.

    This property stores the complete manifest JSON as a literal,
    enabling simple reconstruction of PackageVersion objects.
    """
    graph = Graph()
    property_iri = get_property_iri("manifest_json")

    graph.add((property_iri, RDF.type, OWL.DatatypeProperty))
    graph.add((property_iri, RDFS.range, XSD.string))

    # Add domain for both package manifest types
    domains_include = URIRef("http://schema.org/domainIncludes")
    graph.add((property_iri, domains_include, get_class_iri(ProjectPackageManifest)))
    graph.add((property_iri, domains_include, get_class_iri(VocabularyPackageManifest)))

    graph.add((property_iri, RDFS.label, Literal("Manifest JSON", lang="en")))
    graph.add(
        (
            property_iri,
            RDFS.comment,
            Literal(
                "Complete manifest JSON string for easy reconstruction of PackageVersion objects",
                lang="en",
            ),
        )
    )
    return graph


def get_ontology_description() -> Graph:
    """Get Ontology Description"""
    ontology = URIRef(NS_IRI)
    graph = Graph()
    graph.add((ontology, RDF.type, OWL.Ontology))
    graph.add((ontology, RDFS.label, Literal(NS_LABEL, lang="en")))
    graph.add((ontology, RDFS.comment, Literal(NS_COMMENT, lang="en")))
    graph.add((ontology, OWL.versionInfo, Literal(NS_VERSION)))
    graph.add((ontology, VANN.preferredNamespaceUri, Literal(NS_IRI)))
    graph.add((ontology, VANN.preferredNamespacePrefix, Literal(NS_PREFIX)))
    return graph


def get_class_iri(model: ModelMetaclass) -> URIRef:
    """Get Class IRI"""
    return URIRef(NS_IRI + "class_" + model.__name__)


def get_property_iri(key: str) -> URIRef:
    """Get Property IRI"""
    return URIRef(NS_IRI + "property_" + key)


def get_class_description(model: ModelMetaclass) -> Graph:
    """Get Class Description"""
    graph = Graph()
    class_iri = get_class_iri(model)
    graph.add((class_iri, RDF.type, OWL.Class))

    class_label_str = model.__doc__.split("\n")[0] if model.__doc__ else model.__name__
    class_label = Literal(class_label_str, lang="en")
    graph.add((class_iri, RDFS.label, class_label))

    class_comment_str = ("\n".join(model.__doc__.split("\n")[2:])).strip() if model.__doc__ else ""
    if class_comment_str != "":
        class_comment = Literal(class_comment_str, lang="en")
        graph.add((class_iri, RDFS.comment, class_comment))
    return graph


def is_datatype_property(field_info: FieldInfo) -> bool:
    """Get Datatype Property Flag"""
    normalized = normalize_type(field_info.annotation)

    if normalized in TYPE_TO_XSD:
        return True

    if str(normalized) == "str | None":
        return True

    if type(normalized) is UnionType:
        return False

    return not (isinstance(normalized, ModelMetaclass) and issubclass(normalized, BaseModel))


def get_property_range(field_info: FieldInfo) -> URIRef:
    """Get Property Range"""
    normalized = normalize_type(field_info.annotation)

    if normalized in TYPE_TO_XSD:
        return TYPE_TO_XSD[normalized]

    if isinstance(normalized, ModelMetaclass) and issubclass(normalized, BaseModel):
        return get_class_iri(normalized)

    return XSD.string


def get_property_description(domain: ModelMetaclass, key: str, field_info: FieldInfo) -> Graph:
    """Get Property Description"""
    graph = Graph()
    property_iri = get_property_iri(key)

    if is_datatype_property(field_info):
        graph.add((property_iri, RDF.type, OWL.DatatypeProperty))
    else:
        graph.add((property_iri, RDF.type, OWL.ObjectProperty))
    graph.add((property_iri, RDFS.range, get_property_range(field_info)))

    domains_include = URIRef("http://schema.org/domainIncludes")
    graph.add((property_iri, domains_include, get_class_iri(domain)))

    property_label_str = field_info.title if field_info.title else key
    graph.add((property_iri, RDFS.label, Literal(property_label_str, lang="en")))

    property_comment_str = field_info.description
    if field_info.description is not None:
        graph.add((property_iri, RDFS.comment, Literal(property_comment_str, lang="en")))
    return graph


def get_property_descriptions(model: ModelMetaclass) -> Graph:
    """Get Property Descriptions"""
    graph = Graph()
    if issubclass(model, BaseModel):
        for key, field_info in model.model_fields.items():
            graph += get_property_description(model, key, field_info)
    return graph


def get_subclass_relationships() -> Graph:
    """Get Subclass Relationships"""
    graph = Graph()
    for model in NS_CLASSES:
        for base in model.__bases__:
            if base in NS_CLASSES:
                child_iri = get_class_iri(model)
                parent_iri = get_class_iri(base)  # type: ignore[arg-type]
                graph.add((child_iri, RDFS.subClassOf, parent_iri))
    return graph


def get_data_graph_iri() -> str:
    """Get Package Data Graph IRI"""
    return "https://ns.eccenca.com/data/config/"


def get_fetch_query() -> str:
    """Get Package Fetch Query.

    Fetches the manifest_json property which contains the complete manifest
    as JSON, enabling simple reconstruction with packages_from_sparql_bindings().
    """
    return f"""
    PREFIX {NS_PREFIX}: <{NS_IRI}>

    SELECT ?manifest_json
    WHERE {{
        GRAPH <{get_data_graph_iri()}> {{
            ?package {NS_PREFIX}:property_manifest_json ?manifest_json .
        }}
    }}
    """


def get_delete_query(package_iri: str) -> str:
    """Get Package Delete Query"""
    return f"""
    PREFIX {NS_PREFIX}: <{NS_IRI}>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    DELETE {{
        GRAPH <{get_data_graph_iri()}> {{
            ?s ?p ?o .
        }}
    }}
    WHERE {{
        GRAPH <{get_data_graph_iri()}> {{
            ?s ?p ?o .
            FILTER(STRSTARTS(STR(?s), "{package_iri}"))
        }}
    }}
    """
