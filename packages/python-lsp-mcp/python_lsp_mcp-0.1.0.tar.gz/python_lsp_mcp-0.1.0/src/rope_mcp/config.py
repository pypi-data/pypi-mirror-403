"""Configuration for Rope MCP Server."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import os


class Backend(Enum):
    """Available backends for code analysis."""

    ROPE = "rope"
    PYRIGHT = "pyright"


# Tools that support both backends
SHARED_TOOLS = {"hover", "definition", "references", "completions", "symbols"}

# Tools exclusive to each backend
ROPE_ONLY_TOOLS = {"rename"}  # Rope has better refactoring
PYRIGHT_ONLY_TOOLS = {"diagnostics", "signature_help"}  # Pyright exclusive


@dataclass
class ServerConfig:
    """Configuration for the MCP server."""

    # Default backend for shared features
    default_backend: Backend = Backend.ROPE

    # Per-tool backend overrides (None = use default)
    hover_backend: Optional[Backend] = None
    definition_backend: Optional[Backend] = None
    references_backend: Optional[Backend] = None
    completions_backend: Optional[Backend] = None
    symbols_backend: Optional[Backend] = None

    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Create config from environment variables.

        Environment variables:
            ROPE_MCP_BACKEND: Default backend (rope/pyright), default: rope
            ROPE_MCP_HOVER_BACKEND: Backend for hover (rope/pyright)
            ROPE_MCP_DEFINITION_BACKEND: Backend for definition
            ROPE_MCP_REFERENCES_BACKEND: Backend for references
            ROPE_MCP_COMPLETIONS_BACKEND: Backend for completions
            ROPE_MCP_SYMBOLS_BACKEND: Backend for symbols
        """
        default = os.environ.get("ROPE_MCP_BACKEND", "rope").lower()
        default_backend = Backend(default) if default in ["rope", "pyright"] else Backend.ROPE

        def get_backend(name: str) -> Optional[Backend]:
            val = os.environ.get(f"ROPE_MCP_{name.upper()}_BACKEND", "").lower()
            if val in ["rope", "pyright"]:
                return Backend(val)
            return None

        return cls(
            default_backend=default_backend,
            hover_backend=get_backend("hover"),
            definition_backend=get_backend("definition"),
            references_backend=get_backend("references"),
            completions_backend=get_backend("completions"),
            symbols_backend=get_backend("symbols"),
        )

    def get_backend_for(self, tool: str) -> Backend:
        """Get the backend to use for a specific tool."""
        if tool in ROPE_ONLY_TOOLS:
            return Backend.ROPE
        if tool in PYRIGHT_ONLY_TOOLS:
            return Backend.PYRIGHT

        override = getattr(self, f"{tool}_backend", None)
        if override is not None:
            return override
        return self.default_backend


# Global config instance
_config: Optional[ServerConfig] = None


def get_config() -> ServerConfig:
    """Get the global server configuration."""
    global _config
    if _config is None:
        _config = ServerConfig.from_env()
    return _config


def set_config(config: ServerConfig) -> None:
    """Set the global server configuration."""
    global _config
    _config = config
