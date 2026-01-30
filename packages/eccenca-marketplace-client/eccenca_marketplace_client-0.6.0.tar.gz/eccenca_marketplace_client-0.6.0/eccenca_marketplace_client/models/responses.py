"""Response Models"""

from pydantic import BaseModel

from eccenca_marketplace_client import fields
from eccenca_marketplace_client.fields import PackageType


class PackageExcerpt(BaseModel):
    """Item for Package Listings (Excerpt)"""

    package_id: fields.PackageIdentifier
    package_type: fields.PackageType
    name: fields.PackageName
    description: fields.PackageDescription


class PackageVersionExcerpt(BaseModel):
    """Item for Package Version Listings (Excerpt)"""

    package_id: fields.PackageIdentifier
    package_type: fields.PackageType
    package_version: fields.PackageVersionIdentifier
    name: fields.PackageName


class PackageMetadata(BaseModel):
    """Package Metadata"""

    id: fields.PackageIdentifier
    name: fields.PackageName
    description: fields.PackageDescription
    type: PackageType
