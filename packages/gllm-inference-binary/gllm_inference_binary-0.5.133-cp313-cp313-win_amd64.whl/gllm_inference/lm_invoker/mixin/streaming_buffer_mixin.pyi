from gllm_inference.output_transformer.output_transformer import BaseOutputTransformer as BaseOutputTransformer
from gllm_inference.schema import LMOutput as LMOutput, Reasoning as Reasoning, StreamBuffer as StreamBuffer, StreamBufferType as StreamBufferType, ThinkingEvent as ThinkingEvent, ToolCall as ToolCall

class Key:
    """Defines constants for tool call keys."""
    FUNCTION: str
    FUNCTION_NAME: str
    FUNCTION_ARGUMENTS: str
    ID: str

class StreamingBufferMixin:
    """Mixin class that provides streaming buffer state management functionality.

    This mixin provides methods to manage streaming buffers for different content types and handles
    transitions between buffer states. It is designed to be used by LM invokers that process streaming
    responses from language model APIs.
    """
