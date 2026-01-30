"""Manifests"""

from abc import ABC
from collections import defaultdict
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from eccenca_marketplace_client import fields, limits
from eccenca_marketplace_client.models.base import PackageBaseModel
from eccenca_marketplace_client.models.dependencies import (
    MarketplacePackageDependency,
    PythonPackageDependency,
    ValidDependency,
)
from eccenca_marketplace_client.models.files import (
    GraphFileSpec,
    ImageFileSpec,
    ProjectFileSpec,
    TextFileSpec,
    ValidFileSpec,
)
from eccenca_marketplace_client.models.metadata import Metadata


class AbstractPackageManifest(PackageBaseModel, ABC):
    """Abstract Package Manifest

    Abstract Base Class for all Package Manifests.
    """

    schema_: fields.SchemaResource
    package_id: fields.PackageIdentifier
    package_version: fields.PackageVersionIdentifier
    metadata: Metadata
    dependencies: Annotated[
        list[ValidDependency],
        Field(
            title="Dependency List",
            description="List of dependency specifications.",
            default_factory=list,
        ),
    ]
    files: Annotated[
        list[ValidFileSpec],
        Field(
            title="File List",
            description="List of file specifications.",
            default_factory=list,
        ),
    ]

    @classmethod
    def validate_dependencies(cls, manifest: "AbstractPackageManifest") -> None:
        """Validate dependencies

        Checks:
        - Unique pypi_id values in PythonPackageDependency items
        - Unique package_id values in MarketplacePackageDependency items

        Args:
            manifest: The package manifest to validate

        Raises:
            ValueError

        """
        pypi_ids = set()
        package_ids = set()
        for dependency in manifest.dependencies:
            if isinstance(dependency, PythonPackageDependency):
                if dependency.pypi_id in pypi_ids:
                    raise ValueError(f"Duplicate pypi id in dependency list: {dependency.pypi_id}")
                pypi_ids.add(dependency.pypi_id)
                if not dependency.pypi_id.startswith("cmem-plugin-"):
                    raise ValueError(
                        f"pypi dependencies must start with 'cmem-plugin-': {dependency.pypi_id}"
                    )
            if isinstance(dependency, MarketplacePackageDependency):
                if dependency.package_id in package_ids:
                    raise ValueError(
                        f"Duplicate identifier in dependency list: {dependency.package_id}"
                    )
                package_ids.add(dependency.package_id)

    @classmethod
    def validate_license(cls, manifest: "AbstractPackageManifest") -> None:
        """Validate license metadata and file consistency

        Ensures that license metadata matches the presence of license files:
        - If a license is specified, a license file must exist
        - If a license file exists, a license must be specified

        Args:
            manifest: The package manifest to validate

        Raises:
            ValueError

        """
        if manifest.metadata.license != fields.PackageLicenseDefault and not manifest.get_license():
            raise ValueError(
                f"License set to {manifest.metadata.license} but no license file found."
            )
        if (
            manifest.metadata.license == fields.PackageLicenseDefault
            and manifest.get_license() is not None
        ):
            raise ValueError("License file found but no license specified.")

    @classmethod
    def validate_images(cls, manifest: "AbstractPackageManifest") -> None:
        """Validate images

        - only once icon
        - only MAX_MARKETPLACE_IMAGES marketplace images
        """
        # count images per role
        image_counts: dict[str, int] = defaultdict(int)
        for image in manifest.get_images():
            image_counts[image.file_role] += 1

        # check rules
        if image_counts[fields.ImageFileRoles.icon] > 1:
            raise ValueError("Only a single icon per package allowed.")
        if image_counts[fields.ImageFileRoles.marketplace] > limits.MAX_MARKETPLACE_IMAGES:
            raise ValueError("Maximum of 10 marketplace images per package allowed.")

    @classmethod
    def validate_urls(cls, manifest: "AbstractPackageManifest") -> None:
        """Validate URLs

        - only one URL per role
        - only HTTPS URLs
        """
        role_count: dict[str, int] = defaultdict(int)
        for url in manifest.metadata.urls:
            role_count[url.url_role] += 1
            if role_count[url.url_role] > 1:
                raise ValueError("Only a single URL per role allowed.")
            if url.url_ref.scheme != "https":
                raise ValueError("Only HTTPS URLs allowed.")

    @classmethod
    def validate_all(cls, manifest: "AbstractPackageManifest") -> None:
        """Additional top level checks

        this method is used to do checks on all manifest types
        """
        cls.validate_dependencies(manifest)
        cls.validate_license(manifest)
        cls.validate_images(manifest)
        cls.validate_urls(manifest)

    def get_graphs(self) -> list[GraphFileSpec]:
        """Get graph file specs"""
        return [_ for _ in self.files if isinstance(_, GraphFileSpec)]

    def get_projects(self) -> list[ProjectFileSpec]:
        """Get project file specs"""
        return [_ for _ in self.files if isinstance(_, ProjectFileSpec)]

    def get_images(self) -> list[ImageFileSpec]:
        """Get image file specs"""
        return [_ for _ in self.files if isinstance(_, ImageFileSpec)]

    def get_texts(self, role: str | None = None) -> list[TextFileSpec]:
        """Get text file specs"""
        if role:
            return [_ for _ in self.files if isinstance(_, TextFileSpec) and _.file_role == role]
        return [_ for _ in self.files if isinstance(_, TextFileSpec)]

    def get_license(self) -> TextFileSpec | None:
        """Get license file spec"""
        licenses = self.get_texts(role=fields.TextFileRoles.license)
        if len(licenses) == 0:
            return None
        return licenses[0]

    def get_readme(self) -> TextFileSpec | None:
        """Get readme file spec"""
        readme = self.get_texts(role=fields.TextFileRoles.readme)
        if len(readme) == 0:
            return None
        return readme[0]


