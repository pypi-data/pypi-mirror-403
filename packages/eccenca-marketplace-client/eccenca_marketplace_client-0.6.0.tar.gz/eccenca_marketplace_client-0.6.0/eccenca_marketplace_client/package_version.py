"""Package Version"""

import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, is_zipfile

from pydantic import TypeAdapter
from rdflib import RDF, Graph, Literal, Namespace, URIRef

from eccenca_marketplace_client import limits
from eccenca_marketplace_client.exceptions import (
    ManifestContentMismatchError,
    PackageArchiveNotZIPError,
)
from eccenca_marketplace_client.fields import FileSpecFilePathPattern, PackageIdentifier
from eccenca_marketplace_client.image import PortableNetworkGraphics
from eccenca_marketplace_client.models.dependencies import (
    MarketplacePackageDependency,
    PythonPackageDependency,
)
from eccenca_marketplace_client.models.files import (
    GraphFileSpec,
    ImageFileSpec,
    ProjectFileSpec,
    TextFileSpec,
)
from eccenca_marketplace_client.models.manifests import (
    ProjectPackageManifest,
    ValidManifest,
    VocabularyPackageManifest,
)
from eccenca_marketplace_client.models.responses import PackageMetadata, PackageVersionExcerpt
from eccenca_marketplace_client.ontology import NS_IRI, get_data_graph_iri


