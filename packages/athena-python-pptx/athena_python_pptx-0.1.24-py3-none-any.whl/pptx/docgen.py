"""
Documentation generator for Athena Python PPTX.

Generates Markdown documentation for all functions marked with @athena_only.
This allows automatic generation of docs that highlight Athena-specific features
not available in the standard python-pptx library.

Usage:
    # As a module
    python -m pptx.docgen > docs/athena-api.md

    # Programmatically
    from pptx.docgen import generate_docs, generate_docs_json
    markdown = generate_docs()
    json_data = generate_docs_json()
"""

from __future__ import annotations

import inspect
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional, get_type_hints


@dataclass
class ParamDoc:
    """Documentation for a function parameter."""

    name: str
    type_hint: str = ""
    description: str = ""
    default: Optional[str] = None


@dataclass
class FunctionDoc:
    """Complete documentation for a function."""

    name: str
    qualname: str
    module: str
    signature: str
    description: str
    since: str
    summary: str = ""
    params: list[ParamDoc] = field(default_factory=list)
    returns: str = ""
    return_type: str = ""
    raises: list[tuple[str, str]] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _parse_docstring(docstring: Optional[str]) -> dict[str, Any]:
    """
    Parse a Google-style docstring into components.

    Returns dict with: summary, params, returns, raises, examples, notes
    """
    if not docstring:
        return {"summary": "", "params": [], "returns": "", "raises": [], "examples": [], "notes": []}

    lines = docstring.strip().split("\n")
    result: dict[str, Any] = {
        "summary": "",
        "params": [],
        "returns": "",
        "raises": [],
        "examples": [],
        "notes": [],
    }

    # Extract summary (first paragraph before any section)
    summary_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line in ("Args:", "Arguments:", "Parameters:", "Returns:", "Raises:", "Example:", "Examples:", "Note:", "Notes:"):
            break
        if line:
            summary_lines.append(line)
        elif summary_lines:  # Empty line after content = end of summary
            break
        i += 1
    result["summary"] = " ".join(summary_lines)

    # Parse sections
    current_section = None
    current_content: list[str] = []
    current_param_name = ""

    for line in lines[i:]:
        stripped = line.strip()

        # Check for section headers
        if stripped in ("Args:", "Arguments:", "Parameters:"):
            _flush_section(result, current_section, current_content, current_param_name)
            current_section = "params"
            current_content = []
            current_param_name = ""
            continue
        elif stripped in ("Returns:", "Return:"):
            _flush_section(result, current_section, current_content, current_param_name)
            current_section = "returns"
            current_content = []
            continue
        elif stripped in ("Raises:", "Raise:"):
            _flush_section(result, current_section, current_content, current_param_name)
            current_section = "raises"
            current_content = []
            continue
        elif stripped in ("Example:", "Examples:"):
            _flush_section(result, current_section, current_content, current_param_name)
            current_section = "examples"
            current_content = []
            continue
        elif stripped in ("Note:", "Notes:"):
            _flush_section(result, current_section, current_content, current_param_name)
            current_section = "notes"
            current_content = []
            continue

        # Parse content based on current section
        if current_section == "params":
            # Check if this is a new parameter (name: description or name (type): description)
            param_match = re.match(r"^(\w+)(?:\s*\(([^)]+)\))?:\s*(.*)$", stripped)
            if param_match:
                # Flush previous param
                if current_param_name:
                    result["params"].append({
                        "name": current_param_name,
                        "description": " ".join(current_content).strip(),
                    })
                current_param_name = param_match.group(1)
                current_content = [param_match.group(3)] if param_match.group(3) else []
            elif stripped and current_param_name:
                current_content.append(stripped)
        elif current_section == "raises":
            # Check if this is a new exception (e.g., "ValueError: description")
            raises_match = re.match(r"^(\w+(?:Error|Exception)):?\s*(.*)$", stripped)
            if raises_match:
                # Flush previous exception
                if current_content:
                    exc_text = " ".join(current_content).strip()
                    exc_match = re.match(r"^(\w+(?:Error|Exception)):?\s*(.*)$", exc_text)
                    if exc_match:
                        result["raises"].append((exc_match.group(1), exc_match.group(2)))
                    else:
                        result["raises"].append(("", exc_text))
                current_content = [f"{raises_match.group(1)}: {raises_match.group(2)}".strip()]
            elif stripped:
                current_content.append(stripped)
        elif current_section in ("returns", "notes"):
            if stripped:
                current_content.append(stripped)
        elif current_section == "examples":
            # Preserve example formatting
            current_content.append(line.rstrip())

    # Flush final section
    _flush_section(result, current_section, current_content, current_param_name)

    return result


