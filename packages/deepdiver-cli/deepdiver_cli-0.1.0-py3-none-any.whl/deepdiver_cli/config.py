import shutil
from pathlib import Path
import threading
from typing import List, Optional

from pydantic import BaseModel, Field
import tomllib
import structlog


# DeepDiver Home
HOME_ROOT = (Path.home() / ".deepdiver").expanduser()
# 会话目录
SESSION_ROOT = HOME_ROOT / "sessions"
# 配置目录
CONFIG_ROOT = HOME_ROOT / "config"
# 知识目录
KNOWLEDGE_ROOT = HOME_ROOT / "knowledge"
# 经验目录
EXPERIENCE_ROOT = HOME_ROOT / "experience"

# 配置文件
CONFIG_FILE = CONFIG_ROOT / "config.toml"

# 提示目录（内部）
PROMPT_DIR = Path(__file__).resolve().parent / "prompt"

# 配置模板目录
CONFIG_TEMPLATES_DIR = Path(__file__).resolve().parent / "config_templates"


dirs_to_make = [
    HOME_ROOT,
    SESSION_ROOT,
    CONFIG_ROOT,
    KNOWLEDGE_ROOT,
    EXPERIENCE_ROOT,
]
for dir in dirs_to_make:
    dir.mkdir(parents=True, exist_ok=True)


class ConfigError(Exception):
    pass


class APIKeyNotConfiguredError(ConfigError):
    """API key 未配置异常"""
    def __init__(self, provider_name: str, base_url: str, config_path: str):
        self.provider_name = provider_name
        self.base_url = base_url
        self.config_path = config_path
        message = (
            f"API key for provider '{provider_name}' is not configured.\n"
            f"Please set the api_key in: {config_path}\n"
            f"Provider: {provider_name}\n"
            f"Base URL: {base_url}"
        )
        super().__init__(message)


class LLMProviderConfig(BaseModel):
    provider_name: str
    base_url: str
    api_key: str


class LLMConfig(BaseModel):
    provider_name: str
    model: str
    max_tokens: int
    temperature: float
    timeout: float
    enable_thinking: bool
    dump_thinking: bool
    dump_answer: bool
    stream: bool


class DeepDiverConfig(BaseModel):
    max_steps: int = Field(default=30, description="max loop steps")
    llm: dict[str, LLMConfig]


class InspectPatternConfig(BaseModel):
    apply_time_filter: bool = Field(default=False, description="是否应用时间过滤")
    patterns: List[str] = Field(default_factory=list, description="模式字符串列表")
    before_context: int = Field(default=0, description="匹配行之前的上下文行数")
    after_context: int = Field(default=0, description="匹配行之后的上下文行数")
    line_limit: Optional[int] = Field(
        default=None,
        description="单个pattern的行数限制，为空时使用inspect工具的line_limit",
    )


class InspectConfig(BaseModel):
    enable: bool = Field(default=True, description="是否启用inspect工具")
    line_limit: int = Field(default=800, description="inspect工具专用的行数限制")
    patterns: List[InspectPatternConfig] = Field(
        default_factory=list, description="模式配置列表"
    )
    llm: LLMConfig


class ReviewConfig(BaseModel):
    enable: bool = Field(default=False, description="是否启用review工具")
    max_commit_count: int = Field(default=3, description="最大提交数量")
    llm: LLMConfig


class AnalyzeCodeConfig(BaseModel):
    enable: bool = Field(default=False, description="是否启用代码分析工具")


class ToolsConfig(BaseModel):
    review: ReviewConfig
    inspect: InspectConfig
    analyze_code: AnalyzeCodeConfig = Field(
        default_factory=AnalyzeCodeConfig, description="代码分析工具配置"
    )


class TruncateConfig(BaseModel):
    line_length_limit: int = Field(default=400, description="行长度限制")
    line_limit: int = Field(default=100, description="行数限制")


class PluginItemConfig(BaseModel):
    key: str = Field(description="插件键名")
    path: str = Field(description="插件路径")


class PluginConfig(BaseModel):
    plugin_dir: str = Field(default="", description="插件目录")
    plugins: List[PluginItemConfig] = Field(
        default_factory=list, description="插件列表"
    )


