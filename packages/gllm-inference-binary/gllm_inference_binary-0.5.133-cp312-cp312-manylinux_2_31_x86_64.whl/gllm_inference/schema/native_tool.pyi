from gllm_inference.schema.enums import NativeToolType as NativeToolType
from gllm_inference.utils.validation import validate_enum as validate_enum
from pydantic import BaseModel
from typing import Any

class Key:
    """Defines valid keys in native tool."""
    TYPE: str
    URL: str
    NAME: str
    ALLOWED_TOOLS: str
    EXTRA_PARAMS: str

class NativeTool(BaseModel):
    """Defines the native tool schema.

    Attributes:
        type (NativeToolType): The type of the native tool.
        kwargs (dict[str, Any]): The additional keyword arguments of the native tool.
    """
    type: NativeToolType
    kwargs: dict[str, Any]
    @classmethod
    def code_interpreter(cls, **kwargs: Any) -> NativeTool:
        """Create a code interpreter native tool.

        Args:
            **kwargs (Any): Additional configuration for the code interpreter native tool.

        Returns:
            NativeTool: A new code interpreter native tool.
        """
    @classmethod
    def web_search(cls, **kwargs: Any) -> NativeTool:
        """Create a web search native tool.

        Args:
            **kwargs (Any): Additional configuration for the web search native tool.

        Returns:
            NativeTool: A new web search native tool.
        """
    @classmethod
    def mcp_server(cls, url: str, name: str, allowed_tools: list[str] | None = None, **kwargs: Any) -> NativeTool:
        """Create a MCP server native tool.

        Args:
            url (str): The URL of the MCP server.
            name (str): The name of the MCP server.
            allowed_tools (list[str] | None, optional): The allowed tools of the MCP server. Defaults to None.
            **kwargs (Any): Additional configuration for the MCP server native tool.

        Returns:
            NativeTool: A new MCP server native tool.
        """
    @classmethod
    def from_str_or_dict(cls, data: str | dict[str, Any]) -> NativeTool:
        """Create a native tool from a string or a dictionary.

        Args:
            data (str | dict[str, Any]): The string or dictionary that represents the native tool.

        Returns:
            NativeTool: A new native tool.
        """
