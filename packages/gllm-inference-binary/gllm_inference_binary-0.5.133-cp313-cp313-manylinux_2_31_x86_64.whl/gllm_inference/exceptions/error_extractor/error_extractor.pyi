from gllm_inference.exceptions.exceptions import BaseInvokerError as BaseInvokerError, InvokerRuntimeError as InvokerRuntimeError
from gllm_inference.exceptions.extractor_strategy.extractor_strategy import BaseExtractionStrategy as BaseExtractionStrategy

class BaseErrorExtractor:
    """Error extractor facade.

    This class provides a simple interface for parsing provider errors by delegating
    to a list of extraction strategies. It is the main entry point used by invokers.
    """
    def __init__(self, provider_strategy: list[BaseExtractionStrategy]) -> None:
        """Initialize the error resolver with error extraction strategies.

        Args:
            provider_strategy (list[BaseExtractionStrategy]): List of extraction strategies.
        """
    def resolve(self, error: Exception, class_name: str) -> BaseInvokerError:
        """Resolve a provider error to a BaseInvokerError.

        This is the main method called by invokers to convert provider-specific
        errors into standardized BaseInvokerError subclasses.

        Args:
            error (Exception): The raw provider error to resolve.
            class_name (str): The invoker class name for error context.

        Returns:
            BaseInvokerError: The resolved error with appropriate type and debug info.
        """
