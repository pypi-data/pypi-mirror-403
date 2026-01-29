"""Prompts Module.

System prompts for the AI coding agent.
Loads prompts from .nexus/prompts/ if available.
Loads rules from .nexus/rules/ if available.
"""

from pathlib import Path
from typing import Any

from nexus.config.settings import settings


def _load_prompt(name: str, default: str) -> str:
    """Load prompt from file or return default.

    Args:
        name: str - Prompt file name (without extension).
        default: str - Default prompt content.

    Returns:
        str - Prompt content.
    """

    prompt_file: Path = settings.nexus_dir / "prompts" / f"{name}.md"
    if prompt_file.exists():
        try:
            return prompt_file.read_text(encoding="utf-8")
        except OSError:
            return default
    return default


def _load_rules() -> str:
    """Load user defined rules from .nexus/rules directory.

    Returns:
        str - Combined rules content or empty string.
    """

    rules_dir: Path = settings.nexus_dir / "rules"
    if not rules_dir.exists():
        return ""

    rules_content: list[str] = []
    for rule_file in rules_dir.glob("*.md"):
        try:
            content = rule_file.read_text(encoding="utf-8")
            rules_content.append(f"## Rule Configuration: {rule_file.stem}\n{content}")
        except OSError:
            continue

    if not rules_content:
        return ""

    return "\n\n# User Defined Rules (MANDATORY COMPLIANCE)\n\n" + "\n\n".join(rules_content)


def get_config_status() -> dict[str, Any]:
    """Get configuration loading status.

    Returns:
        dict[str, Any] - Status details including loaded prompts and rules.
    """

    status: dict[str, Any] = {
        "prompts": {"loaded": 0, "files": []},
        "rules": {"loaded": 0, "files": []},
    }

    prompts_dir: Path = settings.nexus_dir / "prompts"
    if prompts_dir.exists():
        for p in prompts_dir.glob("*.md"):
            try:
                line_count = len(p.read_text(encoding="utf-8").splitlines())
                status["prompts"]["loaded"] += 1
                status["prompts"]["files"].append({"name": p.name, "lines": line_count})
            except OSError:
                continue

    rules_dir: Path = settings.nexus_dir / "rules"
    if rules_dir.exists():
        for r in rules_dir.glob("*.md"):
            try:
                line_count = len(r.read_text(encoding="utf-8").splitlines())
                status["rules"]["loaded"] += 1
                status["rules"]["files"].append({"name": r.name, "lines": line_count})
            except OSError:
                continue

    return status


_DEFAULT_SYSTEM_PROMPT: str = """You are Nexus, an elite AI coding agent.

Your capabilities:
- Search and analyze code
- Provide expert coding assistance

Guidelines:
2. Use tools efficiently and in the correct order
3. Respect .gitignore patterns: Avoid reading or listing files that are typically ignored (e.g., .venv,
   node_modules, __pycache__) unless explicitly requested.
4. Ask for clarification when needed
5. Follow best practices and coding standards
6. Be concise but thorough in your responses

When working with code:
- Write clean, well-documented code
- Follow language-specific conventions
- Consider edge cases and error handling
- Optimize for readability and maintainability

Remember: You have access to powerful tools. Use them responsibly and always confirm destructive operations.
"""

_DEFAULT_CODE_REVIEW_PROMPT: str = """Review the following code and provide feedback on:
1. Code quality and style
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement

Code:
{code}
"""

_DEFAULT_CODE_GENERATION_PROMPT: str = """Generate code based on the following requirements:

Requirements:
{requirements}

Language: {language}

Please provide:
1. Clean, well-documented code
2. Error handling
3. Type hints (if applicable)
4. Brief explanation of the implementation
"""

_base_system_prompt: str = _load_prompt("system_prompt", _DEFAULT_SYSTEM_PROMPT)
_rules: str = _load_rules()

SYSTEM_PROMPT: str = f"{_base_system_prompt}{_rules}"
CODE_REVIEW_PROMPT: str = _load_prompt("code_review_prompt", _DEFAULT_CODE_REVIEW_PROMPT)
CODE_GENERATION_PROMPT: str = _load_prompt("code_generation_prompt", _DEFAULT_CODE_GENERATION_PROMPT)


__all__: list[str] = [
    "CODE_GENERATION_PROMPT",
    "CODE_REVIEW_PROMPT",
    "SYSTEM_PROMPT",
    "get_config_status",
]
