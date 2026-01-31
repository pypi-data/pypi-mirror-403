from gllm_inference.exceptions.error_extractor.common_extractor import CommonErrorExtractor as CommonErrorExtractor
from gllm_inference.exceptions.error_extractor.error_extractor import BaseErrorExtractor as BaseErrorExtractor
from gllm_inference.schema import ModelProvider as ModelProvider

EXTRACTOR_MAP: dict[ModelProvider, type[BaseErrorExtractor]]

def get_error_extractor(provider: ModelProvider) -> type[BaseErrorExtractor]:
    """Get the registered provider error extractor class.

    Args:
        provider (ModelProvider): The provider name.

    Returns:
        type[BaseErrorExtractor]: The registered provider error extractor class.
    """
def get_all_provider_extractors() -> list[BaseErrorExtractor]:
    """Get all registered provider error extractor instances.

    Returns:
        list[BaseErrorExtractor]: List of all provider extractor instances.
    """
