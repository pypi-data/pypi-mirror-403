# ----------------------------------------------------------------------------
# Description    : Test mixins
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2025)
# ----------------------------------------------------------------------------
"""
Tests for ParentAttributeRegistrationMixin class.

This module tests the parent attribute registration functionality,
including basic registration, index binding, renaming, and batch operations.
"""

import pytest

from qblox_instruments.qcodes_drivers.registration_mixin import ParentAttributeRegistrationMixin


class MockParent:
    """Mock parent class for testing registration."""

    name = "mock_parent"

    def existing_method(self, value: int) -> int:
        """An existing method in the parent."""
        return value * 2

    def another_method(self, x: int, y: int) -> int:
        """Another method for testing."""
        return x + y


class SimpleComponent(ParentAttributeRegistrationMixin):
    """Simple child class for basic registration tests with index."""

    def __init__(self, parent, some_index) -> None:
        self._index = some_index
        self.parent = parent
        self._register_all_required_attrs(self._get_required_parent_attr_names())

    def _get_bind_index(self) -> None:
        return self._index

    def _get_required_parent_attr_names(self) -> list[str]:
        return [
            "another_method",
        ]


class ConditionalComponent(ParentAttributeRegistrationMixin):
    """Component to showcase conditional Registration with no index."""

    def __init__(self, parent) -> None:
        self.parent = parent
        self._register("existing_method")

    def _get_required_parent_attr_names(self) -> list[str]:
        return ["existing_method"]


def test_simple_register_existing_attribute():
    """Test registering an attribute that exists in parent."""
    parent = MockParent()
    child = SimpleComponent(parent, 0)

    child._register("existing_method")

    # Verify the attribute was registered
    assert hasattr(child, "another_method")
    assert callable(child.another_method)
    assert parent.another_method.__doc__ in child.another_method.__doc__

    # Call the registered method
    result = child.another_method(5)
    assert result == 5  # 5 + 0


def test_conditional_register_existing_attribute():
    """Test registering an attribute that exists in parent."""
    parent = MockParent()
    child = ConditionalComponent(parent)

    child._register("existing_method")

    # Verify the attribute was registered
    assert hasattr(child, "existing_method")
    assert callable(child.existing_method)
    assert parent.existing_method.__doc__ in child.existing_method.__doc__

    # Call the registered method
    result = child.existing_method(5)
    assert result == 10  # 5 * 2


def test_nonexistent_attribute_raises_not_implemented():
    """Test that calling a nonexistent registered attribute raises NotImplementedError."""
    parent = MockParent()
    child = SimpleComponent(parent, 0)

    child._register("nonexistent_method")

    # Calling should raise NotImplementedError
    with pytest.raises(NotImplementedError) as exc_info:
        child.nonexistent_method()

    assert "nonexistent_method" in str(exc_info.value)
    assert parent.name in str(exc_info.value)
