"""Tests for paracord.utils.config module."""

from pathlib import Path

import pytest

from paracord.utils.config import (
    COPIER_ANSWERS_FILE,
    RAV_CONFIG_FILE,
    PARACORD_COMPONENTS_FILE,
    load_yaml,
    save_yaml,
    get_copier_answers,
    get_rav_config,
    get_template_info,
)


class TestLoadYaml:
    """Tests for load_yaml function."""

    def test_loads_valid_yaml(self, tmp_path: Path) -> None:
        """Should load a valid YAML file."""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("key: value\nnumber: 42\n")

        result = load_yaml(yaml_file)

        assert result == {"key": "value", "number": 42}

    def test_returns_empty_dict_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Should return empty dict when file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.yaml"

        result = load_yaml(nonexistent)

        assert result == {}

    def test_returns_empty_dict_for_empty_file(self, tmp_path: Path) -> None:
        """Should return empty dict for an empty YAML file."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("")

        result = load_yaml(empty_file)

        assert result == {}

    def test_loads_nested_yaml(self, tmp_path: Path) -> None:
        """Should load nested YAML structures."""
        yaml_file = tmp_path / "nested.yaml"
        yaml_file.write_text(
            """
parent:
  child: value
  list:
    - item1
    - item2
"""
        )

        result = load_yaml(yaml_file)

        assert result["parent"]["child"] == "value"
        assert result["parent"]["list"] == ["item1", "item2"]


class TestSaveYaml:
    """Tests for save_yaml function."""

    def test_saves_yaml(self, tmp_path: Path) -> None:
        """Should save data to YAML file."""
        yaml_file = tmp_path / "output.yaml"
        data = {"key": "value", "number": 42}

        save_yaml(yaml_file, data)

        assert yaml_file.exists()
        loaded = load_yaml(yaml_file)
        assert loaded == data

    def test_saves_nested_data(self, tmp_path: Path) -> None:
        """Should save nested data structures."""
        yaml_file = tmp_path / "nested.yaml"
        data = {"parent": {"child": "value", "list": [1, 2, 3]}}

        save_yaml(yaml_file, data)

        loaded = load_yaml(yaml_file)
        assert loaded == data


class TestGetCopierAnswers:
    """Tests for get_copier_answers function."""

    def test_loads_copier_answers(self, paracord_project: Path) -> None:
        """Should load copier answers from project directory."""
        answers = get_copier_answers(paracord_project)

        assert answers["_src_path"] == "gh:paracord-run/dash"
        assert answers["_commit"] == "abc12345"
        assert answers["project_name"] == "test-project"

    def test_returns_empty_when_no_answers_file(self, temp_dir: Path) -> None:
        """Should return empty dict when no .copier-answers.yml exists."""
        answers = get_copier_answers(temp_dir)

        assert answers == {}


class TestGetRavConfig:
    """Tests for get_rav_config function."""

    def test_loads_rav_config(self, paracord_project: Path) -> None:
        """Should load rav config from project directory."""
        config = get_rav_config(paracord_project)

        assert "scripts" in config
        assert "dev" in config["scripts"]
        assert "test" in config["scripts"]

    def test_returns_empty_when_no_config_file(self, temp_dir: Path) -> None:
        """Should return empty dict when no rav.yaml exists."""
        config = get_rav_config(temp_dir)

        assert config == {}


class TestGetTemplateInfo:
    """Tests for get_template_info function."""

    def test_extracts_template_info(self) -> None:
        """Should extract template source and commit from answers."""
        answers = {
            "_src_path": "gh:paracord-run/dash",
            "_commit": "abc12345",
            "project_name": "test",
        }

        source, commit = get_template_info(answers)

        assert source == "gh:paracord-run/dash"
        assert commit == "abc12345"

    def test_returns_none_for_missing_fields(self) -> None:
        """Should return None when fields are missing."""
        answers = {"project_name": "test"}

        source, commit = get_template_info(answers)

        assert source is None
        assert commit is None

    def test_handles_empty_answers(self) -> None:
        """Should handle empty answers dict."""
        source, commit = get_template_info({})

        assert source is None
        assert commit is None


class TestConstants:
    """Tests for module constants."""

    def test_copier_answers_filename(self) -> None:
        """Should have correct copier answers filename."""
        assert COPIER_ANSWERS_FILE == ".copier-answers.yml"

    def test_rav_config_filename(self) -> None:
        """Should have correct rav config filename."""
        assert RAV_CONFIG_FILE == "rav.yaml"

    def test_paracord_components_filename(self) -> None:
        """Should have correct paracord components filename."""
        assert PARACORD_COMPONENTS_FILE == ".paracord-components.yml"
