from gllm_inference.exceptions.exceptions import APIConnectionError as APIConnectionError, APITimeoutError as APITimeoutError, BaseInvokerError as BaseInvokerError
from gllm_inference.exceptions.extractor_strategy.extractor_strategy import BaseExtractionStrategy as BaseExtractionStrategy
from typing import Final

HTTP_ERROR_MAPPING: Final[dict[str, type[BaseInvokerError]]]

class CommonExtractionStrategy(BaseExtractionStrategy):
    """Extraction strategy for common cross-provider errors.

    This strategy handles errors that can occur across multiple providers, such as
    httpx connection errors and timeouts. It is typically used as a fallback in the
    extraction pipeline after provider-specific strategies.

    Attributes:
        exception_mapping (dict[str, type[BaseInvokerError]]): Maps fully qualified
            exception class names to BaseInvokerError subclasses.
    """
    exception_mapping: dict[str, type[BaseInvokerError]]
