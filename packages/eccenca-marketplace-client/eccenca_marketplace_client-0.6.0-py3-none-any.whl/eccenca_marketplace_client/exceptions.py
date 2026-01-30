"""exceptions"""


class BaseError(Exception):
    """Base exception for all eccenca marketplace client exceptions."""


class PackageArchiveNotZIPError(BaseError):
    """Package archive is not ZIP file"""


class ManifestContentMismatchError(BaseError):
    """Either a specified file is missing or an additional file exists"""
