"""person and organization metadata"""

from abc import ABC
from typing import Annotated, Literal

from pydantic import EmailStr, Field, HttpUrl

from eccenca_marketplace_client import fields
from eccenca_marketplace_client.models.base import PackageBaseModel


class Agent(PackageBaseModel, ABC):
    """Agent (abstract)"""

    agent_role: fields.AgentRole
    agent_name: fields.AgentName
    agent_url: HttpUrl | None = None
    agent_email: EmailStr | None = None


class Person(Agent):
    """Person"""

    agent_type: Literal[fields.AgentTypes.person]


class Organization(Agent):
    """Organization"""

    agent_type: Literal[fields.AgentTypes.organization]


ValidAgent = Annotated[Person | Organization, Field(discriminator="agent_type")]
