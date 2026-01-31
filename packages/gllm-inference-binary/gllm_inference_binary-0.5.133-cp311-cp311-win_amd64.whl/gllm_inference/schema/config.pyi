from gllm_inference.schema.enums import TruncateSide as TruncateSide
from pydantic import BaseModel
from typing import Any

class ThinkingConfig(BaseModel):
    """Configuration for thinking behavior.

    Attributes:
        enabled (bool): Whether thinking is enabled. Defaults to False.
        kwargs (dict[str, Any]): Additional thinking-related keyword arguments. Defaults to an empty dictionary.
    """
    enabled: bool
    kwargs: dict[str, Any]

class TruncationConfig(BaseModel):
    """Configuration for text truncation behavior.

    Attributes:
        max_length (int): Maximum length of text content. Required.
        truncate_side (TruncateSide | None): Side to truncate from when max_length is exceeded.
            1. TruncateSide.RIGHT: Keep the beginning of the text, truncate from the end (default)
            2. TruncateSide.LEFT: Keep the end of the text, truncate from the beginning
            If None, defaults to TruncateSide.RIGHT
    """
    max_length: int
    truncate_side: TruncateSide | None
