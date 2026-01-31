"""Paths to prompt template files."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent

SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "system_prompt.md"
SUMMARIZE_CONTEXT_PROMPT_PATH = _PROMPTS_DIR / "summarize_context.md"
CODE_REVIEWER_PROMPT_PATH = _PROMPTS_DIR / "code_reviewer_system_prompt.md"
