# New architecture imports
from typing import Any, Dict, Optional
from deepdiver_cli.providers.deepseek_provider import (
    DeepSeekRequestBuilder,
    DeepSeekResponseParser,
    DeepSeekProvider,
)

class AliBaBaProvider(DeepSeekProvider):
    """
    New AliBaBa provider implementation using the updated architecture.

    This provider inherits from DeepSeekProvider but uses AliBaBa-specific
    request builder for handling AliBaBa's API differences.
    """

    def __init__(self, provider_config):
        request_builder = AliBaBaRequestBuilder()
        response_parser = AliBaBaResponseParser()
        super().__init__(provider_config, request_builder, response_parser)


# ============================================================================
# AliBaBa Transformer Classes
# ============================================================================

class AliBaBaRequestBuilder(DeepSeekRequestBuilder):
    """Request builder for AliBaBa API."""

    def build_reasoning_config(self, enable_thinking: bool, extra_body: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Build reasoning configuration for AliBaBa."""
        if not enable_thinking:
            return extra_body

        extra_body = extra_body or {}
        if extra_body.get("enable_thinking") is None:
            extra_body["enable_thinking"] = True
        return extra_body


class AliBaBaResponseParser(DeepSeekResponseParser):
    """Response parser for AliBaBa API (same as DeepSeek)."""
    pass