def _flush_section(
    result: dict[str, Any],
    section: Optional[str],
    content: list[str],
    param_name: str,
) -> None:
    """Flush accumulated content to the result dict."""
    if not section or not content:
        if section == "params" and param_name:
            result["params"].append({"name": param_name, "description": ""})
        return

    if section == "params" and param_name:
        result["params"].append({
            "name": param_name,
            "description": " ".join(content).strip(),
        })
    elif section == "returns":
        result["returns"] = " ".join(content).strip()
    elif section == "raises":
        # Parse raises entries
        text = " ".join(content).strip()
        for match in re.finditer(r"(\w+(?:Error|Exception)?):?\s*([^A-Z].*?)(?=\s+\w+(?:Error|Exception)|$)", text, re.DOTALL):
            result["raises"].append((match.group(1), match.group(2).strip()))
        if not result["raises"] and text:
            result["raises"].append(("", text))
    elif section == "examples":
        # Clean up examples - preserve formatting but dedent
        import textwrap
        example_text = "\n".join(content)
        # Dedent removes common leading whitespace from all lines
        dedented = textwrap.dedent(example_text)
        result["examples"].append(dedented.strip())
    elif section == "notes":
        result["notes"].append(" ".join(content).strip())


def _get_signature(func: Any) -> str:
    """Get the function signature as a string (without return annotation)."""
    try:
        sig = inspect.signature(func)
        # Build signature without return annotation
        params = []
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            if param.annotation is inspect.Parameter.empty:
                if param.default is inspect.Parameter.empty:
                    params.append(name)
                else:
                    params.append(f"{name}={param.default!r}")
            else:
                ann = _format_type(param.annotation)
                if param.default is inspect.Parameter.empty:
                    params.append(f"{name}: {ann}")
                else:
                    params.append(f"{name}: {ann} = {param.default!r}")
        return f"({', '.join(params)})"
    except (ValueError, TypeError):
        return "()"


def _get_type_hints_safe(func: Any) -> dict[str, Any]:
    """Safely get type hints, returning empty dict on failure."""
    try:
        return get_type_hints(func)
    except Exception:
        return {}


def _format_type(type_hint: Any) -> str:
    """Format a type hint as a readable string."""
    if type_hint is None:
        return ""
    if hasattr(type_hint, "__origin__"):
        # Handle generic types like list[int], Optional[str], etc.
        origin = getattr(type_hint, "__origin__", None)
        args = getattr(type_hint, "__args__", ())

        if origin is list:
            if args:
                return f"list[{_format_type(args[0])}]"
            return "list"
        elif origin is dict:
            if len(args) >= 2:
                return f"dict[{_format_type(args[0])}, {_format_type(args[1])}]"
            return "dict"
        elif origin is type(None):
            return "None"
        elif str(origin) == "typing.Union":
            # Handle Optional (Union with None)
            non_none_args = [a for a in args if a is not type(None)]
            if len(non_none_args) == 1 and type(None) in args:
                return f"Optional[{_format_type(non_none_args[0])}]"
            return " | ".join(_format_type(a) for a in args)

    if hasattr(type_hint, "__name__"):
        return type_hint.__name__

    return str(type_hint).replace("typing.", "")


def _resolve_function(qualname: str, module_name: str) -> Optional[Any]:
    """Resolve a function from its qualname and module."""
    try:
        module = sys.modules.get(module_name)
        if not module:
            return None

        parts = qualname.split(".")
        obj = module
        for part in parts:
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        return obj
    except Exception:
        return None


def collect_athena_docs() -> list[FunctionDoc]:
    """
    Collect documentation for all @athena_only decorated functions.

    Returns:
        List of FunctionDoc objects with complete documentation.
    """
    # Import all pptx modules to ensure decorators are registered
    from . import (
        presentation,
        slides,
        shapes,
        text,
        commands,
        client,
    )
    from .decorators import get_athena_functions

    docs: list[FunctionDoc] = []
    registered = get_athena_functions()

    for entry in registered:
        func = _resolve_function(entry["qualname"], entry["module"])

        # Get signature
        signature = _get_signature(func) if func else "()"

        # Parse docstring
        parsed = _parse_docstring(entry.get("doc"))

        # Get type hints
        type_hints = _get_type_hints_safe(func) if func else {}
        return_type = _format_type(type_hints.get("return"))

        # Build params with type info
        params: list[ParamDoc] = []
        if func:
            try:
                sig = inspect.signature(func)
                for param_name, param in sig.parameters.items():
                    if param_name == "self":
                        continue

                    # Find description from docstring
                    desc = ""
                    for p in parsed["params"]:
                        if p["name"] == param_name:
                            desc = p["description"]
                            break

                    # Get type hint
                    type_str = _format_type(type_hints.get(param_name))

                    # Get default
                    default = None
                    if param.default is not inspect.Parameter.empty:
                        default = repr(param.default)

                    params.append(ParamDoc(
                        name=param_name,
                        type_hint=type_str,
                        description=desc,
                        default=default,
                    ))
            except (ValueError, TypeError):
                pass

        # Build raises list
        raises = [(exc, desc) for exc, desc in parsed.get("raises", [])]

        docs.append(FunctionDoc(
            name=entry["name"],
            qualname=entry["qualname"],
            module=entry["module"],
            signature=signature,
            description=entry.get("description", ""),
            since=entry.get("since", ""),
            summary=parsed.get("summary", ""),
            params=params,
            returns=parsed.get("returns", ""),
            return_type=return_type,
            raises=raises,
            examples=parsed.get("examples", []),
            notes=parsed.get("notes", []),
        ))

    return docs


