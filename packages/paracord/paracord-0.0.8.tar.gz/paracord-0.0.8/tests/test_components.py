"""Tests for paracord.core.components module."""

from pathlib import Path

import pytest

from paracord.core.components import (
    ComponentInfo,
    AppliedComponent,
    get_applied_components,
    save_applied_component,
    remove_applied_component,
    check_component_conflicts,
    check_component_dependencies,
    create_applied_component,
)
from paracord.utils.config import PARACORD_COMPONENTS_FILE


class TestComponentInfo:
    """Tests for ComponentInfo dataclass."""

    def test_creates_with_defaults(self) -> None:
        """Should create ComponentInfo with default values."""
        info = ComponentInfo(
            name="stripe",
            description="Stripe integration",
            version="1.0.0",
        )

        assert info.name == "stripe"
        assert info.description == "Stripe integration"
        assert info.version == "1.0.0"
        assert info.tags == []
        assert info.requires == []
        assert info.conflicts == []

    def test_creates_with_all_fields(self) -> None:
        """Should create ComponentInfo with all fields."""
        info = ComponentInfo(
            name="stripe",
            description="Stripe integration",
            version="1.0.0",
            tags=["payments"],
            requires=["auth"],
            conflicts=["braintree"],
        )

        assert info.tags == ["payments"]
        assert info.requires == ["auth"]
        assert info.conflicts == ["braintree"]


class TestAppliedComponent:
    """Tests for AppliedComponent dataclass."""

    def test_from_dict(self) -> None:
        """Should create AppliedComponent from dictionary."""
        data = {
            "version": "1.0.0",
            "commit": "abc1234",
            "source": "gh:paracord-run/library/stripe",
            "applied_at": "2024-01-15T10:30:00Z",
        }

        component = AppliedComponent.from_dict("stripe", data)

        assert component.name == "stripe"
        assert component.version == "1.0.0"
        assert component.commit == "abc1234"
        assert component.source == "gh:paracord-run/library/stripe"
        assert component.applied_at == "2024-01-15T10:30:00Z"

    def test_from_dict_with_missing_fields(self) -> None:
        """Should handle missing fields with defaults."""
        data = {}

        component = AppliedComponent.from_dict("stripe", data)

        assert component.name == "stripe"
        assert component.version == "unknown"
        assert component.commit == "unknown"

    def test_to_dict(self) -> None:
        """Should convert AppliedComponent to dictionary."""
        component = AppliedComponent(
            name="stripe",
            version="1.0.0",
            commit="abc1234",
            source="gh:paracord-run/library/stripe",
            applied_at="2024-01-15T10:30:00Z",
        )

        result = component.to_dict()

        assert result == {
            "version": "1.0.0",
            "commit": "abc1234",
            "source": "gh:paracord-run/library/stripe",
            "applied_at": "2024-01-15T10:30:00Z",
        }


class TestGetAppliedComponents:
    """Tests for get_applied_components function."""

    def test_returns_empty_when_no_file(self, tmp_path: Path) -> None:
        """Should return empty dict when file doesn't exist."""
        result = get_applied_components(tmp_path)

        assert result == {}

    def test_loads_components_from_file(self, tmp_path: Path) -> None:
        """Should load components from .paracord-components.yml."""
        components_file = tmp_path / PARACORD_COMPONENTS_FILE
        components_file.write_text(
            """components:
  stripe:
    version: "1.0.0"
    commit: "abc1234"
    source: "gh:paracord-run/library/stripe"
    applied_at: "2024-01-15T10:30:00Z"
"""
        )

        result = get_applied_components(tmp_path)

        assert "stripe" in result
        assert result["stripe"].version == "1.0.0"
        assert result["stripe"].commit == "abc1234"

    def test_loads_multiple_components(self, tmp_path: Path) -> None:
        """Should load multiple components."""
        components_file = tmp_path / PARACORD_COMPONENTS_FILE
        components_file.write_text(
            """components:
  stripe:
    version: "1.0.0"
    commit: "abc1234"
    source: "gh:paracord-run/library/stripe"
    applied_at: "2024-01-15T10:30:00Z"
  celery:
    version: "2.0.0"
    commit: "def5678"
    source: "gh:paracord-run/library/celery"
    applied_at: "2024-01-16T11:00:00Z"
"""
        )

        result = get_applied_components(tmp_path)

        assert len(result) == 2
        assert "stripe" in result
        assert "celery" in result


