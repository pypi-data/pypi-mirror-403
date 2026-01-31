from gllm_inference.exceptions.error_extractor.error_extractor import BaseErrorExtractor as BaseErrorExtractor
from gllm_inference.exceptions.extractor_strategy.common_strategy import CommonExtractionStrategy as CommonExtractionStrategy

class CommonErrorExtractor(BaseErrorExtractor):
    """Common error extractor for cross-provider error handling.

    This class handles common error patterns that occur across all providers,
    such as httpx connection errors, timeouts, and network issues. It exclusively
    uses CommonExtractionStrategy for error resolution.
    """
    def __init__(self) -> None:
        """Initialize the common error extractor.

        This extractor uses only CommonExtractionStrategy to handle cross-provider
        errors (e.g., httpx connection errors, timeouts, network issues).
        """
