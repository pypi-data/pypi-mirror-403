from deepdiver_cli.config import config
from .chat_provider import ChatProvider
from .chat_model import LLMProviderConfig as ProviderConfig

# Import new architecture providers
from ..providers.openrouter_provider import OpenRouterProvider
from ..providers.deepseek_provider import DeepSeekProvider
from ..providers.alibaba_provider import AliBaBaProvider


class ChatProviderFactory:
    @staticmethod
    def get_provider(provider_name: str) -> ChatProvider:
        provider_config = config.get_provider(provider_name)
        provider_config = ProviderConfig(
            provider_name=provider_config.provider_name,
            base_url=provider_config.base_url,
            api_key=provider_config.api_key,
        )

        # Use new architecture providers
        match provider_config.provider_name:
            case "deepseek":
                return DeepSeekProvider(provider_config)
            case "openrouter":
                return OpenRouterProvider(provider_config)
            case "alibaba":
                return AliBaBaProvider(provider_config)
            case _:
                return DeepSeekProvider(provider_config)
