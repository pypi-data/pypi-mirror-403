import inspect
from typing import Callable, List, Tuple

def parse_docstring(func: Callable) -> Tuple[str, dict]:
    """Parse Google-style docstring to extract description and param descriptions."""
    docstring = func.__doc__ or ""
    lines = docstring.strip().split("\n")

    description_lines = []
    param_descriptions = {}
    in_args = False

    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("args:"):
            in_args = True
            continue
        if stripped.lower().startswith(("returns:", "raises:", "example:")):
            in_args = False
            continue

        if in_args and ":" in stripped:
            param_name, param_desc = stripped.split(":", 1)
            param_descriptions[param_name.strip()] = param_desc.strip()
        elif not in_args and stripped:
            description_lines.append(stripped)

    return " ".join(description_lines), param_descriptions


def convert_tools(tools: List[Callable]) -> Tuple[list, dict]:
    """Convert Python functions to OpenAI-compatible tool schemas."""
    schemas = []
    functions = {}

    for func in tools:
        sig = inspect.signature(func)
        description, param_descriptions = parse_docstring(func)

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                if param.annotation in (float, int):
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"

            properties[param_name] = {
                "type": param_type,
                "description": param_descriptions.get(param_name, f"The {param_name} parameter"),
            }

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        schema = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": description or f"Function {func.__name__}",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }
        schemas.append(schema)
        functions[func.__name__] = func

    return schemas, functions
