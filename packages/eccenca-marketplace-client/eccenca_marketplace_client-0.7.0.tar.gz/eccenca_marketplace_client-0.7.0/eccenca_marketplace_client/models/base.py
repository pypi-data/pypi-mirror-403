"""Marketplace Base Model"""

from abc import ABC

from pydantic import BaseModel, ConfigDict

default_config = ConfigDict(
    # strip leading and trailing whitespace for str types
    str_strip_whitespace=True,
    # aliased field may be populated to object by its alias
    validate_by_alias=True,
    # aliased field should be serialized by its alias
    serialize_by_alias=True,
    # error on any fields not in the spec
    extra="forbid",
    # do not populate models with the value property of enums, rather than the raw enum
    use_enum_values=False,
)


class PackageBaseModel(BaseModel, ABC):
    """Package Base Model"""

    model_config = default_config
