# ----------------------------------------------------------------------------
# Description    : Parent Attribute Registration Mixin
# Git repository : https://gitlab.com/qblox/packages/software/qblox_instruments.git
# Copyright (C) Qblox BV (2025)
# ----------------------------------------------------------------------------


from typing import Optional

from qblox_instruments.docstring_helpers import partial_with_numpy_doc


class ParentAttributeRegistrationMixin:
    """
    Mixin class that provides parent attribute registration functionality.

    This mixin allows child components to register parent attributes as their own
    using functools.partial, enabling delegation of functionality from parent to child.

    Subclasses can use one of two patterns:

    **Pattern 1 (e.g. IOChannelQSM) - Simple (for uniform registration):**
        - Implement `_get_required_parent_attr_names()` to return list of attributes
        - Optionally implement `_get_bind_index()` if index binding is needed (like slot index)
        - Call `_register_all_required_attrs()` in `__init__`

    **Pattern 2 (e.g. Module) - Complex (for conditional registration):**
        - Implement `_get_bind_index()` if index binding is needed
        - Call `_register()` directly for each attribute with conditional logic in `__init__`
        - No need to implement `_get_required_parent_attr_names()`
    """

    def _register(
        self,
        attr_name: str,
        bind_index: Optional[int] = None,
        new_name: Optional[str] = None,
    ) -> None:
        """
        Register parent attribute to this component using functools.partial.

        If the attribute does not exist in the parent class, a method that raises
        a `NotImplementedError` exception is registered instead. The docstring of
        the parent attribute is also copied to the registered attribute.

        Parameters
        ----------
        attr_name : str
            Attribute name of parent to register.
        bind_index : Optional[int]
            Index to bind to the parent method (e.g., io_channel_idx, slot_idx, quad_idx).
            If None, attempts to use `_get_bind_index()` if implemented.
            If `_get_bind_index()` is not implemented, no index is bound.
        new_name : Optional[str]
            If provided, registers the attribute with this new name instead of attr_name.
            Useful for exposing internal methods as public API.

        """
        # If bind_index not explicitly provided, try to get it from _get_bind_index()
        if bind_index is None and hasattr(self, "_get_bind_index"):
            bind_index = self._get_bind_index()

        # Register with original or new name
        target_name = new_name or attr_name

        if hasattr(self.parent, attr_name):
            parent_attr = getattr(self.parent, attr_name)

            # Standard documentation
            partial_doc = (
                f"Note\n----------\nThis method calls {type(self.parent).__name__}.{attr_name} \
                    using functools.partial"
            )

            # Bind index if provided
            if bind_index is not None:
                partial_func = partial_with_numpy_doc(parent_attr, bind_index, end_with=partial_doc)
            else:
                partial_func = partial_with_numpy_doc(parent_attr, end_with=partial_doc)

            setattr(self, target_name, partial_func)
        else:

            def raise_not_implemented_error(*args, **kwargs) -> None:
                raise NotImplementedError(
                    f'{self.parent.name} does not have "{attr_name}" attribute.'
                )

            setattr(self, target_name, raise_not_implemented_error)

    def _register_all_required_attrs(self, attr_names: list[str]) -> None:
        """
        Register all required parent attributes.

        This is a convenience method for simple cases where all instances
        need the same attributes. Classes with conditional registration
        (like Module) should call `_register()` directly instead.

        Parameters
        ----------
        attr_names : list[str]
            List of parent attribute names to register.

        """
        for attr_name in attr_names:
            # _register will automatically use _get_bind_index() if available
            self._register(attr_name)

    def _get_bind_index(self) -> Optional[int]:
        """
        Override this function depending on the needs of the respective component.
        """
        return None
