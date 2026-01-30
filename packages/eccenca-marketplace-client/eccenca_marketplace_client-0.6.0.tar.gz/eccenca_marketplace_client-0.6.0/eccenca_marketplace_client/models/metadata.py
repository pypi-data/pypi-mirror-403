"""package metadata models"""

from collections import defaultdict
from typing import Annotated, Self

from license_expression import get_spdx_licensing
from pydantic import Field, HttpUrl, model_validator

from eccenca_marketplace_client import fields, limits
from eccenca_marketplace_client.models.agents import ValidAgent
from eccenca_marketplace_client.models.base import PackageBaseModel


class PackageUrl(PackageBaseModel):
    """Package Url"""

    url_ref: HttpUrl
    url_role: fields.UrlRole


class Metadata(PackageBaseModel):
    """Package Metadata"""

    name: fields.PackageName
    description: fields.PackageDescription
    license: fields.PackageLicense
    comment: fields.PackageComment
    agents: Annotated[
        list[ValidAgent],
        Field(
            title="Agents",
            description="List of person and organizations",
            default_factory=list,
            max_length=limits.MAX_AGENTS,
        ),
    ]
    urls: Annotated[
        list[PackageUrl],
        Field(
            title="URLs",
            description="List of package URLs",
            default_factory=list,
        ),
    ]
    tags: Annotated[
        list[fields.PackageTag],
        Field(
            title="Tags",
            description="List of package tags.",
            default_factory=list,
            max_length=limits.MAX_TAGS,
        ),
    ]

    @model_validator(mode="after")
    def check(self: Self) -> Self:
        """Check the validity of metadata

        - license expression validation
        - license normalization
        - only one license allowed in the expression
        - agents need either HTTPS url or email
        - at least one publisher agent
        """
        licensing = get_spdx_licensing()
        expression_info = licensing.validate(self.license)
        if len(expression_info.errors) > 0:
            raise ValueError("SPDX Expression Error: " + ",".join(expression_info.errors))
        parsed_license = licensing.parse(self.license)
        if len(parsed_license.objects) > 1:
            raise ValueError("SPDX Expression Error: Only a single license is allowed.")
        self.license = expression_info.normalized_expression

        agent_role_count: dict[str, int] = defaultdict(int)
        for agent in self.agents:
            agent_role_count[agent.agent_role] += 1
            if agent.agent_url and agent.agent_url.scheme != "https":
                raise ValueError("Only HTTPS URLs allowed.")
            if not agent.agent_url and not agent.agent_email:
                raise ValueError("Agents need an email address or URL (or both).")
        if len(self.agents) == 0:
            raise ValueError("Packages need at least one agent.")
        return self