class SessionConfig(BaseModel):
    """Session management configuration."""

    max_sessions: int = Field(
        default=100, description="Maximum number of sessions to keep"
    )
    auto_cleanup_days: int = Field(
        default=30,
        description="Automatically cleanup sessions older than this many days",
    )
    session_id_format: str = Field(
        default="%Y%m%d_%H%M%S_%random6%", description="Session ID format pattern"
    )
    enable_session_management: bool = Field(
        default=True, description="Enable session management features"
    )


class AppConfig(BaseModel):
    deepdiver: DeepDiverConfig
    providers: list[LLMProviderConfig]
    tools: ToolsConfig
    plugin: PluginConfig = Field(default_factory=PluginConfig, description="插件配置")
    truncate: TruncateConfig
    session: SessionConfig = Field(
        default_factory=SessionConfig, description="会话配置"
    )


class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_config()
                    self._initialized = True

    def _get_config_path(self) -> Path:
        return CONFIG_FILE

    def _ensure_config_files(self):
        """确保配置文件存在，如果不存在则从模板创建"""
        logger = structlog.get_logger()

        config_file = CONFIG_ROOT / "config.toml"
        knowledge_file = CONFIG_ROOT / "knowledge_config.toml"

        # 检查并创建 config.toml
        if not config_file.exists():
            config_template = CONFIG_TEMPLATES_DIR / "config.toml"
            if config_template.exists():
                shutil.copy(config_template, config_file)
                logger.info(
                    "config_file_created",
                    file=str(config_file),
                    template=str(config_template)
                )
            else:
                raise ConfigError(
                    f"配置模板文件不存在: {config_template}\n"
                    f"请手动创建配置文件: {config_file}"
                )

        # 检查并创建 knowledge_config.toml
        if not knowledge_file.exists():
            knowledge_template = CONFIG_TEMPLATES_DIR / "knowledge_config.toml"
            if knowledge_template.exists():
                shutil.copy(knowledge_template, knowledge_file)
                logger.info(
                    "knowledge_config_created",
                    file=str(knowledge_file),
                    template=str(knowledge_template)
                )
            else:
                # knowledge_config.toml 是可选的，不抛出错误
                logger.warning(
                    "knowledge_config_template_not_found",
                    template=str(knowledge_template)
                )

    def _load_config_as_dict(self) -> dict:
        # 确保配置文件存在
        self._ensure_config_files()

        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_config(self):
        raw_config = self._load_config_as_dict()
        deepdiver = raw_config.get("deepdiver", {})
        deepdiver_base_llm = deepdiver.get("llm", {})

        deepdiver_llm_settings_overrides = {
            k: v for k, v in deepdiver.get("llm", {}).items() if isinstance(v, dict)
        }

        app_config = {
            "deepdiver": {
                "max_steps": deepdiver.get("max_steps", 30),
                "llm": {
                    "default": deepdiver_base_llm,
                    **{
                        name: {**deepdiver_base_llm, **override_config}
                        for name, override_config in deepdiver_llm_settings_overrides.items()
                    },
                },
            },
            "tools": raw_config.get("tools", {}),
            "truncate": raw_config.get("truncate", {}),
            "plugin": raw_config.get("plugin", {}),
            "providers": raw_config.get("providers", []),
        }

        self._config = AppConfig.model_validate(app_config)

    def get_provider(self, provider_name: str) -> LLMProviderConfig:
        assert self._config
        provider = next(
            (
                provider
                for provider in self._config.providers
                if provider.provider_name == provider_name
            ),
            None,
        )
        if provider is None:
            raise ConfigError(f"provider is not found: {provider_name}")

        # 检查 api_key 是否已配置
        if not provider.api_key or provider.api_key.strip() == "":
            raise APIKeyNotConfiguredError(
                provider_name=provider_name,
                base_url=provider.base_url,
                config_path=str(CONFIG_FILE)
            )

        return provider

    @property
    def deepdiver(self) -> DeepDiverConfig:
        assert self._config
        return self._config.deepdiver

    @property
    def tools(self) -> ToolsConfig:
        assert self._config
        return self._config.tools

    @property
    def truncate(self) -> TruncateConfig:
        assert self._config
        return self._config.truncate

    @property
    def plugin(self) -> PluginConfig:
        assert self._config
        return self._config.plugin

    @property
    def prompt_dir(self) -> Path:
        return PROMPT_DIR

    @property
    def config_dir(self) -> Path:
        return CONFIG_ROOT

    @property
    def knowledge_dir(self) -> Path:
        return KNOWLEDGE_ROOT

    @property
    def project_root_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent


config = Config()
