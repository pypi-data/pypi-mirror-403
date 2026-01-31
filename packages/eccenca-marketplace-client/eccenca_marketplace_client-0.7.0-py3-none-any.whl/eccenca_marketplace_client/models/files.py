"""file specs"""

from abc import ABC
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from eccenca_marketplace_client import fields
from eccenca_marketplace_client.models.base import PackageBaseModel


class AbstractFileSpec(PackageBaseModel, ABC):
    """Abstract File Spec"""

    file_path: fields.FileSpecFilePath


class GraphFileSpec(AbstractFileSpec):
    """Graph File Spec"""

    file_type: Literal[fields.FileSpecTypes.graph]
    graph_iri: fields.ResourceIdentifier
    import_into: fields.FileSpecImportedIntoList
    register_as_vocabulary: fields.FileSpecRegisterAsVocabularyFlag = False

    @model_validator(mode="after")
    def check(self: Self) -> Self:
        """Check the validity of the graph file spec"""
        if not self.file_path.endswith(".ttl"):
            raise ValueError("Only turtle files (ttl) supported.")
        return self


class ProjectFileSpec(AbstractFileSpec):
    """Build Project File Spec"""

    file_type: Literal[fields.FileSpecTypes.project]
    project_id: str

    @model_validator(mode="after")
    def check(self: Self) -> Self:
        """Check the validity of the project file spec"""
        if not self.file_path.endswith(".zip"):
            raise ValueError("Only ZIP files (zip) supported.")
        return self


class TextFileSpec(AbstractFileSpec):
    """Text File Spec"""

    file_type: Literal[fields.FileSpecTypes.text]
    file_role: fields.TextFileRole

    @model_validator(mode="after")
    def check(self: Self) -> Self:
        """Check the validity of the text file spec

        - check mandatory naming conventions for license, readme and changelog
        """
        if self.file_role == "license" and self.file_path != "LICENSE":
            raise ValueError("License file needs to be LICENSE in the root folder.")
        if self.file_role == "readme" and self.file_path != "README.md":
            raise ValueError("Readme file needs to be README.md in the root folder.")
        if self.file_role == "changelog" and self.file_path != "CHANGELOG.md":
            raise ValueError("Changelog file needs to be CHANGELOG.md in the root folder.")
        return self


class ImageFileSpec(AbstractFileSpec):
    """Text File Spec"""

    file_type: Literal[fields.FileSpecTypes.image]
    file_role: fields.ImageFileRole


ValidFileSpec = Annotated[
    GraphFileSpec | ProjectFileSpec | TextFileSpec | ImageFileSpec, Field(discriminator="file_type")
]
