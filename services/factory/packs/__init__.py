"""Tool packs: curated Python tools served by the executor behind agentgateway.

A pack is a module. Each tool is a function whose first parameter is a
ToolContext; the remaining typed parameters become the MCP input schema and the
docstring becomes the tool description shown to agents.

Two origins exist. *Built-in* packs live in this package and ship with the
runtime image. *Project* packs are files an administrator writes from the Builder
into project storage (FACTORY_PACKS_DIR); they are read without a restart and
snapshotted into each release so published servers never change underneath.
Only the executor and the inspection subprocess import project code; the Builder
process never does.
"""
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
import pkgutil
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import httpx

PACK_NAME = re.compile(r"^[a-z][a-z0-9_]{0,29}$")
PARAMETER_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean"}
MAX_SOURCE = 64 * 1024
TEMPLATE = '''"""Describe what this pack is for; it appears in the Builder palette."""
from factory.packs import ToolContext, pack_tool


@pack_tool(effect="read", requires_connection=False)
def hello(ctx: ToolContext, name: str) -> dict:
    """Greet someone by name. Explain here when an agent should use this tool."""
    return {"greeting": f"Hello, {name}", "user": ctx.caller.username}
'''
_inspections = {}


@dataclass(frozen=True)
class Caller:
    """The verified identity a tool acts for. Tools never read headers themselves."""
    username: str
    token: str | None = None


@dataclass
class ToolContext:
    caller: Caller
    connection: dict | None
    config: dict = field(default_factory=dict)

    def client(self, timeout=10.0):
        """An HTTP client bound to the approved connection origin. Authentication
        strategies (caller token forwarding, proxy identities) are applied here."""
        if not self.connection:
            raise ValueError("This tool requires a connection")
        return httpx.Client(base_url=self.connection["base_url"].rstrip("/"), timeout=timeout, trust_env=False, follow_redirects=False)


def pack_tool(effect="read", requires_connection=False):
    if effect not in {"read", "write"}:
        raise ValueError("effect must be read or write")

    def register(function):
        parameters = list(inspect.signature(function).parameters.values())
        if not parameters or parameters[0].name != "ctx":
            raise TypeError(f"{function.__name__}: the first parameter must be ctx")
        for parameter in parameters[1:]:
            if parameter.annotation not in PARAMETER_TYPES or parameter.kind != parameter.POSITIONAL_OR_KEYWORD:
                raise TypeError(f"{function.__name__}: parameter {parameter.name} must be a str, int, float or bool")
        if not (function.__doc__ or "").strip():
            raise TypeError(f"{function.__name__}: add a docstring; it becomes the tool description")
        function.daedalus = {"effect": effect, "requires_connection": requires_connection}
        return function
    return register


def project_dir():
    return Path(os.getenv("FACTORY_PACKS_DIR") or Path.home() / "daedalus-packs")


def builtin_names():
    return sorted(info.name for info in pkgutil.iter_modules(__path__) if PACK_NAME.match(info.name))


def project_path(name):
    if not PACK_NAME.match(name or ""):
        raise ValueError("Pack names use lowercase letters, digits and underscores and start with a letter")
    return project_dir() / f"{name}.py"


