"""Configuration management for cli-edit."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

import tomli
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "cli-edit"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.toml"
LOCAL_CONFIG_NAME = ".cli-edit.toml"

ModelName = Literal[
    "claude-sonnet",
    "claude-haiku",
    "claude-opus",
    "gpt-4o",
    "gpt-4o-mini",
]

MODEL_MAP: dict[str, str] = {
    "claude-sonnet": "claude-sonnet-4-20250514",
    "claude-haiku": "claude-haiku-4-20250414",
    "claude-opus": "claude-opus-4-20250514",
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
}

PROVIDER_FOR_MODEL: dict[str, Literal["anthropic", "openai"]] = {
    "claude-sonnet": "anthropic",
    "claude-haiku": "anthropic",
    "claude-opus": "anthropic",
    "gpt-4o": "openai",
    "gpt-4o-mini": "openai",
}


class Config(BaseModel):
    """Application configuration."""

    model: str = Field(default="claude-sonnet", description="AI model to use")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    context_lines: int = Field(default=3, description="Context lines in diff")
    backup_enabled: bool = Field(default=True, description="Create backups before edits")
    max_file_size_mb: int = Field(default=10, description="Maximum file size in MB")
    theme: str = Field(default="monokai", description="Syntax highlighting theme")
    streaming: bool = Field(default=True, description="Stream AI responses")


def _load_toml(path: Path) -> dict[str, object]:
    """Load a TOML file and return its contents."""
    try:
        with open(path, "rb") as f:
            data: dict[str, object] = tomli.load(f)
            return data
    except FileNotFoundError:
        return {}
    except tomli.TOMLDecodeError:
        logger.warning("Invalid TOML in %s, skipping", path)
        return {}


def load_config(
    config_path: Path | None = None,
    project_dir: Path | None = None,
) -> Config:
    """Load configuration from files and environment variables.

    Priority (highest to lowest):
    1. Environment variables
    2. Local project config (.cli-edit.toml)
    3. User config (~/.config/cli-edit/config.toml)
    4. Defaults
    """
    merged: dict[str, object] = {}

    user_config_path = config_path or DEFAULT_CONFIG_PATH
    user_data = _load_toml(user_config_path)
    merged.update(user_data)

    if project_dir is not None:
        local_path = project_dir / LOCAL_CONFIG_NAME
    else:
        local_path = Path.cwd() / LOCAL_CONFIG_NAME
    local_data = _load_toml(local_path)
    merged.update(local_data)

    env_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if env_key:
        merged["anthropic_api_key"] = env_key

    env_openai = os.environ.get("OPENAI_API_KEY", "")
    if env_openai:
        merged["openai_api_key"] = env_openai

    env_model = os.environ.get("CLI_EDIT_MODEL", "")
    if env_model:
        merged["model"] = env_model

    return Config.model_validate(merged)


def resolve_model(model_name: str) -> tuple[str, Literal["anthropic", "openai"]]:
    """Resolve a model shorthand to its full API name and provider."""
    if model_name in MODEL_MAP:
        return MODEL_MAP[model_name], PROVIDER_FOR_MODEL[model_name]
    if model_name.startswith("claude"):
        return model_name, "anthropic"
    return model_name, "openai"
