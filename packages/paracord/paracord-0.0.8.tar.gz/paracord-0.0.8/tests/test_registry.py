"""Tests for paracord.core.registry module."""

import pytest

from paracord.core.registry import (
    ComponentRegistry,
    get_component_source,
    COMPONENT_LIBRARY_REPO,
)


class TestComponentRegistry:
    """Tests for ComponentRegistry dataclass."""

    def test_from_dict_empty(self) -> None:
        """Should handle empty registry data."""
        data = {}

        registry = ComponentRegistry.from_dict(data)

        assert registry.version == "1.0"
        assert registry.components == {}

    def test_from_dict_with_components(self) -> None:
        """Should parse components from registry data."""
        data = {
            "version": "1.1",
            "components": {
                "stripe": {
                    "description": "Stripe payment integration",
                    "version": "1.0.0",
                    "tags": ["payments"],
                    "requires": [],
                    "conflicts": ["braintree"],
                },
                "celery": {
                    "description": "Celery task queue",
                    "version": "2.0.0",
                    "tags": ["async", "tasks"],
                    "requires": [],
                    "conflicts": [],
                },
            },
        }

        registry = ComponentRegistry.from_dict(data)

        assert registry.version == "1.1"
        assert len(registry.components) == 2
        assert "stripe" in registry.components
        assert "celery" in registry.components

        stripe = registry.components["stripe"]
        assert stripe.name == "stripe"
        assert stripe.description == "Stripe payment integration"
        assert stripe.version == "1.0.0"
        assert stripe.tags == ["payments"]
        assert stripe.conflicts == ["braintree"]

    def test_from_dict_with_defaults(self) -> None:
        """Should use defaults for missing component fields."""
        data = {
            "components": {
                "minimal": {
                    "description": "Minimal component",
                },
            },
        }

        registry = ComponentRegistry.from_dict(data)

        component = registry.components["minimal"]
        assert component.version == "1.0.0"
        assert component.tags == []
        assert component.requires == []
        assert component.conflicts == []


class TestGetComponentSource:
    """Tests for get_component_source function."""

    def test_returns_correct_source(self) -> None:
        """Should return the correct copier source path."""
        result = get_component_source("stripe")

        assert result == f"{COMPONENT_LIBRARY_REPO}/stripe"

    def test_works_with_any_component_name(self) -> None:
        """Should work with any component name."""
        result = get_component_source("my-custom-component")

        assert result == f"{COMPONENT_LIBRARY_REPO}/my-custom-component"


class TestConstants:
    """Tests for module constants."""

    def test_component_library_repo(self) -> None:
        """Should have correct component library repo."""
        assert COMPONENT_LIBRARY_REPO == "gh:paracord-run/library"
