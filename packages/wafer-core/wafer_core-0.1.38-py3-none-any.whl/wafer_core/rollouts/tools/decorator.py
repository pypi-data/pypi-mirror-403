"""
Tool decorator for creating type-safe, auto-documented tools from functions.

Usage:
    @tool("Search the codebase for a pattern")
    async def grep(pattern: str, path: str = ".") -> str:
        # Implementation
        return results

    # With dataclass for complex parameters
    @dataclass(frozen=True)
    class FileRange:
        path: str
        start: int | None = None
        end: int | None = None

    @tool("Consult the oracle for planning and review")
    async def oracle(task: str, files: list[FileRange] | None = None) -> str:
        ...

    # With dependency injection for runtime context
    from typing import Annotated

    @tool("Read a file")
    async def read(
        path: str,
        fs: Annotated[FileSystem, Depends(get_filesystem)],
    ) -> str:
        return await fs.read(path)
"""

import asyncio
import inspect
import json
import types
from collections.abc import Awaitable, Callable
from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from typing import (
    Annotated,
    Any,
    Generic,
    Literal,
    ParamSpec,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    is_typeddict,
)

from ..dtypes import Tool as ToolDef
from ..dtypes import ToolFunction, ToolFunctionParameter

T = TypeVar("T")
P = ParamSpec("P")


# ── Dependency Injection ──────────────────────────────────────────────────────


class Depends(Generic[T]):
    """
    Dependency injection marker, similar to FastAPI's Depends.

    The dependency callable will be invoked when the tool is called,
    and its return value will be injected into the tool function.
    These parameters are hidden from the LLM's schema.

    Usage:
        from typing import Annotated

        def get_filesystem() -> FileSystem:
            return FileSystem()

        @tool("Read a file")
        async def read(
            path: str,
            fs: Annotated[FileSystem, Depends(get_filesystem)],
        ) -> str:
            return await fs.read(path)
    """

    __slots__ = ("dependency",)

    def __init__(self, dependency: Callable[[], T | Awaitable[T]]) -> None:
        self.dependency = dependency

    async def resolve(self, overrides: dict[Callable, Callable] | None = None) -> T:
        """Resolve the dependency, handling both sync and async callables."""
        func = self.dependency
        if overrides and func in overrides:
            func = overrides[func]

        result = func()
        if asyncio.iscoroutine(result):
            return await result
        return result  # type: ignore[return-value]


# ── Type to JSON Schema Conversion ────────────────────────────────────────────


def _python_type_to_json_schema(python_type: type) -> dict[str, Any]:
    """Convert a Python type to JSON schema."""
    origin = get_origin(python_type)

    # Handle NoneType directly
    if python_type is type(None):
        return {"type": "null"}

    # Handle Union types (including X | None and Optional[X])
    # Union for typing.Union, types.UnionType for X | Y syntax (Python 3.10+)
    if origin is Union or origin is types.UnionType:
        args = get_args(python_type)
        non_none_args = [a for a in args if a is not type(None)]
        has_none = len(non_none_args) < len(args)

        if len(non_none_args) == 0:
            # All None - unusual but handle it
            return {"type": "null"}
        elif len(non_none_args) == 1 and not has_none:
            # Single non-None type, no None in union
            return _python_type_to_json_schema(non_none_args[0])
        elif len(non_none_args) == 1 and has_none:
            # Optional[X] - single type that can be null
            # Note: Many LLM providers don't need explicit null in schema for optional params
            return _python_type_to_json_schema(non_none_args[0])
        else:
            # Multiple non-None types - use anyOf
            return {"anyOf": [_python_type_to_json_schema(a) for a in non_none_args]}

    # Handle Literal types
    if origin is Literal:
        values = get_args(python_type)
        # Infer type from first value
        if values and isinstance(values[0], str):
            return {"type": "string", "enum": list(values)}
        elif values and isinstance(values[0], int):
            return {"type": "integer", "enum": list(values)}
        return {"enum": list(values)}

    # Handle basic types
    if python_type is str:
        return {"type": "string"}
    elif python_type is int:
        return {"type": "integer"}
    elif python_type is float:
        return {"type": "number"}
    elif python_type is bool:
        return {"type": "boolean"}
    elif python_type is type(None):
        return {"type": "null"}

    # Handle list types
    if origin is list:
        args = get_args(python_type)
        if args:
            return {"type": "array", "items": _python_type_to_json_schema(args[0])}
        return {"type": "array"}

    # Handle dict types
    if origin is dict or python_type is dict:
        args = get_args(python_type)
        if len(args) >= 2:
            return {
                "type": "object",
                "additionalProperties": _python_type_to_json_schema(args[1]),
            }
        return {"type": "object"}

    # Handle tuple types (as fixed-length arrays)
    if origin is tuple:
        args = get_args(python_type)
        if args:
            return {
                "type": "array",
                "prefixItems": [_python_type_to_json_schema(a) for a in args],
                "minItems": len(args),
                "maxItems": len(args),
            }
        return {"type": "array"}

    # Handle frozen dataclass
    if is_dataclass(python_type) and not isinstance(python_type, type(None)):
        props = {}
        required = []
        for f in fields(python_type):
            props[f.name] = _python_type_to_json_schema(f.type)
            # Field is required if no default and no default_factory
            if f.default is MISSING and f.default_factory is MISSING:
                required.append(f.name)
        return {
            "type": "object",
            "properties": props,
            "required": required,
            "additionalProperties": False,
        }

    # Handle TypedDict
    if is_typeddict(python_type):
        hints = get_type_hints(python_type)
        required_keys = getattr(python_type, "__required_keys__", set())
        properties = {k: _python_type_to_json_schema(v) for k, v in hints.items()}
        return {
            "type": "object",
            "properties": properties,
            "required": list(required_keys),
            "additionalProperties": False,
        }

    # Default to string for unknown types
    return {"type": "string"}


