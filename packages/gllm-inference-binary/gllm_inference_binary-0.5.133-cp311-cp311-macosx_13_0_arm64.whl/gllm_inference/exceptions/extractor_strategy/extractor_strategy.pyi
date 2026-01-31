from abc import ABC
from enum import IntEnum, StrEnum
from gllm_inference.exceptions.exceptions import BaseInvokerError as BaseInvokerError, ModelNotFoundError as ModelNotFoundError, ProviderAuthError as ProviderAuthError, ProviderInternalError as ProviderInternalError, ProviderInvalidArgsError as ProviderInvalidArgsError, ProviderOverloadedError as ProviderOverloadedError, ProviderRateLimitError as ProviderRateLimitError
from typing import Any, Callable

class ErrorResolverType(StrEnum):
    """Error resolver type for the 4-stage resolution pipeline."""
    RESPONSE_DETAIL: str
    MESSAGE_PATTERN: str
    STATUS_CODE: str
    EXCEPTION_NAME: str

class ExtendedHTTPStatus(IntEnum):
    """HTTP status codes outside of the standard HTTPStatus enum.

    Attributes:
        SERVICE_OVERLOADED (int): HTTP status code for service overloaded.
    """
    SERVICE_OVERLOADED: int

HTTP_STATUS_TO_EXCEPTION_MAP: dict[int, type[BaseInvokerError]]
ResolutionStage = tuple[ErrorResolverType, Callable[[Exception], Any], dict[Any, type[BaseInvokerError]]]

class BaseExtractionStrategy(ABC):
    """Base extraction strategy for provider-specific error parsing.

    This class provides a self-contained error parsing system with a 4-stage resolution pipeline.
    Subclasses define provider-specific mappings and extraction logic.

    The 4-stage resolution pipeline:
        1. Response detail mapping (error codes/types)
        2. Message pattern matching (regex)
        3. HTTP status code mapping
        4. Exception type mapping (fully qualified class name)

    Attributes:
        response_detail_mapping (dict[str, type[BaseInvokerError]]): Maps provider error codes/types
            to BaseInvokerError subclasses.
        message_pattern_mapping (dict[str, type[BaseInvokerError]]): Maps regex patterns to
            BaseInvokerError subclasses.
        status_code_mapping (dict[int, type[BaseInvokerError]]): Maps HTTP status codes to
            BaseInvokerError subclasses.
        exception_mapping (dict[str, type[BaseInvokerError]]): Maps fully qualified exception
            class names to BaseInvokerError subclasses.
    """
    response_detail_mapping: dict[str, type[BaseInvokerError]]
    message_pattern_mapping: dict[str, type[BaseInvokerError]]
    status_code_mapping: dict[int, type[BaseInvokerError]]
    exception_mapping: dict[str, type[BaseInvokerError]]
    def parse(self, error: Exception, class_name: str) -> BaseInvokerError | None:
        """Parse error using the 4-stage resolution pipeline.

        This method orchestrates the error parsing process by attempting each stage
        of the resolution pipeline in order until a match is found.

        Args:
            error (Exception): The raw provider error.
            class_name (str): Invoker class name for error context.

        Returns:
            BaseInvokerError | None: Parsed and classified error if a match is found,
                None if no stage could resolve the error.
        """
