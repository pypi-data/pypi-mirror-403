"""Client: Reusable Field Definitions"""

import re
from enum import Enum
from typing import Annotated, Literal

from pydantic import Field, HttpUrl
from pydantic_extra_types.semantic_version import SemanticVersion

from eccenca_marketplace_client import limits


class PackageTypes(str, Enum):
    """Package Types"""

    vocabulary = "vocabulary"
    project = "project"


PackageType = Annotated[
    PackageTypes,
    Field(
        title="Package Type",
        description="Type of the package (vocabulary, project, etc.)",
        examples=[
            "vocabulary",
            "project",
        ],
    ),
]


class DependencyTypes(str, Enum):
    """Dependency Types"""

    marketplace_package = "marketplace-package"
    python_package = "python-package"


DependencyType = Annotated[
    DependencyTypes,
    Field(
        title="Dependency Type",
        description="Type of the dependency (vocabulary, python-package)",
        examples=[
            "vocabulary",
            "python-package",
        ],
    ),
]


class ImageFileRoles(str, Enum):
    """File Spec Types"""

    icon = "icon"
    marketplace = "marketplace"


ImageFileRole = Annotated[
    ImageFileRoles,
    Field(
        title="Image File Role",
        description="Role of the image in the context of the package.",
        examples=[
            "icon",
            "marketplace",
        ],
    ),
]


class TextFileRoles(str, Enum):
    """File Spec Types"""

    readme = "readme"
    license = "license"
    changelog = "changelog"


TextFileRole = Annotated[
    TextFileRoles,
    Field(
        title="Text File Role",
        description="Role of the text document in the context of the package.",
        examples=[
            "readme",
            "license",
            "changelog",
        ],
    ),
]


class UrlsRoles(str, Enum):
    """URL Roles"""

    homepage = "homepage"
    documentation = "documentation"
    source = "source"
    issues = "issues"


UrlRole = Annotated[
    UrlsRoles,
    Field(
        title="URL Role",
        description="Role of the URL in the context of the package.",
        examples=[
            "homepage",
            "source",
            "issues",
        ],
    ),
]


class AgentTypes(str, Enum):
    """Agent Types"""

    person = "person"
    organization = "organization"


AgentType = Annotated[
    AgentTypes,
    Field(
        title="Agent Type",
        description="Type of agent (person, organization)",
        examples=[
            "person",
            "organization",
        ],
    ),
]


class AgentRoles(str, Enum):
    """File Spec Types"""

    publisher = "publisher"
    maintainer = "maintainer"
    author = "author"


AgentRole = Annotated[
    AgentRoles,
    Field(
        title="Agent Role",
        description="Role of the agent regarding the content of the package.",
        examples=[
            "publisher",
            "maintainer",
            "author",
        ],
    ),
]

AgentName = Annotated[
    str,
    Field(
        title="Agent Name",
        description="The agent name (preferred in english).",
        min_length=limits.MIN_NAME_LENGTH,
        max_length=limits.MAX_NAME_LENGTH,
        examples=[
            "eccenca GmbH",
            "John Doe",
        ],
    ),
]


class FileSpecTypes(str, Enum):
    """File Spec Types"""

    graph = "graph"
    project = "project"
    text = "text"
    image = "image"


FileSpecType = Annotated[
    FileSpecTypes,
    Field(
        title="File Type",
        description="Type of file (graph, project, text, image)",
        examples=["graph", "project", "text", "image"],
    ),
]

SchemaResource = Annotated[
    str,
    Field(
        title="JSON Schema Resource",
        description="Identifier / address (URL) of a JSON Schema resource. "
        "This field was added for practical reasons. "
        "Marketplace validation is done with pydantic and includes additional validation rules.",
        validation_alias="$schema",
        serialization_alias="$schema",
        examples=[
            "https://marketplace.eccenca.dev/api/manifest",
            "https://eccenca.market/api/manifest",
        ],
        default="https://marketplace.eccenca.dev/api/manifest",
    ),
]


# see also: https://regex101.com/r/TWlqmZ/1
PackageIdentifier = Annotated[
    str,
    Field(
        title="Package Identifier",
        description="Unique package identifier",
        pattern=r"^[a-z][a-z0-9]{1,19}(-[a-z][a-z0-9]{0,19}){1,4}$",
        examples=["ecc-pv-vocab", "w3c-rdfs-vocab", "ecc-product-data-project"],
    ),
]

