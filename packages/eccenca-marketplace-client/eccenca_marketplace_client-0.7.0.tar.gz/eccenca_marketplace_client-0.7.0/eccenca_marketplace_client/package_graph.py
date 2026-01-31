"""Package Graph to query for dependencies"""

from rdflib import Graph, Literal, Namespace

from eccenca_marketplace_client.fields import PackageIdentifier, PyPiIdentifier
from eccenca_marketplace_client.ontology import NS_IRI
from eccenca_marketplace_client.package_version import PackageVersion


class PackageGraph:
    """Package Graph

    combined graph of multiple package manifest with methods to solve
    dependency questions.

    see also: https://github.com/python-poetry/poetry/blob/main/src/poetry/mixology/version_solver.py#L147
    """

    _graph: Graph

    def __init__(self):
        self._graph = self.init_graph()

    @staticmethod
    def init_graph() -> Graph:
        """Initialize the package graph"""
        graph = Graph()
        graph.bind("eccm", Namespace(NS_IRI))
        return graph

    def add_package(self, package_version: PackageVersion) -> None:
        """Add a manifest to the package graph"""
        self._graph = self._graph + package_version.to_rdf_graph()

    def get_python_dependants(self, pypi_id: PyPiIdentifier) -> set[PackageIdentifier]:
        """Get dependants of a python package."""
        query = """
        PREFIX eccm: <https://marketplace.eccenca.com/schema/>
        SELECT DISTINCT ?dependant
        WHERE {
            ?dependant eccm:dependsOnPython ?pypi_id .
        }
        """
        results = self._graph.query(query, initBindings={"pypi_id": Literal(pypi_id)})
        return {PackageVersion.iri_to_id(row.dependant) for row in results}  # type: ignore[union-attr]

    def get_package_dependants(self, package_id: PackageIdentifier) -> set[PackageIdentifier]:
        """Get dependants of a python package."""
        query = """
        PREFIX eccm: <https://marketplace.eccenca.com/schema/>

        SELECT DISTINCT ?dependant
        WHERE {
            ?dependant eccm:dependsOnPackage* ?package_id .
        }
        """
        results = self._graph.query(
            query, initBindings={"package_id": PackageVersion.id_to_iri(package_id)}
        )
        dependants = {PackageVersion.iri_to_id(str(row.dependant)) for row in results}  # type: ignore[union-attr]
        dependants.remove(package_id)
        return dependants
