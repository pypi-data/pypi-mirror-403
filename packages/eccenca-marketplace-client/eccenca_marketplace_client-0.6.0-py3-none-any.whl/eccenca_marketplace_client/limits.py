"""Limit constants for manifest descriptions and package content

In addition to these limits, all strings should have length limitations attached to the field.
"""

MAX_NAME_LENGTH = 50
"""Maximum number of characters in a package or agent name."""

MIN_NAME_LENGTH = 3
"""Minimum number of characters in a package or agent name."""

MAX_TAGS = 20
"""Maximum number of package tags."""

MAX_AGENTS = 10
"""Maximum number of agents."""

# image related limits

MAX_MARKETPLACE_IMAGES = 10
"""Maximum number of marketplace images allowed per package"""

MAX_MARKETPLACE_IMAGE_SIZE = 5 * 1024 * 1024
"""Maximum image file size in byts"""

MARKETPLACE_IMAGE_WIDTH = 1920
"""Marketplace image width in pixel"""

MARKETPLACE_IMAGE_HEIGHT = 1080
"""Marketplace image height in pixel"""

ICON_IMAGE_WIDTH = 166
"""Icon image width in pixel"""

ICON_IMAGE_HEIGHT = 166
"""Icon image height in pixel"""

# content file related limits

MAX_GRAPH_FILES = 30
"""Maximum number of graph files allowed per package"""

MAX_PROJECT_FILES = 10
"""Maximum number of project files allowed per package"""

MAX_TEXT_FILE_SIZE = 1 * 1024 * 1024
"""Maximum text document size in bytes"""

# overall package related limits

MAX_PACKAGE_SIZE = 200 * 1024 * 1024
"""Maximum package sizes in bytes"""
