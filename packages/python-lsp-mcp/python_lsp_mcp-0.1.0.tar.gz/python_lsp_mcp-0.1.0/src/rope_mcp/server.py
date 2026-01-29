"""MCP Server for Python code analysis using Rope and Pyright."""

import atexit
import json
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

from .config import Backend, get_config, SHARED_TOOLS
from .rope_client import get_client as get_rope_client
from .lsp import get_lsp_client, close_all_clients
from .tools import (
    do_rename,
    get_completions as rope_completions,
    get_definition as rope_definition,
    get_hover as rope_hover,
    get_references as rope_references,
    get_symbols as rope_symbols,
    get_diagnostics,
)

# Create the MCP server
mcp = FastMCP("Rope MCP Server")

# Register cleanup on exit
atexit.register(close_all_clients)


def _find_workspace(file_path: str) -> str:
    """Find workspace root for a file."""
    client = get_rope_client()
    return client.find_workspace_for_file(file_path)


def _get_effective_backend(tool: str, backend: Optional[str]) -> Backend:
    """Get the effective backend for a tool."""
    if backend:
        try:
            return Backend(backend.lower())
        except ValueError:
            pass
    return get_config().get_backend_for(tool)


@mcp.tool()
def hover(
    file: str,
    line: int,
    column: int,
    backend: Optional[Literal["rope", "pyright"]] = None,
) -> str:
    """Get documentation for the symbol at the given position.

    Args:
        file: Absolute path to the Python file
        line: 1-based line number
        column: 1-based column number
        backend: Backend to use (rope/pyright). Default: from config or 'rope'

    Returns:
        JSON string with documentation or error message
    """
    effective_backend = _get_effective_backend("hover", backend)

    if effective_backend == Backend.PYRIGHT:
        try:
            workspace = _find_workspace(file)
            client = get_lsp_client(workspace)
            result = client.hover(file, line, column)
            if result:
                return json.dumps({"contents": result.get("contents", ""), "backend": "pyright"}, indent=2)
            return json.dumps({"contents": None, "message": "No hover info", "backend": "pyright"}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "backend": "pyright"}, indent=2)
    else:
        result = rope_hover(file, line, column)
        result["backend"] = "rope"
        return json.dumps(result, indent=2)


@mcp.tool()
def definition(
    file: str,
    line: int,
    column: int,
    backend: Optional[Literal["rope", "pyright"]] = None,
) -> str:
    """Get the definition location for the symbol at the given position.

    Args:
        file: Absolute path to the Python file
        line: 1-based line number
        column: 1-based column number
        backend: Backend to use (rope/pyright). Default: from config or 'rope'

    Returns:
        JSON string with definition location or error message
    """
    effective_backend = _get_effective_backend("definition", backend)

    if effective_backend == Backend.PYRIGHT:
        try:
            workspace = _find_workspace(file)
            client = get_lsp_client(workspace)
            locations = client.definition(file, line, column)
            if locations:
                result = locations[0]
                result["backend"] = "pyright"
                return json.dumps(result, indent=2)
            return json.dumps({"file": None, "message": "No definition found", "backend": "pyright"}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "backend": "pyright"}, indent=2)
    else:
        result = rope_definition(file, line, column)
        result["backend"] = "rope"
        return json.dumps(result, indent=2)


@mcp.tool()
def references(
    file: str,
    line: int,
    column: int,
    backend: Optional[Literal["rope", "pyright"]] = None,
) -> str:
    """Find all references to the symbol at the given position.

    Args:
        file: Absolute path to the Python file
        line: 1-based line number
        column: 1-based column number
        backend: Backend to use (rope/pyright). Default: from config or 'rope'

    Returns:
        JSON string with list of references or error message
    """
    effective_backend = _get_effective_backend("references", backend)

    if effective_backend == Backend.PYRIGHT:
        try:
            workspace = _find_workspace(file)
            client = get_lsp_client(workspace)
            refs = client.references(file, line, column)
            return json.dumps({"references": refs, "count": len(refs), "backend": "pyright"}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "backend": "pyright"}, indent=2)
    else:
        result = rope_references(file, line, column)
        result["backend"] = "rope"
        return json.dumps(result, indent=2)