def load(name, search=None):
    """Import a pack module. `search` lists directories holding project pack files;
    only the executor and the inspection subprocess pass one."""
    if not PACK_NAME.match(name or ""):
        raise ValueError("Unknown tool pack")
    if name in builtin_names():
        return importlib.import_module(f"{__name__}.{name}")
    for directory in search or []:
        path = Path(directory) / f"{name}.py"
        if path.is_file():
            spec = importlib.util.spec_from_file_location(f"{__name__}.project.{name}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise ValueError(f"Unknown tool pack: {name}")


def tools(module):
    return {name: value for name, value in vars(module).items() if callable(value) and hasattr(value, "daedalus")}


def resolve(pack, function, search=None):
    available = tools(load(pack, search))
    if function not in available:
        raise ValueError(f"Pack {pack} has no tool named {function}")
    return available[function]


def describe(function):
    parameters = [{"name": p.name, "type": PARAMETER_TYPES[p.annotation], "required": p.default is p.empty}
        for p in list(inspect.signature(function).parameters.values())[1:]]
    return {"function": function.__name__, "description": inspect.getdoc(function), "parameters": parameters, "source": inspect.getsource(function), **function.daedalus}


def describe_module(module):
    return {"description": inspect.getdoc(module) or "", "tools": [describe(f) for f in tools(module).values()]}


def input_schema(parameters):
    return {"type": "object", "properties": {p["name"]: {"type": p["type"]} for p in parameters},
        "required": [p["name"] for p in parameters if p["required"]], "additionalProperties": False}


def inspect_file(path):
    """Describe a project pack by importing it in a short-lived subprocess with no
    credentials, so a broken or hostile file cannot take the Builder down."""
    path = Path(path)
    key = (str(path), path.stat().st_mtime_ns)
    if key in _inspections:
        return _inspections[key]
    env = {k: v for k, v in os.environ.items() if not k.startswith(("FACTORY_", "DATABASE_", "POSTGRES_"))}
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])  # the services directory
    try:
        completed = subprocess.run([sys.executable, "-m", "factory.packs", str(path)], capture_output=True, text=True, timeout=15, env=env)
    except subprocess.TimeoutExpired:
        return {"error": "Pack import did not finish within 15 seconds"}
    if completed.returncode:
        result = {"error": (completed.stderr.strip().splitlines() or ["Pack import failed"])[-1][:600]}
    else:
        result = json.loads(completed.stdout)
    _inspections.clear()
    _inspections[key] = result
    return result


def source_digest(name):
    """Digest of a project pack's current source; built-in packs are versioned by the image."""
    path = project_path(name)
    return hashlib.sha256(path.read_bytes()).hexdigest() if name not in builtin_names() and path.is_file() else None


def pack_info(name):
    if name in builtin_names():
        module = load(name)
        return {"name": name, "origin": "builtin", "editable": False, "error": None, "source": inspect.getsource(module), **describe_module(module)}
    path = project_path(name)
    if not path.is_file():
        raise ValueError(f"Unknown tool pack: {name}")
    inspected = inspect_file(path)
    return {"name": name, "origin": "project", "editable": True, "source": path.read_text(), "error": inspected.get("error"),
        "description": inspected.get("description", ""), "tools": inspected.get("tools", [])}


def tool_info(pack, function):
    info = pack_info(pack)
    if info["error"]:
        raise ValueError(f"Pack {pack} cannot be loaded: {info['error']}")
    for tool in info["tools"]:
        if tool["function"] == function:
            return tool
    raise ValueError(f"Pack {pack} has no tool named {function}")


def catalog(include_source=False):
    names = builtin_names() + sorted(p.stem for p in project_dir().glob("*.py") if PACK_NAME.match(p.stem) and p.stem not in builtin_names())
    entries = [pack_info(name) for name in names]
    if not include_source:
        for entry in entries:
            entry.pop("source")
            for tool in entry["tools"]:
                tool.pop("source", None)
    return entries


def save_project_pack(name, source):
    """Validate and write a project pack atomically. Returns its catalog entry."""
    path = project_path(name)
    if name in builtin_names():
        raise ValueError("Built-in packs are read-only; choose another name")
    if len(source.encode()) > MAX_SOURCE:
        raise ValueError("Pack source exceeds 64 KiB")
    compile(source, path.name, "exec")  # SyntaxError surfaces with line numbers
    with tempfile.TemporaryDirectory(prefix="factory-pack-") as directory:
        candidate = Path(directory) / path.name
        candidate.write_text(source)
        inspected = inspect_file(candidate)
    if inspected.get("error"):
        raise ValueError(inspected["error"])
    if not inspected["tools"]:
        raise ValueError("Define at least one function decorated with @pack_tool")
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(f".{name}.staging")  # never matches the *.py catalog glob
    staged.write_text(source)
    os.replace(staged, path)
    return pack_info(name)


def delete_project_pack(name):
    path = project_path(name)
    if name in builtin_names() or not path.is_file():
        raise ValueError("Only project packs can be deleted")
    path.unlink()