class TestSaveAppliedComponent:
    """Tests for save_applied_component function."""

    def test_creates_new_file(self, tmp_path: Path) -> None:
        """Should create file when it doesn't exist."""
        component = AppliedComponent(
            name="stripe",
            version="1.0.0",
            commit="abc1234",
            source="gh:paracord-run/library/stripe",
            applied_at="2024-01-15T10:30:00Z",
        )

        save_applied_component(tmp_path, component)

        components_file = tmp_path / PARACORD_COMPONENTS_FILE
        assert components_file.exists()

        # Verify by reading back
        loaded = get_applied_components(tmp_path)
        assert "stripe" in loaded
        assert loaded["stripe"].version == "1.0.0"

    def test_appends_to_existing_file(self, tmp_path: Path) -> None:
        """Should add component to existing file."""
        # Create initial file
        components_file = tmp_path / PARACORD_COMPONENTS_FILE
        components_file.write_text(
            """components:
  celery:
    version: "2.0.0"
    commit: "def5678"
    source: "gh:paracord-run/library/celery"
    applied_at: "2024-01-16T11:00:00Z"
"""
        )

        # Add new component
        component = AppliedComponent(
            name="stripe",
            version="1.0.0",
            commit="abc1234",
            source="gh:paracord-run/library/stripe",
            applied_at="2024-01-15T10:30:00Z",
        )
        save_applied_component(tmp_path, component)

        # Verify both are present
        loaded = get_applied_components(tmp_path)
        assert len(loaded) == 2
        assert "stripe" in loaded
        assert "celery" in loaded

    def test_updates_existing_component(self, tmp_path: Path) -> None:
        """Should update existing component."""
        # Create initial file
        components_file = tmp_path / PARACORD_COMPONENTS_FILE
        components_file.write_text(
            """components:
  stripe:
    version: "1.0.0"
    commit: "abc1234"
    source: "gh:paracord-run/library/stripe"
    applied_at: "2024-01-15T10:30:00Z"
"""
        )

        # Update component
        component = AppliedComponent(
            name="stripe",
            version="2.0.0",
            commit="xyz9999",
            source="gh:paracord-run/library/stripe",
            applied_at="2024-01-20T12:00:00Z",
        )
        save_applied_component(tmp_path, component)

        # Verify update
        loaded = get_applied_components(tmp_path)
        assert len(loaded) == 1
        assert loaded["stripe"].version == "2.0.0"
        assert loaded["stripe"].commit == "xyz9999"


class TestRemoveAppliedComponent:
    """Tests for remove_applied_component function."""

    def test_removes_component(self, tmp_path: Path) -> None:
        """Should remove a component from file."""
        components_file = tmp_path / PARACORD_COMPONENTS_FILE
        components_file.write_text(
            """components:
  stripe:
    version: "1.0.0"
    commit: "abc1234"
    source: "gh:paracord-run/library/stripe"
    applied_at: "2024-01-15T10:30:00Z"
  celery:
    version: "2.0.0"
    commit: "def5678"
    source: "gh:paracord-run/library/celery"
    applied_at: "2024-01-16T11:00:00Z"
"""
        )

        result = remove_applied_component(tmp_path, "stripe")

        assert result is True
        loaded = get_applied_components(tmp_path)
        assert len(loaded) == 1
        assert "stripe" not in loaded
        assert "celery" in loaded

    def test_returns_false_for_nonexistent(self, tmp_path: Path) -> None:
        """Should return False when component doesn't exist."""
        result = remove_applied_component(tmp_path, "stripe")

        assert result is False


class TestCheckComponentConflicts:
    """Tests for check_component_conflicts function."""

    def test_no_conflicts(self, tmp_path: Path) -> None:
        """Should return empty list when no conflicts."""
        info = ComponentInfo(
            name="stripe",
            description="Stripe",
            version="1.0.0",
            conflicts=["braintree"],
        )

        result = check_component_conflicts(tmp_path, info)

        assert result == []

    def test_detects_conflicts(self, tmp_path: Path) -> None:
        """Should detect conflicting components."""
        # Add conflicting component
        components_file = tmp_path / PARACORD_COMPONENTS_FILE
        components_file.write_text(
            """components:
  braintree:
    version: "1.0.0"
    commit: "abc1234"
    source: "gh:paracord-run/library/braintree"
    applied_at: "2024-01-15T10:30:00Z"
"""
        )

        info = ComponentInfo(
            name="stripe",
            description="Stripe",
            version="1.0.0",
            conflicts=["braintree"],
        )

        result = check_component_conflicts(tmp_path, info)

        assert result == ["braintree"]


class TestCheckComponentDependencies:
    """Tests for check_component_dependencies function."""

    def test_no_missing_deps(self, tmp_path: Path) -> None:
        """Should return empty list when all deps exist."""
        # Add required component
        components_file = tmp_path / PARACORD_COMPONENTS_FILE
        components_file.write_text(
            """components:
  auth:
    version: "1.0.0"
    commit: "abc1234"
    source: "gh:paracord-run/library/auth"
    applied_at: "2024-01-15T10:30:00Z"
"""
        )

        info = ComponentInfo(
            name="stripe",
            description="Stripe",
            version="1.0.0",
            requires=["auth"],
        )

        result = check_component_dependencies(tmp_path, info)

        assert result == []

    def test_detects_missing_deps(self, tmp_path: Path) -> None:
        """Should detect missing dependencies."""
        info = ComponentInfo(
            name="stripe",
            description="Stripe",
            version="1.0.0",
            requires=["auth", "celery"],
        )

        result = check_component_dependencies(tmp_path, info)

        assert result == ["auth", "celery"]


class TestCreateAppliedComponent:
    """Tests for create_applied_component function."""

    def test_creates_with_timestamp(self) -> None:
        """Should create component with current timestamp."""
        component = create_applied_component(
            name="stripe",
            version="1.0.0",
            commit="abc1234",
            source="gh:paracord-run/library/stripe",
        )

        assert component.name == "stripe"
        assert component.version == "1.0.0"
        assert component.commit == "abc1234"
        assert component.source == "gh:paracord-run/library/stripe"
        assert component.applied_at.endswith("Z")  # ISO format with Z