@mcp.tool()
def completions(
    file: str,
    line: int,
    column: int,
    backend: Optional[Literal["rope", "pyright"]] = None,
) -> str:
    """Get code completion suggestions at the given position.

    Args:
        file: Absolute path to the Python file
        line: 1-based line number
        column: 1-based column number
        backend: Backend to use (rope/pyright). Default: from config or 'rope'

    Returns:
        JSON string with completion items or error message
    """
    effective_backend = _get_effective_backend("completions", backend)

    if effective_backend == Backend.PYRIGHT:
        try:
            workspace = _find_workspace(file)
            client = get_lsp_client(workspace)
            items = client.completions(file, line, column)
            return json.dumps({"completions": items, "count": len(items), "backend": "pyright"}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "backend": "pyright"}, indent=2)
    else:
        result = rope_completions(file, line, column)
        result["backend"] = "rope"
        return json.dumps(result, indent=2)


@mcp.tool()
def symbols(
    file: str,
    query: Optional[str] = None,
    backend: Optional[Literal["rope", "pyright"]] = None,
) -> str:
    """Get symbols from a Python file.

    Args:
        file: Absolute path to the Python file
        query: Optional filter query for symbol names
        backend: Backend to use (rope/pyright). Default: from config or 'rope'

    Returns:
        JSON string with list of symbols or error message
    """
    effective_backend = _get_effective_backend("symbols", backend)

    if effective_backend == Backend.PYRIGHT:
        try:
            workspace = _find_workspace(file)
            client = get_lsp_client(workspace)
            syms = client.document_symbols(file)
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                syms = [s for s in syms if query_lower in s["name"].lower()]
            return json.dumps({"symbols": syms, "count": len(syms), "file": file, "backend": "pyright"}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "backend": "pyright"}, indent=2)
    else:
        result = rope_symbols(file, query)
        result["backend"] = "rope"
        return json.dumps(result, indent=2)


@mcp.tool()
def rename(file: str, line: int, column: int, new_name: str) -> str:
    """Rename the symbol at the given position.

    This will modify files on disk to rename all occurrences of the symbol.
    Uses Rope backend for best refactoring support.

    Args:
        file: Absolute path to the Python file
        line: 1-based line number
        column: 1-based column number
        new_name: The new name for the symbol

    Returns:
        JSON string with changes made or error message
    """
    result = do_rename(file, line, column, new_name)
    result["backend"] = "rope"
    return json.dumps(result, indent=2)


@mcp.tool()
def diagnostics(path: str) -> str:
    """Get type errors and warnings for a Python file or directory.

    Uses Pyright for type checking. Requires Pyright to be installed.

    Args:
        path: Absolute path to a Python file or directory

    Returns:
        JSON string with diagnostics or error message
    """
    result = get_diagnostics(path)
    result["backend"] = "pyright"
    return json.dumps(result, indent=2)


@mcp.tool()
def signature_help(file: str, line: int, column: int) -> str:
    """Get function signature information at the given position.

    Uses Pyright backend for accurate signature information.

    Args:
        file: Absolute path to the Python file
        line: 1-based line number
        column: 1-based column number

    Returns:
        JSON string with signature help or error message
    """
    try:
        workspace = _find_workspace(file)
        client = get_lsp_client(workspace)
        result = client.signature_help(file, line, column)
        if result:
            result["backend"] = "pyright"
            return json.dumps(result, indent=2)
        return json.dumps({"message": "No signature help available", "backend": "pyright"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "backend": "pyright"}, indent=2)


@mcp.tool()
def update_document(file: str, content: str) -> str:
    """Update file content for incremental analysis without writing to disk.

    Useful for testing code changes before saving.
    Uses Pyright backend for incremental updates.

    Args:
        file: Absolute path to the Python file
        content: New file content

    Returns:
        JSON string with confirmation
    """
    try:
        workspace = _find_workspace(file)
        client = get_lsp_client(workspace)
        client.update_document(file, content)
        return json.dumps({"success": True, "file": file, "backend": "pyright"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "backend": "pyright"}, indent=2)


@mcp.tool()
def status() -> str:
    """Get the status of the MCP server.

    Returns:
        JSON string with server status information
    """
    rope_client = get_rope_client()
    rope_status = rope_client.get_status()

    config = get_config()

    status_info = {
        "server": "Rope MCP Server",
        "version": "0.2.0",
        "backends": {
            "rope": {
                "available": True,
                "active_projects": rope_status.get("active_projects", []),
            },
            "pyright": {
                "available": True,  # Will be updated when first used
            },
        },
        "config": {
            "default_backend": config.default_backend.value,
            "shared_tools": list(SHARED_TOOLS),
            "tool_backends": {
                tool: config.get_backend_for(tool).value for tool in SHARED_TOOLS
            },
        },
    }
    return json.dumps(status_info, indent=2)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
