"""exceptions"""


class BaseError(Exception):
    """Base exception for all eccenca marketplace client exceptions."""


class PackageArchiveNotZIPError(BaseError):
    """Package archive is not ZIP file"""


class PackageContentError(BaseError):
    """Something is wrong with the content or files of the package"""