class PackageVersion:
    """Package Version

    This is a concrete version of a package.
    """

    manifest: ValidManifest
    archive: Path | None = None
    directory: Path | None = None

    def __init__(
        self, manifest: ValidManifest, archive: Path | None = None, directory: Path | None = None
    ) -> None:
        """Init from an already parsed Manifest model

        Note: This initialization DOES NOT validate missing/additional files.
        """
        self.manifest = manifest
        self.archive = archive
        self.directory = directory

    @classmethod
    def from_json(cls, json_text: str) -> "PackageVersion":
        """Init from a JSON Manifest Text

        Note: This initialization DOES NOT validate missing/additional files.
        """
        return cls(manifest=PackageVersion.load_manifest(json_text))

    @classmethod
    def from_path(cls, path: Path) -> "PackageVersion":
        """Init from a JSON Manifest File Path

        Note: This initialization DOES NOT validate missing/additional files.
        """
        json_text = Path(path).read_text()
        return cls(manifest=PackageVersion.load_manifest(json_text))

    @classmethod
    def from_archive(cls, archive: Path, validate_files: bool = True) -> "PackageVersion":
        """Init from package archive

        Note: This initialization DOES VALIDATE missing/additional files.
        """
        if not is_zipfile(archive):
            raise PackageArchiveNotZIPError(str(archive.name))
        with zipfile.ZipFile(archive, "r") as zipf, zipf.open("manifest.json") as file:
            json_text = file.read().decode("utf-8")
        manifest = PackageVersion.load_manifest(json_text)
        if validate_files:
            PackageVersion.validate_file_paths(manifest, archive)
        return cls(manifest=manifest, archive=archive)

    @classmethod
    def from_directory(cls, directory: Path, validate_files: bool = True) -> "PackageVersion":
        """Init from package root directory

        Note: This initialization DOES VALIDATE missing/additional files.
        """
        if not directory.is_dir():
            raise ValueError(f"Path {directory} is not a directory.")
        json_text = (directory / "manifest.json").read_text()
        manifest = PackageVersion.load_manifest(json_text)
        if validate_files:
            PackageVersion.validate_file_paths(manifest, directory)
            PackageVersion.validate_text_files(manifest, directory)
            PackageVersion.validate_image_files(manifest, directory)
        return cls(manifest=manifest, directory=directory)

    @staticmethod
    def load_manifest(json_text: str) -> ValidManifest:
        """Load / Parse Manifest JSON text"""
        manifest: ValidManifest = TypeAdapter(ValidManifest).validate_json(json_text)
        return manifest

    @staticmethod
    def serialize_manifest(manifest: ValidManifest) -> str:
        """Get a manifest as a string"""
        return manifest.model_dump_json(
            indent=2, exclude_none=False, exclude_unset=False, exclude_defaults=False
        )

    def build_archive(self, archive: Path | None = None) -> Path:
        """Build a package archive

        This method will build a package archive from the manifest data.
        It will create an empty ZIP file, serialize the manifest as
        manifest.json and add all files which are described as file spec to the ZIP.

        The location of the archive can be given with the archive option.
        If not target archive is given, self.archive is used.
        """
        if not self.directory:
            raise ValueError("Cannot build archive: package directory not specified")

        # Determine archive path: use parameter, fallback to self.archive, or create default
        if archive is not None:
            archive_path = archive
        elif self.archive is not None:
            archive_path = self.archive
        else:
            archive_path = Path(f"{self.manifest.package_id}-v{self.manifest.package_version}.cpa")

        with ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            # Add manifest.json
            manifest_json = PackageVersion.serialize_manifest(self.manifest)
            zipf.writestr("manifest.json", manifest_json)
            # Add files from file specs
            for file_spec in self.manifest.files:
                file_path = self.directory / file_spec.file_path
                if not file_path.is_file(follow_symlinks=True):
                    raise FileNotFoundError(
                        f"File not found: {file_spec.file_path} in directory {self.directory}"
                    )
                zipf.write(file_path, file_spec.file_path)

        return archive_path

    @staticmethod
    def validate_image_files(manifest: ValidManifest, content: Path) -> None:
        """Validate is_png, height, width and size of the images"""
        if not content.is_dir():
            raise ValueError("Cannot validate: content is not a directory")
        for image_spec in manifest.get_images():
            image = PortableNetworkGraphics(content / image_spec.file_path)
            image.check_size(limits.MAX_MARKETPLACE_IMAGE_SIZE)
            if image_spec.file_role == "icon":
                image.check_dimensions(limits.ICON_IMAGE_WIDTH, limits.ICON_IMAGE_HEIGHT)
            if image_spec.file_role == "marketplace":
                image.check_dimensions(
                    limits.MARKETPLACE_IMAGE_WIDTH, limits.MARKETPLACE_IMAGE_HEIGHT
                )

    @staticmethod
    def validate_text_files(manifest: ValidManifest, content: Path) -> None:
        """Validate file sizes according to limits"""
        if not content.is_dir():
            raise ValueError("Cannot validate: content is not a directory")
        for file_spec in manifest.get_texts():
            file_path = content / file_spec.file_path
            file_stat = file_path.stat()
            if file_stat.st_size > limits.MAX_TEXT_FILE_SIZE:
                raise ValueError(
                    f"Size of text file {file_spec.file_path} exceeds limit "
                    f"of {limits.MAX_TEXT_FILE_SIZE / 1024 / 1024} MiB."
                )

    @staticmethod
    def validate_file_paths(manifest: ValidManifest, content: Path) -> bool:
        """Compare file lists from manifest and content (archive or directory)."""
        manifest_list = {_.file_path for _ in manifest.files}
        content_list: set[str] = set()
        if content.is_dir():
            content_list = {
                _.relative_to(content).as_posix()
                for _ in content.rglob("*")
                if _.is_file() and _.name != "manifest.json"
            }
        if content.is_file():
            with ZipFile(content) as zip_archive:
                content_list = {
                    _.filename
                    for _ in zip_archive.filelist
                    if not _.is_dir() and _.filename != "manifest.json"
                }

        not_in_manifest = content_list - manifest_list
        if not_in_manifest:
            raise ManifestContentMismatchError(
                "Some paths are not described in the manifests "
                f"file_spec list: {','.join(not_in_manifest)}"
            )
        not_in_directory = manifest_list - content_list
        if not_in_directory:
            raise ManifestContentMismatchError(
                f"Some file_spec paths are not present in the package: {','.join(not_in_directory)}"
            )
        return True

    def metadata(self) -> PackageMetadata:
        """Get Package Metadata"""
        return PackageMetadata(
            id=self.manifest.package_id,
            type=self.manifest.package_type,
            name=self.manifest.metadata.name,
            description=self.manifest.metadata.description,
        )

    def excerpt(self) -> PackageVersionExcerpt:
        """Get Package Version Excerpt"""
        return PackageVersionExcerpt(
            package_id=self.manifest.package_id,
            package_type=self.manifest.package_type,
            name=self.manifest.metadata.name,
            package_version=self.manifest.package_version,
        )

    def versions(self, package_dir: Path) -> list[PackageVersionExcerpt]:
        """Get Package Versions"""
        manifest_files = package_dir.glob(f"{self.manifest.package_id}-v*.json")
        return [
            PackageVersion.from_json(json_text=Path(file).read_text()).excerpt()
            for file in manifest_files
        ]

    def iri(self) -> URIRef:
        """Get Package Version IRI"""
        return self.id_to_iri(self.manifest.package_id)

    @staticmethod
    def id_to_iri(package_id: PackageIdentifier) -> URIRef:
        """Get Package Version IRI

        reverse of iri_to_id() method
        """
        return URIRef(f"{get_data_graph_iri()}{package_id}")

    @staticmethod
    def iri_to_id(iri: URIRef | str) -> PackageIdentifier:
        """Get a PackageIdentifier from a Package Version IRI

        reverse of id_to_iri() method
        """
        return str(iri).replace(get_data_graph_iri(), "")

    def to_rdf_graph(self) -> Graph:  # noqa: C901, PLR0915, PLR0912
        """Get a Graph representation of the package version"""
        g = Graph()

        eccm = Namespace(NS_IRI)

        g.bind("eccm", eccm)

        package_iri = self.iri()
        metadata_iri = URIRef(f"{package_iri}/metadata")

        if isinstance(self.manifest, ProjectPackageManifest):
            manifest_class = eccm.class_ProjectPackageManifest
        elif isinstance(self.manifest, VocabularyPackageManifest):
            manifest_class = eccm.class_VocabularyPackageManifest
        else:
            raise TypeError("Manifest type not supported")

        # Add package triples
        g.add((package_iri, RDF.type, manifest_class))
        g.add((package_iri, eccm.property_package_id, Literal(self.manifest.package_id)))
        g.add(
            (
                package_iri,
                eccm.property_package_version,
                Literal(str(self.manifest.package_version)),
            )
        )
        g.add((package_iri, eccm.property_package_type, Literal(self.manifest.package_type.value)))
        g.add((package_iri, eccm.property_metadata, metadata_iri))

        # Add metadata triples
        g.add((metadata_iri, RDF.type, eccm.class_ManifestMetadata))
        g.add((metadata_iri, eccm.property_name, Literal(self.manifest.metadata.name)))
        g.add(
            (metadata_iri, eccm.property_description, Literal(self.manifest.metadata.description))
        )

        if self.manifest.metadata.comment:
            g.add((metadata_iri, eccm.property_comment, Literal(self.manifest.metadata.comment)))

        g.add((metadata_iri, eccm.property_license, Literal(self.manifest.metadata.license)))

        for tag in self.manifest.metadata.tags:
            g.add((metadata_iri, eccm.property_tag, Literal(tag)))

        for idx, agent in enumerate(self.manifest.metadata.agents):
            agent_iri = URIRef(f"{metadata_iri}/agent_{idx}")
            g.add((metadata_iri, eccm.property_agent, agent_iri))
            g.add((agent_iri, RDF.type, eccm.class_Agent))
            g.add((agent_iri, eccm.property_agent_type, Literal(agent.agent_type.value)))
            g.add((agent_iri, eccm.property_agent_role, Literal(agent.agent_role.value)))
            g.add((agent_iri, eccm.property_agent_name, Literal(agent.agent_name)))
            if agent.agent_url:
                g.add((agent_iri, eccm.property_agent_url, URIRef(str(agent.agent_url))))
            if agent.agent_email:
                g.add((agent_iri, eccm.property_agent_email, Literal(agent.agent_email)))

        for idx, url in enumerate(self.manifest.metadata.urls):
            url_iri = URIRef(f"{metadata_iri}/url_{idx}")
            g.add((metadata_iri, eccm.property_url, url_iri))
            g.add((url_iri, RDF.type, eccm.class_PackageUrl))
            g.add((url_iri, eccm.property_url_ref, URIRef(str(url.url_ref))))
            g.add((url_iri, eccm.property_url_role, Literal(url.url_role.value)))

        # Add file specs triples
        for idx, file_spec in enumerate(self.manifest.files):
            file_spec_iri = URIRef(f"{package_iri}/file_spec_{idx}")
            g.add((package_iri, eccm.property_file_specs, file_spec_iri))

            if isinstance(file_spec, GraphFileSpec):
                g.add((file_spec_iri, RDF.type, eccm.class_GraphFileSpec))
                g.add((file_spec_iri, eccm.property_file_path, Literal(file_spec.file_path)))
                g.add((file_spec_iri, eccm.property_file_type, Literal(file_spec.file_type.value)))
                g.add((file_spec_iri, eccm.property_graph_iri, URIRef(str(file_spec.graph_iri))))

                if file_spec.import_into:
                    for imported_graph in file_spec.import_into:
                        g.add(
                            (
                                file_spec_iri,
                                eccm.property_imported_into,
                                URIRef(str(imported_graph)),
                            )
                        )

            if isinstance(file_spec, (TextFileSpec, ImageFileSpec)):
                g.add((file_spec_iri, RDF.type, eccm.class_TextFileSpec))
                g.add((file_spec_iri, eccm.property_file_path, Literal(file_spec.file_path)))
                g.add((file_spec_iri, eccm.property_file_type, Literal(file_spec.file_type.value)))
                g.add((file_spec_iri, eccm.property_file_role, Literal(file_spec.file_role.value)))

            if isinstance(file_spec, ProjectFileSpec):
                g.add((file_spec_iri, RDF.type, eccm.class_ProjectFileSpec))
                g.add((file_spec_iri, eccm.property_file_path, Literal(file_spec.file_path)))
                g.add((file_spec_iri, eccm.property_file_type, Literal(file_spec.file_type.value)))
                g.add((file_spec_iri, eccm.property_project_id, Literal(file_spec.project_id)))

        # add dependencies
        for dependency in self.manifest.dependencies:
            if isinstance(dependency, PythonPackageDependency):
                g.add((self.iri(), eccm.dependsOnPython, Literal(dependency.pypi_id)))
                continue
            if isinstance(dependency, MarketplacePackageDependency):
                g.add(
                    (
                        self.iri(),
                        eccm.dependsOnPackage,
                        PackageVersion.id_to_iri(package_id=dependency.package_id),
                    )
                )
                continue

        # Add complete manifest JSON for easy reconstruction
        # would need to add this property manifest json for this, i think this is not nice
        # but it is easy to then create packages again via the from_json for unwrapping
        # sparql results so this is here for trying
        g.add(
            (
                package_iri,
                eccm.property_manifest_json,
                Literal(PackageVersion.serialize_manifest(self.manifest)),
            )
        )

        return g

    @staticmethod
    def packages_from_sparql_bindings(bindings: list[dict]) -> list["PackageVersion"]:
        """Parse SPARQL result bindings into PackageVersion objects.

        This method expects bindings that contain a manifest_json field with
        the complete manifest JSON stored as a literal in RDF (Option A approach).

        Args:
            bindings: List of SPARQL result bindings (from response.json()["results"]["bindings"])
                      Each binding should contain a "manifest_json" field.

        Returns:
            List of PackageVersion objects.

        """
        packages = []
        for binding in bindings:
            if "manifest_json" in binding:
                manifest_json = binding["manifest_json"]["value"]
                try:
                    package = PackageVersion.from_json(manifest_json)
                    packages.append(package)
                except Exception as e:
                    raise RuntimeError(f"Failed to parse manifest_json: {manifest_json}") from e

        return packages

    def get_file_path(self, path: str) -> Path:
        """Get a file path from the package.

        Retrieves a file from the package, handling both directory-based and
        archive-based packages. For directory packages, returns the direct file path.
        For archive packages, extracts the file to a temporary directory and returns
        the temporary path.

        Args:
            path: The relative file path within the package. Must match the
                FileSpecFilePathPattern.

        Returns:
            Path: The absolute path to the file (either in the package directory
                or in a temporary directory for archived packages).

        Raises:
            ValueError: If the path does not match the FileSpecFilePathPattern.
            FileNotFoundError: If the file does not exist in the package directory
                or archive.

        """
        if not FileSpecFilePathPattern.match(path):
            raise ValueError(
                f"Invalid file path: {path} (does not match {FileSpecFilePathPattern.pattern})"
            )
        if self.directory:
            file_path = self.directory / path
            if file_path.is_file():
                return file_path
            raise FileNotFoundError(
                f"File not found: '{path}' in directory '{self.directory.name}'"
            )
        if self.archive:
            try:
                with (
                    zipfile.ZipFile(self.archive, "r") as zipf,
                    zipf.open(path) as file,
                    TemporaryDirectory(delete=False) as temp_dir,
                ):
                    file_path = Path(temp_dir) / path.split("/")[-1]
                    with file_path.open("wb") as opened_file:
                        opened_file.write(file.read())
                    return file_path
            except KeyError as error:
                raise FileNotFoundError(
                    f"File not found: '{path}' in archive '{self.archive.name}'"
                ) from error

        raise FileNotFoundError("Package has neither an archive nor a directory.")