def _get_param_description(func: Callable, param_name: str) -> str | None:
    """Extract parameter description from docstring (Google-style Args section)."""
    docstring = func.__doc__
    if not docstring:
        return None

    lines = docstring.split("\n")
    in_args = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if in_args:
            if stripped.startswith(param_name + ":"):
                return stripped.split(":", 1)[1].strip()
            if stripped.lower().startswith(("returns:", "raises:", "example")):
                break
    return None


# ── Tool Wrapper Class ────────────────────────────────────────────────────────


@dataclass
class Tool:
    """
    Wrapper for a tool function with metadata and definition.

    Created by the @tool decorator. Provides:
    - Automatic JSON schema generation from function signature
    - Dependency injection resolution
    - Type-safe execution
    """

    func: Callable[..., Awaitable[Any]]
    description: str
    name: str = ""
    _definition: ToolDef | None = field(default=None, repr=False)
    _dependencies: dict[str, Depends] = field(default_factory=dict, repr=False)
    _param_types: dict[str, type] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        if not self.name:
            self.name = self.func.__name__
        self._analyze_signature()

    def _analyze_signature(self):
        """Extract parameters and dependencies from function signature."""
        sig = inspect.signature(self.func)

        try:
            hints = get_type_hints(self.func, include_extras=True)
        except Exception:
            hints = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # Check if default value is Depends instance
            if isinstance(param.default, Depends):
                self._dependencies[param_name] = param.default
                continue

            hint = hints.get(param_name)

            # Check for Annotated[Type, Depends(...)]
            if get_origin(hint) is Annotated:
                args = get_args(hint)
                actual_type = args[0] if args else str
                for metadata in args[1:]:
                    if isinstance(metadata, Depends):
                        self._dependencies[param_name] = metadata
                        break
                else:
                    self._param_types[param_name] = actual_type
                continue

            # Regular parameter
            if hint is None:
                hint = str
            self._param_types[param_name] = hint

    @property
    def definition(self) -> ToolDef:
        """Generate the ToolDef for this tool (cached)."""
        if self._definition is not None:
            return self._definition

        properties: dict[str, Any] = {}
        required: list[str] = []

        sig = inspect.signature(self.func)

        for param_name, param_type in self._param_types.items():
            prop_schema = _python_type_to_json_schema(param_type)

            # Add description from docstring
            param_desc = _get_param_description(self.func, param_name)
            if param_desc:
                prop_schema["description"] = param_desc

            properties[param_name] = prop_schema

            # Required if no default
            param = sig.parameters[param_name]
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        self._definition = ToolDef(
            function=ToolFunction(
                name=self.name,
                description=self.description,
                parameters=ToolFunctionParameter(properties=properties),
                required=required,
            )
        )
        return self._definition

    async def execute(
        self,
        args: dict[str, Any],
        overrides: dict[Callable, Callable] | None = None,
    ) -> str:
        """
        Execute the tool with given arguments.

        Args:
            args: Tool arguments from the LLM
            overrides: Optional dependency overrides (for testing or scoped context)

        Returns:
            Tool result as string
        """
        # Resolve dependencies
        resolved_deps = {}
        for dep_name, depends in self._dependencies.items():
            resolved_deps[dep_name] = await depends.resolve(overrides)

        # Merge with provided args
        call_kwargs = {**args, **resolved_deps}

        # Instantiate dataclass parameters from dicts
        for param_name, param_type in self._param_types.items():
            if is_dataclass(param_type) and param_name in call_kwargs:
                val = call_kwargs[param_name]
                if isinstance(val, dict):
                    call_kwargs[param_name] = param_type(**val)
            # Handle list of dataclasses
            elif (
                get_origin(param_type) is list
                and param_name in call_kwargs
                and call_kwargs[param_name] is not None
            ):
                item_type = get_args(param_type)[0] if get_args(param_type) else None
                if item_type and is_dataclass(item_type):
                    call_kwargs[param_name] = [
                        item_type(**item) if isinstance(item, dict) else item
                        for item in call_kwargs[param_name]
                    ]

        result = await self.func(**call_kwargs)
        return self._serialize_result(result)

    def _serialize_result(self, result: Any) -> str:
        """Serialize tool result to string."""
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        if isinstance(result, (dict, list)):
            return json.dumps(result)
        if is_dataclass(result):
            from dataclasses import asdict

            return json.dumps(asdict(result))
        return str(result)


# ── Decorator ─────────────────────────────────────────────────────────────────


def tool(
    description: str,
    *,
    name: str | None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Tool]:
    """
    Decorator to create a tool from an async function.

    Args:
        description: Description of what the tool does (sent to LLM)
        name: Optional custom name (defaults to function name)

    Returns:
        A Tool instance wrapping the decorated function

    Example:
        @tool("Search the codebase")
        async def grep(pattern: str, path: str = ".") -> str:
            ...
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Tool:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                f"Tool '{func.__name__}' must be async. Use 'async def {func.__name__}(...)'."
            )

        return Tool(
            func=func,
            description=description,
            name=name or func.__name__,
        )

    return decorator
