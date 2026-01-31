from gllm_inference.exceptions.error_parser import convert_to_base_invoker_error as convert_to_base_invoker_error
from gllm_inference.exceptions.exceptions import BaseInvokerError as BaseInvokerError
from gllm_inference.exceptions.provider_error_map import OPENAI_MESSAGE_MAPPING as OPENAI_MESSAGE_MAPPING, OPENAI_RESPONSE_DETAIL_MAPPING as OPENAI_RESPONSE_DETAIL_MAPPING

class OpenAIErrorExtractorMixin:
    """Mixin that provides OpenAI error extraction for OpenAI-based invokers.

    This mixin is used by both OpenAILMInvoker and OpenAIChatCompletionsLMInvoker
    to extract provider errors into BaseInvokerError instances.
    """
