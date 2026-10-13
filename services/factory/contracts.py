from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ConnectionSpec(Contract):
    name: str = Field(min_length=1, max_length=80)
    base_url: str = Field(min_length=1, max_length=300)
    auth_mode: Literal["none"] = "none"


class ApiOriginSpec(Contract):
    origin: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=240)
    enabled: bool = True


class ServerSpec(Contract):
    name: str = Field(min_length=1, max_length=80)


class PackSource(Contract):
    source: str = Field(min_length=1, max_length=65536)


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
    # http: one declarative API operation served by agentgateway. python: a pack
    # function served by the executor; a connection is optional for it.
    kind: Literal["http", "python"] = "http"
    connection_id: str | None = None
    method: Literal["GET", "POST"] = "GET"
    path: str = Field(default="/", max_length=300)
    parameters: list[Parameter] = Field(default_factory=list, max_length=30)
    body_schema: dict | None = None
    pack: str = Field(default="", max_length=40)
    function: str = Field(default="", max_length=64)
    config: dict = Field(default_factory=dict)
    effect: Literal["read", "write"] = "read"
    enabled: bool = True

    @model_validator(mode="after")
    def check_kind(self):
        if self.kind == "http" and not self.connection_id:
            raise ValueError("HTTP tools require a connection")
        if self.kind == "python" and not (self.pack and self.function):
            raise ValueError("Python tools require a pack and a function")
        if len(str(self.config)) > 4000:
            raise ValueError("Tool configuration exceeds 4000 characters")
        return self


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