class VocabularyPackageManifest(AbstractPackageManifest):
    """Vocabulary Package Manifest

    A manifest which describes a vocabulary package. This package type contains of
    a single graph which is registered as a vocabulary.
    """

    package_type: Literal[fields.PackageTypes.vocabulary]

    @model_validator(mode="after")
    def check(self: Self) -> Self:
        """Check the validity of file specs

        - exactly one file spec, which needs to be registered as a vocabulary
        - no dependencies
        """
        for file_spec in self.files:
            if not isinstance(file_spec, GraphFileSpec | TextFileSpec | ImageFileSpec):
                raise ValueError(f"Vocabulary Packages: illegal files spec ({type(file_spec)})")  # noqa: TRY004
        if len(self.get_graphs()) > 1:
            raise ValueError("Vocabulary Packages allow a single graph file spec only.")
        if len(self.get_graphs()) == 0:
            raise ValueError("Vocabulary Packages need a single graph file spec.")
        if not self.get_graphs()[0].register_as_vocabulary:
            raise ValueError("The graph of a Vocabulary Package needs register_as_vocabulary=true.")
        if len(self.dependencies) > 0:
            raise ValueError("Vocabulary Packages do not allow dependencies.")
        AbstractPackageManifest.validate_all(self)
        return self


class ProjectPackageManifest(AbstractPackageManifest):
    """Project Package Manifest

    A manifest which describes a project package. This package type contains of
    multiple graph and project files which work together as a project.
    """

    package_type: Literal[fields.PackageTypes.project]

    @model_validator(mode="after")
    def check(self: Self) -> Self:
        """Check the validity of file specs

        - the same file path is not allowed in more than one file spec
        - the same graph iri is not allowed in more than one file spec
        - allowed maximum of graphs and files
        - + all checks from abstract manifest
        """
        file_paths: list[str] = []
        graph_iris: list[str] = []
        project_ids: list[str] = []
        for file_spec in self.files:
            file_path = file_spec.file_path
            if file_path in file_paths:
                raise ValueError(f"Same path in more than one filespec: {file_path}")
            file_paths.append(file_path)
            if isinstance(file_spec, GraphFileSpec):
                graph_iri = str(file_spec.graph_iri)
                if graph_iri in graph_iris:
                    raise ValueError(f"Same Graph IRI in more than one filespec: {graph_iri}")
                graph_iris.append(graph_iri)
            if isinstance(file_spec, ProjectFileSpec):
                project_id = file_spec.project_id
                if project_id in project_ids:
                    raise ValueError(f"Same Project ID in more than one filespec: {project_id}")
                project_ids.append(project_id)
            if len(graph_iris) > limits.MAX_GRAPH_FILES:
                raise ValueError(f"Maximum graphs of {limits.MAX_GRAPH_FILES} reached.")
            if len(project_ids) > limits.MAX_PROJECT_FILES:
                raise ValueError(f"Maximum projects of {limits.MAX_PROJECT_FILES} reached.")

        AbstractPackageManifest.validate_all(self)
        return self


ValidManifest = Annotated[
    VocabularyPackageManifest | ProjectPackageManifest, Field(discriminator="package_type")
]