def generate_docs_json() -> dict[str, Any]:
    """
    Generate documentation as a JSON-serializable dictionary.

    Returns:
        Dictionary with metadata and list of function documentation.
    """
    from . import __version__

    docs = collect_athena_docs()

    return {
        "meta": {
            "title": "Athena Python PPTX - Extended API Reference",
            "version": __version__,
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "description": "Documentation for Athena-specific functions not available in python-pptx",
        },
        "functions": [
            {
                "name": doc.name,
                "qualname": doc.qualname,
                "module": doc.module,
                "signature": doc.signature,
                "description": doc.description,
                "since": doc.since,
                "summary": doc.summary,
                "params": [asdict(p) for p in doc.params],
                "returns": doc.returns,
                "return_type": doc.return_type,
                "raises": [{"exception": e, "description": d} for e, d in doc.raises],
                "examples": doc.examples,
                "notes": doc.notes,
            }
            for doc in docs
        ],
    }


def generate_docs(format: str = "markdown") -> str:
    """
    Generate documentation in the specified format.

    Args:
        format: Output format - "markdown" or "json"

    Returns:
        Documentation string in the requested format.
    """
    if format == "json":
        return json.dumps(generate_docs_json(), indent=2)

    # Generate Markdown
    from . import __version__

    docs = collect_athena_docs()

    lines: list[str] = []

    # Header
    lines.append("# Athena Python PPTX - Extended API Reference")
    lines.append("")
    lines.append(f"> **Version:** {__version__}")
    lines.append(f"> **Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append("")
    lines.append("This document covers **Athena-specific extensions** to the python-pptx API.")
    lines.append("These functions are NOT available in the standard python-pptx library.")
    lines.append("")

    # Table of contents
    lines.append("## Table of Contents")
    lines.append("")
    for doc in docs:
        anchor = doc.qualname.lower().replace(".", "")
        lines.append(f"- [{doc.qualname}](#{anchor})")
    lines.append("")

    # Group by class
    by_class: dict[str, list[FunctionDoc]] = {}
    for doc in docs:
        parts = doc.qualname.split(".")
        class_name = parts[0] if len(parts) > 1 else "Functions"
        by_class.setdefault(class_name, []).append(doc)

    # Generate docs for each class
    for class_name, class_docs in by_class.items():
        lines.append(f"## {class_name}")
        lines.append("")

        for doc in class_docs:
            # Method header
            lines.append(f"### {doc.qualname}")
            lines.append("")

            # Badge for version
            lines.append(f"*Added in v{doc.since}*")
            lines.append("")

            # Summary
            if doc.summary:
                lines.append(doc.summary)
                lines.append("")

            # Signature
            lines.append("```python")
            return_annotation = doc.return_type if doc.return_type and doc.return_type != "NoneType" else "None"
            if "." in doc.qualname:
                # Method
                lines.append(f"def {doc.name}{doc.signature} -> {return_annotation}")
            else:
                lines.append(f"def {doc.qualname}{doc.signature} -> {return_annotation}")
            lines.append("```")
            lines.append("")

            # Parameters
            if doc.params:
                lines.append("**Parameters:**")
                lines.append("")
                for param in doc.params:
                    type_str = f" (`{param.type_hint}`)" if param.type_hint else ""
                    default_str = f" (default: `{param.default}`)" if param.default else ""
                    lines.append(f"- **{param.name}**{type_str}: {param.description}{default_str}")
                lines.append("")

            # Returns
            if doc.returns:
                lines.append("**Returns:**")
                lines.append("")
                ret_type = f" (`{doc.return_type}`)" if doc.return_type else ""
                lines.append(f"{doc.returns}{ret_type}")
                lines.append("")

            # Raises
            if doc.raises:
                lines.append("**Raises:**")
                lines.append("")
                for exc, desc in doc.raises:
                    if exc:
                        lines.append(f"- `{exc}`: {desc}")
                    else:
                        lines.append(f"- {desc}")
                lines.append("")

            # Examples
            if doc.examples:
                lines.append("**Example:**")
                lines.append("")
                for example in doc.examples:
                    # Detect if example has code
                    if ">>>" in example or example.startswith("#") or "=" in example or "(" in example:
                        lines.append("```python")
                        lines.append(example)
                        lines.append("```")
                    else:
                        lines.append(example)
                lines.append("")

            # Notes
            if doc.notes:
                lines.append("**Note:**")
                lines.append("")
                for note in doc.notes:
                    lines.append(f"> {note}")
                lines.append("")

            lines.append("---")
            lines.append("")

    # Footer
    lines.append("## See Also")
    lines.append("")
    lines.append("- [python-pptx Documentation](https://python-pptx.readthedocs.io/) - Standard API reference")
    lines.append("- [Athena Python PPTX on PyPI](https://pypi.org/project/athena-python-pptx/) - Package page")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    """CLI entry point for documentation generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate documentation for Athena Python PPTX extensions"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file (default: stdout)"
    )

    args = parser.parse_args()

    output = generate_docs(format=args.format)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Documentation written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
