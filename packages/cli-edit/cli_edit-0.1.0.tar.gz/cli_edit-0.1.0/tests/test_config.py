"""Tests for configuration management."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from pathlib import Path

from src.utils.config import Config, load_config, resolve_model


class TestConfig:
    """Tests for Config model."""

    def test_default_values(self) -> None:
        config = Config()
        assert config.model == "claude-sonnet"
        assert config.context_lines == 3
        assert config.backup_enabled is True
        assert config.max_file_size_mb == 10
        assert config.theme == "monokai"
        assert config.streaming is True

    def test_custom_values(self) -> None:
        config = Config(model="gpt-4o", context_lines=5, theme="dracula")
        assert config.model == "gpt-4o"
        assert config.context_lines == 5
        assert config.theme == "dracula"


class TestLoadConfig:
    """Tests for config file loading."""

    def test_loads_defaults_when_no_files(self, tmp_path: Path) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = load_config(
                config_path=tmp_path / "nonexistent.toml",
                project_dir=tmp_path,
            )
        assert config.model == "claude-sonnet"

    def test_env_var_overrides(self, tmp_path: Path) -> None:
        env = {
            "ANTHROPIC_API_KEY": "test-key-123",
            "OPENAI_API_KEY": "openai-key-456",
            "CLI_EDIT_MODEL": "gpt-4o",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config(
                config_path=tmp_path / "nonexistent.toml",
                project_dir=tmp_path,
            )
        assert config.anthropic_api_key == "test-key-123"
        assert config.openai_api_key == "openai-key-456"
        assert config.model == "gpt-4o"

    def test_toml_config_loading(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text('model = "claude-haiku"\ncontext_lines = 5\n')

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(config_path=config_file, project_dir=tmp_path)
        assert config.model == "claude-haiku"
        assert config.context_lines == 5

    def test_invalid_toml_is_skipped(self, tmp_path: Path) -> None:
        config_file = tmp_path / "config.toml"
        config_file.write_text("this is { not valid toml")

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(config_path=config_file, project_dir=tmp_path)
        assert config.model == "claude-sonnet"

    def test_local_config_overrides_user_config(self, tmp_path: Path) -> None:
        user_config = tmp_path / "user.toml"
        user_config.write_text('model = "claude-haiku"\ntheme = "dracula"\n')

        local_config = tmp_path / ".cli-edit.toml"
        local_config.write_text('model = "gpt-4o"\n')

        with patch.dict(os.environ, {}, clear=True):
            config = load_config(config_path=user_config, project_dir=tmp_path)
        assert config.model == "gpt-4o"
        assert config.theme == "dracula"


class TestResolveModel:
    """Tests for model name resolution."""

    def test_claude_sonnet(self) -> None:
        model_id, provider = resolve_model("claude-sonnet")
        assert model_id == "claude-sonnet-4-20250514"
        assert provider == "anthropic"

    def test_gpt4o(self) -> None:
        model_id, provider = resolve_model("gpt-4o")
        assert model_id == "gpt-4o"
        assert provider == "openai"

    def test_unknown_claude_model(self) -> None:
        model_id, provider = resolve_model("claude-custom-model")
        assert model_id == "claude-custom-model"
        assert provider == "anthropic"

    def test_unknown_model_defaults_openai(self) -> None:
        model_id, provider = resolve_model("some-model")
        assert model_id == "some-model"
        assert provider == "openai"
