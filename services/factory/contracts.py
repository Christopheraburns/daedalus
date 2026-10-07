from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ConnectionSpec(Contract):
    name: str = Field(min_length=1, max_length=80)
    base_url: str = Field(min_length=1, max_length=300)
    auth_mode: Literal["none"] = "none"


class ServerSpec(Contract):
    name: str = Field(min_length=1, max_length=80)


class OpenAPIImportRequest(Contract):
    url: str = Field(min_length=1, max_length=500)


class DeploymentRequest(Contract):
    revision: int = Field(ge=1)


class DeploymentAction(Contract):
    revision: int = Field(ge=1)


class Parameter(Contract):
    name: str = Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$", max_length=64)
    location: Literal["path", "query"] = "path"
    type: Literal["string", "integer", "number", "boolean"] = "string"
    required: bool = True
    description: str = Field(default="", max_length=400)


class ToolSpec(Contract):
    name: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$", max_length=64)
    description: str = Field(default="", max_length=2000)
    connection_id: str
    method: Literal["GET", "POST"] = "GET"
    path: str = Field(default="/", max_length=300)
    parameters: list[Parameter] = Field(default_factory=list, max_length=30)
    body_schema: dict | None = None
    effect: Literal["read", "write"] = "read"
    enabled: bool = True


class Position(Contract):
    x: float = Field(ge=-10000, le=10000)
    y: float = Field(ge=-10000, le=10000)


class LayoutSpec(Contract):
    positions: dict[str, Position] = Field(default_factory=dict, max_length=500)


class TestRequest(Contract):
    arguments: dict = Field(default_factory=dict)
    confirm_write: bool = False


class PublishRequest(Contract):
    revision: int = Field(ge=1)


class RollbackRequest(PublishRequest):
    release_id: str