PackageName = Annotated[
    str,
    Field(
        title="Package Name",
        description="The package name in english.",
        min_length=limits.MIN_NAME_LENGTH,
        max_length=limits.MAX_NAME_LENGTH,
        examples=[
            "Nextcloud Integration",
            "RDF Schema",
            "My Nice Package",
        ],
    ),
]

PackageTag = Annotated[
    str,
    Field(
        title="Tag",
        description="lowercase keyword or term assigned to the package.",
        min_length=1,
        max_length=50,
        pattern=r"^[a-z][a-z0-9-]*(\ [a-z][a-z0-9-]+)*$",
        examples=["year-2000", "supply chain", "demonstrator"],
    ),
]


PackageDescription = Annotated[
    str,
    Field(
        title="Package Description",
        description="The package description in english.",
        min_length=10,
        max_length=150,
        examples=[
            "Extract and process data from your Nextcloud instance.",
            "A set of classes with certain properties providing basic elements "
            "for the description of ontologies.",
        ],
    ),
]


PackageLicenseDefault = "LicenseRef-scancode-unknown"
PackageLicense = Annotated[
    Literal[
        "AFL-3.0",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "CC-BY-1.0",
        "CC-BY-4.0",
        "CC-BY-SA-3.0",
        "CC-BY-SA-4.0",
        "CC0-1.0",
        "CDLA-Permissive-2.0",
        "CDLA-Sharing-1.0",
        "EPL-2.0",
        "MIT",
        "ODC-By-1.0",
        "ODbL-1.0",
        "PDDL-1.0",
        "W3C-20150513",
        "LicenseRef-scancode-unknown",
    ],
    Field(
        title="Package License",
        description="The license of the package as an SPDX license identifier.",
        examples=[
            "Apache-2.0",
            "MIT",
            "CC-BY-4.0",
        ],
        default=PackageLicenseDefault,
    ),
]

PackageComment = Annotated[
    str | None,
    Field(
        title="Package Comment",
        description="A maintainer or publisher comment - not processed or shown to users.",
        max_length=300,
        default=None,
    ),
]

PackageVersionIdentifier = Annotated[
    SemanticVersion,
    Field(
        title="Package Version",
        description="Semantic version identifier string of the package, "
        "but limited to proper releases.",
        # use this pattern=r"^(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})\.(0|[1-9]\d{0,2})$",
        examples=[
            "1.0.0",
            "14.4.1",
        ],
    ),
]


ResourceIdentifier = Annotated[
    HttpUrl,
    Field(
        title="Resource Identifier (IRI)",
        description="Identifier for subjects in a Knowledge Graph.",
        examples=[
            "https://example.org/graph/",
            "urn:x-example:graph/",
            "https://my-schema.org/vocab#",
        ],
    ),
]

FileSpecImportedIntoList = Annotated[
    list[ResourceIdentifier],
    Field(
        title="Imported into Graph List",
        description="List of Graph IRIs where this current graph needs to be owl:imported"
        " after it was uploaded to Corporate Memory.",
        default_factory=list,
    ),
]

PyPiIdentifier = Annotated[
    str,
    Field(
        title="PyPI Identifier",
        description="A Python distribution name as defined in PEP 345.",
    ),
]

FileSpecRegisterAsVocabularyFlag = Annotated[
    bool,
    Field(
        title="Register as Vocabulary",
        description="A graph with this flag will be registered as a vocabulary.",
    ),
]

FileSpecFilePathPattern = re.compile(
    r"^([0-9a-z][0-9a-z-_.]{1,29}(/[0-9a-z][0-9a-z-_.]{1,29})?\.(zip|ttl|png))|LICENSE|README\.md|CHANGELOG\.md$"
)
FileSpecFilePath = Annotated[
    str,
    Field(
        title="File Path",
        description="A relative path of a file inside of the package archive.",
        examples=[
            "graphs/my-graph.ttl",
            "projects/my-project.zip",
        ],
        pattern=FileSpecFilePathPattern,
    ),
]
