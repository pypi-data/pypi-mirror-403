# SWEDeepDiver

SWEDeepDiver is an automated analysis agent for **Software Engineering (SWE) problems**, designed to perform deep diagnosis and root cause analysis for multi-technology stack issues including Android, iOS, Backend, and Frontend.

It simulates experienced engineers' troubleshooting habits: from whole to part, from symptoms to root causes, comprehensively utilizing logs, exception traces, various issue files, source code, and knowledge bases to build "timeline + evidence chains", ultimately providing structured, verifiable diagnostic conclusions.

## Features

- **Automated Problem Diagnosis**: Simulates experienced engineers' troubleshooting approach
- **Multi-source Evidence Analysis**: Uses logs, exception traces, issue files, source code, and knowledge bases
- **Structured Reasoning**: Builds "timeline + evidence chain" for verifiable diagnostic conclusions
- **Multi-technology Stack Support**: Android, iOS, backend (Java, Python, Node.js, etc.), frontend
- **Zero-intrusion Design**: All state saved in `~/.deepdiver/`, no files written to user projects
- **Session Management**: Independent sessions, traceable and reproducible
- **Plugin System**: Custom desensitization, decryption, and filtering strategies
- **Knowledge Base Integration**: Domain-specific knowledge injection
- **Multi-LLM Support**: DeepSeek, Moonshot, Alibaba Tongyi, OpenRouter, and more
- **ReAct Architecture**: Reasoning + Acting mode for structured reasoning

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver written in Rust. It's the recommended way to install SWEDeepDiver:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install SWEDeepDiver using uv tool
uv tool install deepdiver-cli
```

### Using pip (Alternative)

```bash
pip install deepdiver-cli
```

### Additional Requirements

SWEDeepDiver requires `ripgrep` for efficient file searching:

```bash
# On macOS
brew install ripgrep

# On Ubuntu/Debian
sudo apt-get install ripgrep

# Other platforms: refer to ripgrep installation guide
```

For code analysis functionality, Claude Code CLI is optional:
```bash
npm install -g @anthropic-ai/claude-code
```

## Quick Start

### Basic Usage

```bash
# Analyze issue with code directory
cd /path/to/your/code
deepdiver -c --attachment_path /path/to/issue/attachments --issue "Application crashes on startup"

# Analyze issue from attachment directory
cd /path/to/issue/attachments
deepdiver --code_path /path/to/your/code --issue "Performance degradation in payment service"

# Analyze attachments only (no code)
cd /path/to/issue/attachments
deepdiver --issue "Database connection timeout errors"
```

### Parameter Reference

- `-c`, `--code`: Declare current working directory as code directory
- `--code-path <PATH>`: Additional code directories (multiple allowed)
- `--attachment-path <PATH>`: Attachment directories (multiple allowed)
- `--issue "<TEXT>"`: Problem description in natural language
- `--list-sessions`: List historical diagnosis sessions
- `--show-report <session_id>`: Show diagnostic report for specific session

## Configuration

### Agent Configuration

Configuration files are automatically created on first run. The first time you run DeepDiver, it will automatically generate configuration files from templates:

```bash
# Configuration files are auto-created in ~/.deepdiver/config/
# - config.toml: Main configuration (LLM providers, API keys, model settings)
# - knowledge_config.toml: Knowledge base configuration (optional)
```

To manually configure or update settings:

```bash
# Edit the main configuration
# Configure LLM providers, API keys, model settings, etc.
vim ~/.deepdiver/config/config.toml
```

### Plugin Development

Implement custom plugins for data processing:

```python
# Example: Custom data masking
from deepdiver_cli.plugins.datamask import DataMasker

class MyDataMasker(DataMasker):
    def mask(self, raw: str) -> str:
        # Implement your data masking logic
        return masked
```

The plugin system automatically discovers and loads classes implementing Protocol interfaces.

## Usage Example

Analyzing an Android ANR issue:

```bash
deepdiver -c --attachment_path examples/android/anr --issue "Application experiences ANR, please analyze the cause"
```

SWEDeepDiver will:
1. Parse problem description and attachments
2. Identify problem type and evidence sources
3. Call analysis tools (Glob, ProcessFile, Grep, Inspect, AnalyzeCode, etc.)
4. Build timeline and evidence chains
5. Output structured diagnostic report
6. Save intermediate results in `~/.deepdiver/sessions/<session_id>/`

## Output Example

```markdown
**Conclusion**: ANR root cause is `HeavyService.performHeavyOperation` calling `Thread.sleep` in main thread.

**Confidence**: High

**Evidence Strength**: High

**Core Evidence**:
1. **Log/Trace Evidence**:
   - `03:34:05.428` MainActivity: "Performing heavy database operation"
   - `03:34:11.428` ActivityManager reports ANR for service `com.example.testapp/.HeavyService`
   - ANR Trace shows main thread Sleeping at `Thread.sleep`, called by `HeavyService.performHeavyOperation`

**Timeline**:
| Time           | Event                                       | Source              |
|----------------|---------------------------------------------|---------------------|
| 03:34:05.428   | Heavy operation starts                      | MainActivity log    |
| 03:34:11.428   | ANR reported                                | ActivityManager log |
| 03:34:11       | Main thread blocked in sleep                | ANR Trace           |
```

## Project Structure

```
SWEDeepDiver/
├── src/deepdiver_cli/          # Source code
│   ├── react_core/             # ReAct core engine
│   ├── tools/                  # Analysis tools
│   ├── app/                    # Application logic
│   ├── chat/                   # Chat models and providers
│   ├── plugins/                # Plugin interfaces
│   ├── config.py              # Configuration
│   └── cli.py                 # CLI entry
├── examples/                   # Example files
├── pyproject.toml             # Python project config
└── README.md                  # Documentation
```

## Technology Stack

- **Python 3.12+** - Primary language
- **Typer** - CLI framework
- **Pydantic** - Data validation
- **OpenAI** - API client
- **HTTPX** - HTTP client
- **Tenacity** - Retry library
- **Structlog** - Structured logging
- **ReAct Pattern** - Reasoning + Acting architecture

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/SteveYang92/SWEDeepDiver.git
cd SWEDeepDiver
uv venv --python 3.12
source .venv/bin/activate  # Unix/macOS
uv pip install -e ".[dev]"
uv run pytest tests/ -v
```

## License

MIT License - see [LICENSE](LICENSE) file.

## Disclaimer

### Security & Privacy
- SWEDeepDiver is designed for local/self-hosted use
- Logs, traces, and source code may contain sensitive information
- Implement proper data masking/decryption plugins for your security requirements
- API keys and configurations should be kept secure

### Diagnostic Limitations
- Results depend on available data, knowledge bases, and LLM capabilities
- Not guaranteed to be completely accurate in all scenarios
- Use as an auxiliary analysis tool, not the sole basis for decisions

### Usage Responsibility
- Provided "as-is" without warranties
- Test thoroughly in controlled environments before production use

## Acknowledgments

- Configuration system references [OpenManus](https://github.com/FoundationAgents/OpenManus)
- Prompt and tool design references [ClaudeCode](https://github.com/anthropics/claude-code)

---

*For Chinese documentation, see [README_CN.md](README_CN.md)*