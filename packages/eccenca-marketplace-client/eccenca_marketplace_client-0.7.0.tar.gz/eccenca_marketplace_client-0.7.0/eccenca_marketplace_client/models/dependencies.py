"""Dependencies models"""

from abc import ABC
from typing import Annotated, Literal

from pydantic import Field

from eccenca_marketplace_client import fields
from eccenca_marketplace_client.models.base import PackageBaseModel


class AbstractDependency(PackageBaseModel, ABC):
    """Abstract Dependency"""


class MarketplacePackageDependency(AbstractDependency):
    """Dependency to a marketplace package"""

    dependency_type: Literal[fields.DependencyTypes.marketplace_package]
    package_id: fields.PackageIdentifier


class PythonPackageDependency(AbstractDependency):
    """Dependency to a python plugin package"""

    dependency_type: Literal[fields.DependencyTypes.python_package]
    pypi_id: fields.PyPiIdentifier


ValidDependency = Annotated[
    MarketplacePackageDependency | PythonPackageDependency, Field(discriminator="dependency_type")
]
